"""Domestic Aholo Lux3D adapter using the installed lux3d-cn Skill client.

This adapter is deliberately explicit about the mainland endpoint and region:
Lux3D China and international credentials are not interchangeable.
"""
from __future__ import annotations

import asyncio
import importlib.util
import os
from pathlib import Path
from typing import Any

from spatial_agent.config import Settings

SKILL_CLIENT = Path.home() / ".codex/skills/lux3d-cn/lux3d_client.py"
CN_BASE_URL = "https://api.aholo3d.cn"


class Lux3DClient:
    def __init__(self, settings: Settings):
        self.settings = settings
        self._module: Any = None

    @property
    def enabled(self) -> bool:
        return bool(self.settings.lux3d_api_key and self.settings.use_external_tools)

    def _load(self) -> Any:
        if self._module is None:
            if not SKILL_CLIENT.exists():
                raise RuntimeError(f"Lux3D Skill client not found: {SKILL_CLIENT}")
            spec = importlib.util.spec_from_file_location("lux3d_cn_client", SKILL_CLIENT)
            if spec is None or spec.loader is None:
                raise RuntimeError(f"Unable to load Lux3D Skill client: {SKILL_CLIENT}")
            module = importlib.util.module_from_spec(spec)
            spec.loader.exec_module(module)
            self._module = module
        return self._module

    async def image_to_3d(
        self,
        image_urls: list[str],
        version: str = "G1-Turbo",
        wait: bool = False,
    ) -> dict[str, Any]:
        if not image_urls:
            raise ValueError("At least one publicly reachable image URL is required")
        if version not in {"G1", "G1-Turbo"}:
            raise ValueError("version must be G1 or G1-Turbo")
        if not self.enabled:
            return {
                "status": "mock",
                "region": "cn",
                "version": version,
                "task_id": "mock-lux3d-task",
                "message": "Set LUX3D_API_KEY and USE_EXTERNAL_TOOLS=true to submit a domestic Lux3D task.",
            }

        # The Skill client reads its key and region from process environment.
        # Force the mainland endpoint to prevent accidental international-key
        # mixing when this service shares a shell with another deployment.
        os.environ["LUX3D_API_KEY"] = self.settings.lux3d_api_key
        os.environ["LUX3D_REGION"] = "cn"
        os.environ["LUX3D_BASE_URL"] = CN_BASE_URL
        module = self._load()
        kwargs = {
            "version": version,
            "region": "cn",
            "base_url": CN_BASE_URL,
            "outputFormat": ["glb"],
        }
        if len(image_urls) == 1:
            task_id = await asyncio.to_thread(module.create_image_to_3d_task, img=image_urls[0], **kwargs)
        else:
            task_id = await asyncio.to_thread(module.create_image_to_3d_task, imgs=image_urls, **kwargs)
        result: dict[str, Any] = {
            "status": "submitted",
            "region": "cn",
            "version": version,
            "task_id": task_id,
        }
        if wait:
            result["task"] = await asyncio.to_thread(
                module.query_task_status,
                task_id,
                base_url=CN_BASE_URL,
                region="cn",
                max_attempts=1,
                interval=0,
            )
        return result

    async def get_task(self, task_id: str) -> dict[str, Any]:
        """Query one Lux3D task using the installed domestic Skill client."""
        if not task_id:
            raise ValueError("task_id is required")
        if not self.enabled:
            return {
                "status": "mock",
                "region": "cn",
                "task_id": task_id,
                "message": "Set LUX3D_API_KEY and USE_EXTERNAL_TOOLS=true to query a domestic Lux3D task.",
            }
        os.environ["LUX3D_API_KEY"] = self.settings.lux3d_api_key
        os.environ["LUX3D_REGION"] = "cn"
        os.environ["LUX3D_BASE_URL"] = CN_BASE_URL
        module = self._load()
        return await asyncio.to_thread(
            module.get_task,
            task_id,
            base_url=CN_BASE_URL,
            region="cn",
        )
