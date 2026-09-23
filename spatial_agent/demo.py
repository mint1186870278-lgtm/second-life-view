from __future__ import annotations

import asyncio
import json
from collections import Counter
from functools import lru_cache
from pathlib import Path
from typing import Any

from spatial_agent.graph import SpatialAgentGraph
from spatial_agent.models import AgentEvent, DemoAnalyzeRequest, Detection, Evidence, RunState
from spatial_agent.providers.aholo_world import AholoWorldClient


ROOT = Path(__file__).resolve().parents[1]
PICTURE_DIR = ROOT / "data" / "samples" / "pictures"
FIXTURE_PATH = ROOT / "data" / "fixtures" / "picture_demo_detections.json"
DEFAULT_SCENE_LIMIT = 5
ANNOTATION_PREVIEW_WIDTH = 1440
ANNOTATION_LABEL_LIMIT = 18

_CATEGORY_GROUP_NAMES = {
    "cabinet": "柜体",
    "chair": "座椅",
    "door": "门",
    "sofa": "沙发",
    "table": "桌台",
    "window": "窗",
}

_CATEGORY_ANNOTATION_COLORS = {
    "cabinet": (246, 159, 64),
    "chair": (86, 181, 105),
    "door": (226, 94, 88),
    "sofa": (184, 104, 227),
    "table": (74, 152, 238),
    "window": (75, 203, 221),
}


def _load_fixture() -> dict[str, Any]:
    return json.loads(FIXTURE_PATH.read_text(encoding="utf-8"))


def _scene_asset_url(filename: str) -> str:
    return f"/demo-assets/{filename}"


def _scene_thumbnail_url(scene_id: str) -> str:
    return f"/api/v1/demo/scenes/{scene_id}/thumbnail"


def _scene_annotated_url(scene_id: str) -> str:
    return f"/api/v1/demo/scenes/{scene_id}/annotated"


def _find_demo_scene(scene_id: str) -> dict[str, Any]:
    scene = next((item for item in _load_fixture().get("scenes", []) if item["id"] == scene_id), None)
    if not scene:
        raise ValueError(f"unknown demo scene: {scene_id}")
    return scene


@lru_cache(maxsize=32)
def load_demo_thumbnail(scene_id: str) -> bytes:
    scene = _find_demo_scene(scene_id)
    import cv2

    image = cv2.imread(str(PICTURE_DIR / scene["filename"]))
    if image is None:
        raise FileNotFoundError(scene["filename"])
    height, width = image.shape[:2]
    target_width = min(720, width)
    target_height = max(1, round(height * target_width / width))
    thumbnail = cv2.resize(image, (target_width, target_height), interpolation=cv2.INTER_AREA)
    encoded, buffer = cv2.imencode(".jpg", thumbnail, [int(cv2.IMWRITE_JPEG_QUALITY), 78])
    if not encoded:
        raise RuntimeError(f"failed to encode thumbnail for {scene_id}")
    return buffer.tobytes()


def _group_display_name(group: dict[str, Any], ordinal: int) -> str:
    category = group.get("category", "component")
    return f"{_CATEGORY_GROUP_NAMES.get(category, group.get('label', category))}组 {ordinal:02d}"


def _group_annotation_label(group: dict[str, Any], ordinal: int) -> str:
    return _group_display_name(group, ordinal)


def _draw_annotated_group(
    image: Any,
    group: dict[str, Any],
    ordinal: int,
    *,
    show_label: bool,
) -> None:
    """Approximate one perspective YOLO box on the equirectangular preview.

    The checked-in fixture keeps the primary detection's bbox, yaw and pitch.
    Its source view uses a 90° field of view, so the angular extent can be
    reconstructed for a compact ERP preview without depending on run artifacts.
    """
    import cv2

    image_height, image_width = image.shape[:2]
    box = group.get("bbox_xyxy") or []
    if len(box) != 4:
        return

    x1, y1, x2, y2 = [float(value) for value in box]
    yaw = float(group.get("yaw", 0.0))
    pitch = float(group.get("pitch", 0.0))
    yaw_extent = min(150.0, max(4.0, abs(x2 - x1) / 768.0 * 90.0))
    pitch_extent = min(120.0, max(4.0, abs(y2 - y1) / 768.0 * 90.0))
    yaw_left = float(group.get("yaw_min", yaw - yaw_extent / 2.0))
    yaw_right = float(group.get("yaw_max", yaw + yaw_extent / 2.0))
    pitch_top = min(90.0, float(group.get("pitch_max", pitch + pitch_extent / 2.0)))
    pitch_bottom = max(-90.0, float(group.get("pitch_min", pitch - pitch_extent / 2.0)))

    raw_left = (yaw_left + 180.0) / 360.0 * image_width
    raw_right = (yaw_right + 180.0) / 360.0 * image_width
    top = int(round((0.5 - pitch_top / 180.0) * image_height))
    bottom = int(round((0.5 - pitch_bottom / 180.0) * image_height))
    top = max(0, min(image_height - 1, top))
    bottom = max(top + 1, min(image_height - 1, bottom))

    if raw_left < 0:
        ranges = [(int(round(raw_left + image_width)), image_width - 1), (0, int(round(raw_right)))]
    elif raw_right >= image_width:
        ranges = [(int(round(raw_left)), image_width - 1), (0, int(round(raw_right - image_width)))]
    else:
        ranges = [(int(round(raw_left)), int(round(raw_right)))]

    color = _CATEGORY_ANNOTATION_COLORS.get(group.get("category"), (35, 209, 233))
    label = _group_annotation_label(group, ordinal)
    for range_index, (left, right) in enumerate(ranges):
        left = max(0, min(image_width - 1, left))
        right = max(left + 1, min(image_width - 1, right))
        cv2.rectangle(image, (left, top), (right, bottom), color, 2, cv2.LINE_AA)
        if not show_label or range_index != 0:
            continue
        (label_width, label_height), baseline = cv2.getTextSize(label, cv2.FONT_HERSHEY_SIMPLEX, 0.45, 1)
        label_top = max(0, top - label_height - baseline - 7)
        label_right = min(image_width - 1, left + label_width + 10)
        cv2.rectangle(image, (left, label_top), (label_right, top), color, -1)
        cv2.putText(
            image,
            label,
            (left + 5, max(label_height + 3, top - baseline - 4)),
            cv2.FONT_HERSHEY_SIMPLEX,
            0.45,
            (22, 27, 34),
            1,
            cv2.LINE_AA,
        )


@lru_cache(maxsize=32)
def load_demo_annotated_preview(scene_id: str) -> bytes:
    scene = _find_demo_scene(scene_id)
    import cv2

    image = cv2.imread(str(PICTURE_DIR / scene["filename"]))
    if image is None:
        raise FileNotFoundError(scene["filename"])
    image_height, image_width = image.shape[:2]
    preview_height = max(1, round(image_height * ANNOTATION_PREVIEW_WIDTH / image_width))
    preview = cv2.resize(image, (ANNOTATION_PREVIEW_WIDTH, preview_height), interpolation=cv2.INTER_AREA)

    category_ordinals: Counter[str] = Counter()
    ordered_groups = sorted(scene.get("groups", []), key=lambda group: float(group.get("confidence", 0)), reverse=True)
    for index, group in enumerate(ordered_groups):
        category = str(group.get("category", "component"))
        category_ordinals[category] += 1
        _draw_annotated_group(
            preview,
            group,
            category_ordinals[category],
            show_label=index < ANNOTATION_LABEL_LIMIT,
        )

    encoded, buffer = cv2.imencode(".jpg", preview, [int(cv2.IMWRITE_JPEG_QUALITY), 82])
    if not encoded:
        raise RuntimeError(f"failed to encode annotated preview for {scene_id}")
    return buffer.tobytes()


def list_demo_scenes() -> list[dict[str, Any]]:
    fixture = _load_fixture()
    scenes: list[dict[str, Any]] = []
    for item in fixture.get("scenes", []):
        path = PICTURE_DIR / item["filename"]
        scenes.append({
            "id": item["id"],
            "name": item["name"],
            "filename": item["filename"],
            "asset_url": _scene_asset_url(item["filename"]),
            "thumbnail_url": _scene_thumbnail_url(item["id"]),
            "annotated_url": _scene_annotated_url(item["id"]),
            "width": item["width"],
            "height": item["height"],
            "size_bytes": path.stat().st_size if path.exists() else 0,
            "has_cached_yolo": bool(item.get("groups")),
            "detection_count": item.get("raw_detection_count", 0),
            "group_count": item.get("group_count", 0),
            "category_counts": item.get("group_category_counts", {}),
            "default_selected": int(item.get("order", 999)) <= DEFAULT_SCENE_LIMIT,
        })
    return scenes


def _select_scenes(scene_ids: list[str]) -> list[dict[str, Any]]:
    fixture = _load_fixture()
    available = {scene["id"]: scene for scene in fixture.get("scenes", [])}
    selected_ids = scene_ids or [
        scene["id"]
        for scene in fixture.get("scenes", [])
        if int(scene.get("order", 999)) <= DEFAULT_SCENE_LIMIT
    ]
    unknown = [scene_id for scene_id in selected_ids if scene_id not in available]
    if unknown:
        raise ValueError(f"unknown demo scenes: {', '.join(unknown)}")
    return [available[scene_id] for scene_id in selected_ids]


def _detections_for_scenes(scenes: list[dict[str, Any]]) -> list[Detection]:
    detections: list[Detection] = []
    for scene in scenes:
        for group in scene.get("groups", []):
            supported = group.get("evidence_status") == "supported"
            detections.append(Detection(
                id=group["id"],
                **{
                    "class": group["category"],
                    "bbox": group["bbox_xyxy"],
                    "bbox_xyxy": group["bbox_xyxy"],
                    "confidence": group["confidence"],
                    "track_id": group["id"],
                    "source": "pipeline-b:yolov8s-worldv2-cache",
                    "raw_label": group.get("raw_label"),
                    "yaw": group.get("yaw"),
                    "pitch": group.get("pitch"),
                    "material": group.get("material"),
                    "visible_condition": "可见状态基本完整" if supported else None,
                    "component_batch_id": group["id"],
                    "recommended_pathway": group.get("recommended_pathway"),
                    "scene_id": scene["id"],
                    "detected_count": group.get("detected_count", 1),
                    "cached_yolo": True,
                },
            ))
    return detections


def _public_scene(scene: dict[str, Any]) -> dict[str, Any]:
    path = PICTURE_DIR / scene["filename"]
    return {
        "id": scene["id"],
        "name": scene["name"],
        "filename": scene["filename"],
        "asset_url": _scene_asset_url(scene["filename"]),
        "thumbnail_url": _scene_thumbnail_url(scene["id"]),
        "annotated_url": _scene_annotated_url(scene["id"]),
        "width": scene["width"],
        "height": scene["height"],
        "size_bytes": path.stat().st_size if path.exists() else 0,
        "has_cached_yolo": bool(scene.get("groups")),
        "detection_count": scene.get("raw_detection_count", 0),
        "group_count": scene.get("group_count", 0),
        "category_counts": scene.get("group_category_counts", {}),
        "default_selected": int(scene.get("order", 999)) <= DEFAULT_SCENE_LIMIT,
    }


def _resolve_demo_evidence(state: RunState) -> int:
    actions = list(state.capture_actions)
    if not actions:
        return 0
    by_id = {item.id: item for item in state.objects}
    image_uri = state.image_urls[0] if state.image_urls else None
    for action in actions:
        target = by_id.get(action.target_object_id or "")
        if target:
            target.confidence = max(target.confidence, 0.92)
            target.condition = target.condition or "样例近景查证：未见明显结构性损伤"
            target.missing_fields.clear()
        state.evidence.append(Evidence(
            kind="user",
            source="demo:evidence-agent-auto-check",
            uri=image_uri,
            confidence=0.96,
            claims={
                "capture_action_id": action.id,
                "target_object_id": action.target_object_id,
                "confirmed": True,
                "mode": "sample-picture-demo",
            },
            provenance="verified",
        ))
    state.metadata["capture_confirmed"] = True
    state.metadata["demo_evidence_auto_resolved"] = len(actions)
    state.capture_actions.clear()
    state.status = "running"
    state.next_agent = None
    state.events.append(AgentEvent(
        agent="evidence",
        action="auto_verify_demo",
        message=f"Demo 使用样例素材自动完成 {len(actions)} 项补充查证",
        data={"resolved_actions": len(actions)},
    ))
    return len(actions)


async def _run_spatial_generation(
    client: AholoWorldClient,
    scene: dict[str, Any],
    prompt: str,
) -> dict[str, Any]:
    preview_url = _scene_thumbnail_url(scene["id"])
    local_path = PICTURE_DIR / scene["filename"]
    try:
        if client.enabled:
            result = await client.generate_from_local_file(
                str(local_path),
                prompt,
                name=f"Second Life View · {scene['name']}",
            )
        else:
            result = await client.generate(prompt, preview_url, name=f"Second Life View · {scene['name']}")
    except Exception as exc:
        return {
            "status": "failed",
            "provider": "aholo-spatial-gen",
            "preview_url": preview_url,
            "message": str(exc),
        }
    return {
        "provider": "aholo-spatial-gen",
        "preview_url": preview_url,
        **result,
    }


def _group_summary(scenes: list[dict[str, Any]]) -> tuple[list[dict[str, Any]], Counter[str]]:
    groups: list[dict[str, Any]] = []
    categories: Counter[str] = Counter()
    for scene in scenes:
        category_ordinals: Counter[str] = Counter()
        for group in sorted(scene.get("groups", []), key=lambda item: float(item.get("confidence", 0)), reverse=True):
            categories[group["category"]] += 1
            category_ordinals[group["category"]] += 1
            groups.append({
                "id": group["id"],
                "group_name": _group_display_name(group, category_ordinals[group["category"]]),
                "label": group["label"],
                "category": group["category"],
                "scene_id": scene["id"],
                "scene_name": scene["name"],
                "confidence": group["confidence"],
                "detected_count": group.get("detected_count", 1),
                "recommended_pathway": group.get("recommended_pathway"),
                "evidence_status": group.get("evidence_status"),
            })
    groups.sort(key=lambda item: item["confidence"], reverse=True)
    return groups, categories


async def analyze_demo(
    request: DemoAnalyzeRequest,
    *,
    agent: SpatialAgentGraph,
    aholo_world: AholoWorldClient,
) -> tuple[RunState, dict[str, Any]]:
    scenes = _select_scenes(request.scene_ids)
    if not scenes:
        raise ValueError("select at least one demo scene")
    image_paths = [str(PICTURE_DIR / scene["filename"]) for scene in scenes]
    state = RunState(
        user_goal=request.user_goal,
        image_urls=image_paths,
        detections=_detections_for_scenes(scenes),
        metadata={
            "region": request.region,
            "include_web": request.include_web,
            "demo_scene_ids": [scene["id"] for scene in scenes],
            "perception_source": "Pipeline B cached YOLO-World output",
            "skip_vlm_enrichment": True,
        },
    )
    spatial_task = asyncio.create_task(
        _run_spatial_generation(aholo_world, scenes[0], request.spatial_prompt)
    )
    state = await agent.run(
        state,
        enable_research=False,
        enable_design=False,
        include_web=False,
    )
    evidence_checked_count = _resolve_demo_evidence(state)
    state.status = "running"
    state.next_agent = None
    state = await agent.run(
        state,
        enable_research=True,
        enable_design=True,
        include_web=request.include_web,
    )
    spatial_generation = await spatial_task
    state.metadata["spatial_generation"] = spatial_generation
    state.events.append(AgentEvent(
        agent="spatial",
        action="generate",
        message=(
            "Aholo Spatial Gen 已提交空间改造任务"
            if spatial_generation.get("status") not in {"mock", "failed"}
            else "Aholo Spatial Gen 使用离线预览" if spatial_generation.get("status") == "mock"
            else "Aholo Spatial Gen 调用失败"
        ),
        data={
            "status": spatial_generation.get("status"),
            "world_id": spatial_generation.get("world_id"),
        },
    ))

    groups, category_counts = _group_summary(scenes)
    design = state.designs[0].model_dump(mode="json") if state.designs else None
    pending_evidence_count = len(state.capture_actions)
    public_scenes = [_public_scene(scene) for scene in scenes]
    response = {
        "run_id": state.run_id,
        "status": state.status,
        "scenes": public_scenes,
        "scene_count": len(scenes),
        "raw_detection_count": sum(scene.get("raw_detection_count", 0) for scene in scenes),
        "component_count": sum(scene.get("raw_detection_count", 0) for scene in scenes),
        "group_count": len(groups),
        "category_counts": dict(sorted(category_counts.items())),
        "evidence_checked_count": evidence_checked_count,
        "pending_evidence_count": pending_evidence_count,
        "groups": groups,
        "groups_truncated": 0,
        "design": design,
        "spatial_generation": spatial_generation,
        "stages": {
            "preprocess": {
                "status": "completed" if spatial_generation.get("status") != "failed" else "failed",
                "provider": "Aholo Spatial Gen",
                "message": "已提交 AI 空间改造生成" if spatial_generation.get("status") != "mock" else "离线 Demo：保留 Aholo 调用契约并使用原图预览",
            },
            "perception": {
                "status": "completed",
                "provider": "Perception Agent · YOLO-World",
                "message": f"从 {sum(scene.get('raw_detection_count', 0) for scene in scenes)} 个检测框去重形成 {len(groups)} 个构件组",
            },
            "evidence": {
                "status": "completed" if not pending_evidence_count else "needs_input",
                "provider": "Evidence Agent",
                "message": f"已查证 {evidence_checked_count} 项证据，仍有 {pending_evidence_count} 项待确认",
            },
            "design": {
                "status": design.get("status", "draft") if design else "failed",
                "provider": "Design Agent",
                "message": design.get("title", "未生成方案") if design else "未生成方案",
            },
        },
        "sources": [source.model_dump(mode="json") for source in state.sources[:10]],
        "events": [event.model_dump(mode="json") for event in state.events[-24:]],
        "errors": state.errors,
    }
    return state, response
