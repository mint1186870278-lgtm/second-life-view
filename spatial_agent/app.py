from __future__ import annotations
import asyncio
import json
import secrets
from pathlib import Path
from typing import AsyncIterator
from uuid import uuid4
import httpx
from fastapi import File, Form, Header, Request, UploadFile, FastAPI, HTTPException
from fastapi.middleware.cors import CORSMiddleware
from fastapi.responses import FileResponse, RedirectResponse, Response, StreamingResponse
from fastapi.staticfiles import StaticFiles
from spatial_agent.config import get_settings
from spatial_agent.camera_gateway import CameraGatewayError, CameraGatewayNotConfigured, WindowsCameraGateway
from spatial_agent.demo import (
    PICTURE_DIR,
    analyze_demo,
    build_demo_component_design_advice,
    build_demo_component_detail,
    build_demo_component_preview_prompt,
    demo_component_crop_path,
    find_demo_group,
    list_demo_component_groups,
    list_demo_scenes,
    load_demo_annotated_preview,
    load_demo_component_crop,
    load_demo_component_preview,
    load_demo_thumbnail,
)
from spatial_agent.graph import SpatialAgentGraph
from spatial_agent.providers.aholo_world import AholoWorldClient
from spatial_agent.providers.oss import OSSClient, save_upload_to_temp
from spatial_agent.providers.tripo import TripoClient
from spatial_agent.models import AnalyzeRequest, CameraFrameRequest, CaptureRequest, DemoAnalyzeRequest, DemoComponentDesignAdviceRequest, DemoComponentPreviewRequest, DesignRequest, Evidence, ReconstructRequest, ResearchRequest, RunState, WindowsCameraCaptureRequest, WindowsCameraDownloadRequest, WorldRequest, SpatialGenRequest
from spatial_agent.yolo_adapter import available_scenes, load_scene
from spatial_agent.yolo_service import LiveYoloDetector, LiveYoloError, LiveYoloResult

settings = get_settings()
agent = SpatialAgentGraph(settings)
aholo_world = AholoWorldClient(settings)
oss = OSSClient(settings)
tripo = TripoClient(settings)
camera_gateway = WindowsCameraGateway(settings)
live_yolo = LiveYoloDetector(settings)
runs: dict[str, RunState] = {}
CAMERA_ARTIFACT_DIR = Path(__file__).resolve().parents[1] / "run_artifacts" / "camera"
CAMERA_ARTIFACT_DIR.mkdir(parents=True, exist_ok=True)
DEMO_COMPONENT_EVIDENCE_DIR = Path(__file__).resolve().parents[1] / "run_artifacts" / "demo_component_evidence"
DEMO_COMPONENT_EVIDENCE_DIR.mkdir(parents=True, exist_ok=True)
demo_component_evidence: dict[str, list[dict]] = {}
IMAGE_EXTENSIONS = {".jpg", ".jpeg", ".png", ".webp"}

app = FastAPI(title="Second Life View · Spatial Agent", version="0.1.0", description="Insta360 + YOLO + active perception multi-agent backend")
app.add_middleware(
    CORSMiddleware,
    allow_origins=["http://localhost:5173", "http://127.0.0.1:5173"],
    allow_credentials=True,
    allow_methods=["*"],
    allow_headers=["*"],
)
app.mount("/demo-assets", StaticFiles(directory=PICTURE_DIR), name="demo-assets")
app.mount("/camera-assets", StaticFiles(directory=CAMERA_ARTIFACT_DIR), name="camera-assets")
app.mount("/demo-evidence", StaticFiles(directory=DEMO_COMPONENT_EVIDENCE_DIR), name="demo-evidence")

@app.get("/health")
def health() -> dict:
    return {"status": "ok", "service": "second-life-spatial-agent", "langgraph": True, "bailian_enabled": agent.bailian.enabled, "lux3d_enabled": agent.lux3d.enabled, "aholo_world_enabled": aholo_world.enabled, "tripo_enabled": tripo.enabled, "oss_enabled": oss.enabled, "windows_camera_gateway_configured": camera_gateway.configured, "camera_ingest_configured": bool(settings.camera_ingest_token), "yolo_device": settings.yolo_device, "lux3d_region": settings.lux3d_region, "aholo_region": "cn"}


@app.get("/api/v1/assets/config")
def asset_config() -> dict:
    """Safe OSS diagnostic; never returns access keys or secrets."""
    return oss.validate_config()


@app.post("/api/v1/assets/upload")
async def upload_asset(
    file: UploadFile = File(...),
    session_id: str | None = Form(default=None),
) -> dict:
    """Upload a camera frame, crop, video, or INSV to the configured OSS bucket.

    The response contains a short-lived signed URL suitable for VLM/Lux3D/
    Tripo inputs.  The object remains private in OSS.
    """
    if not oss.enabled:
        raise HTTPException(503, "OSS is not configured on this server")
    if not file.filename:
        raise HTTPException(400, "filename is required")
    max_bytes = int(settings.oss_max_upload_mb) * 1024 * 1024
    temporary_path = None
    try:
        temporary_path, size = await asyncio.to_thread(save_upload_to_temp, file, max_bytes)
        result = await asyncio.to_thread(
            oss.upload_file,
            temporary_path,
            session_id=session_id,
            filename=file.filename,
            content_type=file.content_type,
        )
        result["size_bytes"] = size
        return result
    except ValueError as exc:
        raise HTTPException(413, str(exc)) from exc
    except FileNotFoundError as exc:
        raise HTTPException(400, str(exc)) from exc
    finally:
        if temporary_path:
            try:
                import os
                os.unlink(temporary_path)
            except FileNotFoundError:
                pass


@app.get("/api/v1/assets/url")
def signed_asset_url(key: str, expires: int | None = None) -> dict:
    if not oss.enabled:
        raise HTTPException(503, "OSS is not configured on this server")
    ttl = max(60, min(int(expires or settings.oss_signed_url_ttl), 86400))
    try:
        return {"key": key, "url": oss.signed_url(key, expires=ttl), "expires_in": ttl}
    except Exception as exc:
        raise HTTPException(400, str(exc)) from exc

@app.get("/api/v1/yolo/scenes")
def yolo_scenes() -> dict:
    return {"scenes": available_scenes(), "source": "TAY-LI Pipeline B fixtures"}

@app.get("/api/v1/demo")
def demo_contract() -> dict:
    return {"story": "发现旧木柜 → 证据闸门 → 相机补拍材质近景 → 再利用评估 → 翻新方案", "agents": ["supervisor", "perception", "evidence", "research", "design"], "windows_bridge": {"input": "POST /api/v1/runs", "resume": "POST /api/v1/runs/{run_id}/capture/complete", "detection_schema": {"class": "wood_cabinet", "bbox": [0.1, 0.2, 0.4, 0.8], "confidence": 0.9}}, "evidence_labels": ["verified", "inferred", "to_confirm"]}


@app.get("/api/v1/demo/scenes")
def demo_scenes() -> dict:
    return {"scenes": list_demo_scenes(), "source": "data/samples/pictures"}


@app.get("/api/v1/demo/components")
def demo_components(scene_ids: list[str] | None = None) -> dict:
    try:
        return {"groups": list_demo_component_groups(scene_ids), "source": "Pipeline B cached YOLO groups"}
    except ValueError as exc:
        raise HTTPException(400, str(exc)) from exc


@app.get("/api/v1/demo/scenes/{scene_id}/thumbnail")
def demo_scene_thumbnail(scene_id: str) -> Response:
    try:
        content = load_demo_thumbnail(scene_id)
    except ValueError as exc:
        raise HTTPException(404, str(exc)) from exc
    except FileNotFoundError as exc:
        raise HTTPException(404, str(exc)) from exc
    return Response(content=content, media_type="image/jpeg", headers={"Cache-Control": "public, max-age=3600"})


@app.get("/api/v1/demo/scenes/{scene_id}/annotated")
def demo_scene_annotated(scene_id: str, width: int = 2880) -> Response:
    try:
        content = load_demo_annotated_preview(scene_id, width)
    except ValueError as exc:
        raise HTTPException(404, str(exc)) from exc
    except FileNotFoundError as exc:
        raise HTTPException(404, str(exc)) from exc
    return Response(content=content, media_type="image/jpeg", headers={"Cache-Control": "public, max-age=3600"})


@app.get("/api/v1/demo/components/{group_id}/crop")
def demo_component_crop(group_id: str) -> Response:
    try:
        content = load_demo_component_crop(group_id)
    except ValueError as exc:
        raise HTTPException(404, str(exc)) from exc
    except FileNotFoundError as exc:
        raise HTTPException(404, str(exc)) from exc
    return Response(content=content, media_type="image/jpeg", headers={"Cache-Control": "public, max-age=86400"})


@app.get("/api/v1/demo/components/{group_id}/preview-image")
def demo_component_preview_image(group_id: str) -> Response:
    try:
        content = load_demo_component_preview(group_id)
    except ValueError as exc:
        raise HTTPException(404, str(exc)) from exc
    except FileNotFoundError as exc:
        raise HTTPException(404, str(exc)) from exc
    return Response(content=content, media_type="image/jpeg", headers={"Cache-Control": "public, max-age=3600"})


@app.get("/api/v1/demo/components/{group_id}/detail")
async def demo_component_detail(group_id: str, region: str | None = None) -> dict:
    try:
        return await build_demo_component_detail(
            group_id,
            region=region,
            research_client=agent.research_client,
            supplemental_evidence=demo_component_evidence.get(group_id, []),
        )
    except ValueError as exc:
        raise HTTPException(404, str(exc)) from exc


def demo_component_can_generate_preview(group_id: str) -> bool:
    _, group, _ = find_demo_group(group_id)
    return bool(
        group.get("evidence_status") == "supported"
        and group.get("recommended_pathway") in {"REFURBISH", "REPURPOSE"}
    )


@app.post("/api/v1/demo/components/{group_id}/design-advice")
async def demo_component_design_advice(group_id: str, request: DemoComponentDesignAdviceRequest) -> dict:
    try:
        if not demo_component_can_generate_preview(group_id):
            raise HTTPException(409, "仅有依据且建议为修复翻新或改造再利用的构件可生成再生预览")
        return await build_demo_component_design_advice(group_id, region=request.region, agent=agent)
    except ValueError as exc:
        raise HTTPException(404, str(exc)) from exc


@app.post("/api/v1/demo/components/{group_id}/preview")
async def demo_component_preview(group_id: str, request: DemoComponentPreviewRequest) -> dict:
    try:
        if not demo_component_can_generate_preview(group_id):
            raise HTTPException(409, "仅有依据且建议为修复翻新或改造再利用的构件可生成再生预览")
        prompt = build_demo_component_preview_prompt(group_id, request.advice, request.region)
        fallback_url = f"/api/v1/demo/components/{group_id}/preview-image"
        result: dict = {}
        image_url: str | None = None
        generation_task_id: str | None = None
        provider = "qwen-image-3.0-pro"
        status = "generated"
        if settings.dashscope_api_key and settings.use_external_tools:
            try:
                result = await agent.bailian.generate_image(prompt, str(demo_component_crop_path(group_id)))
                image_url = result.get("image_url") if isinstance(result, dict) else None
                output = result.get("output") if isinstance(result, dict) else None
                if isinstance(output, dict):
                    generation_task_id = output.get("task_id")
                if not image_url:
                    status = "submitted" if generation_task_id else "fallback"
            except Exception as exc:
                status = "fallback"
                result = {"error": str(exc)}
        else:
            provider = "qwen-image-3.0-pro (offline preview)"
            status = "fallback"
        return {
            "component_id": group_id,
            "status": status,
            "provider": provider,
            "prompt": prompt,
            "image_url": image_url or fallback_url,
            "is_offline_fallback": image_url is None,
            "generation_task_id": generation_task_id,
            "raw": result if result else None,
        }
    except ValueError as exc:
        raise HTTPException(404, str(exc)) from exc


@app.post("/api/v1/demo/components/{group_id}/evidence")
async def demo_component_evidence_upload(
    group_id: str,
    file: UploadFile | None = File(default=None),
    image_url: str | None = Form(default=None),
    note: str | None = Form(default=None),
) -> dict:
    try:
        find_demo_group(group_id)
    except ValueError as exc:
        raise HTTPException(404, str(exc)) from exc
    if not file and not (image_url or "").strip() and not (note or "").strip():
        raise HTTPException(400, "请至少上传照片、填写图片地址或补充说明")
    evidence_item: dict = {
        "id": f"demo_evidence_{uuid4().hex[:12]}",
        "note": (note or "").strip() or None,
        "image_url": (image_url or "").strip() or None,
        "source": "user-supplement",
    }
    if file:
        extension = Path(file.filename or "evidence.jpg").suffix.lower()
        if extension not in IMAGE_EXTENSIONS:
            raise HTTPException(400, "补充照片仅支持 JPG、PNG、WEBP 格式")
        content = await file.read()
        if len(content) > 12 * 1024 * 1024:
            raise HTTPException(413, "补充照片不能超过 12MB")
        filename = f"{uuid4().hex}{extension}"
        (DEMO_COMPONENT_EVIDENCE_DIR / filename).write_bytes(content)
        evidence_item["image_url"] = f"/demo-evidence/{filename}"
        evidence_item["filename"] = file.filename
    demo_component_evidence.setdefault(group_id, []).append(evidence_item)
    return {"evidence": evidence_item, "count": len(demo_component_evidence[group_id])}


@app.post("/api/v1/demo/analyze")
async def demo_analyze(request: DemoAnalyzeRequest) -> dict:
    try:
        state, result = await analyze_demo(request, agent=agent, aholo_world=aholo_world)
    except ValueError as exc:
        raise HTTPException(400, str(exc)) from exc
    runs[state.run_id] = state
    return result

@app.post("/api/v1/runs", response_model=RunState)
async def create_run(request: AnalyzeRequest) -> RunState:
    detections = request.detections
    image_urls = request.image_urls
    metadata: dict = {}
    if request.scene_slug or request.use_yolo_fixture:
        scene = load_scene(request.scene_slug or "hotel_room")
        detections = detections or scene["detections"]
        image_urls = image_urls or [scene["image_url"]]
        metadata.update({"scene_slug": scene["scene_slug"], "scene_id": scene["scene_id"], "panorama_id": scene["panorama_id"], "yolo_batches": scene["batches"], "yolo_source": "TAY-LI Pipeline B"})
    if request.region:
        metadata["region"] = request.region
    metadata["include_web"] = request.include_web
    init = {"user_goal": request.user_goal, "image_urls": image_urls, "detections": detections, "metadata": metadata}
    if request.run_id:
        init["run_id"] = request.run_id
    state = RunState(**init)
    result = await agent.run(state, enable_research=request.enable_research, enable_design=request.enable_design, enable_3d=request.enable_3d, include_web=request.include_web)
    runs[result.run_id] = result
    return result


async def accept_camera_frame(request: CameraFrameRequest) -> RunState:
    """Accept a frame and YOLO JSON from the Windows CameraSDK bridge.

    The bridge never needs to import CameraSDK on Linux.  A first frame starts
    a run; a frame tied to an Evidence Agent action resumes that run.  This
    single endpoint is convenient for the demo bridge while the lower-level
    ``/runs`` and ``/capture/complete`` endpoints remain available for clients
    that want explicit control.
    """
    if request.run_id:
        state = runs.get(request.run_id)
        if not state:
            raise HTTPException(404, "run not found")
        if not request.action_id:
            raise HTTPException(400, "action_id is required when run_id is supplied")
        state.metadata.update(request.run_metadata)
        result = await complete_capture(
            request.run_id,
            CaptureRequest(
                run_id=request.run_id,
                action_id=request.action_id,
                image_url=request.image_url,
                detections=request.detections,
            ),
        )
        result.metadata.setdefault("camera", {}).update(request.metadata)
        runs[result.run_id] = result
        return result

    if request.run_metadata:
        initial_metadata = {"include_web": False, **request.run_metadata}
        state = RunState(
            user_goal=request.user_goal,
            image_urls=[request.image_url],
            detections=request.detections,
            metadata=initial_metadata,
        )
        result = await agent.run(state)
        runs[result.run_id] = result
    else:
        init = AnalyzeRequest(
            user_goal=request.user_goal,
            image_urls=[request.image_url],
            detections=request.detections,
        )
        result = await create_run(init)
    result.metadata["camera"] = request.metadata
    runs[result.run_id] = result
    return result


def camera_gateway_exception(error: CameraGatewayError) -> HTTPException:
    if isinstance(error, CameraGatewayNotConfigured):
        return HTTPException(503, str(error))
    return HTTPException(502, str(error))


def camera_artifact_extension(gateway_result: dict) -> str:
    candidate = str(gateway_result.get("filename") or "")
    extension = Path(candidate).suffix.lower()
    return extension if extension in IMAGE_EXTENSIONS | {".insp", ".insv", ".dng"} else ".bin"


def safe_camera_frame_id(value: object) -> str:
    raw = str(value or "camera-frame")
    normalized = "".join(character if character.isalnum() or character in {"-", "_"} else "_" for character in raw)
    return normalized.strip("._-")[:120] or "camera-frame"


def camera_asset_url(request: Request, path: Path) -> str:
    return str(request.url_for("camera-assets", path=path.name))


def require_camera_ingest_token(authorization: str | None) -> None:
    if not settings.camera_ingest_token:
        raise HTTPException(503, "camera ingest is disabled; set CAMERA_INGEST_TOKEN on the Linux server")
    expected = f"Bearer {settings.camera_ingest_token}"
    if not authorization or not secrets.compare_digest(authorization, expected):
        raise HTTPException(401, "invalid camera ingest token")


def parse_camera_ingest_metadata(raw_metadata: str | None) -> dict:
    if not raw_metadata or not raw_metadata.strip():
        return {}
    try:
        metadata = json.loads(raw_metadata)
    except json.JSONDecodeError as exc:
        raise HTTPException(422, "metadata must be a JSON object") from exc
    if not isinstance(metadata, dict):
        raise HTTPException(422, "metadata must be a JSON object")
    return metadata


def validate_camera_upload(file: UploadFile) -> str:
    filename = file.filename or "camera-frame.jpg"
    extension = Path(filename).suffix.lower()
    if extension not in IMAGE_EXTENSIONS:
        raise HTTPException(400, "camera ingest supports JPG, PNG and WEBP images only")
    content_type = (file.content_type or "").lower()
    if content_type and content_type != "application/octet-stream" and not content_type.startswith("image/"):
        raise HTTPException(400, "camera ingest requires an image content type")
    return extension


async def save_camera_upload(file: UploadFile, destination: Path, *, max_bytes: int) -> int:
    temporary_path = destination.with_name(f".{destination.name}.{uuid4().hex}.part")
    size = 0
    try:
        with temporary_path.open("wb") as output:
            while chunk := await file.read(1024 * 1024):
                size += len(chunk)
                if size > max_bytes:
                    raise HTTPException(413, f"camera upload exceeds {max_bytes // (1024 * 1024)}MB")
                output.write(chunk)
        temporary_path.replace(destination)
        return size
    except Exception:
        temporary_path.unlink(missing_ok=True)
        raise
    finally:
        await file.close()


async def publish_camera_artifact(
    request: Request,
    local_path: Path,
    *,
    frame_id: str,
    content_type: str | None,
    source_metadata: dict,
) -> tuple[str, dict]:
    metadata = {
        "frame_id": frame_id,
        "filename": local_path.name,
        "content_type": content_type,
        **source_metadata,
    }
    if oss.enabled:
        try:
            upload = await asyncio.to_thread(
                oss.upload_file,
                local_path,
                session_id=frame_id,
                filename=local_path.name,
                content_type=content_type,
            )
        except Exception as error:
            raise HTTPException(502, f"failed to upload camera artifact to OSS: {error}") from error
        metadata["oss"] = upload
        return upload["url"], metadata
    return camera_asset_url(request, local_path), metadata


async def persist_camera_artifact(request: Request, gateway_result: dict) -> tuple[str, dict, Path]:
    artifact_url = gateway_result.get("artifact_url")
    if not isinstance(artifact_url, str) or not artifact_url:
        raise HTTPException(502, "Windows camera gateway did not return an artifact URL")

    frame_id = safe_camera_frame_id(gateway_result.get("frame_id"))
    extension = camera_artifact_extension(gateway_result)
    local_name = f"{frame_id}-{uuid4().hex[:12]}{extension}"
    local_path = CAMERA_ARTIFACT_DIR / local_name
    try:
        content_type = await camera_gateway.download_artifact_to(artifact_url, local_path)
    except CameraGatewayError as error:
        raise camera_gateway_exception(error) from error

    image_url, metadata = await publish_camera_artifact(
        request,
        local_path,
        frame_id=frame_id,
        content_type=content_type,
        source_metadata={
            "gateway_artifact_id": gateway_result.get("artifact_id"),
            "remote_paths": gateway_result.get("remote_paths", []),
            "stitched": bool(gateway_result.get("stitched")),
        },
    )
    return image_url, metadata, local_path


async def persist_ingested_camera_artifact(
    request: Request,
    file: UploadFile,
    *,
    frame_id: str,
    projection: str,
) -> tuple[str, dict, Path]:
    extension = validate_camera_upload(file)
    content_type = file.content_type or "application/octet-stream"
    local_name = f"{frame_id}-{uuid4().hex[:12]}{extension}"
    local_path = CAMERA_ARTIFACT_DIR / local_name
    size = await save_camera_upload(
        file,
        local_path,
        max_bytes=int(settings.camera_ingest_max_upload_mb) * 1024 * 1024,
    )
    image_url, metadata = await publish_camera_artifact(
        request,
        local_path,
        frame_id=frame_id,
        content_type=content_type,
        source_metadata={
            "source": "windows_multipart",
            "original_filename": file.filename,
            "size_bytes": size,
            "stitched": projection.strip().lower() in {"erp", "equirectangular", "panorama", "spherical"},
        },
    )
    return image_url, metadata, local_path


async def detect_camera_artifact(
    request: Request,
    local_path: Path,
    *,
    projection: str,
) -> tuple[LiveYoloResult, dict]:
    try:
        result = await live_yolo.detect(
            local_path,
            artifact_id=local_path.stem,
            projection=projection,
            output_dir=CAMERA_ARTIFACT_DIR,
        )
    except LiveYoloError as error:
        raise HTTPException(503, f"Linux live YOLO failed: {error}") from error
    payload = result.public_metadata(
        annotated_image_url=camera_asset_url(request, result.annotated_path),
        detections_url=camera_asset_url(request, result.detections_path),
    )
    return result, payload


async def run_live_camera_analysis(
    request: Request,
    *,
    local_path: Path,
    image_url: str,
    artifact: dict,
    run_id: str | None,
    action_id: str | None,
    user_goal: str,
    camera: dict,
) -> tuple[RunState, dict]:
    projection = str(camera.get("projection") or "equirectangular")
    yolo_result, yolo_payload = await detect_camera_artifact(
        request,
        local_path,
        projection=projection,
    )
    state = await accept_camera_frame(
        CameraFrameRequest(
            run_id=run_id,
            action_id=action_id,
            user_goal=user_goal,
            image_url=image_url,
            detections=yolo_result.detections,
            metadata=camera,
            run_metadata={
                "yolo": yolo_payload,
                "yolo_batches": yolo_result.component_batches,
                "yolo_source": "Linux live YOLO-World",
                "yolo_mode": "live",
            },
        )
    )
    state.metadata["yolo"] = yolo_payload
    state.metadata["yolo_batches"] = yolo_result.component_batches
    state.metadata["yolo_source"] = "Linux live YOLO-World"
    state.metadata["yolo_mode"] = "live"
    runs[state.run_id] = state
    return state, yolo_payload


def camera_metadata(gateway_result: dict, artifact: dict) -> dict:
    camera = gateway_result.get("camera")
    details = camera if isinstance(camera, dict) else {}
    return {
        "source": "windows_camera_gateway",
        "camera_model": details.get("camera_name"),
        "camera_serial": details.get("serial"),
        "camera_firmware": details.get("firmware"),
        "camera_type": details.get("camera_type"),
        "frame_id": artifact["frame_id"],
        "projection": "equirectangular" if artifact["stitched"] else "insta360_native",
        "artifact": artifact,
    }


async def run_windows_camera_operation(
    request: Request,
    payload: WindowsCameraCaptureRequest,
    *,
    remote_path: str | None = None,
) -> dict:
    gateway_payload = {
        "raw_type": payload.raw_type,
        "timeout_ms": payload.timeout_ms,
        "stitch": payload.stitch,
        "output_width": payload.output_width,
        "output_height": payload.output_height,
    }
    try:
        gateway_result = (
            await camera_gateway.download({**gateway_payload, "remote_path": remote_path})
            if remote_path
            else await camera_gateway.capture(gateway_payload)
        )
    except CameraGatewayError as error:
        raise camera_gateway_exception(error) from error

    image_url, artifact, local_path = await persist_camera_artifact(request, gateway_result)
    response: dict = {
        "gateway": {
            "frame_id": gateway_result.get("frame_id"),
            "camera": gateway_result.get("camera"),
            "remote_paths": gateway_result.get("remote_paths", []),
        },
        "asset": {"image_url": image_url, **artifact},
    }
    if Path(artifact["filename"]).suffix.lower() not in IMAGE_EXTENSIONS:
        response["message"] = "已下载相机原始文件；请以 stitch=true 生成全景图后再提交分析。"
        return response

    state, yolo_payload = await run_live_camera_analysis(
        request,
        local_path=local_path,
        image_url=image_url,
        artifact=artifact,
        run_id=payload.run_id,
        action_id=payload.action_id,
        user_goal=payload.user_goal,
        camera=camera_metadata(gateway_result, artifact),
    )
    response["yolo"] = yolo_payload
    response["run"] = state.model_dump(mode="json")
    return response


@app.get("/api/v1/camera/status")
async def windows_camera_status() -> dict:
    try:
        return await camera_gateway.status()
    except CameraGatewayError as error:
        raise camera_gateway_exception(error) from error


@app.get("/api/v1/camera/files")
async def windows_camera_files() -> dict:
    try:
        return await camera_gateway.list_files()
    except CameraGatewayError as error:
        raise camera_gateway_exception(error) from error


@app.post("/api/v1/camera/capture")
async def windows_camera_capture(request: Request, payload: WindowsCameraCaptureRequest) -> dict:
    """Capture on Windows, transfer it through the tunnel, and start/resume a run."""
    return await run_windows_camera_operation(request, payload)


@app.post("/api/v1/camera/download")
async def windows_camera_download(request: Request, payload: WindowsCameraDownloadRequest) -> dict:
    """Transfer an existing camera file and optionally stitch it before analysis."""
    return await run_windows_camera_operation(request, payload, remote_path=payload.remote_path)


@app.post("/api/v1/camera/ingest")
async def ingest_windows_camera_frame(
    request: Request,
    file: UploadFile = File(...),
    run_id: str | None = Form(default=None),
    action_id: str | None = Form(default=None),
    user_goal: str = Form(default="评估空间构件的再利用机会，并提出下一步需要采集的证据"),
    metadata: str | None = Form(default=None),
    authorization: str | None = Header(default=None),
) -> dict:
    """Receive a Windows-local image, run Linux YOLO, then create or resume a run.

    This is the push-based counterpart to ``/camera/capture`` and
    ``/camera/download``.  The Windows host sends only the image and camera
    metadata; detector boxes always originate from this Linux process.
    """
    require_camera_ingest_token(authorization)
    run_id = (run_id or "").strip() or None
    action_id = (action_id or "").strip() or None
    if run_id and not action_id:
        raise HTTPException(400, "action_id is required when run_id is supplied")

    camera_metadata_from_upload = parse_camera_ingest_metadata(metadata)
    source_name = file.filename or "camera-frame.jpg"
    frame_id = safe_camera_frame_id(
        camera_metadata_from_upload.get("frame_id") or Path(source_name).stem
    )
    projection = str(camera_metadata_from_upload.get("projection") or "equirectangular")
    image_url, artifact, local_path = await persist_ingested_camera_artifact(
        request,
        file,
        frame_id=frame_id,
        projection=projection,
    )
    camera = {
        **camera_metadata_from_upload,
        "source": "windows_multipart",
        "frame_id": frame_id,
        "projection": projection,
        "artifact": artifact,
    }
    state, yolo_payload = await run_live_camera_analysis(
        request,
        local_path=local_path,
        image_url=image_url,
        artifact=artifact,
        run_id=run_id,
        action_id=action_id,
        user_goal=user_goal,
        camera=camera,
    )
    return {
        "asset": {"image_url": image_url, **artifact},
        "yolo": yolo_payload,
        "run": state.model_dump(mode="json"),
    }


@app.post("/api/v1/camera/frame", response_model=RunState)
async def camera_frame(request: CameraFrameRequest) -> RunState:
    return await accept_camera_frame(request)

@app.get("/api/v1/runs/{run_id}", response_model=RunState)
def get_run(run_id: str) -> RunState:
    state = runs.get(run_id)
    if not state:
        raise HTTPException(404, "run not found")
    return state

@app.get("/api/v1/runs/{run_id}/events")
def get_events(run_id: str) -> dict:
    state = runs.get(run_id)
    if not state:
        raise HTTPException(404, "run not found")
    return {"run_id": run_id, "events": [e.model_dump(mode="json") for e in state.events]}

@app.get("/api/v1/runs/{run_id}/stream")
async def stream_events(run_id: str) -> StreamingResponse:
    if run_id not in runs:
        raise HTTPException(404, "run not found")
    async def events() -> AsyncIterator[str]:
        sent = 0
        for _ in range(30):
            state = runs.get(run_id)
            if not state: break
            items = state.events[sent:]
            sent = len(state.events)
            for item in items:
                yield f"data: {json.dumps(item.model_dump(mode='json'), ensure_ascii=False)}\n\n"
            if state.status in {"completed", "awaiting_evidence", "failed"} and sent:
                break
            await asyncio.sleep(0.5)
    return StreamingResponse(events(), media_type="text/event-stream")

@app.post("/api/v1/runs/{run_id}/capture/complete", response_model=RunState)
async def complete_capture(run_id: str, payload: CaptureRequest) -> RunState:
    if payload.run_id != run_id:
        raise HTTPException(400, "payload.run_id must match path run_id")
    state = runs.get(run_id)
    if not state:
        raise HTTPException(404, "run not found")
    if not any(a.id == payload.action_id for a in state.capture_actions):
        raise HTTPException(400, "action_id is not pending for this run")
    if payload.image_url:
        state.image_urls.append(payload.image_url)
    if payload.detections or state.metadata.get("yolo_mode") == "live":
        state.detections = payload.detections
    state.evidence.append(Evidence(kind="user", source="windows_camera_gateway", uri=payload.image_url, confidence=0.95, claims={"capture_action_id": payload.action_id, "confirmed": True}, provenance="verified"))
    state.metadata["capture_confirmed"] = True
    # Rebuild perception from the new observation while preserving the audit trail.
    state.objects.clear()
    state.relations.clear()
    state.capture_actions.clear()
    state.designs.clear()
    state.sources.clear()
    state.status = "running"
    state.iteration = 0
    result = await agent.run(state, include_web=bool(state.metadata.get("include_web", False)))
    runs[result.run_id] = result
    return result

@app.post("/api/v1/runs/{run_id}/design", response_model=RunState)
async def design_run(run_id: str, request: DesignRequest) -> RunState:
    state = runs.get(run_id)
    if not state:
        raise HTTPException(404, "run not found")
    result = await agent.generate_design(state, request.brief, request.object_ids, request.reference_image_url)
    runs[run_id] = result
    return result

@app.post("/api/v1/3dgs/reconstruct")
async def reconstruct_world(request: WorldRequest) -> dict:
    state = runs.get(request.run_id) if request.run_id else None
    resources = request.resources
    if request.image_url:
        resources = resources or [request.image_url]
    if not resources and state:
        resources = state.image_urls
    try:
        if resources:
            result = await aholo_world.reconstruct(resources, quality=request.quality, wait=request.wait)
        elif request.prompt:
            result = await aholo_world.generate(request.prompt, request.image_url)
        else:
            raise HTTPException(400, "resources, image_url or prompt is required")
    except ValueError as exc:
        raise HTTPException(400, str(exc)) from exc
    if state:
        state.metadata["aholo_world"] = result
        state.evidence.append(Evidence(kind="3d", source="aholo:world-3dgs-cn", uri=resources[0] if resources else None, confidence=0.8 if result.get("status") == "submitted" else 0.3, claims=result, provenance="verified" if result.get("status") == "submitted" else "to_confirm"))
        runs[state.run_id] = state
    return result


@app.post("/api/v1/3dgs/reconstruct-upload")
async def reconstruct_world_upload(
    file: UploadFile = File(...),
    quality: str = Form(default="low"),
    run_id: str | None = Form(default=None),
) -> dict:
    """Upload an MP4/INSV (or one image) through Aholo Asset and submit World.

    This is the convenient Windows-to-Linux demo path. Aholo World accepts a
    single video/INSV resource; image-only reconstruction should use the URL
    endpoint with at least 20 overlapping perspective images.
    """
    if not aholo_world.enabled:
        raise HTTPException(503, "Aholo World is disabled; set AHOLO_API_KEY and USE_EXTERNAL_TOOLS=true")
    if quality not in {"low", "normal", "high"}:
        raise HTTPException(400, "quality must be low, normal or high")
    if not file.filename:
        raise HTTPException(400, "filename is required")
    temporary_path = None
    try:
        temporary_path, _ = await asyncio.to_thread(
            save_upload_to_temp,
            file,
            int(settings.oss_max_upload_mb) * 1024 * 1024,
        )
        asset_url = await aholo_world.upload_local_file(temporary_path)
        result = await aholo_world.reconstruct([asset_url], quality=quality, wait=False)
        result["asset_url"] = asset_url
        if run_id and run_id in runs:
            runs[run_id].metadata["aholo_world"] = result
        return result
    except ValueError as exc:
        raise HTTPException(413, str(exc)) from exc
    except Exception as exc:
        raise HTTPException(502, f"Aholo World upload or submission failed: {exc}") from exc
    finally:
        if temporary_path:
            try:
                import os
                os.unlink(temporary_path)
            except FileNotFoundError:
                pass


@app.post("/api/v1/3dgs/spatial-gen")
async def spatial_gen(request: SpatialGenRequest) -> dict:
    """Prompt or prompt + an already uploaded HTTP image → Spatial Gen."""
    if not request.prompt.strip():
        raise HTTPException(400, "prompt is required")
    try:
        result = await aholo_world.generate(request.prompt.strip(), request.image_url)
    except ValueError as exc:
        raise HTTPException(400, str(exc)) from exc
    if request.run_id and request.run_id in runs:
        runs[request.run_id].metadata["aholo_spatial_gen"] = result
    return result


@app.post("/api/v1/3dgs/spatial-gen-upload")
async def spatial_gen_upload(
    file: UploadFile = File(...),
    prompt: str = Form(...),
    run_id: str | None = Form(default=None),
) -> dict:
    """Local JPG/PNG + prompt → Aholo Spatial Gen World.

    This mirrors the MCP ``world_generate(localPath=..., prompt=...)`` path,
    but exposes the result to the backend directly. It is a generative design
    result and should be labelled separately from measured scene reconstruction.
    """
    if not aholo_world.enabled:
        raise HTTPException(503, "Aholo World is disabled; set AHOLO_API_KEY and USE_EXTERNAL_TOOLS=true")
    if not file.filename or not prompt.strip():
        raise HTTPException(400, "filename and prompt are required")
    temporary_path = None
    try:
        temporary_path, _ = await asyncio.to_thread(
            save_upload_to_temp,
            file,
            int(settings.oss_max_upload_mb) * 1024 * 1024,
        )
        result = await aholo_world.generate_from_local_file(temporary_path, prompt.strip())
        if run_id and run_id in runs:
            runs[run_id].metadata["aholo_spatial_gen"] = result
        return result
    except ValueError as exc:
        raise HTTPException(400, str(exc)) from exc
    except Exception as exc:
        raise HTTPException(502, f"Aholo Spatial Gen failed: {exc}") from exc
    finally:
        if temporary_path:
            try:
                import os
                os.unlink(temporary_path)
            except FileNotFoundError:
                pass


@app.get("/api/v1/3dgs/world/{world_id}")
async def world_status(world_id: str) -> dict:
    try:
        return await aholo_world.world_status(world_id)
    except ValueError as exc:
        raise HTTPException(400, str(exc)) from exc


@app.get("/api/v1/3dgs/world/{world_id}/open")
async def open_world_asset(world_id: str, asset: str = "spz") -> RedirectResponse:
    """Open a completed World result in Aholo's hosted viewer.

    The World API returns a world asset, rather than a Studio project.  This
    redirect is the no-upload demo path: a browser can open this endpoint and
    the official viewer loads the remote SPZ/PLY/LOD file directly.  ``pano``
    opens the generated/reconstructed panorama image instead.
    """
    if asset not in {"spz", "ply", "lod", "pano"}:
        raise HTTPException(400, "asset must be spz, ply, lod or pano")
    try:
        result = await aholo_world.world_status(world_id)
    except ValueError as exc:
        raise HTTPException(400, str(exc)) from exc
    except Exception as exc:
        raise HTTPException(502, f"Aholo World status failed: {exc}") from exc

    status = str(result.get("status") or "").upper()
    if status not in {"SUCCEEDED", "SUCCESS", "COMPLETED"}:
        raise HTTPException(409, f"World {world_id} is not ready (status={status or 'UNKNOWN'})")
    viewers = result.get("viewer_urls") or {}
    imagery_url = result.get("imagery_url")
    target = imagery_url if asset == "pano" else viewers.get(asset)
    if not target:
        raise HTTPException(404, f"{asset} is not available for world {world_id}")
    # 307 preserves the browser GET and works for both a normal link and an
    # iframe.  The target is an Aholo-hosted URL, never a local filesystem
    # path, so no server-side file upload is needed at viewing time.
    return RedirectResponse(target, status_code=307)


@app.get("/api/v1/3dgs/world/{world_id}/asset/{asset_name}")
async def world_asset(world_id: str, asset_name: str) -> StreamingResponse:
    """Proxy a completed World visualization asset through this API.

    ``cover`` is a normal preview JPEG. ``spz`` is the preferred compact
    Gaussian-Splat payload for a compatible viewer; ``ply`` is a larger point
    cloud useful for offline processing. The endpoint keeps the provider URL
    out of a browser/client and streams the temporary Aholo URL directly.
    """
    if asset_name not in {"cover", "pano", "spz", "ply", "lod-meta"}:
        raise HTTPException(400, "asset_name must be cover, pano, spz, ply or lod-meta")
    try:
        status = await aholo_world.world_status(world_id)
    except Exception as exc:
        raise HTTPException(502, f"Aholo World status failed: {exc}") from exc
    urls = ((status.get("assets") or {}).get("splats") or {}).get("urls") or {}
    key = {"cover": "cover", "pano": "imagery_url", "spz": "spzPath", "ply": "plyPath", "lod-meta": "lodMetaPath"}[asset_name]
    imagery_url = ((status.get("assets") or {}).get("imagery") or {}).get("panoUrl") or status.get("imagery_url")
    url = status.get(key) if key == "cover" else imagery_url if key == "imagery_url" else urls.get(key)
    if not url:
        raise HTTPException(404, f"{asset_name} is not available for world {world_id}")
    try:
        async def body():
            async with httpx.AsyncClient(timeout=180, trust_env=False) as client:
                async with client.stream("GET", url) as response:
                    if response.status_code >= 400:
                        raise RuntimeError(f"HTTP {response.status_code}")
                    async for chunk in response.aiter_bytes(1024 * 1024):
                        yield chunk

        media = {
            "cover": "image/jpeg",
            "pano": "image/jpeg",
            "spz": "application/octet-stream",
            "ply": "application/octet-stream",
            "lod-meta": "application/json",
        }[asset_name]
        return StreamingResponse(body(), media_type=media, headers={"Content-Disposition": f'inline; filename="{world_id}.{asset_name}"'})
    except HTTPException:
        raise
    except Exception as exc:
        raise HTTPException(502, f"Aholo asset download failed: {exc}") from exc


@app.post("/api/v1/3dgs/world/{world_id}/download")
async def download_world_assets(world_id: str) -> dict:
    """Download all available completed World assets into run_artifacts."""
    try:
        return await aholo_world.download_assets(world_id)
    except ValueError as exc:
        raise HTTPException(400, str(exc)) from exc
    except RuntimeError as exc:
        raise HTTPException(409, str(exc)) from exc
    except Exception as exc:
        raise HTTPException(502, f"Aholo asset download failed: {exc}") from exc

@app.post("/api/v1/reconstruct")
async def reconstruct(request: ReconstructRequest) -> dict:
    state = runs.get(request.run_id) if request.run_id else None
    image_urls = request.image_urls or ([request.image_url] if request.image_url else [])
    if not image_urls and state:
        image_urls = state.image_urls
    if not image_urls:
        raise HTTPException(400, "image_url or image_urls is required")
    try:
        result = await agent.lux3d.image_to_3d(image_urls, request.version, request.wait)
    except ValueError as exc:
        raise HTTPException(400, str(exc)) from exc
    if state:
        state.evidence.append(Evidence(kind="3d", source="lux3d-cn", uri=image_urls[0], confidence=0.8 if result.get("status") == "submitted" else 0.3, claims=result, provenance="verified" if result.get("status") == "submitted" else "to_confirm"))
        runs[state.run_id] = state
    return result


@app.get("/api/v1/reconstruct/{task_id}")
async def lux3d_status(task_id: str) -> dict:
    """Query a domestic Lux3D task created by ``/api/v1/reconstruct``."""
    try:
        return await agent.lux3d.get_task(task_id)
    except ValueError as exc:
        raise HTTPException(400, str(exc)) from exc
    except Exception as exc:
        raise HTTPException(502, f"Lux3D task query failed: {exc}") from exc


@app.post("/api/v1/tripo/reconstruct")
async def reconstruct_tripo(request: ReconstructRequest) -> dict:
    state = runs.get(request.run_id) if request.run_id else None
    image_urls = request.image_urls or ([request.image_url] if request.image_url else [])
    if not image_urls and state:
        image_urls = state.image_urls
    if not image_urls:
        raise HTTPException(400, "image_url or image_urls is required")
    try:
        result = await tripo.image_to_model(image_urls, wait=request.wait)
    except ValueError as exc:
        raise HTTPException(400, str(exc)) from exc
    if state:
        state.metadata["tripo"] = result
        state.evidence.append(Evidence(kind="3d", source="tripo-v3", uri=image_urls[0], confidence=0.8 if result.get("status") == "submitted" else 0.3, claims=result, provenance="verified" if result.get("status") == "submitted" else "to_confirm"))
        runs[state.run_id] = state
    return result


@app.get("/api/v1/tripo/tasks/{task_id}")
async def tripo_status(task_id: str) -> dict:
    try:
        return await tripo.get(task_id)
    except ValueError as exc:
        raise HTTPException(400, str(exc)) from exc

@app.post("/api/v1/research")
async def research(request: ResearchRequest) -> dict:
    state = runs.get(request.run_id)
    if not state:
        raise HTTPException(404, "run not found")
    state.sources = []
    state.user_goal = request.query
    region = request.region or request.location
    if region:
        state.metadata["region"] = region
    categories = [value for value in (request.furniture_type, request.location) if value]
    result = await agent.research_client.retrieve_with_opportunities(
        request.query,
        categories,
        region=region,
        include_web=request.include_web,
    )
    state.sources = result.sources
    runs[state.run_id] = state
    return {
        "run_id": state.run_id,
        "sources": [source.model_dump(mode="json") for source in state.sources],
        "opportunities": [item.model_dump(mode="json") for item in result.opportunities],
        "research": {
            "web_attempted": result.web_attempted,
            "web_results_count": result.web_results_count,
            "used_fallback": result.used_fallback,
        },
    }


frontend_dist = Path(__file__).resolve().parents[1] / "dist"
if frontend_dist.exists():
    assets_dir = frontend_dist / "assets"
    if assets_dir.exists():
        app.mount("/assets", StaticFiles(directory=assets_dir), name="frontend-assets")

    @app.get("/{full_path:path}", include_in_schema=False)
    def frontend_app(full_path: str) -> FileResponse:
        if full_path.startswith("api/"):
            raise HTTPException(404, "API route not found")
        candidate = frontend_dist / full_path
        if candidate.is_file() and frontend_dist in candidate.resolve().parents:
            return FileResponse(candidate)
        return FileResponse(frontend_dist / "index.html")
