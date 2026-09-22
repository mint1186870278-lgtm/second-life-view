from __future__ import annotations
import asyncio
import json
from typing import AsyncIterator
import httpx
from fastapi import File, Form, UploadFile, FastAPI, HTTPException
from fastapi.responses import RedirectResponse, StreamingResponse
from spatial_agent.config import get_settings
from spatial_agent.graph import SpatialAgentGraph
from spatial_agent.providers.aholo_world import AholoWorldClient
from spatial_agent.providers.oss import OSSClient, save_upload_to_temp
from spatial_agent.providers.tripo import TripoClient
from spatial_agent.models import AnalyzeRequest, CameraFrameRequest, CaptureRequest, DesignRequest, Evidence, ReconstructRequest, ResearchRequest, RunState, WorldRequest, SpatialGenRequest
from spatial_agent.yolo_adapter import available_scenes, load_scene

settings = get_settings()
agent = SpatialAgentGraph(settings)
aholo_world = AholoWorldClient(settings)
oss = OSSClient(settings)
tripo = TripoClient(settings)
runs: dict[str, RunState] = {}

app = FastAPI(title="Second Life View · Spatial Agent", version="0.1.0", description="Insta360 + YOLO + active perception multi-agent backend")

@app.get("/health")
def health() -> dict:
    return {"status": "ok", "service": "second-life-spatial-agent", "langgraph": True, "bailian_enabled": agent.bailian.enabled, "lux3d_enabled": agent.lux3d.enabled, "aholo_world_enabled": aholo_world.enabled, "tripo_enabled": tripo.enabled, "oss_enabled": oss.enabled, "lux3d_region": settings.lux3d_region, "aholo_region": "cn"}


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


@app.post("/api/v1/camera/frame", response_model=RunState)
async def camera_frame(request: CameraFrameRequest) -> RunState:
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

    init = AnalyzeRequest(
        user_goal=request.user_goal,
        image_urls=[request.image_url],
        detections=request.detections,
    )
    result = await create_run(init)
    result.metadata["camera"] = request.metadata
    runs[result.run_id] = result
    return result

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
    if payload.detections:
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
    if request.region:
        state.metadata["region"] = request.region
    # Explicit request-level web opt-in keeps the default demo offline and
    # prevents accidental outbound search calls.
    await agent.research({"state": state, "enable_research": True, "enable_design": False, "include_web": request.include_web})
    runs[state.run_id] = state
    return {"run_id": state.run_id, "sources": [s.model_dump(mode="json") for s in state.sources]}
