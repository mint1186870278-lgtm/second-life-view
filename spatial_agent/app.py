from __future__ import annotations
import asyncio
import json
from typing import AsyncIterator
from fastapi import FastAPI, HTTPException
from fastapi.responses import StreamingResponse
from spatial_agent.config import get_settings
from spatial_agent.graph import SpatialAgentGraph
from spatial_agent.models import AnalyzeRequest, CaptureRequest, DesignRequest, Evidence, ReconstructRequest, ResearchRequest, RunState

settings = get_settings()
agent = SpatialAgentGraph(settings)
runs: dict[str, RunState] = {}

app = FastAPI(title="Second Life View · Spatial Agent", version="0.1.0", description="Insta360 + YOLO + active perception multi-agent backend")

@app.get("/health")
def health() -> dict:
    return {"status": "ok", "service": "second-life-spatial-agent", "langgraph": True, "bailian_enabled": agent.bailian.enabled, "lux3d_enabled": agent.lux3d.enabled, "lux3d_region": settings.lux3d_region}

@app.get("/api/v1/demo")
def demo_contract() -> dict:
    return {"story": "发现旧木柜 → 证据闸门 → 相机补拍材质近景 → 再利用评估 → 翻新方案", "agents": ["supervisor", "perception", "evidence", "research", "design"], "windows_bridge": {"input": "POST /api/v1/runs", "resume": "POST /api/v1/runs/{run_id}/capture/complete", "detection_schema": {"class": "wood_cabinet", "bbox": [0.1, 0.2, 0.4, 0.8], "confidence": 0.9}}, "evidence_labels": ["verified", "inferred", "to_confirm"]}

@app.post("/api/v1/runs", response_model=RunState)
async def create_run(request: AnalyzeRequest) -> RunState:
    init = {"user_goal": request.user_goal, "image_urls": request.image_urls, "detections": request.detections}
    if request.run_id:
        init["run_id"] = request.run_id
    state = RunState(**init)
    result = await agent.run(state, enable_research=request.enable_research, enable_design=request.enable_design, enable_3d=request.enable_3d)
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
    result = await agent.run(state)
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

@app.post("/api/v1/reconstruct")
async def reconstruct(request: ReconstructRequest) -> dict:
    state = runs.get(request.run_id) if request.run_id else None
    image_urls = request.image_urls or ([request.image_url] if request.image_url else [])
    if not image_urls and state:
        image_urls = state.image_urls
    if not image_urls:
        raise HTTPException(400, "image_url or image_urls is required")
    result = await agent.lux3d.image_to_3d(image_urls, request.version, request.wait)
    if state:
        state.evidence.append(Evidence(kind="3d", source="lux3d-cn", uri=image_urls[0], confidence=0.8 if result.get("status") == "submitted" else 0.3, claims=result, provenance="verified" if result.get("status") == "submitted" else "to_confirm"))
        runs[state.run_id] = state
    return result

@app.post("/api/v1/research")
async def research(request: ResearchRequest) -> dict:
    state = runs.get(request.run_id)
    if not state:
        raise HTTPException(404, "run not found")
    # The graph's research node is deterministic and source-labelled today; this endpoint keeps the tool boundary explicit.
    state.sources = []
    state.user_goal = request.query
    await agent.research({"state": state, "enable_research": True, "enable_design": False})
    return {"run_id": state.run_id, "sources": [s.model_dump(mode="json") for s in state.sources]}
