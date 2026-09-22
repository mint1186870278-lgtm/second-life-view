"""Small Tripo V3 HTTP adapter for object-level reconstruction.

Tripo is intentionally separate from Aholo World: it takes one object image
or 2-4 views of the same object, while World handles room-scale video/INSV or
20+ overlapping perspective images.
"""
from __future__ import annotations

import asyncio
from typing import Any

import httpx

from spatial_agent.config import Settings


class TripoClient:
    def __init__(self, settings: Settings):
        self.settings = settings

    @property
    def enabled(self) -> bool:
        return bool(self.settings.tripo_api_key and self.settings.use_external_tools)

    @property
    def base_url(self) -> str:
        return self.settings.tripo_base_url.rstrip("/")

    def _headers(self) -> dict[str, str]:
        return {
            "Authorization": f"Bearer {self.settings.tripo_api_key}",
            "Content-Type": "application/json",
        }

    async def image_to_model(
        self,
        image_urls: list[str],
        *,
        model: str = "tripo-v3.1",
        wait: bool = False,
    ) -> dict[str, Any]:
        if not image_urls:
            raise ValueError("at least one object image URL is required")
        if len(image_urls) > 4:
            raise ValueError("Tripo accepts one image or at most four object views")
        if not all(url.startswith(("http://", "https://")) for url in image_urls):
            raise ValueError("Tripo input must be an HTTP(S) URL; upload local files to OSS first")
        if not self.enabled:
            return {
                "status": "mock",
                "provider": "tripo",
                "model": model,
                "input_count": len(image_urls),
                "message": "Set TRIPO_API_KEY and USE_EXTERNAL_TOOLS=true to submit Tripo V3.",
            }
        endpoint = "/generation/image-to-model" if len(image_urls) == 1 else "/generation/multiview-to-model"
        payload: dict[str, Any] = {"model": model, "texture": True, "pbr": True}
        if len(image_urls) == 1:
            payload["input"] = image_urls[0]
        else:
            # The API's recommended format is keyed canonical views.  For a
            # two-view call front + left is enough; callers should preserve
            # their own view order when more images are supplied.
            names = ("front", "left", "back", "right")
            payload["inputs"] = [{names[i]: url} for i, url in enumerate(image_urls)]
        async with httpx.AsyncClient(timeout=90, trust_env=False) as client:
            response = await client.post(f"{self.base_url}{endpoint}", headers=self._headers(), json=payload)
            response.raise_for_status()
            data = response.json()
        task_id = self._task_id(data)
        result = {"status": "submitted", "provider": "tripo", "model": model, "task_id": task_id, "response": data}
        if wait and task_id:
            result["task"] = await self.wait(task_id)
        return result

    @staticmethod
    def _task_id(data: dict[str, Any]) -> str | None:
        nested = data.get("data") if isinstance(data, dict) else None
        value = nested.get("task_id") if isinstance(nested, dict) else None
        return str(value) if value else None

    async def get(self, task_id: str) -> dict[str, Any]:
        if not task_id:
            raise ValueError("task_id is required")
        if not self.enabled:
            return {"status": "mock", "provider": "tripo", "task_id": task_id}
        async with httpx.AsyncClient(timeout=60, trust_env=False) as client:
            response = await client.get(f"{self.base_url}/tasks/{task_id}", headers=self._headers())
            response.raise_for_status()
            return response.json()

    async def wait(self, task_id: str, attempts: int = 150, interval: float = 2.0) -> dict[str, Any]:
        terminal = {"success", "failed", "cancelled", "banned", "succeeded"}
        for index in range(attempts):
            result = await self.get(task_id)
            data = result.get("data") if isinstance(result, dict) else {}
            status = str((data or {}).get("status") or result.get("status") or "").lower()
            if status in terminal:
                return result
            if index + 1 < attempts:
                await asyncio.sleep(interval)
        raise TimeoutError(f"Tripo task {task_id} did not finish")
