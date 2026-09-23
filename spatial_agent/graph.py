from __future__ import annotations
import json
from typing import Any, Literal, TypedDict
from spatial_agent.config import Settings
from spatial_agent.models import (
    AgentEvent, CaptureAction, DesignProposal, Detection, Evidence,
    RunState, SearchSource, SpatialObject, SpatialRelation,
)
from spatial_agent.providers import BailianClient, Lux3DClient
from spatial_agent.providers.research import ResearchClient

class GraphState(TypedDict, total=False):
    state: RunState
    enable_research: bool
    enable_design: bool
    enable_3d: bool
    include_web: bool

class SpatialAgentGraph:
    """A cooperative graph with explicit evidence gates and resumable state."""
    def __init__(self, settings: Settings):
        self.settings = settings
        self.bailian = BailianClient(settings)
        self.lux3d = Lux3DClient(settings)
        self.research_client = ResearchClient(settings)
        try:
            from langgraph.graph import StateGraph, START, END
            builder = StateGraph(GraphState)
            builder.add_node("supervisor", self.supervisor)
            builder.add_node("perception", self.perception)
            builder.add_node("evidence", self.evidence)
            builder.add_node("research", self.research)
            builder.add_node("design", self.design)
            builder.add_edge(START, "supervisor")
            builder.add_conditional_edges("supervisor", self.route_supervisor, {"perception": "perception", "research": "research", "design": "design", "end": END})
            builder.add_edge("perception", "evidence")
            builder.add_conditional_edges("evidence", self.route_evidence, {"awaiting_evidence": END, "supervisor": "supervisor", "end": END})
            builder.add_edge("research", "design")
            builder.add_edge("design", END)
            self.compiled = builder.compile()
        except ImportError as exc:
            raise RuntimeError("LangGraph is required. Install requirements.txt") from exc

    @staticmethod
    def _event(state: RunState, agent: str, action: str, message: str, **data: Any) -> None:
        state.events.append(AgentEvent(agent=agent, action=action, message=message, data=data))

    def supervisor(self, data: GraphState) -> GraphState:
        state = data["state"]
        state.iteration += 1
        if not state.objects:
            state.next_agent = "perception"
        elif data.get("enable_research", True) and not state.sources:
            state.next_agent = "research"
        elif data.get("enable_design", True) and not state.designs:
            state.next_agent = "design"
        else:
            state.status = "completed"
            state.next_agent = "end"
        self._event(state, "supervisor", "route", f"调度 {state.next_agent}", iteration=state.iteration)
        return data

    def route_supervisor(self, data: GraphState) -> Literal["perception", "research", "design", "end"]:
        return data["state"].next_agent or "end"

    async def perception(self, data: GraphState) -> GraphState:
        state = data["state"]
        detections = state.detections
        if not detections:
            if state.metadata.get("yolo_mode") == "live":
                state.metadata["live_yolo_empty"] = True
                self._event(state, "perception", "no_detections", "Linux YOLO 已完成实时检测，但未识别到配置类别")
                return data
            # A deterministic fixture lets the hackathon demo run before the Windows gateway is connected.
            detections = [
                Detection(class_name="wood_cabinet", bbox=[0.22, 0.22, 0.49, 0.78], confidence=0.91, track_id="demo-cabinet"),
                Detection(class_name="door", bbox=[0.70, 0.15, 0.94, 0.92], confidence=0.86, track_id="demo-door"),
            ]
            state.detections = detections
            self._event(state, "perception", "fixture", "未收到 YOLO JSON，载入演示检测结果")
        vlm_results: list[dict[str, Any]] = []
        if self.bailian.enabled and state.image_urls and not state.metadata.get("skip_vlm_enrichment"):
            for image_url in state.image_urls[:2]:
                try:
                    result = await self.bailian.inspect_space(image_url, [d.model_dump(by_alias=True) for d in detections], state.user_goal)
                    vlm_results.extend(result.get("objects", []))
                except Exception as exc:
                    state.errors.append(f"VLM failed: {exc}")
        for idx, detection in enumerate(detections):
            vr = vlm_results[idx] if idx < len(vlm_results) else {}
            category = detection.class_name
            # TAY-LI semantic facts are authoritative observations from its fixture
            # pipeline; VLM is an optional enrichment layer on top.
            material = vr.get("material") or detection.material
            condition = vr.get("condition") or detection.visible_condition
            if not condition and state.metadata.get("capture_confirmed"):
                condition = "补拍确认：结构/表面状态已观察"
            raw_reuse = str(vr.get("reuse_potential") or "").lower()
            # VLMs often use natural-language grades (high/medium/low) or
            # pathway names. Keep the state contract intentionally small.
            reuse_map = {
                "high": "reuse", "medium": "refurbish", "low": "recycle",
                "direct_reuse": "reuse", "reuse": "reuse", "refurbish": "refurbish",
                "recycle": "recycle", "material_recovery": "recycle",
            }
            reuse = reuse_map.get(raw_reuse, "refurbish" if "cabinet" in category else "unknown")
            confidence = float(vr.get("confidence", detection.confidence))
            # Keep the evidence gate about fields we can actually collect in
            # this workflow. VLMs may return bookkeeping fields such as
            # component_batch_id or visible_damage_clue even after giving a
            # usable material/condition answer; those should not create a
            # false recapture request.
            aliases = {"visible_condition": "condition", "state": "condition", "damage": "visible_damage_clue"}
            missing = []
            for field in vr.get("missing_fields", []) if isinstance(vr.get("missing_fields", []), list) else []:
                normalized = aliases.get(str(field), str(field))
                if normalized in {"material", "condition", "dimensions", "visible_damage_clue"} and normalized not in missing:
                    missing.append(normalized)
            if material:
                missing = [field for field in missing if field != "material"]
            else:
                missing.append("material")
            if condition and condition != "待现场确认":
                missing = [field for field in missing if field != "condition"]
            else:
                missing.append("condition")
            if detection.visible_damage_clue:
                missing = [field for field in missing if field != "visible_damage_clue"]
            if state.metadata.get("capture_confirmed") and not vr.get("missing_fields"):
                missing = []
            obj = SpatialObject(id=detection.id or detection.track_id or f"obj_{idx}", category=category, bbox=detection.bbox, bbox_xyxy=detection.bbox_xyxy, segmentation=detection.segmentation, confidence=confidence, source=detection.source, raw_label=detection.raw_label, yaw=detection.yaw, pitch=detection.pitch, material=material, condition=condition, visible_damage_clue=detection.visible_damage_clue, component_batch_id=detection.component_batch_id, pathway_assessment=detection.pathway_assessment, recommended_pathway=detection.recommended_pathway, reuse_potential=("reuse" if detection.recommended_pathway == "DIRECT_REUSE" else "refurbish" if detection.recommended_pathway == "REFURBISH" else "recycle" if detection.recommended_pathway == "MATERIAL_RECOVERY" else reuse), missing_fields=list(dict.fromkeys(missing)))
            obj.evidence_ids.append(f"det_{idx}")
            state.objects.append(obj)
            state.evidence.append(Evidence(id=f"det_{idx}", kind="detection", source=detection.source, uri=state.image_urls[0] if state.image_urls else None, confidence=detection.confidence, claims={"class": category, "bbox": detection.bbox, "yaw": detection.yaw, "pitch": detection.pitch, "component_batch_id": detection.component_batch_id, "recommended_pathway": detection.recommended_pathway}, provenance="verified"))
            if vr:
                state.evidence.append(Evidence(kind="vlm", source="bailian_qwen3.8-max", uri=state.image_urls[0], confidence=confidence, claims=vr, provenance="inferred"))
        if len(state.objects) >= 2:
            state.relations.append(SpatialRelation(subject_id=state.objects[0].id, predicate="inside_same_space_as", object_id=state.objects[1].id, confidence=0.72))
        if data.get("enable_3d"):
            public_urls = [u for u in state.image_urls if isinstance(u, str) and u.startswith(("http://", "https://"))]
            if public_urls:
                try:
                    state.metadata["lux3d"] = await self.lux3d.image_to_3d(public_urls[:4], version="G1-Turbo", wait=False)
                    state.evidence.append(Evidence(kind="3d", source="aholo:lux3d-cn", uri=public_urls[0], confidence=0.8, claims=state.metadata["lux3d"], provenance="verified"))
                    self._event(state, "perception", "reconstruct_3d", "提交 Aholo Lux3D 国内图生 3D 任务", task=state.metadata["lux3d"])
                except Exception as exc:
                    state.errors.append(f"Lux3D failed: {exc}")
            else:
                state.metadata["lux3d"] = {"status": "needs_public_url", "message": "Lux3D requires an HTTP(S) image URL; upload the Windows frame first."}
        self._event(state, "perception", "understand", f"建立 {len(state.objects)} 个空间资产", objects=len(state.objects), detections=len(detections))
        return data

    def evidence(self, data: GraphState) -> GraphState:
        state = data["state"]
        if state.metadata.get("live_yolo_empty"):
            state.status = "completed"
            self._event(state, "evidence", "no_objects", "实时 YOLO 未检测到构件，未回退到演示 fixture")
            return data
        state.capture_actions.clear()
        for obj in state.objects:
            if obj.missing_fields or obj.confidence < self.settings.evidence_confidence_threshold:
                target = obj.missing_fields[0] if obj.missing_fields else "condition"
                action_type = "zoom_region" if obj.bbox else "request_user_photo"
                state.capture_actions.append(CaptureAction(action_type=action_type, target_object_id=obj.id, target_bbox=obj.bbox, reason=f"{obj.category} 的 {target} 证据不足，无法可靠判断再利用方式", priority="high", camera_command={"bbox": obj.bbox, "capture": "high_res"}))
        if state.capture_actions:
            state.status = "awaiting_evidence"
            state.next_agent = None
            self._event(state, "evidence", "request", "暂停在证据门，等待相机或用户补证", actions=[a.model_dump() for a in state.capture_actions])
            return data
        state.status = "ready_for_design"
        self._event(state, "evidence", "approve", "证据满足当前任务阈值")
        return data

    def route_evidence(self, data: GraphState) -> Literal["awaiting_evidence", "supervisor", "end"]:
        if data["state"].status == "completed":
            return "end"
        return "awaiting_evidence" if data["state"].status == "awaiting_evidence" else "supervisor"

    async def research(self, data: GraphState) -> GraphState:
        state = data["state"]
        query = state.user_goal + " " + ", ".join(f"{o.category} {o.material or ''}" for o in state.objects)
        categories = [o.category for o in state.objects]
        state.sources = await self.research_client.retrieve(
            query, categories, region=state.metadata.get("region"), include_web=data.get("include_web")
        )
        state.evidence.extend(
            Evidence(kind="search", source=item.source_type, uri=item.url, confidence=item.confidence,
                     claims={"title": item.title, "snippet": item.snippet}, provenance=item.provenance)
            for item in state.sources
        )
        self._event(state, "research", "retrieve", "检索知识库与本地机会，并标注来源状态", query=query, count=len(state.sources))
        return data

    async def design(self, data: GraphState) -> GraphState:
        state = data["state"]
        if not data.get("enable_design", True):
            state.status = "completed"
            self._event(state, "design", "skip", "调用方关闭设计阶段")
            return data
        objects = list(state.objects)
        target_ids = [o.id for o in objects]
        source_context = "；".join(f"{s.title}: {s.snippet} [{s.provenance}]" for s in state.sources[:6])
        prompt = f"{state.user_goal}；目标构件：" + "、".join(f"{o.category}（{o.material or '材质待定'}，{o.condition or '状态待定'}）" for o in objects)
        if source_context:
            prompt += f"；研究依据（不得把待确认信息写成事实）：{source_context}"
        generation_task_id = None
        if self.bailian.enabled and state.image_urls:
            try:
                result = await self.bailian.generate_image(prompt, state.image_urls[0])
                image_url = result.get("image_url") if isinstance(result, dict) else None
                output = (result or {}).get("output") or {} if isinstance(result, dict) else {}
                results = output.get("results") if isinstance(output, dict) else None
                generation_task_id = output.get("task_id") if isinstance(output, dict) else None
                if not image_url and isinstance(results, list) and results:
                    image_url = results[0].get("url")
                status = "generated" if image_url else ("submitted" if generation_task_id else "draft")
                state.metadata["bailian_image_generation"] = result
            except Exception as exc:
                state.errors.append(f"image generation failed: {exc}")
                image_url, status = None, "failed"
        else:
            image_url, status = None, "draft"
        state.designs = [DesignProposal(title="保留结构的低碳翻新方案", rationale="先保留可逆连接与主体骨架，再对表面材料和五金进行可替换升级。", prompt=prompt, image_url=image_url, generation_task_id=generation_task_id, asset_object_ids=target_ids, constraints=["不改变主体尺寸与开合关系", "输出标注推测区域并保留人工确认点"], status=status)]
        state.status = "completed"
        self._event(state, "design", "propose", "生成可追溯的改造方案", design_status=status)
        return data

    async def run(self, state: RunState, *, enable_research: bool = True, enable_design: bool = True, enable_3d: bool = False, include_web: bool = False) -> RunState:
        result = await self.compiled.ainvoke({"state": state, "enable_research": enable_research, "enable_design": enable_design, "enable_3d": enable_3d, "include_web": include_web})
        return result["state"]

    async def generate_design(self, state: RunState, brief: str, object_ids: list[str] | None = None, reference_image_url: str | None = None) -> RunState:
        """Regenerate only the design node for an interactive design iteration."""
        selected = object_ids or [o.id for o in state.objects]
        selected_objects = [o for o in state.objects if o.id in selected] or state.objects
        source_context = "；".join(f"{s.title}: {s.snippet} [{s.provenance}]" for s in state.sources[:6])
        prompt = f"{brief}。目标构件：" + "、".join(f"{o.category}（材质：{o.material or '待确认'}；状态：{o.condition or '待确认'}）" for o in selected_objects)
        if source_context:
            prompt += f"。参考研究依据（待确认内容需明确标记）：{source_context}"
        result = await self.bailian.generate_image(prompt, reference_image_url or (state.image_urls[0] if state.image_urls else None))
        image_url = None
        generation_task_id = None
        if isinstance(result, dict):
            image_url = result.get("image_url")
            output = result.get("output") or {}
            results = output.get("results") if isinstance(output, dict) else None
            generation_task_id = output.get("task_id") if isinstance(output, dict) else None
            if not image_url and isinstance(results, list) and results:
                image_url = results[0].get("url")
        state.designs = [DesignProposal(title="交互式构件翻新效果", rationale="把结构保持、材料替换和可逆施工约束写入生成提示词。", prompt=prompt, image_url=image_url, generation_task_id=generation_task_id, asset_object_ids=[o.id for o in selected_objects], constraints=["保留原始结构", "保持原空间位置与比例", "标注不确定区域"], status="generated" if image_url else ("submitted" if generation_task_id else "draft"))]
        state.status = "completed"
        self._event(state, "design", "regenerate", "基于用户 brief 生成翻新方案", object_ids=selected)
        return state
