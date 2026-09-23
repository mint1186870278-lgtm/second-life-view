"""Loopback-only HTTP wrapper around the Windows CameraSDK CLI.

Run this process on the Windows host physically connected to the Insta360
camera.  It intentionally does not expose a public listener; the Linux server
reaches it through an SSH reverse tunnel and a shared bearer token.
"""
from __future__ import annotations

import asyncio
import json
import os
import secrets
import subprocess
from dataclasses import dataclass
from pathlib import Path
from typing import Any, Literal

from fastapi import Depends, FastAPI, Header, HTTPException
from fastapi.responses import FileResponse
from pydantic import BaseModel, Field
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


async def require_gateway_token(authorization: str | None = Header(default=None)) -> None:
    expected = f"Bearer {settings.token}"
    if not authorization or not secrets.compare_digest(authorization, expected):
        raise HTTPException(status_code=401, detail="invalid camera gateway token")


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


@app.get("/v1/artifacts/{artifact_id}", dependencies=[Depends(require_gateway_token)])
async def get_artifact(artifact_id: str) -> FileResponse:
    path = artifacts.get(artifact_id)
    if not path or not path.is_file() or not path.is_relative_to(settings.output_dir):
        raise HTTPException(status_code=404, detail="camera artifact not found")
    return FileResponse(path, filename=path.name)
