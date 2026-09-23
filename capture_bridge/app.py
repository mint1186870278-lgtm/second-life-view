from __future__ import annotations

from datetime import datetime
from pathlib import Path

from fastapi import FastAPI, HTTPException
from fastapi.middleware.cors import CORSMiddleware
from fastapi.responses import FileResponse

from capture_bridge import __version__
from capture_bridge.camera.aspect import assert_erp_aspect
from capture_bridge.camera.errors import BridgeError
from capture_bridge.camera.demo_auto import DemoAutoBackend, _default_demo_exe
from capture_bridge.camera.mock import MockCameraBackend
from capture_bridge.camera.sdk_import import SdkImportBackend, default_helper_path
from capture_bridge.camera.watch_demo import WatchDemoBackend
from capture_bridge.config import (
    BACKEND,
    CAPTURE_SESSION_DIR,
    CAPTURES_RAW,
    DEMO_PHOTO_MODE_INDEX,
    HOST,
    PORT,
    SDK_VERSION,
    WATCH_TIMEOUT_SEC,
)
from capture_bridge.config import repo_root
from capture_bridge.models import (
    CaptureMeta,
    CaptureResponse,
    CaptureStartRequest,
    CaptureStatus,
    ErrorBody,
    HealthResponse,
)
from capture_bridge.store import CaptureRecord, CaptureStore

store = CaptureStore()


def build_backend():
    if BACKEND == "mock":
        return MockCameraBackend()
    if BACKEND in {"demo_auto", "demo", "auto"}:
        return DemoAutoBackend(
            demo_exe=_default_demo_exe(repo_root()),
            download_dir=CAPTURES_RAW,
            timeout_sec=WATCH_TIMEOUT_SEC,
            photo_mode_index=DEMO_PHOTO_MODE_INDEX,
        )
    if BACKEND in {"watch", "watch_demo"}:
        return WatchDemoBackend(
            watch_dir=CAPTURES_RAW,
            timeout_sec=WATCH_TIMEOUT_SEC,
        )
    if BACKEND in {"sdk", "sdk_import", "import"}:
        return SdkImportBackend(helper_path=default_helper_path(repo_root()))
    raise RuntimeError(
        f"Unknown CAPTURE_BRIDGE_BACKEND={BACKEND!r} "
        "(use demo_auto|mock|watch|sdk_import)"
    )


backend = build_backend()

app = FastAPI(
    title="Second Life View Capture Bridge",
    version=__version__,
    description=(
        "Local import bridge: user shoots on camera body, software pulls JPG via Camera SDK. "
        "See docs/SDK_CAPTURE_DESIGN.md"
    ),
)

# Local web UI will call this; tighten later when auth is defined with FE/BE.
app.add_middleware(
    CORSMiddleware,
    allow_origins=["*"],
    allow_credentials=True,
    allow_methods=["*"],
    allow_headers=["*"],
)


def _new_capture_id() -> str:
    return "cap_" + datetime.now().strftime("%Y%m%d_%H%M%S_%f")[:-3]


def _preview_url(capture_id: str) -> str:
    return f"http://{HOST}:{PORT}/capture/{capture_id}/preview"


def _to_response(record: CaptureRecord) -> CaptureResponse:
    return CaptureResponse(
        capture_id=record.capture_id,
        status=CaptureStatus(record.status),
        local_path=str(record.local_path) if record.local_path else None,
        preview_url=_preview_url(record.capture_id) if record.local_path else None,
        width=record.width,
        height=record.height,
        file_size_bytes=record.file_size_bytes,
        project_id=record.project_id,
        scene_label=record.scene_label,
        meta=CaptureMeta(
            camera_model="X4 Air",
            sdk_version=SDK_VERSION,
            in_camera_stitch=record.in_camera_stitch,
            camera_file=record.camera_file,
            backend=record.backend,
        ),
        error_code=record.error_code,
        error_message=record.error_message,
    )


@app.get("/health", response_model=HealthResponse)
def health() -> HealthResponse:
    info = backend.health()
    return HealthResponse(
        ok=True,
        sdk_version=SDK_VERSION,
        camera_connected=info.connected,
        camera_model=info.model,
        firmware=info.firmware,
        backend=backend.name,
        detail=info.detail,
    )


@app.post(
    "/import/latest",
    response_model=CaptureResponse,
    responses={409: {"model": ErrorBody}, 400: {"model": ErrorBody}, 503: {"model": ErrorBody}},
)
@app.post(
    "/capture/start",
    response_model=CaptureResponse,
    responses={409: {"model": ErrorBody}, 400: {"model": ErrorBody}, 503: {"model": ErrorBody}},
)
def import_latest(body: CaptureStartRequest) -> CaptureResponse:
    """Pull latest photo from camera (or mock/watch backend). Not remote TakePhoto."""
    if not store.try_begin():
        raise HTTPException(
            status_code=409,
            detail=ErrorBody(
                error_code="BUSY",
                error_message="Another import is in progress",
            ).model_dump(),
        )

    capture_id = _new_capture_id()
    CAPTURE_SESSION_DIR.mkdir(parents=True, exist_ok=True)

    try:
        raw = backend.capture_photo(CAPTURE_SESSION_DIR, capture_id)
        assert_erp_aspect(raw.width, raw.height)
        size = raw.local_path.stat().st_size
        record = CaptureRecord(
            capture_id=capture_id,
            project_id=body.project_id,
            scene_label=body.scene_label,
            status=CaptureStatus.preview_ready.value,
            local_path=raw.local_path,
            width=raw.width,
            height=raw.height,
            file_size_bytes=size,
            camera_file=raw.camera_file,
            backend=backend.name,
            in_camera_stitch=raw.in_camera_stitch,
        )
        store.put(record)
        return _to_response(record)
    except BridgeError as exc:
        record = CaptureRecord(
            capture_id=capture_id,
            project_id=body.project_id,
            scene_label=body.scene_label,
            status=CaptureStatus.error.value,
            backend=backend.name,
            error_code=exc.code,
            error_message=exc.message,
        )
        store.put(record)
        status = 503 if exc.code in {"CAMERA_NOT_FOUND", "SDK_INIT_FAILED", "NO_NEW_FILE"} else 400
        raise HTTPException(
            status_code=status,
            detail=ErrorBody(error_code=exc.code, error_message=exc.message).model_dump(),
        ) from exc
    finally:
        store.end()


@app.get("/capture/{capture_id}", response_model=CaptureResponse)
def capture_get(capture_id: str) -> CaptureResponse:
    record = store.get(capture_id)
    if record is None:
        raise HTTPException(status_code=404, detail="capture not found")
    return _to_response(record)


@app.get("/capture/{capture_id}/preview")
def capture_preview(capture_id: str) -> FileResponse:
    record = store.get(capture_id)
    if record is None or record.local_path is None or not record.local_path.exists():
        raise HTTPException(status_code=404, detail="preview not available")
    return FileResponse(record.local_path, media_type="image/jpeg")


@app.post("/capture/{capture_id}/discard", response_model=CaptureResponse)
def capture_discard(capture_id: str) -> CaptureResponse:
    record = store.discard(capture_id)
    if record is None:
        raise HTTPException(status_code=404, detail="capture not found")
    return _to_response(record)


def create_app() -> FastAPI:
    return app
