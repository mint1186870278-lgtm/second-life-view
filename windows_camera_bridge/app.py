"""Loopback-only HTTP wrapper around the Windows CameraSDK CLI.

Run this process on the Windows host physically connected to the Insta360
camera.  It intentionally does not expose a public listener; the Linux server
reaches it through an SSH reverse tunnel and a shared bearer token.
"""
from __future__ import annotations

import asyncio
import json
import mimetypes
import os
import secrets
import subprocess
from dataclasses import dataclass
from pathlib import Path
from typing import Any, Literal
from urllib.parse import urlsplit

import httpx
from fastapi import Depends, Header, HTTPException, FastAPI
from fastapi.responses import FileResponse, JSONResponse, Response
from pydantic import BaseModel, ConfigDict, Field
from dotenv import load_dotenv


RESULT_PREFIX = "SECOND_LIFE_CAMERA_RESULT="
load_dotenv(Path(__file__).with_name(".env"))


@dataclass(frozen=True)
class BridgeSettings:
    executable: Path
    output_dir: Path
    token: str
    service_port: int
    camera_serial: str
    media_models_dir: str
    linux_ingest_url: str
    linux_ingest_token: str
    linux_ingest_timeout: float
    allowed_web_origin: str

    @classmethod
    def from_environment(cls) -> "BridgeSettings":
        executable = os.getenv("CAMERA_BRIDGE_EXECUTABLE", "").strip()
        token = os.getenv("CAMERA_BRIDGE_TOKEN", "").strip()
        if not executable:
            raise RuntimeError("CAMERA_BRIDGE_EXECUTABLE is required")
        if not token:
            raise RuntimeError("CAMERA_BRIDGE_TOKEN is required")
        return cls(
            executable=Path(executable).expanduser().resolve(),
            output_dir=Path(os.getenv("CAMERA_BRIDGE_OUTPUT_DIR", "./captures")).expanduser().resolve(),
            token=token,
            service_port=int(os.getenv("CAMERA_BRIDGE_SERVICE_PORT", "9099")),
            camera_serial=os.getenv("CAMERA_BRIDGE_CAMERA_SERIAL", "").strip(),
            media_models_dir=os.getenv("CAMERA_BRIDGE_MEDIA_MODELS_DIR", "").strip(),
            linux_ingest_url=os.getenv("LINUX_CAMERA_INGEST_URL", "").strip(),
            linux_ingest_token=os.getenv("LINUX_CAMERA_INGEST_TOKEN", "").strip(),
            linux_ingest_timeout=float(os.getenv("LINUX_CAMERA_INGEST_TIMEOUT", "900")),
            allowed_web_origin=os.getenv("CAMERA_BRIDGE_ALLOWED_WEB_ORIGIN", "").strip(),
        )


settings = BridgeSettings.from_environment()
settings.output_dir.mkdir(parents=True, exist_ok=True)
command_lock = asyncio.Lock()
artifacts: dict[str, Path] = {}

app = FastAPI(title="Second Life View Windows Camera Gateway", version="1.0.0")


class CapturePayload(BaseModel):
    raw_type: Literal["off", "dng", "pureshot", "pureshot_raw"] = "off"
    timeout_ms: int = Field(default=0, ge=0, le=600_000)
    stitch: bool = True
    output_width: int = Field(default=4096, ge=512, le=15_520)
    output_height: int = Field(default=2048, ge=256, le=7_760)


class DownloadPayload(CapturePayload):
    remote_path: str = Field(min_length=1, max_length=2048)


class LinuxIngestPayload(BaseModel):
    """Fields forwarded to Linux alongside a Windows-local ERP JPEG.

    There intentionally is no ``detections`` field: the Linux service owns
    all YOLO-World inference and the resulting detection JSON.
    """

    run_id: str | None = Field(default=None, max_length=256)
    action_id: str | None = Field(default=None, max_length=256)
    user_goal: str = Field(
        default="评估空间构件的再利用机会，并提出下一步需要采集的证据",
        max_length=4000,
    )
    metadata: dict[str, Any] = Field(default_factory=dict)


class LocalFileIngestPayload(LinuxIngestPayload):
    """Push an already downloaded file below ``CAMERA_BRIDGE_OUTPUT_DIR``."""

    filename: str = Field(min_length=1, max_length=1024)


class CaptureAndIngestPayload(CapturePayload, LinuxIngestPayload):
    """Capture/stitch on Windows and push the produced ERP JPEG to Linux."""


class BrowserCaptureAndIngestPayload(CaptureAndIngestPayload):
    """Public-web-safe browser command; secrets remain in the Windows gateway."""

    model_config = ConfigDict(extra="forbid")


async def require_gateway_token(authorization: str | None = Header(default=None)) -> None:
    expected = f"Bearer {settings.token}"
    if not authorization or not secrets.compare_digest(authorization, expected):
        raise HTTPException(status_code=401, detail="invalid camera gateway token")


def _allowed_browser_origin() -> str:
    """Return the one web origin permitted to operate this loopback gateway."""
    if not settings.allowed_web_origin:
        raise HTTPException(
            status_code=503,
            detail="browser capture is disabled; set CAMERA_BRIDGE_ALLOWED_WEB_ORIGIN",
        )
    parsed = urlsplit(settings.allowed_web_origin)
    hostname = (parsed.hostname or "").lower()
    if (
        parsed.scheme not in {"http", "https"}
        or not parsed.netloc
        or parsed.path not in {"", "/"}
        or parsed.query
        or parsed.fragment
        or (parsed.scheme == "http" and hostname not in {"localhost", "127.0.0.1", "::1"})
    ):
        raise HTTPException(
            status_code=503,
            detail=(
                "CAMERA_BRIDGE_ALLOWED_WEB_ORIGIN must be one HTTPS origin "
                "(HTTP is allowed only for localhost development)"
            ),
        )
    return f"{parsed.scheme}://{parsed.netloc}"


def _browser_cors_headers(origin: str) -> dict[str, str]:
    return {
        "Access-Control-Allow-Origin": origin,
        "Access-Control-Allow-Methods": "POST, OPTIONS",
        "Access-Control-Allow-Headers": "Content-Type, X-Second-Life-Client",
        # Older Chromium PNA implementations use this explicit opt-in. Newer
        # Local Network Access implementations prompt the user instead, and
        # accept this header harmlessly.
        "Access-Control-Allow-Private-Network": "true",
        "Access-Control-Max-Age": "600",
        "Vary": "Origin",
    }


async def require_browser_client(
    origin: str | None = Header(default=None),
    client_marker: str | None = Header(default=None, alias="X-Second-Life-Client"),
) -> str:
    expected_origin = _allowed_browser_origin()
    if origin != expected_origin:
        raise HTTPException(status_code=403, detail="browser origin is not allowed to control this camera")
    # Force a non-simple CORS request. A malicious site cannot submit this
    # custom header through a cross-origin HTML form, so the browser must first
    # complete the allowlisted preflight above.
    if client_marker != "capture-ui-v1":
        raise HTTPException(status_code=400, detail="missing browser client marker")
    return expected_origin


def _parse_result(stdout: bytes) -> dict[str, Any]:
    text = stdout.decode("utf-8", errors="replace")
    for line in reversed(text.splitlines()):
        if not line.startswith(RESULT_PREFIX):
            continue
        try:
            value = json.loads(line[len(RESULT_PREFIX) :])
        except json.JSONDecodeError as exc:
            raise RuntimeError("camera CLI emitted malformed result JSON") from exc
        if isinstance(value, dict):
            return value
    raise RuntimeError("camera CLI did not emit a result marker")


async def invoke_cli(command: str, *, arguments: list[str] | None = None) -> dict[str, Any]:
    if not settings.executable.is_file():
        raise HTTPException(status_code=503, detail=f"camera CLI does not exist: {settings.executable}")

    invocation = [
        str(settings.executable),
        "--command",
        command,
        "--json",
        "--output-dir",
        str(settings.output_dir),
        "--service-port",
        str(settings.service_port),
    ]
    if settings.camera_serial:
        invocation.extend(["--camera-serial", settings.camera_serial])
    if settings.media_models_dir:
        invocation.extend(["--media-models-dir", settings.media_models_dir])
    invocation.extend(arguments or [])

    try:
        async with command_lock:
            process = await asyncio.create_subprocess_exec(
                *invocation,
                stdout=asyncio.subprocess.PIPE,
                stderr=asyncio.subprocess.PIPE,
                creationflags=getattr(subprocess, "CREATE_NO_WINDOW", 0),
            )
            stdout, stderr = await asyncio.wait_for(process.communicate(), timeout=720)
    except TimeoutError as exc:
        raise HTTPException(status_code=504, detail="camera operation exceeded 12 minutes") from exc
    except OSError as exc:
        raise HTTPException(status_code=503, detail=f"could not start camera CLI: {exc}") from exc

    try:
        result = _parse_result(stdout)
    except RuntimeError as exc:
        diagnostic = stderr.decode("utf-8", errors="replace").strip()[-1000:]
        raise HTTPException(status_code=502, detail=f"camera CLI protocol error: {exc}; {diagnostic}") from exc

    if process.returncode != 0 or not result.get("ok"):
        detail = str(result.get("error") or stderr.decode("utf-8", errors="replace").strip() or "unknown error")
        raise HTTPException(status_code=409, detail=detail[:1000])
    return result


def register_artifact(result: dict[str, Any]) -> dict[str, Any]:
    candidate = result.get("artifact_path")
    if not isinstance(candidate, str) or not candidate:
        raise HTTPException(status_code=502, detail="camera CLI did not return an artifact path")
    artifact_path = Path(candidate).resolve()
    if not artifact_path.is_file() or not artifact_path.is_relative_to(settings.output_dir):
        raise HTTPException(status_code=502, detail="camera CLI returned an invalid artifact path")
    artifact_id = secrets.token_urlsafe(18)
    artifacts[artifact_id] = artifact_path
    result.pop("artifact_path", None)
    result["artifact_id"] = artifact_id
    result["artifact_url"] = f"/v1/artifacts/{artifact_id}"
    result["filename"] = artifact_path.name
    return result


def capture_arguments(payload: CapturePayload) -> list[str]:
    return [
        "--raw-type",
        payload.raw_type,
        "--timeout-ms",
        str(payload.timeout_ms),
        "--stitch",
        "true" if payload.stitch else "false",
        "--output-width",
        str(payload.output_width),
        "--output-height",
        str(payload.output_height),
    ]


def _require_linux_ingest_configuration() -> str:
    """Return the explicitly configured HTTPS Linux ingest endpoint.

    The Windows host carries a bearer token and image evidence, so accepting a
    plain HTTP URL here would make an accidental insecure deployment too easy.
    The endpoint path is fixed to avoid this gateway becoming a generic proxy.
    """
    if not settings.linux_ingest_url or not settings.linux_ingest_token:
        raise HTTPException(
            status_code=503,
            detail=(
                "Linux ingest is not configured; set LINUX_CAMERA_INGEST_URL "
                "and LINUX_CAMERA_INGEST_TOKEN"
            ),
        )
    parsed = urlsplit(settings.linux_ingest_url)
    if (
        parsed.scheme != "https"
        or not parsed.netloc
        or parsed.query
        or parsed.fragment
        or parsed.path.rstrip("/") != "/api/v1/camera/ingest"
    ):
        raise HTTPException(
            status_code=503,
            detail="LINUX_CAMERA_INGEST_URL must be an HTTPS /api/v1/camera/ingest URL",
        )
    if settings.linux_ingest_timeout <= 0:
        raise HTTPException(status_code=503, detail="LINUX_CAMERA_INGEST_TIMEOUT must be positive")
    return settings.linux_ingest_url.rstrip("/")


def _local_output_file(filename: str) -> Path:
    """Resolve one existing image below the configured camera output folder."""
    requested = Path(filename)
    if requested.is_absolute() or any(part == ".." for part in requested.parts):
        raise HTTPException(status_code=400, detail="filename must be relative to CAMERA_BRIDGE_OUTPUT_DIR")
    path = (settings.output_dir / requested).resolve()
    if not path.is_relative_to(settings.output_dir) or not path.is_file():
        raise HTTPException(status_code=404, detail="local camera artifact not found")
    if path.suffix.lower() not in {".jpg", ".jpeg"}:
        raise HTTPException(status_code=400, detail="Linux ingest requires a stitched .jpg or .jpeg artifact")
    return path


def _ingest_metadata(
    *,
    path: Path,
    payload: LinuxIngestPayload,
    gateway_result: dict[str, Any] | None = None,
) -> dict[str, Any]:
    """Build camera metadata without trusting a client to provide SDK facts."""
    metadata = dict(payload.metadata)
    gateway_result = gateway_result or {}
    camera = gateway_result.get("camera")
    camera_details = camera if isinstance(camera, dict) else {}

    # An ERP projection is guaranteed for the only files accepted by this
    # push route.  Preserve caller metadata such as capture timestamp or site
    # label, while taking device identity from the CameraSDK result when known.
    metadata.update(
        {
            "frame_id": str(gateway_result.get("frame_id") or metadata.get("frame_id") or path.stem),
            "projection": "equirectangular",
            "camera_model": camera_details.get("camera_name") or metadata.get("camera_model"),
            "camera_serial": camera_details.get("serial") or metadata.get("camera_serial"),
            "camera_firmware": camera_details.get("firmware") or metadata.get("camera_firmware"),
        }
    )
    if gateway_result.get("remote_paths"):
        metadata["remote_paths"] = gateway_result["remote_paths"]
    return {key: value for key, value in metadata.items() if value is not None}


def _post_artifact_to_linux_sync(
    *,
    endpoint: str,
    path: Path,
    payload: LinuxIngestPayload,
    metadata: dict[str, Any],
) -> dict[str, Any]:
    form: dict[str, str] = {
        "user_goal": payload.user_goal,
        "metadata": json.dumps(metadata, ensure_ascii=False, separators=(",", ":")),
    }
    if payload.run_id:
        form["run_id"] = payload.run_id
    if payload.action_id:
        form["action_id"] = payload.action_id

    media_type = mimetypes.guess_type(path.name)[0] or "image/jpeg"
    headers = {"Authorization": f"Bearer {settings.linux_ingest_token}"}
    try:
        # This synchronous client runs in a worker thread (below), preventing
        # a 200MB multipart upload from blocking the Windows gateway event
        # loop.  Never inherit ambient proxy settings for this bearer request.
        with path.open("rb") as image, httpx.Client(
            timeout=settings.linux_ingest_timeout,
            trust_env=False,
        ) as client:
            response = client.post(
                endpoint,
                headers=headers,
                data=form,
                files={"file": (path.name, image, media_type)},
            )
    except OSError as exc:
        raise HTTPException(status_code=404, detail=f"could not read local camera artifact: {exc}") from exc
    except httpx.HTTPError as exc:
        raise HTTPException(status_code=502, detail=f"Linux camera ingest is unreachable: {exc}") from exc

    if response.is_error:
        detail = response.text.strip().replace("\n", " ")[:1000]
        # The gateway is a trusted proxy for an authenticated local caller;
        # preserve Linux validation codes, but do not forward the server's
        # arbitrary response body unchanged.
        status = response.status_code if 400 <= response.status_code < 500 else 502
        raise HTTPException(
            status_code=status,
            detail=f"Linux camera ingest returned HTTP {response.status_code}: {detail or 'unknown error'}",
        )
    try:
        result = response.json()
    except ValueError as exc:
        raise HTTPException(status_code=502, detail="Linux camera ingest returned invalid JSON") from exc
    if not isinstance(result, dict):
        raise HTTPException(status_code=502, detail="Linux camera ingest returned an invalid response object")
    return result


async def post_artifact_to_linux(
    path: Path,
    payload: LinuxIngestPayload,
    *,
    gateway_result: dict[str, Any] | None = None,
) -> dict[str, Any]:
    endpoint = _require_linux_ingest_configuration()
    metadata = _ingest_metadata(path=path, payload=payload, gateway_result=gateway_result)
    return await asyncio.to_thread(
        _post_artifact_to_linux_sync,
        endpoint=endpoint,
        path=path,
        payload=payload,
        metadata=metadata,
    )


def _gateway_summary(result: dict[str, Any]) -> dict[str, Any]:
    camera = result.get("camera")
    return {
        "frame_id": result.get("frame_id"),
        "artifact_id": result.get("artifact_id"),
        "filename": result.get("filename"),
        "camera": camera if isinstance(camera, dict) else None,
        "remote_paths": result.get("remote_paths", []),
    }


@app.get("/health")
async def health() -> dict[str, Any]:
    return {
        "status": "ok",
        "service": "second-life-view-windows-camera-gateway",
        "output_dir": str(settings.output_dir),
        "cli_exists": settings.executable.is_file(),
    }


@app.get("/v1/status", dependencies=[Depends(require_gateway_token)])
async def camera_status() -> dict[str, Any]:
    return await invoke_cli("status")


@app.get("/v1/files", dependencies=[Depends(require_gateway_token)])
async def camera_files() -> dict[str, Any]:
    return await invoke_cli("list-files")


@app.post("/v1/capture", dependencies=[Depends(require_gateway_token)])
async def capture(payload: CapturePayload) -> dict[str, Any]:
    return register_artifact(await invoke_cli("capture", arguments=capture_arguments(payload)))


@app.post("/v1/download", dependencies=[Depends(require_gateway_token)])
async def download(payload: DownloadPayload) -> dict[str, Any]:
    arguments = ["--remote", payload.remote_path, *capture_arguments(payload)]
    return register_artifact(await invoke_cli("download", arguments=arguments))


@app.post("/v1/local-file/ingest", dependencies=[Depends(require_gateway_token)])
async def ingest_local_file(payload: LocalFileIngestPayload) -> dict[str, Any]:
    """Push an already stitched JPEG from the Windows capture directory to Linux.

    This is the normal endpoint for the "Windows has already downloaded the
    picture" workflow.  ``filename`` is deliberately relative to the gateway
    output folder so an authenticated caller cannot turn the gateway into an
    arbitrary local-file uploader.
    """
    path = _local_output_file(payload.filename)
    result = await post_artifact_to_linux(path, payload)
    result["gateway"] = {
        "source": "windows_local_file",
        "filename": path.name,
        "frame_id": result.get("asset", {}).get("frame_id", path.stem)
        if isinstance(result.get("asset"), dict)
        else path.stem,
    }
    return result


@app.post("/v1/capture-and-ingest", dependencies=[Depends(require_gateway_token)])
async def capture_and_ingest(payload: CaptureAndIngestPayload) -> dict[str, Any]:
    """Capture/stitch with the Windows SDK and immediately upload the JPEG.

    Linux remains the only party that runs YOLO-World.  The returned payload is
    the Linux ingest response (asset, annotation URLs, detection JSON and
    RunState), plus a small Windows gateway audit record.
    """
    gateway_result = register_artifact(
        await invoke_cli("capture", arguments=capture_arguments(payload))
    )
    path = artifacts[gateway_result["artifact_id"]]
    if not gateway_result.get("stitched") or path.suffix.lower() not in {".jpg", ".jpeg"}:
        raise HTTPException(
            status_code=409,
            detail="capture-and-ingest requires stitch=true and a stitched JPEG artifact",
        )
    result = await post_artifact_to_linux(path, payload, gateway_result=gateway_result)
    result["gateway"] = _gateway_summary(gateway_result)
    return result


@app.options("/v1/browser/capture-and-ingest")
async def browser_capture_preflight(origin: str | None = Header(default=None)) -> Response:
    """CORS/PNA preflight for the deployed web app to reach localhost."""
    expected_origin = _allowed_browser_origin()
    if origin != expected_origin:
        raise HTTPException(status_code=403, detail="browser origin is not allowed to control this camera")
    return Response(status_code=204, headers=_browser_cors_headers(expected_origin))


@app.post("/v1/browser/capture-and-ingest")
async def browser_capture_and_ingest(
    payload: BrowserCaptureAndIngestPayload,
    origin: str = Depends(require_browser_client),
) -> JSONResponse:
    """Capture for the public web UI without exposing gateway secrets to JS.

    The endpoint is still loopback-only at the process level.  It additionally
    requires one configured web origin and a CORS-preflighted custom header;
    the private Linux upload token is read only from this Windows process.
    """
    if not payload.stitch:
        raise HTTPException(status_code=422, detail="browser capture requires stitch=true for Linux ERP YOLO")
    result = await capture_and_ingest(payload)
    return JSONResponse(result, headers=_browser_cors_headers(origin))


@app.get("/v1/artifacts/{artifact_id}", dependencies=[Depends(require_gateway_token)])
async def get_artifact(artifact_id: str) -> FileResponse:
    path = artifacts.get(artifact_id)
    if not path or not path.is_file() or not path.is_relative_to(settings.output_dir):
        raise HTTPException(status_code=404, detail="camera artifact not found")
    return FileResponse(path, filename=path.name)
