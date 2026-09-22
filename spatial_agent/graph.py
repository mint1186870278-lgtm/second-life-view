from __future__ import annotations
import json
from typing import Any, Literal, TypedDict
from spatial_agent.config import Settings
from spatial_agent.models import (
    AgentEvent, CaptureAction, DesignProposal, Detection, Evidence,
    RunState, SearchSource, SpatialObject, SpatialRelation,
)
from spatial_agent.providers import BailianClient, Lux3DClient

class GraphState(TypedDict, total=False):
    state: RunState
    enable_research: bool
    enable_design: bool
    enable_3d: bool

class SpatialAgentGraph:
    """A cooperative graph with explicit evidence gates and resumable state."""
    def __init__(self, settings: Settings):
        self.settings = settings
        self.bailian = BailianClient(settings)
        self.lux3d = Lux3DClient(settings)
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
            builder.add_conditional_edges("evidence", self.route_evidence, {"awaiting_evidence": END, "supervisor": "supervisor"})
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
            # A deterministic fixture lets the hackathon demo run before the Windows gateway is connected.
            detections = [
                Detection(class_name="wood_cabinet", bbox=[0.22, 0.22, 0.49, 0.78], confidence=0.91, track_id="demo-cabinet"),
                Detection(class_name="door", bbox=[0.70, 0.15, 0.94, 0.92], confidence=0.86, track_id="demo-door"),
            ]
            state.detections = detections
            self._event(state, "perception", "fixture", "未收到 YOLO JSON，载入演示检测结果")
        vlm_results: list[dict[str, Any]] = []
        if self.bailian.enabled and state.image_urls:
            for image_url in state.image_urls[:2]:
                try:
                    result = await self.bailian.inspect_space(image_url, [d.model_dump(by_alias=True) for d in detections], state.user_goal)
                    vlm_results.extend(result.get("objects", []))
                except Exception as exc:
                    state.errors.append(f"VLM failed: {exc}")
        for idx, detection in enumerate(detections):
            vr = vlm_results[idx] if idx < len(vlm_results) else {}
            category = detection.class_name
            material = vr.get("material") or ("实木/木饰面" if "wood" in category or "cabinet" in category else None)
            condition = vr.get("condition") or ("表面磨损，结构完整" if "cabinet" in category else ("补拍确认：结构/表面状态已观察" if state.metadata.get("capture_confirmed") else "待现场确认"))
            reuse = vr.get("reuse_potential") or ("refurbish" if "cabinet" in category else "unknown")
            confidence = float(vr.get("confidence", detection.confidence))
            missing = list(vr.get("missing_fields", []))
            if not material: missing.append("material")
            if not condition or condition == "待现场确认": missing.append("condition")
            if state.metadata.get("capture_confirmed") and not vr.get("missing_fields"):
                missing = []
            obj = SpatialObject(category=category, bbox=detection.bbox, confidence=confidence, material=material, condition=condition, reuse_potential=reuse, missing_fields=list(dict.fromkeys(missing)))
            obj.evidence_ids.append(f"det_{idx}")
            state.objects.append(obj)
            state.evidence.append(Evidence(id=f"det_{idx}", kind="detection", source="windows_yolo_gateway", uri=state.image_urls[0] if state.image_urls else None, confidence=detection.confidence, claims={"class": category, "bbox": detection.bbox}, provenance="verified"))
            if vr:
                state.evidence.append(Evidence(kind="vlm", source="bailian_qwen3.8-max", uri=state.image_urls[0], confidence=confidence, claims=vr, provenance="inferred"))
        if len(state.objects) >= 2:
            state.relations.append(SpatialRelation(subject_id=state.objects[0].id, predicate="inside_same_space_as", object_id=state.objects[1].id, confidence=0.72))
        self._event(state, "perception", "understand", f"建立 {len(state.objects)} 个空间资产", objects=len(state.objects), detections=len(detections))
        return data

    def evidence(self, data: GraphState) -> GraphState:
        state = data["state"]
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

    def route_evidence(self, data: GraphState) -> Literal["awaiting_evidence", "supervisor"]:
        return "awaiting_evidence" if data["state"].status == "awaiting_evidence" else "supervisor"

    async def research(self, data: GraphState) -> GraphState:
        state = data["state"]
        query = state.user_goal + " " + ", ".join(f"{o.category} {o.material or ''}" for o in state.objects)
        # Replace with a search/RAG MCP tool in production. Sources are explicit and labelled.
        state.sources = [
            SearchSource(title="材料再利用评估清单（演示知识库）", url="kb://circular-construction/material-reuse", snippet="先核验尺寸、连接方式、污染/霉变和拆卸损伤，再决定原位再用、翻新或材料回收。", source_type="knowledge_base", confidence=0.88),
            SearchSource(title="本地回收机会（演示连接器）", url="local://opportunities?query=" + query[:80], snippet="可在接入城市回收商 API 后返回距离、接收类别、价格和预约状态。", source_type="local_opportunity", confidence=0.55),
        ]
        self._event(state, "research", "retrieve", "返回带来源的再利用依据", query=query)
        return data

    async def design(self, data: GraphState) -> GraphState:
        state = data["state"]
        if not data.get("enable_design", True):
            state.status = "completed"
            self._event(state, "design", "skip", "调用方关闭设计阶段")
            return data
        objects = list(state.objects)
        target_ids = [o.id for o in objects]
        prompt = f"{state.user_goal}；目标构件：" + "、".join(f"{o.category}（{o.material or '材质待定'}，{o.condition or '状态待定'}）" for o in objects)
        if self.bailian.enabled and state.image_urls:
            try:
                result = await self.bailian.generate_image(prompt, state.image_urls[0])
                image_url = result.get("image_url") if isinstance(result, dict) else None
                output = (result or {}).get("output") or {} if isinstance(result, dict) else {}
                results = output.get("results") if isinstance(output, dict) else None
                if not image_url and isinstance(results, list) and results:
                    image_url = results[0].get("url")
                status = "generated" if image_url else "draft"
            except Exception as exc:
                state.errors.append(f"image generation failed: {exc}")
                image_url, status = None, "failed"
        else:
            image_url, status = None, "draft"
        state.designs = [DesignProposal(title="保留结构的低碳翻新方案", rationale="先保留可逆连接与主体骨架，再对表面材料和五金进行可替换升级。", prompt=prompt, image_url=image_url, asset_object_ids=target_ids, constraints=["不改变主体尺寸与开合关系", "输出标注推测区域并保留人工确认点"], status=status)]
        state.status = "completed"
        self._event(state, "design", "propose", "生成可追溯的改造方案", design_status=status)
        return data

    async def run(self, state: RunState, *, enable_research: bool = True, enable_design: bool = True, enable_3d: bool = False) -> RunState:
        result = await self.compiled.ainvoke({"state": state, "enable_research": enable_research, "enable_design": enable_design, "enable_3d": enable_3d})
        return result["state"]

    async def generate_design(self, state: RunState, brief: str, object_ids: list[str] | None = None, reference_image_url: str | None = None) -> RunState:
        """Regenerate only the design node for an interactive design iteration."""
        selected = object_ids or [o.id for o in state.objects]
        selected_objects = [o for o in state.objects if o.id in selected] or state.objects
        prompt = f"{brief}。目标构件：" + "、".join(f"{o.category}（材质：{o.material or '待确认'}；状态：{o.condition or '待确认'}）" for o in selected_objects)
        result = await self.bailian.generate_image(prompt, reference_image_url or (state.image_urls[0] if state.image_urls else None))
        image_url = None
        if isinstance(result, dict):
            image_url = result.get("image_url")
            output = result.get("output") or {}
            results = output.get("results") if isinstance(output, dict) else None
            if not image_url and isinstance(results, list) and results:
                image_url = results[0].get("url")
        state.designs = [DesignProposal(title="交互式构件翻新效果", rationale="把结构保持、材料替换和可逆施工约束写入生成提示词。", prompt=prompt, image_url=image_url, asset_object_ids=[o.id for o in selected_objects], constraints=["保留原始结构", "保持原空间位置与比例", "标注不确定区域"], status="generated" if image_url else "draft")]
        state.status = "completed"
        self._event(state, "design", "regenerate", "基于用户 brief 生成翻新方案", object_ids=selected)
        return state
