"""Merge same-category detections whose yaw/pitch boxes overlap.

This is minimal grouping inside one scene. It deduplicates the same object
seen in overlapping perspective views. It is not cross-scene re-identification.
Raw clusters stay inside this function; callers only receive ComponentBatch records.
"""

from __future__ import annotations


def _iou(a: dict, b: dict) -> float:
    yaw_overlap = max(0.0, min(a["yaw_max"], b["yaw_max"]) - max(a["yaw_min"], b["yaw_min"]))
    pitch_overlap = max(0.0, min(a["pitch_max"], b["pitch_max"]) - max(a["pitch_min"], b["pitch_min"]))
    intersection = yaw_overlap * pitch_overlap
    area_a = max(0.0, a["yaw_max"] - a["yaw_min"]) * max(0.0, a["pitch_max"] - a["pitch_min"])
    area_b = max(0.0, b["yaw_max"] - b["yaw_min"]) * max(0.0, b["pitch_max"] - b["pitch_min"])
    union = area_a + area_b - intersection
    if union <= 1e-6:
        return 0.0
    return intersection / union


def _yaw(obj: dict) -> float:
    return float(obj["location"]["yaw"])


def _pitch(obj: dict) -> float:
    return float(obj["location"]["pitch"])


def _center_inside(point: dict, box: dict) -> bool:
    return (
        box["yaw_min"] <= _yaw(point) <= box["yaw_max"]
        and box["pitch_min"] <= _pitch(point) <= box["pitch_max"]
    )


def _should_merge(a: dict, b: dict) -> bool:
    if a["category"] != b["category"]:
        return False
    if _iou(a, b) >= 0.2:
        return True
    if _center_inside(a, b) and _center_inside(b, a):
        return True
    # Degenerate boxes only: fall back to a small angular distance.
    area_a = max(0.0, a["yaw_max"] - a["yaw_min"]) * max(0.0, a["pitch_max"] - a["pitch_min"])
    area_b = max(0.0, b["yaw_max"] - b["yaw_min"]) * max(0.0, b["pitch_max"] - b["pitch_min"])
    if area_a < 1.0 or area_b < 1.0:
        dyaw = abs(_yaw(a) - _yaw(b))
        dyaw = min(dyaw, 360.0 - dyaw)
        return dyaw <= 15.0 and abs(_pitch(a) - _pitch(b)) <= 15.0
    return False


def group_detections(objects: list[dict], scene_id: str) -> list[dict]:
    parent = list(range(len(objects)))

    def find(index: int) -> int:
        while parent[index] != index:
            parent[index] = parent[parent[index]]
            index = parent[index]
        return index

    for i in range(len(objects)):
        for j in range(i + 1, len(objects)):
            if _should_merge(objects[i], objects[j]):
                parent[find(i)] = find(j)

    clusters: dict[int, list[dict]] = {}
    for index, obj in enumerate(objects):
        clusters.setdefault(find(index), []).append(obj)

    batches = []
    ordered = sorted(
        clusters.values(),
        key=lambda members: (members[0]["category"], min(_yaw(m) for m in members)),
    )
    used_ids: set[str] = set()
    for members in ordered:
        primary = max(members, key=lambda item: item["detection"]["confidence"])
        yaw_bin = int(round(_yaw(primary) / 5.0) * 5)
        pitch_bin = int(round(_pitch(primary) / 5.0) * 5)
        batch_id = f"batch_{primary['category']}_{yaw_bin}_{pitch_bin}"
        suffix = 2
        while batch_id in used_ids:
            batch_id = f"batch_{primary['category']}_{yaw_bin}_{pitch_bin}_{suffix}"
            suffix += 1
        used_ids.add(batch_id)
        label = primary["category"].replace("_", " ").title()
        batches.append(
            {
                "id": batch_id,
                "label": label,
                "category": primary["category"],
                "object_ids": [item["id"] for item in members],
                "scene_ids": [scene_id],
                "detected_count": len(members),
                "primary_hotspot": {
                    "scene_id": scene_id,
                    "yaw": _yaw(primary),
                    "pitch": _pitch(primary),
                },
                "primary_object_id": primary["id"],
                "assessment": {},
            }
        )
    return batches
