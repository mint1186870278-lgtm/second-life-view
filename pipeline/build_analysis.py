"""Merge per-scene perception fixtures into one Analysis Root JSON."""

from __future__ import annotations

import json
import sys
from pathlib import Path

ROOT = Path(__file__).resolve().parents[1]
if str(ROOT) not in sys.path:
    sys.path.insert(0, str(ROOT))

FIXTURE_DIR = ROOT / "data" / "fixtures"
SCENES_DIR = FIXTURE_DIR / "scenes"


def _attach_primary_objects(batches: list[dict], by_id: dict[str, dict]) -> None:
    for batch in batches:
        primary = None
        for object_id in batch["object_ids"]:
            obj = by_id.get(object_id)
            if obj is None:
                continue
            if (
                abs(obj["location"]["yaw"] - batch["primary_hotspot"]["yaw"]) < 0.05
                and abs(obj["location"]["pitch"] - batch["primary_hotspot"]["pitch"]) < 0.05
            ):
                primary = obj
                break
        if primary is None and batch["object_ids"]:
            primary = by_id.get(batch["object_ids"][0])
        if primary is None:
            continue
        batch["primary_object"] = {
            "id": primary["id"],
            "category": primary["category"],
            "label": primary["label"],
            "material": primary["material"],
            "visible_condition": primary["visible_condition"],
            "visible_damage_clue": primary.get("visible_damage_clue"),
            "detection": primary["detection"],
        }


def _load_scene_pair(scene_dir: Path) -> tuple[dict, dict] | None:
    detections_path = scene_dir / "detections.json"
    batches_path = scene_dir / "batches.json"
    if not detections_path.exists() or not batches_path.exists():
        return None
    detections = json.loads(detections_path.read_text(encoding="utf-8"))
    batches = json.loads(batches_path.read_text(encoding="utf-8"))
    return detections, batches


def main() -> None:
    from pipeline.scenes import SCENES

    scene_pairs: list[tuple[dict, dict]] = []
    if SCENES_DIR.exists():
        preferred = [spec.slug for spec in sorted(SCENES, key=lambda s: s.order)]
        dirs = {p.name: p for p in SCENES_DIR.iterdir() if p.is_dir()}
        ordered_dirs = [dirs[slug] for slug in preferred if slug in dirs]
        ordered_dirs.extend(sorted(p for name, p in dirs.items() if name not in preferred))
        for scene_dir in ordered_dirs:
            pair = _load_scene_pair(scene_dir)
            if pair is not None:
                scene_pairs.append(pair)

    # Fallback: single-scene root fixtures (legacy).
    if not scene_pairs:
        pair = _load_scene_pair(FIXTURE_DIR)
        if pair is None:
            raise SystemExit("no fixtures found under data/fixtures/scenes or data/fixtures")
        scene_pairs = [pair]

    all_objects: list[dict] = []
    all_batches: list[dict] = []
    scenes_meta: list[dict] = []
    panoramas: list[dict] = []
    sources: list[dict] = []
    pathway_counts = {name: 0 for name in [
        "KEEP_IN_PLACE",
        "DIRECT_REUSE",
        "REFURBISH",
        "REPURPOSE",
        "MATERIAL_RECOVERY",
        "DISPOSAL",
        "NO_PRIMARY_YET",
    ]}
    unresolved = 0

    for order, (detections, batches) in enumerate(scene_pairs, start=1):
        by_id = {obj["id"]: obj for obj in detections["objects"]}
        _attach_primary_objects(batches["component_batches"], by_id)

        slug = detections.get("scene_slug") or detections["scene_id"]
        title = detections["source"]["title"]
        thumb = f"data/samples/runs/{slug}/views/yaw000_pitch000.jpg"
        if not (ROOT / thumb).exists():
            thumb = detections["image"]

        scenes_meta.append(
            {
                "id": detections["scene_id"],
                "name": title,
                "slug": slug,
                "panorama_id": detections["panorama_id"],
                "thumbnail_url": thumb,
                "order": order,
                "default_view": {"yaw": 0, "pitch": 0},
            }
        )
        panoramas.append(
            {
                "id": detections["panorama_id"],
                "source_type": "upload",
                "image_url": detections["image"],
                "width": detections["width"],
                "height": detections["height"],
            }
        )
        sources.append(
            {
                "id": f"source_{slug}",
                "source_type": "public_dataset",
                "title": title,
                "publisher_or_org": detections["source"]["author"],
                "url": detections["source"]["page"],
                "region": None,
                "provenance": "curated_fixture",
                "source_confidence": "primary_source",
                "license": detections["source"]["license"],
            }
        )
        all_objects.extend(detections["objects"])
        for batch in batches["component_batches"]:
            recommendation = (batch.get("assessment") or {}).get("system_recommendation") or {}
            primary = recommendation.get("primary_pathway")
            if primary in pathway_counts and primary != "NO_PRIMARY_YET":
                pathway_counts[primary] += 1
            else:
                pathway_counts["NO_PRIMARY_YET"] += 1
                unresolved += 1
            all_batches.append(batch)

    analysis = {
        "analysis_id": "analysis_multi_001",
        "project_id": "project_001",
        "status": "completed",
        "pipeline": "B",
        "scenes": scenes_meta,
        "panoramas": panoramas,
        "objects": all_objects,
        "component_batches": all_batches,
        "sources": sources,
        "reference_pathways": [],
        "local_opportunities": [],
        "summary": {
            "scenes": len(scenes_meta),
            "detected_objects": len(all_objects),
            "component_batches": len(all_batches),
            "primary_pathway_distribution": pathway_counts,
            "evidence_status_summary": {
                "batches_with_unresolved_verification": unresolved,
                "unresolved_verification_items": 0,
            },
        },
    }
    out = FIXTURE_DIR / "analysis.json"
    out.write_text(json.dumps(analysis, ensure_ascii=False, indent=2), encoding="utf-8")

    index = {
        "scenes": [
            {
                "slug": scene["slug"],
                "scene_id": scene["id"],
                "title": scene["name"],
                "fixture_dir": f"data/fixtures/scenes/{scene['slug']}",
                "views_dir": f"data/samples/runs/{scene['slug']}/views",
                "panorama": next(
                    (p["image_url"] for p in panoramas if p["id"] == scene["panorama_id"]),
                    None,
                ),
            }
            for scene in scenes_meta
        ],
        "analysis": "data/fixtures/analysis.json",
    }
    (FIXTURE_DIR / "scenes_index.json").write_text(
        json.dumps(index, ensure_ascii=False, indent=2), encoding="utf-8"
    )
    print(
        f"wrote {out} with {analysis['summary']['scenes']} scenes, "
        f"{analysis['summary']['component_batches']} batches",
        flush=True,
    )


if __name__ == "__main__":
    main()
