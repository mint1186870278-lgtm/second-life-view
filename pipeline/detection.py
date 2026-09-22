"""Stage 2: open-vocabulary detection on perspective views.

YOLO-World answers what is visible and where. This module also converts
each box back to yaw / pitch using the Stage 1 projection.
"""

from __future__ import annotations

from pathlib import Path

import cv2
import numpy as np

from pipeline.panorama import ViewSpec, bbox_to_yaw_pitch

# Prompt phrases for YOLO-World. Mapped back to the 5 product categories.
CLASS_PROMPTS = [
    "door",
    "window",
    "chair",
    "office chair",
    "table",
    "desk",
    "cabinet",
    "wardrobe",
]

CATEGORY_MAP = {
    "door": "door",
    "window": "window",
    "chair": "chair",
    "office chair": "chair",
    "table": "table",
    "desk": "table",
    "cabinet": "cabinet",
    "wardrobe": "cabinet",
}

CLASSES = ["door", "window", "chair", "table", "cabinet"]


def load_yolo_world(weights: str | None = None):
    from ultralytics import YOLO

    if weights is None:
        root = Path(__file__).resolve().parents[1]
        candidate = root / "yolov8s-worldv2.pt"
        weights = str(candidate if candidate.exists() else "yolov8s-worldv2.pt")
    model = YOLO(weights)
    model.set_classes(CLASS_PROMPTS)
    return model


def detect_view(model, image_bgr: np.ndarray, view: ViewSpec, conf: float = 0.12) -> list[dict]:
    result = model.predict(image_bgr, conf=conf, verbose=False, device=0)[0]
    detections = []
    if result.boxes is None:
        return detections
    names = result.names
    for box in result.boxes:
        cls_id = int(box.cls.item())
        raw_name = names.get(cls_id, str(cls_id))
        category = CATEGORY_MAP.get(raw_name)
        if category not in CLASSES:
            continue
        xyxy = [float(v) for v in box.xyxy[0].tolist()]
        spatial = bbox_to_yaw_pitch(xyxy, view)
        detections.append(
            {
                "category": category,
                "raw_label": raw_name,
                "confidence": float(box.conf.item()),
                "bbox_xyxy": xyxy,
                "view": view.name,
                **spatial,
            }
        )
    return detections


def draw_detections(image_bgr: np.ndarray, detections: list[dict]) -> np.ndarray:
    canvas = image_bgr.copy()
    for item in detections:
        x1, y1, x2, y2 = [int(v) for v in item["bbox_xyxy"]]
        cv2.rectangle(canvas, (x1, y1), (x2, y2), (40, 180, 40), 2)
        label = f"{item['category']} {item['confidence']:.2f}"
        cv2.putText(canvas, label, (x1, max(16, y1 - 6)), cv2.FONT_HERSHEY_SIMPLEX, 0.5, (40, 180, 40), 1)
    return canvas


def save_image(path: Path, image_bgr: np.ndarray) -> None:
    path.parent.mkdir(parents=True, exist_ok=True)
    cv2.imwrite(str(path), image_bgr)
