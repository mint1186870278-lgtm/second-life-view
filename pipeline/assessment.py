"""Deterministic Second Life pathway assessment for a ComponentBatch.

Reads observable facts only. Does not call a VLM and does not invent pathways
outside the six contract enums. DISPOSAL is assessed but never chosen as
primary or alternative while a higher-value path remains viable.
"""

from __future__ import annotations

from typing import Any

PATHWAYS = (
    "KEEP_IN_PLACE",
    "DIRECT_REUSE",
    "REFURBISH",
    "REPURPOSE",
    "MATERIAL_RECOVERY",
    "DISPOSAL",
)

_HIGHER_THAN_DISPOSAL = PATHWAYS[:-1]


def _pa(
    pathway: str,
    evidence_status: str,
    conditions: list[str] | None = None,
) -> dict[str, Any]:
    return {
        "pathway": pathway,
        "evidence_status": evidence_status,
        "conditions": list(conditions or []),
    }


def _insufficient_all(extra: dict[str, list[str]] | None = None) -> list[dict[str, Any]]:
    extras = extra or {}
    return [_pa(name, "insufficient_evidence", extras.get(name, [])) for name in PATHWAYS]


def assess(
    *,
    batch_id: str,
    category: str,
    material: str | None,
    visible_condition: str | None,
    visible_damage_clue: str | None = None,
) -> dict[str, Any]:
    """Return a SecondLifeAssessment dict for one batch."""
    category = (category or "").lower().strip()
    material = (material or "").lower().strip() or None
    condition = (visible_condition or "").lower().strip() or None
    damage = (visible_damage_clue or "").strip() or None

    if condition is None and material is None:
        return {
            "batch_id": batch_id,
            "pathway_assessments": _insufficient_all(
                {
                    "KEEP_IN_PLACE": ["补充分类外的可见状态与固定方式"],
                    "DIRECT_REUSE": ["补充材质与拆卸条件"],
                    "REFURBISH": ["补充可见损伤证据"],
                    "REPURPOSE": ["补充构件尺寸与材质"],
                    "MATERIAL_RECOVERY": ["补充材质识别"],
                    "DISPOSAL": ["仅在更高价值路径均被排除后启用"],
                }
            ),
            "system_recommendation": {
                "primary_pathway": None,
                "alternative_pathways": [],
                "rationale": "当前缺少材质与可见状态，证据不足，需人工复核。",
            },
        }

    worn = condition == "worn" or bool(damage)
    damaged = condition == "damaged"
    intact = condition == "apparently_intact" and not damage
    fixed_in_place = category in {"door", "window"}
    movable = category in {"chair", "table", "cabinet"}

    if damaged and material:
        assessments = [
            _pa("KEEP_IN_PLACE", "not_applicable", ["可见损伤已阻断原位保留"]),
            _pa("DIRECT_REUSE", "not_applicable", ["损伤程度不支持直接再用"]),
            _pa("REFURBISH", "conditional", ["确认修复成本与结构安全性"]),
            _pa("REPURPOSE", "conditional", ["确认改作他用的尺寸与安全要求"]),
            _pa("MATERIAL_RECOVERY", "supported", []),
            _pa(
                "DISPOSAL",
                "conditional",
                ["仅在更高价值路径均被排除、不可执行或法规 / 安全要求必须处置时启用"],
            ),
        ]
        primary = "MATERIAL_RECOVERY"
        alternatives = ["REFURBISH", "REPURPOSE"]
        rationale = f"可见状态为 damaged，材质识别为 {material}，优先材料回收。"
    elif worn:
        assessments = [
            _pa(
                "KEEP_IN_PLACE",
                "conditional" if fixed_in_place else "not_applicable",
                ["确认项目是否仍需要原功能"] if fixed_in_place else ["非固定构件，不适用原位保留"],
            ),
            _pa("DIRECT_REUSE", "conditional", ["确认表面处理与结构完整性"]),
            _pa("REFURBISH", "supported", ["局部打磨与表面重新处理"] if damage else []),
            _pa("REPURPOSE", "supported", []),
            _pa(
                "MATERIAL_RECOVERY",
                "supported" if material else "insufficient_evidence",
                [] if material else ["补充材质识别"],
            ),
            _pa(
                "DISPOSAL",
                "conditional",
                ["仅在更高价值路径均被排除、不可执行或法规 / 安全要求必须处置时启用"],
            ),
        ]
        primary = "REFURBISH"
        alternatives = ["REPURPOSE"]
        if material:
            alternatives.append("MATERIAL_RECOVERY")
        clue = f"；线索：{damage}" if damage else ""
        rationale = f"存在磨损或可见损伤线索{clue}，主体仍可修复后继续使用。"
    elif intact and fixed_in_place:
        assessments = [
            _pa("KEEP_IN_PLACE", "supported", ["确认项目是否仍需要原功能"]),
            _pa("DIRECT_REUSE", "conditional", ["确认固定方式与完整拆卸条件"]),
            _pa("REFURBISH", "conditional", ["仅在表面处理需要时启用"]),
            _pa("REPURPOSE", "conditional", ["确认改作他用的开口尺寸与安装条件"]),
            _pa(
                "MATERIAL_RECOVERY",
                "supported" if material else "insufficient_evidence",
                [] if material else ["补充材质识别"],
            ),
            _pa(
                "DISPOSAL",
                "conditional",
                ["仅在更高价值路径均被排除、不可执行或法规 / 安全要求必须处置时启用"],
            ),
        ]
        primary = "KEEP_IN_PLACE"
        alternatives = ["DIRECT_REUSE"]
        if material:
            alternatives.append("MATERIAL_RECOVERY")
        rationale = f"{category} 外观完好，优先原位保留；拆卸后再用需核实固定条件。"
    elif intact and movable:
        assessments = [
            _pa("KEEP_IN_PLACE", "not_applicable", ["可移动家具，不适用原位保留语义"]),
            _pa("DIRECT_REUSE", "supported", ["确认搬迁与清洁条件"]),
            _pa("REFURBISH", "conditional", ["仅在局部表面处理需要时启用"]),
            _pa("REPURPOSE", "supported", []),
            _pa(
                "MATERIAL_RECOVERY",
                "supported" if material else "insufficient_evidence",
                [] if material else ["补充材质识别"],
            ),
            _pa(
                "DISPOSAL",
                "conditional",
                ["仅在更高价值路径均被排除、不可执行或法规 / 安全要求必须处置时启用"],
            ),
        ]
        primary = "DIRECT_REUSE"
        alternatives = ["REPURPOSE"]
        if material:
            alternatives.append("MATERIAL_RECOVERY")
        mat_bit = f"，材质 {material}" if material else ""
        rationale = f"{category} 外观完好{mat_bit}，优先直接再用。"
    else:
        # Partial facts: e.g. material only, or unknown category/condition combo.
        assessments = [
            _pa("KEEP_IN_PLACE", "insufficient_evidence", ["确认是否固定安装且项目仍需要原功能"]),
            _pa("DIRECT_REUSE", "insufficient_evidence", ["补充可见状态与拆卸条件"]),
            _pa("REFURBISH", "insufficient_evidence", ["补充可见损伤证据"]),
            _pa("REPURPOSE", "conditional" if material else "insufficient_evidence", []),
            _pa(
                "MATERIAL_RECOVERY",
                "supported" if material else "insufficient_evidence",
                [] if material else ["补充材质识别"],
            ),
            _pa(
                "DISPOSAL",
                "conditional",
                ["仅在更高价值路径均被排除、不可执行或法规 / 安全要求必须处置时启用"],
            ),
        ]
        if material:
            primary = "MATERIAL_RECOVERY"
            alternatives = ["REPURPOSE"]
            rationale = f"可见状态不完整，仅材质 {material} 可用，暂以材料回收为保守推荐。"
        else:
            primary = None
            alternatives = []
            rationale = "可见事实不完整，证据不足，需人工复核。"

    alternatives = [p for p in alternatives if p != primary][:2]
    _assert_disposal_not_preferred(assessments, primary, alternatives)

    return {
        "batch_id": batch_id,
        "pathway_assessments": assessments,
        "system_recommendation": {
            "primary_pathway": primary,
            "alternative_pathways": alternatives,
            "rationale": rationale,
        },
    }


def _assert_disposal_not_preferred(
    assessments: list[dict[str, Any]],
    primary: str | None,
    alternatives: list[str],
) -> None:
    """Guardrail: DISPOSAL must not win while higher paths are still open."""
    by_name = {item["pathway"]: item for item in assessments}
    higher_open = any(
        by_name.get(name, {}).get("evidence_status") in {"supported", "conditional"}
        for name in _HIGHER_THAN_DISPOSAL
    )
    if higher_open and (primary == "DISPOSAL" or "DISPOSAL" in alternatives):
        raise RuntimeError("DISPOSAL selected while a higher-value pathway remains open")


def resolve_primary_object(batch: dict[str, Any], by_id: dict[str, dict[str, Any]]) -> dict[str, Any] | None:
    """Pick the batch primary object using hotspot match, then first object_id."""
    primary = None
    for object_id in batch.get("object_ids", []):
        obj = by_id.get(object_id)
        if obj is None:
            continue
        hotspot = batch.get("primary_hotspot") or {}
        if (
            abs(obj["location"]["yaw"] - hotspot.get("yaw", 0)) < 0.05
            and abs(obj["location"]["pitch"] - hotspot.get("pitch", 0)) < 0.05
        ):
            primary = obj
            break
    if primary is None and batch.get("object_ids"):
        primary = by_id.get(batch["object_ids"][0])
    return primary


def assess_batch(batch: dict[str, Any], by_id: dict[str, dict[str, Any]]) -> dict[str, Any]:
    """Assess one ComponentBatch using its primary object's facts."""
    primary = resolve_primary_object(batch, by_id)
    if primary is None:
        return assess(
            batch_id=batch["id"],
            category=batch.get("category", ""),
            material=None,
            visible_condition=None,
            visible_damage_clue=None,
        )
    damage = primary.get("visible_damage_clue") or {}
    damage_value = damage.get("value") if isinstance(damage, dict) else damage
    return assess(
        batch_id=batch["id"],
        category=primary.get("category") or batch.get("category", ""),
        material=(primary.get("material") or {}).get("value"),
        visible_condition=(primary.get("visible_condition") or {}).get("value"),
        visible_damage_clue=damage_value,
    )
