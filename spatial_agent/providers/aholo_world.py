"""Aholo World (3DGS) domestic REST adapter.

Lux3D is for an object/model from one image. World is the separate Aholo
service for an indoor scene, an INSV, video, or a multi-image reconstruction.
The OpenAPI gateway requires the API key without a Bearer prefix.
"""
from __future__ import annotations
import asyncio
from typing import Any
import httpx
from spatial_agent.config import Settings

TERMINAL = {"SUCCEEDED", "FAILED", "CANCELED", "TIMEOUT", "REJECTED"}

class AholoWorldClient:
    def __init__(self, settings: Settings):
        self.settings = settings

    @property
    def enabled(self) -> bool:
        return bool(self.settings.aholo_api_key and self.settings.use_external_tools)

    @property
    def base_url(self) -> str:
        # World and Lux3D must stay on the China gateway for this deployment.
        return "https://api.aholo3d.cn"

    def _headers(self) -> dict[str, str]:
        return {"Authorization": self.settings.aholo_api_key, "Content-Type": "application/json"}

    @staticmethod
    def _world_id(data: dict[str, Any]) -> str | None:
        for key in ("worldId", "world_id", "id"):
            if data.get(key): return str(data[key])
        for key in ("d", "data", "result", "output"):
            nested = data.get(key)
            if isinstance(nested, dict):
                found = AholoWorldClient._world_id(nested)
                if found: return found
        return None

    @staticmethod
    def _resource_type(url: str) -> str:
        path = url.lower().split("?", 1)[0]
        if path.endswith(".insv"): return "insv"
        if path.endswith((".mp4", ".mov")): return "video"
        return "image"

    @classmethod
    def validate_resources(cls, urls: list[str]) -> list[dict[str, str]]:
        if not urls: raise ValueError("at least one World resource URL is required")
        resources = [{"url": url, "type": cls._resource_type(url)} for url in urls]
        kinds = {item["type"] for item in resources}
        if kinds == {"image"} and len(resources) < 20:
            raise ValueError("Aholo World image reconstruction requires at least 20 images; use an .insv/.mp4 or provide more views")
        if len(kinds) > 1:
            raise ValueError("World reconstruction resources must use one resource type")
        return resources

    async def upload_local_file(self, path: str) -> str:
        """Upload a local frame/INSV through the official domestic Asset SDK.

        World rejects arbitrary public URLs for resources; they must first be
        uploaded through Aholo Asset and then referenced by the returned CDN URL.
        """
        if not self.enabled:
            raise RuntimeError("Set AHOLO_API_KEY and USE_EXTERNAL_TOOLS=true before uploading")
        import os
        os.environ["AHOLO_API_KEY"] = self.settings.aholo_api_key
        try:
            from manycore.aholo_sdk_asset import create_asset_client
            from manycore.aholo_sdk_core import AholoClientConfig
        except ImportError as exc:
            raise RuntimeError("Install manycore-aholo-sdk-asset to upload local Aholo assets") from exc
        client = create_asset_client(AholoClientConfig(api_key=self.settings.aholo_api_key, region="cn"))
        result = await asyncio.to_thread(client.upload_file, path)
        return result.url

    async def reconstruct(self, urls: list[str], *, name: str = "Insta360 空间重建", quality: str = "low", wait: bool = False) -> dict[str, Any]:
        resources = self.validate_resources(urls)
        if quality not in {"low", "normal", "high"}: raise ValueError("quality must be low, normal or high")
        if not self.enabled:
            return {"status": "mock", "region": "cn", "scene": "space", "resources": resources, "message": "Set AHOLO_API_KEY and USE_EXTERNAL_TOOLS=true to submit Aholo World 3DGS."}
        payload = {"name": name, "resources": resources, "taskQuality": quality, "scene": "space"}
        async with httpx.AsyncClient(timeout=90, trust_env=False) as client:
            response = await client.post(f"{self.base_url}/world/v1/reconstructions", headers=self._headers(), json=payload)
            response.raise_for_status(); data = response.json()
            world_id = self._world_id(data)
            result = {"status": "submitted", "region": "cn", "scene": "space", "world_id": world_id, "response": data}
            if wait and world_id:
                result["world"] = await self.wait(world_id)
            return result

    async def world_status(self, world_id: str) -> dict[str, Any]:
        """Alias used by API clients for the asynchronous 3DGS world job."""
        return await self.get(world_id)

    async def generate(self, prompt: str, image_url: str | None = None, *, name: str = "空间改造生成") -> dict[str, Any]:
        if not prompt and not image_url: raise ValueError("prompt or image_url is required")
        if not self.enabled:
            return {"status": "mock", "region": "cn", "scene": "space", "message": "Set AHOLO_API_KEY and USE_EXTERNAL_TOOLS=true to submit Aholo World generation."}
        resources = [{"url": image_url, "type": "image"}] if image_url else None
        payload: dict[str, Any] = {"name": name, "prompt": prompt}
        if resources: payload["resources"] = resources
        async with httpx.AsyncClient(timeout=90, trust_env=False) as client:
            response = await client.post(f"{self.base_url}/world/v1/generations", headers=self._headers(), json=payload)
            response.raise_for_status(); data = response.json()
            return {"status": "submitted", "region": "cn", "scene": "space", "world_id": self._world_id(data), "response": data}

    async def get(self, world_id: str) -> dict[str, Any]:
        if not world_id: raise ValueError("world_id is required")
        if not self.enabled: return {"status": "mock", "world_id": world_id}
        async with httpx.AsyncClient(timeout=60, trust_env=False) as client:
            response = await client.get(f"{self.base_url}/world/v1/{world_id}", headers=self._headers())
            response.raise_for_status(); return response.json()

    async def wait(self, world_id: str, attempts: int = 60, interval: float = 10) -> dict[str, Any]:
        for index in range(attempts):
            result = await self.get(world_id)
            status = result.get("status") or result.get("data", {}).get("status")
            if status in TERMINAL: return result
            if index + 1 < attempts: await asyncio.sleep(interval)
        raise TimeoutError(f"Aholo World task {world_id} did not finish")
