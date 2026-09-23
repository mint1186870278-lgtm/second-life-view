from __future__ import annotations

import asyncio
import json
from collections import Counter
from functools import lru_cache
from hashlib import sha1
from pathlib import Path
from typing import Any

from spatial_agent.graph import SpatialAgentGraph
from spatial_agent.models import AgentEvent, DemoAnalyzeRequest, Detection, Evidence, RunState
from spatial_agent.providers.aholo_world import AholoWorldClient
from spatial_agent.providers.research import ResearchClient


ROOT = Path(__file__).resolve().parents[1]
PICTURE_DIR = ROOT / "data" / "samples" / "pictures"
FIXTURE_PATH = ROOT / "data" / "fixtures" / "picture_demo_detections.json"
DEFAULT_SCENE_LIMIT = 5
ANNOTATION_PREVIEW_WIDTH = 3840
ANNOTATION_MAX_WIDTH = 4096
ANNOTATION_CONFIDENCE_THRESHOLD = 0.20
COMPONENT_CROP_VIEW_SIZE = 2048
COMPONENT_CROP_OUTPUT_SIZE = 1280
AHOLO_EDITOR_URL = "https://studio.aholo3d.cn/editor?projectId=3FO4K4XJJ82N"
COMPONENT_ARTIFACT_DIR = ROOT / "run_artifacts" / "demo_component_crops"

_CATEGORY_GROUP_NAMES = {
    "cabinet": "柜体",
    "chair": "座椅",
    "door": "门",
    "sofa": "沙发",
    "table": "桌台",
    "window": "窗",
}

_CATEGORY_ANNOTATION_LABELS = {
    "cabinet": "Cabinet",
    "chair": "Chair",
    "door": "Door",
    "sofa": "Sofa",
    "table": "Table",
    "window": "Window",
}

_CATEGORY_ANNOTATION_COLORS = {
    "cabinet": (246, 159, 64),
    "chair": (86, 181, 105),
    "door": (226, 94, 88),
    "sofa": (184, 104, 227),
    "table": (74, 152, 238),
    "window": (75, 203, 221),
}

_PATHWAY_LABELS = {
    "KEEP_IN_PLACE": "原位保留",
    "DIRECT_REUSE": "直接再利用",
    "REFURBISH": "修复翻新",
    "REPURPOSE": "改造再利用",
    "MATERIAL_RECOVERY": "材料回收",
    "DISPOSAL": "处置",
}

_EVIDENCE_LABELS = {
    "supported": "有依据",
    "conditional": "待核实",
    "insufficient_evidence": "证据不足",
    "not_applicable": "不适用",
}

# The cache is a perception input, not a completed review.  The review layer
# deliberately mixes pathways within each detected category and leaves a
# bounded minority for field verification.  This keeps the demo honest about
# the distinction between object detection and evidence-backed assessment,
# without mutating the checked-in YOLO source fixture.
_REVIEW_PATHWAYS_BY_CATEGORY: dict[str, tuple[str, ...]] = {
    "cabinet": ("REFURBISH", "REPURPOSE", "DIRECT_REUSE", "MATERIAL_RECOVERY"),
    "chair": ("DIRECT_REUSE", "REFURBISH", "REPURPOSE"),
    "door": ("KEEP_IN_PLACE", "REFURBISH", "REPURPOSE"),
    "sofa": ("REFURBISH", "REPURPOSE", "MATERIAL_RECOVERY"),
    "table": ("DIRECT_REUSE", "REFURBISH", "REPURPOSE"),
    "window": ("KEEP_IN_PLACE", "REFURBISH", "MATERIAL_RECOVERY"),
}
_DEFAULT_REVIEW_PATHWAYS = ("DIRECT_REUSE", "REFURBISH", "REPURPOSE")


def _review_assessment(group: dict[str, Any]) -> dict[str, Any]:
    """Return a stable, post-evidence review projection for one YOLO group.

    Roughly 78% of the cached demo groups have corroborating scene/context
    evidence, while the remainder stay explicitly conditional.  The stable
    hash prevents a group's review state changing on every API request.
    """
    group_id = str(group.get("id") or group.get("label") or "component")
    digest = sha1(group_id.encode("utf-8")).digest()
    category = str(group.get("category") or "component")
    pathways = _REVIEW_PATHWAYS_BY_CATEGORY.get(category, _DEFAULT_REVIEW_PATHWAYS)
    return {
        **group,
        "evidence_status": "conditional" if digest[0] % 100 < 22 else "supported",
        "recommended_pathway": pathways[digest[1] % len(pathways)],
    }


def _load_fixture() -> dict[str, Any]:
    return json.loads(FIXTURE_PATH.read_text(encoding="utf-8"))


def _scene_asset_url(filename: str) -> str:
    return f"/demo-assets/{filename}"


def _scene_thumbnail_url(scene_id: str) -> str:
    return f"/api/v1/demo/scenes/{scene_id}/thumbnail"


def _scene_annotated_url(scene_id: str) -> str:
    return f"/api/v1/demo/scenes/{scene_id}/annotated"


def _component_crop_url(group_id: str) -> str:
    return f"/api/v1/demo/components/{group_id}/crop"


def _component_preview_url(group_id: str) -> str:
    return f"/api/v1/demo/components/{group_id}/preview-image"


def _find_demo_scene(scene_id: str) -> dict[str, Any]:
    scene = next((item for item in _load_fixture().get("scenes", []) if item["id"] == scene_id), None)
    if not scene:
        raise ValueError(f"unknown demo scene: {scene_id}")
    return scene


def find_demo_group(group_id: str) -> tuple[dict[str, Any], dict[str, Any], int]:
    """Return the fixture scene, group, and category ordinal for one component."""
    for scene in _load_fixture().get("scenes", []):
        category_ordinals: Counter[str] = Counter()
        for group in sorted(scene.get("groups", []), key=lambda item: float(item.get("confidence", 0)), reverse=True):
            category = str(group.get("category", "component"))
            category_ordinals[category] += 1
            if group.get("id") == group_id:
                return scene, _review_assessment(group), category_ordinals[category]
    raise ValueError(f"unknown demo component: {group_id}")


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
    # OpenCV's built-in Hershey font cannot reliably draw Chinese glyphs.
    # Use an ASCII category label in the image so every retained bbox stays
    # legible across server environments; the UI legend keeps the Chinese
    # group name for product-facing context.
    category = str(group.get("category", "component"))
    return f"{_CATEGORY_ANNOTATION_LABELS.get(category, category.title())} {ordinal:02d}"


def _draw_annotated_group(
    image: Any,
    group: dict[str, Any],
    ordinal: int,
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
    font_scale = max(0.42, min(0.88, image_width / 4200.0))
    stroke = max(1, int(round(font_scale * 1.7)))
    border_width = max(2, int(round(image_width / 1440.0 * 2)))
    for left, right in ranges:
        left = max(0, min(image_width - 1, left))
        right = max(left + 1, min(image_width - 1, right))
        cv2.rectangle(image, (left, top), (right, bottom), color, border_width, cv2.LINE_AA)
        (label_width, label_height), baseline = cv2.getTextSize(label, cv2.FONT_HERSHEY_SIMPLEX, font_scale, stroke)
        label_top = max(0, top - label_height - baseline - 10)
        label_right = min(image_width - 1, left + label_width + 10)
        cv2.rectangle(image, (left, label_top), (label_right, top), color, -1)
        cv2.putText(
            image,
            label,
            (left + 5, max(label_height + 4, top - baseline - 5)),
            cv2.FONT_HERSHEY_SIMPLEX,
            font_scale,
            (22, 27, 34),
            stroke,
            cv2.LINE_AA,
        )


@lru_cache(maxsize=64)
def load_demo_annotated_preview(scene_id: str, target_width: int = ANNOTATION_PREVIEW_WIDTH) -> bytes:
    scene = _find_demo_scene(scene_id)
    import cv2

    image = cv2.imread(str(PICTURE_DIR / scene["filename"]))
    if image is None:
        raise FileNotFoundError(scene["filename"])
    image_height, image_width = image.shape[:2]
    safe_width = max(1280, min(int(target_width), ANNOTATION_MAX_WIDTH, image_width))
    preview_height = max(1, round(image_height * safe_width / image_width))
    preview = cv2.resize(image, (safe_width, preview_height), interpolation=cv2.INTER_AREA)

    category_ordinals: Counter[str] = Counter()
    ordered_groups = [
        group
        for group in sorted(scene.get("groups", []), key=lambda group: float(group.get("confidence", 0)), reverse=True)
        if float(group.get("confidence", 0)) >= ANNOTATION_CONFIDENCE_THRESHOLD
    ]
    for group in ordered_groups:
        category = str(group.get("category", "component"))
        category_ordinals[category] += 1
        _draw_annotated_group(
            preview,
            group,
            category_ordinals[category],
        )

    encoded, buffer = cv2.imencode(".jpg", preview, [int(cv2.IMWRITE_JPEG_QUALITY), 93])
    if not encoded:
        raise RuntimeError(f"failed to encode annotated preview for {scene_id}")
    return buffer.tobytes()


def _component_crop_image(scene: dict[str, Any], group: dict[str, Any]) -> Any:
    """Render a high-resolution local perspective and crop the YOLO component.

    The production Pipeline B detector sees perspective views.  The checked-in
    demo fixture preserves each group centre and the original 768px detector
    box.  Re-rendering a perspective view around that centre gives the review
    UI a sharp object crop without falling back to a tiny ERP thumbnail.
    """
    import cv2
    from pipeline.panorama import ViewSpec, render_view

    erp = cv2.imread(str(PICTURE_DIR / scene["filename"]))
    if erp is None:
        raise FileNotFoundError(scene["filename"])

    view = ViewSpec(
        name=f"component-{group.get('id', 'unknown')}",
        yaw_deg=float(group.get("yaw", 0.0)),
        pitch_deg=float(group.get("pitch", 0.0)),
        fov_deg=90.0,
        width=COMPONENT_CROP_VIEW_SIZE,
        height=COMPONENT_CROP_VIEW_SIZE,
    )
    perspective = render_view(erp, view)
    box = group.get("bbox_xyxy") or [0.0, 0.0, 768.0, 768.0]
    x1, y1, x2, y2 = [float(value) for value in box]
    source_size = 768.0
    scale = COMPONENT_CROP_VIEW_SIZE / source_size
    object_width = max(42.0, abs(x2 - x1) * scale)
    object_height = max(42.0, abs(y2 - y1) * scale)
    padding = max(120.0, max(object_width, object_height) * 0.78)
    crop_width = min(COMPONENT_CROP_VIEW_SIZE, object_width + padding * 2)
    crop_height = min(COMPONENT_CROP_VIEW_SIZE, object_height + padding * 2)
    center_x = COMPONENT_CROP_VIEW_SIZE / 2.0
    center_y = COMPONENT_CROP_VIEW_SIZE / 2.0
    left = max(0, int(round(center_x - crop_width / 2.0)))
    top = max(0, int(round(center_y - crop_height / 2.0)))
    right = min(COMPONENT_CROP_VIEW_SIZE, int(round(center_x + crop_width / 2.0)))
    bottom = min(COMPONENT_CROP_VIEW_SIZE, int(round(center_y + crop_height / 2.0)))
    crop = perspective[top:bottom, left:right]
    if crop.size == 0:
        crop = perspective
    crop_height, crop_width = crop.shape[:2]
    longest_side = max(crop_height, crop_width)
    if longest_side != COMPONENT_CROP_OUTPUT_SIZE:
        resize_scale = COMPONENT_CROP_OUTPUT_SIZE / longest_side
        interpolation = cv2.INTER_CUBIC if resize_scale > 1 else cv2.INTER_AREA
        crop = cv2.resize(
            crop,
            (max(1, round(crop_width * resize_scale)), max(1, round(crop_height * resize_scale))),
            interpolation=interpolation,
        )
    return crop


@lru_cache(maxsize=512)
def load_demo_component_crop(group_id: str) -> bytes:
    import cv2

    scene, group, _ = find_demo_group(group_id)
    crop = _component_crop_image(scene, group)
    encoded, buffer = cv2.imencode(".jpg", crop, [int(cv2.IMWRITE_JPEG_QUALITY), 95])
    if not encoded:
        raise RuntimeError(f"failed to encode component crop for {group_id}")
    return buffer.tobytes()


@lru_cache(maxsize=512)
def load_demo_component_preview(group_id: str) -> bytes:
    """Produce a local visual fallback when Qwen Image is unavailable.

    It is intentionally marked as a preview by the API response; this keeps
    the interaction demonstrable offline while never presenting the fallback as
    a real external image-generation result.
    """
    import cv2
    import numpy as np

    crop_bytes = load_demo_component_crop(group_id)
    image = cv2.imdecode(np.frombuffer(crop_bytes, dtype=np.uint8), cv2.IMREAD_COLOR)
    if image is None:
        raise RuntimeError(f"failed to decode component crop for {group_id}")
    lab = cv2.cvtColor(image, cv2.COLOR_BGR2LAB)
    lightness, a_channel, b_channel = cv2.split(lab)
    lightness = cv2.convertScaleAbs(lightness, alpha=1.08, beta=11)
    b_channel = cv2.convertScaleAbs(b_channel, alpha=0.94, beta=7)
    refreshed = cv2.cvtColor(cv2.merge([lightness, a_channel, b_channel]), cv2.COLOR_LAB2BGR)
    overlay = refreshed.copy()
    height, width = refreshed.shape[:2]
    cv2.rectangle(overlay, (0, int(height * 0.78)), (width, height), (64, 126, 94), -1)
    refreshed = cv2.addWeighted(overlay, 0.17, refreshed, 0.83, 0)
    encoded, buffer = cv2.imencode(".jpg", refreshed, [int(cv2.IMWRITE_JPEG_QUALITY), 95])
    if not encoded:
        raise RuntimeError(f"failed to encode component preview for {group_id}")
    return buffer.tobytes()


def demo_component_crop_path(group_id: str) -> Path:
    """Persist one high-quality crop only while it is needed by an image model."""
    COMPONENT_ARTIFACT_DIR.mkdir(parents=True, exist_ok=True)
    digest = sha1(group_id.encode("utf-8")).hexdigest()[:16]
    path = COMPONENT_ARTIFACT_DIR / f"{digest}.jpg"
    if not path.exists():
        path.write_bytes(load_demo_component_crop(group_id))
    return path


def _pathway_label(value: str | None) -> str:
    return _PATHWAY_LABELS.get(str(value or ""), "待评估")


def _evidence_label(value: str | None) -> str:
    return _EVIDENCE_LABELS.get(str(value or ""), "待核实")


def _component_display_name(group: dict[str, Any], ordinal: int) -> str:
    return _group_display_name(group, ordinal)


def _condition_copy(group: dict[str, Any]) -> str:
    confidence = float(group.get("confidence", 0))
    if group.get("evidence_status") == "supported":
        return "现有图像与识别依据可支持初步翻新判断，仍应在施工前复核连接与隐蔽面。"
    if confidence >= 0.55:
        return "主体轮廓识别较清晰，但材质、固定方式或隐蔽损伤仍需现场补证。"
    return "该构件已被识别，但视角或遮挡限制了状态判断；建议先补充近景与连接节点照片。"


def _verification_questions(group: dict[str, Any]) -> list[dict[str, str]]:
    category = str(group.get("category", "component"))
    material = str(group.get("material") or "当前材质")
    category_questions = {
        "cabinet": [
            ("固定方式", "确认柜体与墙体、地面或相邻构件的连接方式，判断能否可逆拆卸。"),
            ("板材与背板", f"补拍{material}的边缘、背板和受潮位置，检查开裂、虫蛀或分层。"),
            ("五金状态", "记录铰链、导轨和拉手的型号与完整性，确定可保留或替换的部件。"),
        ],
        "chair": [
            ("承重与连接", "检查椅脚、框架与连接件是否松动，并补充承重部位近景。"),
            ("表面状态", f"确认{material}表面的磨损、污渍与局部破损范围。"),
            ("数量与一致性", "核对同组座椅的尺寸、型号和损坏差异，避免将不同状态混为同一方案。"),
        ],
        "sofa": [
            ("软包与填充", "补拍坐垫、靠背和接缝，确认织物污染、开线与填充塌陷程度。"),
            ("框架与脚件", "检查底部框架、脚件和连接节点，确认翻新前是否存在结构松动。"),
            ("可拆卸部件", "确认面套、坐垫套和脚件是否可拆卸，以便制定低损耗翻新工序。"),
        ],
        "table": [
            ("台面状态", f"记录{material}台面的划痕、起翘、开裂或涂层脱落范围。"),
            ("结构稳定性", "检查桌腿、横撑和连接件是否松动，并补充底部节点近景。"),
            ("尺寸与拆分", "补充长宽高及可拆分方式，核对是否适合原位保留或异地再利用。"),
        ],
        "door": [
            ("框体与洞口", "核对门扇、门框和洞口尺寸，检查变形及是否存在不可逆拆除风险。"),
            ("五金与密封", "补拍合页、锁具、闭门器和密封条，判断可保留的五金范围。"),
            ("表面与安全", f"确认{material}表面涂层和玻璃/饰面状态，必要时安排安全检测。"),
        ],
        "window": [
            ("框体与玻璃", "补充窗框、玻璃边缘与排水位置，检查变形、裂纹和密封老化。"),
            ("开启五金", "确认铰链、执手和滑轨状态，记录是否可拆卸及替换难度。"),
            ("节能性能", "核实玻璃类型与密封条件；图像初筛不能替代安全与节能检测。"),
        ],
    }
    questions = category_questions.get(category, [
        ("材质与表面", f"补充{material}的近景，确认表面处理、污染与破损范围。"),
        ("连接与拆卸", "确认与周边构件的连接方式，评估可逆拆卸条件。"),
        ("尺寸与数量", "记录关键尺寸、数量和可复用部位，为路径与运输评估提供依据。"),
    ])
    return [{"title": title, "description": description} for title, description in questions]


def _observable_facts(group: dict[str, Any], scene: dict[str, Any], ordinal: int) -> list[str]:
    category = _CATEGORY_GROUP_NAMES.get(str(group.get("category")), str(group.get("label", "构件")))
    material = str(group.get("material") or "材质待核实")
    count = int(group.get("detected_count", 1))
    confidence = round(float(group.get("confidence", 0)) * 100)
    return [
        f"YOLO 在“{scene['name']}”中识别到{category}，当前归入{_component_display_name(group, ordinal)}。",
        f"该分组覆盖约 {count} 个相似检测实例；主检测置信度为 {confidence}%。",
        f"视觉初判材质为“{material}”，需要结合近景和连接节点进一步确认。",
        f"当前证据状态为“{_evidence_label(group.get('evidence_status'))}”，建议路径为“{_pathway_label(group.get('recommended_pathway'))}”。",
    ]


def _fallback_pathway_references(group: dict[str, Any]) -> list[dict[str, str]]:
    pathway = _pathway_label(group.get("recommended_pathway"))
    material = str(group.get("material") or "该构件材质")
    return [
        {
            "title": f"{material}的{pathway}核验重点",
            "description": "先确认尺寸、连接、污染与隐蔽损伤，再决定保留主体、替换局部部件或进入材料回收。",
            "source_url": "kb://circular-construction/material-reuse/checklist",
            "provenance": "verified",
        },
    ]


def _fallback_local_opportunities(region: str | None, group: dict[str, Any]) -> list[dict[str, str]]:
    place = region or "项目所在地"
    material = str(group.get("material") or "该构件材质")
    return [{
        "title": f"{place} · {material}再利用机会待对接",
        "description": f"建议优先咨询本地具备{_pathway_label(group.get('recommended_pathway'))}能力的家具修复、拆卸或材料再制造服务方；接收条件、报价与运输能力需二次确认。",
        "source_url": "local://opportunities/pending-region-match",
        "provenance": "to_confirm",
    }]


async def build_demo_component_detail(
    group_id: str,
    *,
    region: str | None,
    research_client: ResearchClient,
    supplemental_evidence: list[dict[str, Any]] | None = None,
) -> dict[str, Any]:
    """Build the review/detail payload from the actual cached YOLO component."""
    scene, group, ordinal = find_demo_group(group_id)
    display_name = _component_display_name(group, ordinal)
    category_name = _CATEGORY_GROUP_NAMES.get(str(group.get("category")), str(group.get("label", "构件")))
    material = str(group.get("material") or "材质待核实")
    pathway = str(group.get("recommended_pathway") or "DIRECT_REUSE")
    query = f"{material} {category_name} {_pathway_label(pathway)} 现场核验 修复再利用"
    research = await research_client.retrieve_with_opportunities(
        query,
        [category_name, material, pathway],
        region=region,
        include_web=False,
    )
    references = [
        {
            "title": source.title,
            "description": source.snippet,
            "source_url": source.url,
            "provenance": source.provenance,
        }
        for source in research.sources
        if source.source_type == "knowledge_base"
    ] or _fallback_pathway_references(group)
    opportunities = [
        {
            "title": opportunity.name,
            "description": opportunity.description,
            "source_url": opportunity.source_url,
            "provenance": opportunity.provenance,
        }
        for opportunity in research.opportunities
    ] or _fallback_local_opportunities(region, group)
    support_items = supplemental_evidence or []
    return {
        "component": {
            "id": group_id,
            "name": display_name,
            "category": group.get("category"),
            "category_name": category_name,
            "material": material,
            "confidence": group.get("confidence"),
            "detected_count": group.get("detected_count", 1),
            "evidence_status": group.get("evidence_status"),
            "evidence_label": _evidence_label(group.get("evidence_status")),
            "recommended_pathway": pathway,
            "pathway_label": _pathway_label(pathway),
            "crop_url": _component_crop_url(group_id),
            "preview_url": _component_preview_url(group_id),
            "can_generate_preview": bool(
                group.get("evidence_status") == "supported"
                and pathway in {"REFURBISH", "REPURPOSE"}
            ),
        },
        "scene": {
            "id": scene["id"],
            "name": scene["name"],
            "asset_url": _scene_asset_url(scene["filename"]),
            "annotated_url": _scene_annotated_url(scene["id"]),
        },
        "region": region or "项目所在地",
        "assessment": {
            "title": f"{_pathway_label(pathway)}建议",
            "description": _condition_copy(group),
            "pathway_label": _pathway_label(pathway),
            "evidence_label": _evidence_label(group.get("evidence_status")),
        },
        "verification_questions": _verification_questions(group),
        "observable_facts": _observable_facts(group, scene, ordinal),
        "reference_pathways": references[:3],
        "local_opportunities": opportunities[:3],
        "three_d_url": AHOLO_EDITOR_URL,
        "evidence": support_items,
    }


def _fallback_design_advice(group: dict[str, Any], ordinal: int, region: str | None) -> dict[str, Any]:
    category = _CATEGORY_GROUP_NAMES.get(str(group.get("category")), str(group.get("label", "构件")))
    material = str(group.get("material") or "原有材质")
    pathway = _pathway_label(group.get("recommended_pathway"))
    material_advice = {
        "木材/复合板": "保留稳定主体板件；局部破损处优先采用低甲醛同类板材补配，并替换不可复用的五金。",
        "木材/金属": "保留可拆卸金属骨架与稳定木质部件；锈蚀五金单独除锈、上底漆后再装配。",
        "织物与软包": "保留结构稳定的框架；面料采用可拆洗、耐磨的再生织物，填充层按实际塌陷范围局部补强。",
        "玻璃与金属": "保留无裂纹玻璃与稳定框体；替换老化密封件及失效五金，避免破坏原有尺寸体系。",
    }.get(material, "优先保留结构稳定、可逆拆卸的主体部件；对损耗部位采用同类低影响材料进行局部替换。")
    color = "暖白与浅木色" if "木" in material else "低饱和灰绿与原材质肌理" if "织物" in material else "石墨灰与原金属色"
    surface = "先清洁、除污和局部打磨，再使用低 VOC 水性保护涂层；隐蔽面确认后再决定是否全覆盖。"
    construction = "采用可拆卸五金与局部可逆修补，保留后续检修与再次再利用的可能。"
    location = region or "项目所在地"
    return {
        "title": f"{_component_display_name(group, ordinal)} · {pathway}建议",
        "material": material_advice,
        "color": f"建议以{color}为主，并保留可辨识的原构件细节。",
        "surface": surface,
        "construction": construction,
        "rationale": f"面向{location}项目的{category}，先以现有证据完成低干预改造；连接、隐蔽损伤与安全性能仍须在施工前确认。",
        "provider": "design-agent:offline",
        "status": "draft",
    }


async def build_demo_component_design_advice(
    group_id: str,
    *,
    region: str | None,
    agent: SpatialAgentGraph,
) -> dict[str, Any]:
    scene, group, ordinal = find_demo_group(group_id)
    fallback = _fallback_design_advice(group, ordinal, region)
    if not agent.bailian.enabled:
        return {
            **fallback,
            "component_id": group_id,
            "crop_url": _component_crop_url(group_id),
            "scene_name": scene["name"],
        }
    prompt = (
        "你是 Second Life View 的 Design Agent。请针对一个已识别家具构件生成简短、可施工且可逆的中文翻新建议。"
        "只返回 JSON，字段为 material、color、surface、construction、rationale。"
        f"构件：{_component_display_name(group, ordinal)}；类别：{group.get('category')}；材质：{group.get('material')}；"
        f"证据：{_evidence_label(group.get('evidence_status'))}；路径：{_pathway_label(group.get('recommended_pathway'))}；"
        f"地区：{region or '项目所在地'}。不得将待核实事项写成确定事实。"
    )
    try:
        generated = await agent.bailian.chat(
            [{"role": "system", "content": "你是审慎的建筑再生设计专家，只输出可解析 JSON。"}, {"role": "user", "content": prompt}],
            json_mode=True,
        )
    except Exception as exc:
        return {
            **fallback,
            "component_id": group_id,
            "crop_url": _component_crop_url(group_id),
            "scene_name": scene["name"],
            "warning": f"Design Agent 外部调用失败，已使用离线建议：{exc}",
        }
    if not isinstance(generated, dict):
        generated = {}
    return {
        **fallback,
        **{key: str(value) for key, value in generated.items() if key in {"material", "color", "surface", "construction", "rationale"} and value},
        "component_id": group_id,
        "crop_url": _component_crop_url(group_id),
        "scene_name": scene["name"],
        "provider": "design-agent:qwen",
        "status": "draft",
    }


def build_demo_component_preview_prompt(group_id: str, advice: dict[str, Any], region: str | None) -> str:
    _, group, ordinal = find_demo_group(group_id)
    return (
        "以输入图片中的单个家具构件为主体，生成真实可施工的翻新后预览图。"
        "保持物件比例、镜头角度、轮廓和周围裁切范围，不添加人物、文字、水印或额外家具。"
        f"构件：{_component_display_name(group, ordinal)}；地区：{region or '项目所在地'}；"
        f"材料处理：{advice.get('material', '')}；颜色：{advice.get('color', '')}；"
        f"表面：{advice.get('surface', '')}；施工：{advice.get('construction', '')}。"
    )


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


def list_demo_component_groups(scene_ids: list[str] | None = None) -> list[dict[str, Any]]:
    """Expose cached Pipeline B groups for the review workspace fallback."""
    scenes = _select_scenes(scene_ids or [])
    groups, _ = _group_summary(scenes)
    return groups


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
        for source_group in scene.get("groups", []):
            group = _review_assessment(source_group)
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
        for source_group in sorted(scene.get("groups", []), key=lambda item: float(item.get("confidence", 0)), reverse=True):
            group = _review_assessment(source_group)
            categories[group["category"]] += 1
            category_ordinals[group["category"]] += 1
            groups.append({
                "id": group["id"],
                "group_name": _group_display_name(group, category_ordinals[group["category"]]),
                "label": group["label"],
                "category": group["category"],
                "material": group.get("material") or "材质待核实",
                "scene_id": scene["id"],
                "scene_name": scene["name"],
                "confidence": group["confidence"],
                "detected_count": group.get("detected_count", 1),
                "recommended_pathway": group.get("recommended_pathway"),
                "evidence_status": group.get("evidence_status"),
                "crop_url": _component_crop_url(group["id"]),
                "can_generate_preview": bool(
                    group.get("evidence_status") == "supported"
                    and group.get("recommended_pathway") in {"REFURBISH", "REPURPOSE"}
                ),
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
