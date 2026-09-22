"""Stage 3: semantic enrichment on a detector crop.

The vision-language model fills material, visible condition, and a damage clue.
It must not decide a Second Life pathway. Unknown stays null.
"""

from __future__ import annotations

import base64
import json
import os
import re

import cv2
import numpy as np

from pipeline.env import load_dotenv

load_dotenv()


PROMPT = """Look at this cropped indoor object.
Return only a JSON object with these keys:
- material: short lowercase word such as timber, metal, glass, plastic, fabric, composite, or null
- visible_condition: apparently_intact, worn, or damaged, or null
- visible_damage_clue: a short visible clue, or null
If you cannot tell, use null. Do not guess.
Do not say the object is reusable, recyclable, safe, certified, compliant, or structurally sound.
Do not choose a reuse pathway.
"""


def crop_box(image_bgr: np.ndarray, bbox_xyxy: list[float], pad: int = 8) -> np.ndarray:
    height, width = image_bgr.shape[:2]
    x1, y1, x2, y2 = [int(round(v)) for v in bbox_xyxy]
    x1 = max(0, x1 - pad)
    y1 = max(0, y1 - pad)
    x2 = min(width, x2 + pad)
    y2 = min(height, y2 + pad)
    if x2 <= x1 or y2 <= y1:
        raise ValueError("empty crop")
    return image_bgr[y1:y2, x1:x2]


def _parse_json(text: str) -> dict:
    fenced = re.search(r"\{.*\}", text, flags=re.DOTALL)
    if not fenced:
        raise ValueError(f"model did not return JSON: {text[:200]}")
    data = json.loads(fenced.group(0))
    return {
        "material": data.get("material"),
        "visible_condition": data.get("visible_condition"),
        "visible_damage_clue": data.get("visible_damage_clue"),
    }


DEFAULT_BASE_URL = "https://dashscope.aliyuncs.com/compatible-mode/v1"


def has_api_key() -> bool:
    return bool(os.environ.get("DASHSCOPE_API_KEY", "").strip())


def api_base_url() -> str:
    return (
        os.environ.get("DASHSCOPE_BASE_URL", "").strip()
        or os.environ.get("OPENAI_BASE_URL", "").strip()
        or DEFAULT_BASE_URL
    )


def empty_facts() -> dict:
    return {
        "material": None,
        "visible_condition": None,
        "visible_damage_clue": None,
        "raw_text": None,
    }


def enrich_crop(image_bgr: np.ndarray, model: str = "qwen-vl-plus") -> dict:
    api_key = os.environ.get("DASHSCOPE_API_KEY", "").strip()
    if not api_key:
        raise RuntimeError("DASHSCOPE_API_KEY is not set")
    from openai import OpenAI

    ok, encoded = cv2.imencode(".jpg", image_bgr, [int(cv2.IMWRITE_JPEG_QUALITY), 85])
    if not ok:
        raise RuntimeError("failed to encode crop")
    data_url = "data:image/jpeg;base64," + base64.b64encode(encoded.tobytes()).decode("ascii")
    client = OpenAI(api_key=api_key, base_url=api_base_url())
    response = client.chat.completions.create(
        model=model,
        messages=[
            {
                "role": "user",
                "content": [
                    {"type": "image_url", "image_url": {"url": data_url}},
                    {"type": "text", "text": PROMPT},
                ],
            }
        ],
        temperature=0,
    )
    text = response.choices[0].message.content or ""
    parsed = _parse_json(text)
    parsed["raw_text"] = text
    return parsed
