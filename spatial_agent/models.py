from __future__ import annotations
from datetime import datetime, timezone
from typing import Any, Literal
from uuid import uuid4
from pydantic import BaseModel, Field, ConfigDict, model_validator


def utcnow() -> datetime:
    return datetime.now(timezone.utc)

class Detection(BaseModel):
    model_config = ConfigDict(extra="allow", populate_by_name=True)
    id: str | None = None
    class_name: str = Field(alias="class")
    bbox: list[float] = Field(default_factory=lambda: [0.0, 0.0, 0.0, 0.0], min_length=4, max_length=4)
    bbox_xyxy: list[float] | None = Field(default=None, min_length=4, max_length=4)
    segmentation: dict[str, Any] | list[Any] | None = None
    confidence: float = 0.0
    track_id: str | None = None
    source: str = "windows_yolo_gateway"
    raw_label: str | None = None
    yaw: float | None = None
    pitch: float | None = None
    material: str | None = None
    visible_condition: str | None = None
    visible_damage_clue: str | None = None
    component_batch_id: str | None = None
    pathway_assessment: dict[str, Any] = Field(default_factory=dict)
    recommended_pathway: str | None = None

    @model_validator(mode="before")
    @classmethod
    def normalize_yolo_payload(cls, value: Any) -> Any:
        if not isinstance(value, dict):
            return value
        data = dict(value)
        if "class" not in data and "class_name" not in data:
            data["class"] = data.get("label") or data.get("category") or "unknown"
        if "bbox" not in data and data.get("bbox_xyxy") is not None:
            data["bbox"] = data["bbox_xyxy"]
        return data

class Evidence(BaseModel):
    id: str = Field(default_factory=lambda: f"ev_{uuid4().hex[:10]}")
    kind: Literal["image", "video_frame", "detection", "vlm", "user", "search", "3d"]
    source: str
    uri: str | None = None
    observed_at: datetime = Field(default_factory=utcnow)
    confidence: float = 0.0
    claims: dict[str, Any] = Field(default_factory=dict)
    provenance: Literal["verified", "inferred", "to_confirm"] = "inferred"

class SpatialObject(BaseModel):
    id: str = Field(default_factory=lambda: f"obj_{uuid4().hex[:10]}")
    category: str
    bbox: list[float] | None = None
    bbox_xyxy: list[float] | None = Field(default=None, min_length=4, max_length=4)
    segmentation: dict[str, Any] | list[Any] | None = None
    confidence: float = 0.0
    source: str = "perception"
    raw_label: str | None = None
    yaw: float | None = None
    pitch: float | None = None
    visible_damage_clue: str | None = None
    component_batch_id: str | None = None
    pathway_assessment: dict[str, Any] = Field(default_factory=dict)
    recommended_pathway: str | None = None
    material: str | None = None
    condition: str | None = None
    reuse_potential: Literal["reuse", "refurbish", "recycle", "unknown"] = "unknown"
    dimensions: dict[str, float] | None = None
    evidence_ids: list[str] = Field(default_factory=list)
    missing_fields: list[str] = Field(default_factory=list)

class SpatialRelation(BaseModel):
    subject_id: str
    predicate: str
    object_id: str
    confidence: float = 0.0
    evidence_ids: list[str] = Field(default_factory=list)

class CaptureAction(BaseModel):
    id: str = Field(default_factory=lambda: f"act_{uuid4().hex[:10]}")
    action_type: Literal["rotate_and_capture", "zoom_region", "request_user_photo", "capture_video"]
    target_object_id: str | None = None
    target_bbox: list[float] | None = None
    reason: str
    priority: Literal["low", "medium", "high"] = "medium"
    camera_command: dict[str, Any] = Field(default_factory=dict)

class SearchSource(BaseModel):
    title: str
    url: str
    snippet: str
    source_type: Literal["knowledge_base", "web", "local_opportunity"]
    confidence: float = 0.0
    # verified: curated or directly cited fact; inferred: search lead or
    # model-supported interpretation; to_confirm: live opportunity or claim
    # that still needs field confirmation.
    provenance: Literal["verified", "inferred", "to_confirm"] = "inferred"

class DesignProposal(BaseModel):
    title: str
    rationale: str
    prompt: str
    image_url: str | None = None
    generation_task_id: str | None = None
    asset_object_ids: list[str] = Field(default_factory=list)
    constraints: list[str] = Field(default_factory=list)
    status: Literal["draft", "submitted", "generated", "needs_input", "failed"] = "draft"

class AgentEvent(BaseModel):
    timestamp: datetime = Field(default_factory=utcnow)
    agent: str
    action: str
    message: str
    data: dict[str, Any] = Field(default_factory=dict)

class RunState(BaseModel):
    run_id: str = Field(default_factory=lambda: f"run_{uuid4().hex[:10]}")
    user_goal: str = ""
    image_urls: list[str] = Field(default_factory=list)
    detections: list[Detection] = Field(default_factory=list)
    evidence: list[Evidence] = Field(default_factory=list)
    objects: list[SpatialObject] = Field(default_factory=list)
    relations: list[SpatialRelation] = Field(default_factory=list)
    capture_actions: list[CaptureAction] = Field(default_factory=list)
    sources: list[SearchSource] = Field(default_factory=list)
    designs: list[DesignProposal] = Field(default_factory=list)
    status: Literal["running", "awaiting_evidence", "ready_for_design", "completed", "failed"] = "running"
    next_agent: str | None = None
    iteration: int = 0
    events: list[AgentEvent] = Field(default_factory=list)
    errors: list[str] = Field(default_factory=list)
    metadata: dict[str, Any] = Field(default_factory=dict)

class AnalyzeRequest(BaseModel):
    user_goal: str = "评估空间构件的再利用机会，并提出下一步需要采集的证据"
    image_urls: list[str] = Field(default_factory=list)
    detections: list[Detection] = Field(default_factory=list)
    scene_slug: str | None = None
    use_yolo_fixture: bool = False
    run_id: str | None = None
    enable_research: bool = True
    enable_design: bool = True
    enable_3d: bool = False
    region: str | None = None
    include_web: bool = False

class DesignRequest(BaseModel):
    run_id: str | None = None
    object_ids: list[str] = Field(default_factory=list)
    brief: str = "保留原有结构，将旧木柜翻新为现代风格，使用低挥发环保材料"
    reference_image_url: str | None = None

class ReconstructRequest(BaseModel):
    run_id: str | None = None
    image_url: str | None = None
    image_urls: list[str] = Field(default_factory=list)
    version: Literal["G1", "G1-Turbo"] = "G1-Turbo"
    wait: bool = False

class CaptureRequest(BaseModel):
    run_id: str
    action_id: str
    image_url: str | None = None
    detections: list[Detection] = Field(default_factory=list)


class CameraFrameRequest(BaseModel):
    """Payload emitted by the Windows CameraSDK bridge.

    ``run_id``/``action_id`` are present when the Evidence Agent requested a
    targeted recapture.  For the first frame they can be omitted and the
    bridge creates a new run.  ``metadata`` carries camera-side details such
    as model, projection, frame id and capture timestamp without coupling the
    Linux service to the Windows SDK ABI.
    """

    run_id: str | None = None
    action_id: str | None = None
    user_goal: str = "评估空间构件的再利用机会，并提出下一步需要采集的证据"
    image_url: str
    detections: list[Detection] = Field(default_factory=list)
    metadata: dict[str, Any] = Field(default_factory=dict)

class WorldRequest(BaseModel):
    run_id: str | None = None
    resources: list[str] = Field(default_factory=list)
    prompt: str | None = None
    image_url: str | None = None
    quality: Literal["low", "normal", "high"] = "low"
    wait: bool = False

class SpatialGenRequest(BaseModel):
    run_id: str | None = None
    prompt: str
    image_url: str | None = None

class ResearchRequest(BaseModel):
    run_id: str
    query: str
    region: str | None = None
    include_web: bool = False


class DemoAnalyzeRequest(BaseModel):
    scene_ids: list[str] = Field(default_factory=list)
    user_goal: str = "评估已接入空间中的构件再利用机会，并提出低碳翻新方案"
    region: str | None = None
    spatial_prompt: str = "保留原空间结构与尺度，更新为明亮、低碳、可逆施工的现代室内空间"
    include_web: bool = False
