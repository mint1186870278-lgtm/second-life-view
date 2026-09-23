"""Live YOLO-World inference for images received by the Linux service.

The checked-in ``pipeline`` scripts are intentionally fixture-oriented.  This
module reuses their projection, detection and grouping primitives without
writing into ``data/fixtures`` so every camera upload is processed as a fresh
observation.
"""

from __future__ import annotations

import asyncio
import json
import threading
from dataclasses import dataclass
from pathlib import Path
from typing import Any

from spatial_agent.config import Settings
from spatial_agent.models import Detection


LIVE_YOLO_SOURCE = "linux:yolov8s-worldv2"
LIVE_YOLO_DETECTOR = "yolov8s-worldv2"


class LiveYoloError(RuntimeError):
    """A locally stored camera frame could not be processed by YOLO."""


@dataclass(frozen=True)
class LiveYoloResult:
    detections: list[Detection]
    component_batches: list[dict[str, Any]]
    raw_detection_count: int
    projection: str
    annotation_kind: str
    annotated_path: Path
    detections_path: Path
    device: str | int

    def public_metadata(self, *, annotated_image_url: str, detections_url: str) -> dict[str, Any]:
        return {
            "source": LIVE_YOLO_SOURCE,
            "mode": "live",
            "detector": LIVE_YOLO_DETECTOR,
            "device": str(self.device),
            "projection": self.projection,
            "annotation_kind": self.annotation_kind,
            "raw_detection_count": self.raw_detection_count,
            "component_group_count": len(self.component_batches),
            "annotated_image_url": annotated_image_url,
            "detections_url": detections_url,
        }


class LiveYoloDetector:
    """Lazy, serialized YOLO-World runner for camera uploads.

    A single model instance keeps upload latency predictable and avoids loading
    the  model for every request.  Inference is serialized because one GPU is
    shared by the FastAPI process and the underlying Ultralytics model is not
    treated as thread-safe.
    """

    def __init__(self, settings: Settings):
        self.settings = settings
        self._model: Any | None = None
        self._model_lock = threading.Lock()
        self._inference_lock = threading.Lock()

    async def detect(
        self,
        image_path: Path,
        *,
        artifact_id: str,
        projection: str,
        output_dir: Path,
    ) -> LiveYoloResult:
        return await asyncio.to_thread(
            self._detect_sync,
            image_path,
            artifact_id=artifact_id,
            projection=projection,
            output_dir=output_dir,
        )

    def _detect_sync(
        self,
        image_path: Path,
        *,
        artifact_id: str,
        projection: str,
        output_dir: Path,
    ) -> LiveYoloResult:
        try:
            import cv2
            import numpy as np
            from pipeline.detection import CATEGORY_MAP, CLASSES, detect_view, draw_detections
            from pipeline.grouping import group_detections
            from pipeline.panorama import default_views, render_view
        except ImportError as exc:  # pragma: no cover - environment dependency
            raise LiveYoloError("YOLO runtime dependencies are unavailable") from exc

        image = cv2.imread(str(image_path))
        if image is None:
            raise LiveYoloError(f"cannot decode uploaded image: {image_path.name}")

        normalized_projection = self._normalize_projection(projection)
        output_dir.mkdir(parents=True, exist_ok=True)
        device = self._resolve_device()
        try:
            return self._detect_with_device(
                image,
                artifact_id=artifact_id,
                output_dir=output_dir,
                projection=normalized_projection,
                device=device,
                cv2=cv2,
                np=np,
                category_map=CATEGORY_MAP,
                classes=CLASSES,
                default_views=default_views,
                render_view=render_view,
                detect_view=detect_view,
                draw_detections=draw_detections,
                group_detections=group_detections,
            )
        except LiveYoloError:
            raise
        except Exception as error:  # noqa: BLE001 - retry only the automatic device choice
            if not self._can_fallback_to_cpu(device, error):
                raise LiveYoloError(f"YOLO inference failed: {error}") from error
            try:
                return self._detect_with_device(
                    image,
                    artifact_id=artifact_id,
                    output_dir=output_dir,
                    projection=normalized_projection,
                    device="cpu",
                    cv2=cv2,
                    np=np,
                    category_map=CATEGORY_MAP,
                    classes=CLASSES,
                    default_views=default_views,
                    render_view=render_view,
                    detect_view=detect_view,
                    draw_detections=draw_detections,
                    group_detections=group_detections,
                )
            except LiveYoloError:
                raise
            except Exception as fallback_error:  # noqa: BLE001 - preserve both device failures
                raise LiveYoloError(
                    f"YOLO failed on {device} ({error}) and CPU fallback ({fallback_error})"
                ) from fallback_error

    def _detect_with_device(
        self,
        image: Any,
        *,
        artifact_id: str,
        output_dir: Path,
        projection: str,
        device: str | int,
        cv2: Any,
        np: Any,
        category_map: dict[str, str],
        classes: list[str],
        default_views: Any,
        render_view: Any,
        detect_view: Any,
        draw_detections: Any,
        group_detections: Any,
    ) -> LiveYoloResult:
        with self._inference_lock:
            model = self._load_model()
            if projection == "equirectangular":
                return self._detect_panorama(
                    image,
                    artifact_id=artifact_id,
                    output_dir=output_dir,
                    device=device,
                    cv2=cv2,
                    np=np,
                    default_views=default_views,
                    render_view=render_view,
                    detect_view=detect_view,
                    draw_detections=draw_detections,
                    group_detections=group_detections,
                    model=model,
                )
            return self._detect_single_image(
                image,
                artifact_id=artifact_id,
                output_dir=output_dir,
                device=device,
                cv2=cv2,
                category_map=category_map,
                classes=classes,
                draw_detections=draw_detections,
                model=model,
                projection=projection,
            )

    def _load_model(self) -> Any:
        if self._model is not None:
            return self._model
        with self._model_lock:
            if self._model is not None:
                return self._model
            try:
                from pipeline.detection import load_yolo_world

                self._model = load_yolo_world(self.settings.yolo_weights or None)
            except Exception as exc:  # noqa: BLE001 - normalize backend errors for the API
                raise LiveYoloError(f"failed to load {LIVE_YOLO_DETECTOR}: {exc}") from exc
        return self._model

    def _resolve_device(self) -> str | int:
        configured = self.settings.yolo_device.strip()
        if configured and configured.lower() != "auto":
            return int(configured) if configured.isdigit() else configured
        try:
            import torch

            if not torch.cuda.is_available():
                return "cpu"
            minimum_free_bytes = max(0, self.settings.yolo_auto_min_free_mb) * 1024 * 1024
            candidates: list[tuple[int, int]] = []
            for device_index in range(torch.cuda.device_count()):
                try:
                    free_bytes, _ = torch.cuda.mem_get_info(device_index)
                except Exception:  # CUDA contexts can be exhausted per device.
                    continue
                if free_bytes >= minimum_free_bytes:
                    candidates.append((free_bytes, device_index))
            # On shared multi-GPU servers, CUDA:0 is often occupied by an LLM.
            # Pick the logical CUDA device with the most free memory; this also
            # respects CUDA_VISIBLE_DEVICES because torch indexes that view.
            return max(candidates)[1] if candidates else "cpu"
        except ImportError:  # pragma: no cover - ultralytics needs torch in production
            return "cpu"

    def _can_fallback_to_cpu(self, device: str | int, error: Exception) -> bool:
        configured = self.settings.yolo_device.strip().lower()
        return (
            configured in {"", "auto"}
            and str(device).lower() != "cpu"
            and "cuda" in str(error).lower()
        )

    def _detect_panorama(
        self,
        image: Any,
        *,
        artifact_id: str,
        output_dir: Path,
        device: str | int,
        cv2: Any,
        np: Any,
        default_views: Any,
        render_view: Any,
        detect_view: Any,
        draw_detections: Any,
        group_detections: Any,
        model: Any,
    ) -> LiveYoloResult:
        raw_detections: list[dict[str, Any]] = []
        annotated_views: list[tuple[str, Any]] = []
        views = default_views(size=self.settings.yolo_view_size, fov_deg=self.settings.yolo_fov_deg)
        for view in views:
            perspective = render_view(image, view)
            found = detect_view(
                model,
                perspective,
                view,
                conf=self.settings.yolo_confidence,
                device=device,
            )
            raw_detections.extend(found)
            annotated_views.append((view.name, draw_detections(perspective, found)))

        scene_id = f"scene_{artifact_id}"
        objects = self._panorama_objects(raw_detections, artifact_id)
        batches = group_detections(objects, scene_id)
        for batch in batches:
            batch["id"] = f"{artifact_id}__{batch['id']}"

        detections = self._as_detections(objects, batches)
        annotated = self._build_contact_sheet(annotated_views, cv2=cv2, np=np)
        return self._write_result(
            artifact_id=artifact_id,
            output_dir=output_dir,
            projection="equirectangular",
            annotation_kind="perspective_contact_sheet",
            annotated_image=annotated,
            cv2=cv2,
            device=device,
            objects=objects,
            component_batches=batches,
            detections=detections,
            image_shape=image.shape,
        )

    def _detect_single_image(
        self,
        image: Any,
        *,
        artifact_id: str,
        output_dir: Path,
        device: str | int,
        cv2: Any,
        category_map: dict[str, str],
        classes: list[str],
        draw_detections: Any,
        model: Any,
        projection: str,
    ) -> LiveYoloResult:
        result = model.predict(
            image,
            conf=self.settings.yolo_confidence,
            verbose=False,
            device=device,
        )[0]

        raw_detections: list[dict[str, Any]] = []
        if result.boxes is not None:
            names = result.names
            for box in result.boxes:
                class_id = int(box.cls.item())
                raw_label = names.get(class_id, str(class_id))
                category = category_map.get(raw_label)
                if category not in classes:
                    continue
                raw_detections.append(
                    {
                        "category": category,
                        "raw_label": raw_label,
                        "confidence": float(box.conf.item()),
                        "bbox_xyxy": [float(value) for value in box.xyxy[0].tolist()],
                        "view": "image",
                    }
                )

        objects: list[dict[str, Any]] = []
        batches: list[dict[str, Any]] = []
        for index, item in enumerate(raw_detections, start=1):
            object_id = f"{artifact_id}_obj_{index:03d}"
            batch_id = f"{artifact_id}__batch_{item['category']}_{index:03d}"
            objects.append(
                {
                    "id": object_id,
                    "category": item["category"],
                    "label": item["category"],
                    "detection": {"confidence": round(item["confidence"], 3)},
                    "raw_label": item["raw_label"],
                    "view": "image",
                    "bbox_xyxy": [round(value, 1) for value in item["bbox_xyxy"]],
                }
            )
            batches.append(
                {
                    "id": batch_id,
                    "label": item["category"].replace("_", " ").title(),
                    "category": item["category"],
                    "object_ids": [object_id],
                    "scene_ids": [f"scene_{artifact_id}"],
                    "detected_count": 1,
                    "primary_object_id": object_id,
                    "assessment": {},
                }
            )

        detections = self._as_detections(objects, batches)
        annotated = draw_detections(image, raw_detections)
        return self._write_result(
            artifact_id=artifact_id,
            output_dir=output_dir,
            projection=projection,
            annotation_kind="image_boxes",
            annotated_image=annotated,
            cv2=cv2,
            device=device,
            objects=objects,
            component_batches=batches,
            detections=detections,
            image_shape=image.shape,
        )

    @staticmethod
    def _panorama_objects(raw_detections: list[dict[str, Any]], artifact_id: str) -> list[dict[str, Any]]:
        objects = []
        for index, item in enumerate(raw_detections, start=1):
            objects.append(
                {
                    "id": f"{artifact_id}_obj_{index:03d}",
                    "category": item["category"],
                    "label": item["category"],
                    "raw_label": item["raw_label"],
                    "location": {
                        "yaw": round(float(item["yaw"]), 1),
                        "pitch": round(float(item["pitch"]), 1),
                    },
                    "detection": {"confidence": round(float(item["confidence"]), 3)},
                    "view": item["view"],
                    "bbox_xyxy": [round(float(value), 1) for value in item["bbox_xyxy"]],
                    "yaw_min": float(item["yaw_min"]),
                    "yaw_max": float(item["yaw_max"]),
                    "pitch_min": float(item["pitch_min"]),
                    "pitch_max": float(item["pitch_max"]),
                }
            )
        return objects

    @staticmethod
    def _as_detections(objects: list[dict[str, Any]], batches: list[dict[str, Any]]) -> list[Detection]:
        batch_by_object = {
            object_id: batch
            for batch in batches
            for object_id in batch.get("object_ids", [])
        }
        detections = []
        for item in objects:
            location = item.get("location") or {}
            bbox = item.get("bbox_xyxy") or [0.0, 0.0, 0.0, 0.0]
            batch = batch_by_object.get(item["id"], {})
            detections.append(
                Detection(
                    id=item["id"],
                    class_name=item["category"],
                    bbox=bbox,
                    bbox_xyxy=bbox,
                    confidence=float((item.get("detection") or {}).get("confidence") or 0.0),
                    track_id=item["id"],
                    source=LIVE_YOLO_SOURCE,
                    raw_label=item.get("raw_label"),
                    yaw=location.get("yaw"),
                    pitch=location.get("pitch"),
                    component_batch_id=batch.get("id"),
                )
            )
        return detections

    @staticmethod
    def _build_contact_sheet(annotated_views: list[tuple[str, Any]], *, cv2: Any, np: Any) -> Any:
        if not annotated_views:
            return np.zeros((512, 512, 3), dtype=np.uint8)
        tile_width = 512
        tile_height = 512
        columns = min(5, len(annotated_views))
        rows = (len(annotated_views) + columns - 1) // columns
        canvas = np.full((rows * tile_height, columns * tile_width, 3), 24, dtype=np.uint8)
        for index, (name, view) in enumerate(annotated_views):
            row, column = divmod(index, columns)
            resized = cv2.resize(view, (tile_width, tile_height), interpolation=cv2.INTER_AREA)
            top = row * tile_height
            left = column * tile_width
            canvas[top : top + tile_height, left : left + tile_width] = resized
            cv2.rectangle(canvas, (left, top), (left + tile_width - 1, top + 30), (20, 20, 20), -1)
            cv2.putText(
                canvas,
                name,
                (left + 10, top + 21),
                cv2.FONT_HERSHEY_SIMPLEX,
                0.55,
                (255, 255, 255),
                1,
                cv2.LINE_AA,
            )
        return canvas

    @staticmethod
    def _normalize_projection(value: str) -> str:
        normalized = value.strip().lower().replace("-", "_")
        if normalized in {"erp", "equirectangular", "panorama", "spherical"}:
            return "equirectangular"
        return normalized or "image"

    @staticmethod
    def _write_image(path: Path, image: Any, *, cv2: Any) -> None:
        if not cv2.imwrite(str(path), image):
            raise LiveYoloError(f"failed to write annotation image: {path.name}")

    def _write_result(
        self,
        *,
        artifact_id: str,
        output_dir: Path,
        projection: str,
        annotation_kind: str,
        annotated_image: Any,
        cv2: Any,
        device: str | int,
        objects: list[dict[str, Any]],
        component_batches: list[dict[str, Any]],
        detections: list[Detection],
        image_shape: Any,
    ) -> LiveYoloResult:
        annotated_path = output_dir / f"{artifact_id}-yolo-annotated.jpg"
        detections_path = output_dir / f"{artifact_id}-yolo.json"
        self._write_image(annotated_path, annotated_image, cv2=cv2)
        height, width = image_shape[:2]
        detections_path.write_text(
            json.dumps(
                {
                    "frame_id": artifact_id,
                    "projection": projection,
                    "detector": LIVE_YOLO_DETECTOR,
                    "source": LIVE_YOLO_SOURCE,
                    "device": str(device),
                    "width": int(width),
                    "height": int(height),
                    "raw_detection_count": len(detections),
                    "component_group_count": len(component_batches),
                    "annotation_kind": annotation_kind,
                    "objects": objects,
                    "component_batches": component_batches,
                    "detections": [item.model_dump(mode="json", by_alias=True) for item in detections],
                },
                ensure_ascii=False,
                indent=2,
            ),
            encoding="utf-8",
        )
        return LiveYoloResult(
            detections=detections,
            component_batches=component_batches,
            raw_detection_count=len(detections),
            projection=projection,
            annotation_kind=annotation_kind,
            annotated_path=annotated_path,
            detections_path=detections_path,
            device=device,
        )
