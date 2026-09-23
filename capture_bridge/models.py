from __future__ import annotations

from enum import Enum
from typing import Any

from pydantic import BaseModel, Field


class CaptureStatus(str, Enum):
    preview_ready = "preview_ready"
    discarded = "discarded"
    uploading = "uploading"
    uploaded = "uploaded"
    error = "error"


class CaptureOptions(BaseModel):
    photo_mode: str = "pano"
    require_in_camera_stitch: bool = True


class CaptureStartRequest(BaseModel):
    project_id: str = Field(..., description="Backend project id (opaque to Bridge)")
    scene_label: str = Field("", description="Optional display label, e.g. 屋顶花园")
    options: CaptureOptions = Field(default_factory=CaptureOptions)


class CaptureMeta(BaseModel):
    source_type: str = "insta360_camera"
    camera_model: str = "X4 Air"
    sdk_version: str = "2.2.0"
    in_camera_stitch: bool = True
    camera_file: str | None = None
    backend: str | None = None


class CaptureResponse(BaseModel):
    capture_id: str
    status: CaptureStatus
    local_path: str | None = None
    preview_url: str | None = None
    width: int | None = None
    height: int | None = None
    file_size_bytes: int | None = None
    mime_type: str = "image/jpeg"
    project_id: str | None = None
    scene_label: str | None = None
    meta: CaptureMeta | None = None
    error_code: str | None = None
    error_message: str | None = None


class HealthResponse(BaseModel):
    ok: bool
    sdk_version: str
    camera_connected: bool
    camera_model: str | None = None
    firmware: str | None = None
    backend: str
    detail: str | None = None


class ErrorBody(BaseModel):
    error_code: str
    error_message: str
    detail: dict[str, Any] | None = None
