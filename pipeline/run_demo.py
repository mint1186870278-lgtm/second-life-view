"""Run Pipeline B perception locally and write JSON files.

Usage:
    python pipeline/run_demo.py
    python pipeline/run_demo.py --scene hotel_room
    python pipeline/run_demo.py --all
"""

from __future__ import annotations

import argparse
import json
import sys
import time
from pathlib import Path

import cv2

ROOT = Path(__file__).resolve().parents[1]
if str(ROOT) not in sys.path:
    sys.path.insert(0, str(ROOT))

from pipeline.assessment import assess_batch
from pipeline.env import load_dotenv
from pipeline.detection import detect_view, draw_detections, load_yolo_world, save_image
from pipeline.enrichment import crop_box, enrich_crop, has_api_key
from pipeline.grouping import group_detections
from pipeline.panorama import assert_center_maps_home, default_views, render_view
from pipeline.scenes import SCENES, SceneSpec, available_scenes, get_scene

load_dotenv()


def _round(value: float) -> float:
    return round(float(value), 1)


def run_scene(scene: SceneSpec, model=None) -> dict:
    """Run detect → group → crop → enrich → assess for one scene."""
    started = time.perf_counter()
    assert_center_maps_home()
    erp = cv2.imread(str(scene.image_path))
    if erp is None:
        raise SystemExit(f"cannot read {scene.image_path}")
    height, width = erp.shape[:2]
    views = default_views()
    print(f"[{scene.slug}] panorama {width}x{height}, views {len(views)}", flush=True)

    if model is None:
        print(f"[{scene.slug}] loading YOLO-World", flush=True)
        model = load_yolo_world()

    view_dir = scene.view_dir
    annotated_dir = scene.annotated_dir
    crop_dir = scene.crop_dir
    fixture_dir = scene.fixture_dir
    view_dir.mkdir(parents=True, exist_ok=True)
    annotated_dir.mkdir(parents=True, exist_ok=True)
    crop_dir.mkdir(parents=True, exist_ok=True)
    fixture_dir.mkdir(parents=True, exist_ok=True)

    raw_detections = []
    view_images = {}
    for view in views:
        view_started = time.perf_counter()
        image = render_view(erp, view)
        view_images[view.name] = image
        found = detect_view(model, image, view)
        save_image(view_dir / f"{view.name}.jpg", image)
        save_image(annotated_dir / f"{view.name}.jpg", draw_detections(image, found))
        raw_detections.extend(found)
        print(
            f"  [{scene.slug}] {view.name}: {len(found)} boxes in {time.perf_counter() - view_started:.1f}s",
            flush=True,
        )

    objects = []
    for index, item in enumerate(raw_detections, start=1):
        objects.append(
            {
                "id": f"{scene.slug}_obj_{index:03d}",
                "panorama_id": scene.panorama_id,
                "category": item["category"],
                "label": item["category"],
                "location": {"yaw": _round(item["yaw"]), "pitch": _round(item["pitch"])},
                "detection": {"confidence": round(item["confidence"], 3)},
                "material": {"value": None, "confidence": None},
                "visible_condition": {"value": None, "confidence": None},
                "visible_damage_clue": {"value": None},
                "spatial": None,
                "view": item["view"],
                "bbox_xyxy": [round(v, 1) for v in item["bbox_xyxy"]],
                "yaw_min": item["yaw_min"],
                "yaw_max": item["yaw_max"],
                "pitch_min": item["pitch_min"],
                "pitch_max": item["pitch_max"],
            }
        )

    batches = group_detections(objects, scene.scene_id)
    # Prefix batch ids with scene slug so multi-scene merges stay unique.
    for batch in batches:
        batch["id"] = f"{scene.slug}__{batch['id']}"

    by_id = {obj["id"]: obj for obj in objects}
    enrichment_error = None
    enriched = 0
    use_vl = has_api_key()
    if not use_vl:
        enrichment_error = "DASHSCOPE_API_KEY missing; crops saved, semantic fields left null"
        print(f"[{scene.slug}] {enrichment_error}", flush=True)
    for batch in batches:
        primary = by_id[batch["primary_object_id"]]
        crop = crop_box(view_images[primary["view"]], primary["bbox_xyxy"])
        save_image(crop_dir / f"{batch['id']}.jpg", crop)
        if not use_vl:
            continue
        try:
            facts = enrich_crop(crop)
        except Exception as exc:  # noqa: BLE001 - first failure stops paid calls
            enrichment_error = str(exc)
            print(f"[{scene.slug}] enrichment stopped: {exc}", flush=True)
            break
        primary["material"] = {"value": facts["material"], "confidence": None}
        primary["visible_condition"] = {"value": facts["visible_condition"], "confidence": None}
        primary["visible_damage_clue"] = {"value": facts["visible_damage_clue"]}
        if facts["material"]:
            primary["label"] = f"{facts['material']} {primary['category']}"
            batch["label"] = primary["label"]
        enriched += 1
        print(
            f"  [{scene.slug}] enriched {batch['id']}: {facts['material']} / {facts['visible_condition']}",
            flush=True,
        )

    public_objects = []
    for obj in objects:
        public = {
            key: value
            for key, value in obj.items()
            if key not in {"yaw_min", "yaw_max", "pitch_min", "pitch_max", "bbox_xyxy", "view"}
        }
        public_objects.append(public)

    detections_doc = {
        "scene_id": scene.scene_id,
        "panorama_id": scene.panorama_id,
        "scene_slug": scene.slug,
        "image": scene.image_rel,
        "width": width,
        "height": height,
        "source": {
            "title": scene.title,
            "page": scene.page,
            "author": scene.author,
            "license": scene.license,
        },
        "detector": "yolov8s-worldv2",
        "classes": ["door", "window", "chair", "table", "cabinet"],
        "objects": public_objects,
    }
    public_by_id = {obj["id"]: obj for obj in public_objects}
    component_batches = []
    pathway_counts: dict[str, int] = {}
    for batch in batches:
        public_batch = {key: value for key, value in batch.items() if key != "primary_object_id"}
        assessment = assess_batch(public_batch, public_by_id)
        public_batch["assessment"] = assessment
        primary_pathway = assessment["system_recommendation"]["primary_pathway"] or "NO_PRIMARY_YET"
        pathway_counts[primary_pathway] = pathway_counts.get(primary_pathway, 0) + 1
        component_batches.append(public_batch)
    batches_doc = {
        "scene_id": scene.scene_id,
        "panorama_id": scene.panorama_id,
        "scene_slug": scene.slug,
        "component_batches": component_batches,
    }
    categories = sorted({obj["category"] for obj in objects})
    elapsed = time.perf_counter() - started
    dist = ", ".join(f"{name}={pathway_counts[name]}" for name in sorted(pathway_counts)) or "none"
    notes = [
        f"# Pipeline B perception run — {scene.title}",
        "",
        f"- Scene slug: `{scene.slug}`",
        f"- Image: {scene.title}, {width}x{height}, {scene.license}, {scene.author}.",
        f"- Source page: {scene.page}",
        f"- Detector: yolov8s-worldv2 on CUDA. Classes: {', '.join(categories) or 'none'}.",
        f"- Detections: {len(objects)}. Batches: {len(batches)}. Elapsed: {elapsed:.1f}s.",
        f"- Semantic crops enriched: {enriched}.",
        f"- Enrichment: {enrichment_error or 'qwen-vl-plus via Bailian compatible API'}.",
        f"- Pathway assessment: rule engine on {len(component_batches)} batches (no VLM pathway choice).",
        f"- Primary pathway distribution: {dist}.",
        "- Raw clusters are not in the JSON. Frontend should read component_batches.",
    ]
    (fixture_dir / "detections.json").write_text(
        json.dumps(detections_doc, ensure_ascii=False, indent=2), encoding="utf-8"
    )
    (fixture_dir / "batches.json").write_text(
        json.dumps(batches_doc, ensure_ascii=False, indent=2), encoding="utf-8"
    )
    (fixture_dir / "run_notes.md").write_text("\n".join(notes) + "\n", encoding="utf-8")
    print(
        f"[{scene.slug}] wrote {len(objects)} objects, {len(batches)} batches → {fixture_dir}",
        flush=True,
    )
    return {
        "slug": scene.slug,
        "objects": len(objects),
        "batches": len(batches),
        "enriched": enriched,
        "elapsed": elapsed,
        "pathway_counts": pathway_counts,
    }


def _mirror_root_fixtures(scene: SceneSpec) -> None:
    """Keep root fixtures as a convenience copy of the primary scene."""
    root_fixtures = ROOT / "data" / "fixtures"
    root_fixtures.mkdir(parents=True, exist_ok=True)
    for name in ("detections.json", "batches.json", "run_notes.md"):
        src = scene.fixture_dir / name
        if src.exists():
            (root_fixtures / name).write_text(src.read_text(encoding="utf-8"), encoding="utf-8")


def main(argv: list[str] | None = None) -> None:
    parser = argparse.ArgumentParser(description="Pipeline B perception demo")
    parser.add_argument("--scene", help="Scene slug to run (default: hotel_room)")
    parser.add_argument("--all", action="store_true", help="Run all available scenes")
    parser.add_argument(
        "--list",
        action="store_true",
        help="List curated scenes and exit",
    )
    args = parser.parse_args(argv)

    if args.list:
        for scene in SCENES:
            mark = "ok" if scene.image_path.exists() else "missing"
            print(f"{scene.slug}\t{mark}\t{scene.title}")
        return

    if args.all:
        scenes = available_scenes()
        if not scenes:
            raise SystemExit("no scene images found under data/samples/panoramas")
        print(f"loading YOLO-World once for {len(scenes)} scenes", flush=True)
        model = load_yolo_world()
        summaries = []
        for scene in scenes:
            summaries.append(run_scene(scene, model=model))
        from pipeline.build_analysis import main as build_analysis_main

        build_analysis_main()
        _mirror_root_fixtures(scenes[0])
        print("--- multi-scene summary ---", flush=True)
        for item in summaries:
            print(
                f"  {item['slug']}: objects={item['objects']} batches={item['batches']} "
                f"enriched={item['enriched']} elapsed={item['elapsed']:.1f}s",
                flush=True,
            )
        return

    slug = args.scene or "hotel_room"
    scene = get_scene(slug)
    if not scene.image_path.exists():
        raise SystemExit(f"missing image: {scene.image_path}")
    run_scene(scene)
    _mirror_root_fixtures(scene)
    from pipeline.build_analysis import main as build_analysis_main

    build_analysis_main()


if __name__ == "__main__":
    main()
