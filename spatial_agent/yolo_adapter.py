"""Adapter from TAY-LI Pipeline B fixtures to the agent state contract.

The detector remains responsible for projection, YOLO-World labels, grouping and
rule-based reuse assessment. This module only normalizes those outputs so the
LangGraph perception node can consume the detector as a tool.
"""
from __future__ import annotations
import json
from pathlib import Path
from typing import Any
from spatial_agent.models import Detection

ROOT = Path(__file__).resolve().parents[1]
SCENE_ROOT = ROOT / "data" / "fixtures" / "scenes"
PANORAMA_ROOT = ROOT / "data" / "samples" / "panoramas"


def available_scenes() -> list[str]:
    return sorted(p.name for p in SCENE_ROOT.iterdir() if p.is_dir() and (p / "detections.json").exists()) if SCENE_ROOT.exists() else []


def _read(scene_slug: str) -> tuple[dict[str, Any], dict[str, Any]]:
    if scene_slug not in available_scenes():
        raise ValueError(f"unknown TAY-LI scene '{scene_slug}'; choose from {available_scenes()}")
    directory = SCENE_ROOT / scene_slug
    return json.loads((directory / "detections.json").read_text(encoding="utf-8")), json.loads((directory / "batches.json").read_text(encoding="utf-8"))


def load_scene(scene_slug: str) -> dict[str, Any]:
    """Return a normalized detector observation and preserve raw provenance."""
    detections_doc, batches_doc = _read(scene_slug)
    by_id = {item["id"]: item for item in detections_doc.get("objects", [])}
    batch_by_object: dict[str, dict[str, Any]] = {}
    for batch in batches_doc.get("component_batches", []):
        for object_id in batch.get("object_ids", []):
            batch_by_object[object_id] = batch

    detections: list[Detection] = []
    for item in detections_doc.get("objects", []):
        location = item.get("location") or {}
        detection = item.get("detection") or {}
        batch = batch_by_object.get(item["id"], {})
        assessment = batch.get("assessment") or {}
        recommendation = assessment.get("system_recommendation") or {}
        # TAY-LI public fixture intentionally omits pixel boxes after grouping;
        # preserve angular coordinates and use bbox_xyxy when present in raw runs.
        bbox = item.get("bbox_xyxy")
        detections.append(Detection(
            id=item["id"],
            class_name=item.get("category") or item.get("label") or "unknown",
            bbox=bbox or [0.0, 0.0, 0.0, 0.0],
            bbox_xyxy=bbox,
            confidence=float(detection.get("confidence") or 0.0),
            track_id=item["id"],
            source="tay-li:yolo-world",
            raw_label=item.get("label"),
            yaw=location.get("yaw"),
            pitch=location.get("pitch"),
            material=(item.get("material") or {}).get("value"),
            visible_condition=(item.get("visible_condition") or {}).get("value"),
            visible_damage_clue=(item.get("visible_damage_clue") or {}).get("value"),
            component_batch_id=batch.get("id"),
            pathway_assessment=assessment,
            recommended_pathway=recommendation.get("primary_pathway"),
        ))
    image = detections_doc.get("image") or f"data/samples/panoramas/{scene_slug}.jpg"
    return {
        "scene_slug": scene_slug,
        "scene_id": detections_doc.get("scene_id"),
        "panorama_id": detections_doc.get("panorama_id"),
        "image_url": image,
        "detections": detections,
        "batches": batches_doc.get("component_batches", []),
        "raw": {"detections": detections_doc, "batches": batches_doc},
    }


def load_analysis() -> dict[str, Any]:
    path = ROOT / "data" / "fixtures" / "analysis.json"
    return json.loads(path.read_text(encoding="utf-8"))
