"""Bailian adapters. They are deliberately optional: the demo remains runnable offline."""
from __future__ import annotations
import base64
import json
from pathlib import Path
from typing import Any
import httpx
from spatial_agent.config import Settings

class BailianClient:
    def __init__(self, settings: Settings):
        self.settings = settings

    @property
    def enabled(self) -> bool:
        return bool(self.settings.dashscope_api_key and self.settings.use_llm)

    async def chat(self, messages: list[dict[str, Any]], *, vision: bool = False, json_mode: bool = True) -> dict[str, Any]:
        if not self.enabled:
            raise RuntimeError("Bailian is disabled; set DASHSCOPE_API_KEY and USE_LLM=true")
        model = self.settings.dashscope_vision_model if vision else self.settings.dashscope_text_model
        payload: dict[str, Any] = {"model": model, "messages": messages, "temperature": 0.2}
        if json_mode:
            payload["response_format"] = {"type": "json_object"}
        headers = {"Authorization": f"Bearer {self.settings.dashscope_api_key}", "Content-Type": "application/json"}
        async with httpx.AsyncClient(timeout=self.settings.dashscope_chat_timeout, trust_env=False) as client:
            response = await client.post(f"{self.settings.dashscope_base_url.rstrip('/')}/chat/completions", headers=headers, json=payload)
            response.raise_for_status()
            data = response.json()
        content = data.get("choices", [{}])[0].get("message", {}).get("content", "")
        if isinstance(content, list):
            content = "".join(part.get("text", "") for part in content if isinstance(part, dict))
        if json_mode:
            try:
                return json.loads(content)
            except json.JSONDecodeError:
                return {"raw": content}
        return {"text": content}

    @staticmethod
    def _image_reference(image_url: str) -> str:
        """Convert TAY-LI local fixture paths to a compact vision data URL."""
        if image_url.startswith(("http://", "https://", "data:")):
            return image_url
        path = Path(image_url)
        if not path.is_absolute():
            path = Path.cwd() / path
        if not path.exists():
            return image_url
        try:
            import cv2
            image = cv2.imread(str(path))
            if image is None:
                return image_url
            height, width = image.shape[:2]
            scale = min(1.0, 768.0 / max(width, height))
            if scale < 1.0:
                image = cv2.resize(image, (int(width * scale), int(height * scale)))
            ok, encoded = cv2.imencode(".jpg", image, [int(cv2.IMWRITE_JPEG_QUALITY), 60])
            if not ok:
                return image_url
            return "data:image/jpeg;base64," + base64.b64encode(encoded.tobytes()).decode("ascii")
        except Exception:
            return image_url

    async def inspect_space(self, image_url: str, detections: list[dict[str, Any]], goal: str) -> dict[str, Any]:
        image_reference = self._image_reference(image_url)
        prompt = {
            "role": "user",
            "content": [
                {"type": "text", "text": (
                    "你是建筑改造空间感知专家。根据全景图和YOLO检测结果，返回JSON数组 objects。"
                    "每个对象包含 detection_index, material, condition, reuse_potential, confidence, missing_fields。"
                    f"用户目标：{goal}；检测：{json.dumps(detections, ensure_ascii=False)}"
                )},
                {"type": "image_url", "image_url": {"url": image_reference}},
            ],
        }
        result = await self.chat([{"role": "system", "content": "只输出可解析JSON。"}, prompt], vision=True)
        # Qwen occasionally follows the prompt literally and returns a JSON
        # array instead of the documented object wrapper. Normalize both
        # shapes so the graph can still align results with detections.
        if isinstance(result, list):
            return {"objects": result}
        if not isinstance(result, dict):
            return {"objects": [], "raw": result}
        if "objects" not in result and all(isinstance(v, dict) for v in result.values()):
            return {"objects": list(result.values()), "raw": result}
        return result

    async def generate_image(self, prompt: str, reference_image_url: str | None = None) -> dict[str, Any]:
        """Call a DashScope image endpoint when configured; otherwise return a traceable mock."""
        if not (self.settings.dashscope_api_key and self.settings.use_external_tools):
            return {"status": "mock", "image_url": None, "prompt": prompt}
        # qwen-image uses the multimodal-generation messages schema. The
        # synchronous response is the compatibility default for this account;
        # async remains an explicit opt-in below.
        endpoint = self.settings.dashscope_image_api_host.rstrip("/") + "/api/v1/services/aigc/multimodal-generation/generation"
        content: list[dict[str, str]] = [{"text": prompt}]
        if reference_image_url:
            content.append({"image": self._image_reference(reference_image_url)})
        payload: dict[str, Any] = {
            "model": self.settings.dashscope_image_model,
            "input": {"messages": [{"role": "user", "content": content}]},
            # Match the official multimodal-generation example.  ``size`` is
            # optional and is omitted because some workspaces reject it for
            # qwen-image-3.0-pro.
            "parameters": {"prompt_extend": True},
        }
        headers = {"Authorization": f"Bearer {self.settings.dashscope_api_key}", "Content-Type": "application/json"}
        if self.settings.dashscope_image_async:
            headers["X-DashScope-Async"] = "enable"
        async with httpx.AsyncClient(timeout=self.settings.dashscope_image_timeout, trust_env=False) as client:
            response = await client.post(endpoint, headers=headers, json=payload)
            try:
                response.raise_for_status()
            except httpx.HTTPStatusError as exc:
                detail = response.text[:500]
                raise RuntimeError(f"Bailian image request failed ({response.status_code}): {detail}") from exc
            result = response.json()
            # qwen-image-3.0-pro synchronous responses place the generated
            # image under output.choices[0].message.content[*].image. Keep
            # the raw response for provenance but expose a stable image_url
            # for DesignProposal and API clients.
            image_url = self._extract_generated_image_url(result)
            if image_url:
                result["image_url"] = image_url
            return result

    @staticmethod
    def _extract_generated_image_url(result: dict[str, Any]) -> str | None:
        output = result.get("output") if isinstance(result, dict) else None
        if not isinstance(output, dict):
            return None
        choices = output.get("choices") or []
        for choice in choices if isinstance(choices, list) else []:
            message = choice.get("message") if isinstance(choice, dict) else None
            content = message.get("content") if isinstance(message, dict) else None
            for part in content if isinstance(content, list) else []:
                if not isinstance(part, dict):
                    continue
                candidate = part.get("image") or part.get("image_url") or part.get("url")
                if isinstance(candidate, dict):
                    candidate = candidate.get("url")
                if isinstance(candidate, str) and candidate.startswith(("http://", "https://")):
                    return candidate
        # Some gateway versions return the image in output.results.
        results = output.get("results")
        if isinstance(results, list) and results:
            first = results[0] if isinstance(results[0], dict) else {}
            candidate = first.get("url") or first.get("image")
            if isinstance(candidate, str):
                return candidate
        return None
