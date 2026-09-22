"""Enrich saved primary-batch crops with Bailian qwen-vl-plus.

Requires DASHSCOPE_API_KEY. Updates detections.json material / condition fields.
Does not write pathways.

Usage:
    python pipeline/enrich_crops.py
    python pipeline/enrich_crops.py --scene hotel_room
"""

from __future__ import annotations

import argparse
import json
import sys
from pathlib import Path

import cv2

ROOT = Path(__file__).resolve().parents[1]
if str(ROOT) not in sys.path:
    sys.path.insert(0, str(ROOT))

from pipeline.env import load_dotenv
from pipeline.enrichment import enrich_crop, has_api_key
from pipeline.scenes import RUNS, get_scene

load_dotenv()

FIXTURE_DIR = ROOT / "data" / "fixtures"
SCENES_DIR = FIXTURE_DIR / "scenes"


def _enrich_scene(detections: dict, batches: dict, crop_dir: Path) -> int:
    by_id = {obj["id"]: obj for obj in detections["objects"]}
    enriched = 0
    for batch in batches["component_batches"]:
        crop_path = crop_dir / f"{batch['id']}.jpg"
        if not crop_path.exists():
            print(f"missing crop {crop_path}", flush=True)
            continue
        image = cv2.imread(str(crop_path))
        if image is None:
            print(f"cannot read {crop_path}", flush=True)
            continue
        facts = enrich_crop(image)
        primary_id = batch["object_ids"][0]
        for object_id in batch["object_ids"]:
            obj = by_id[object_id]
            if (
                abs(obj["location"]["yaw"] - batch["primary_hotspot"]["yaw"]) < 0.05
                and abs(obj["location"]["pitch"] - batch["primary_hotspot"]["pitch"]) < 0.05
            ):
                primary_id = object_id
                break
        primary = by_id[primary_id]
        primary["material"] = {"value": facts["material"], "confidence": None}
        primary["visible_condition"] = {"value": facts["visible_condition"], "confidence": None}
        primary["visible_damage_clue"] = {"value": facts["visible_damage_clue"]}
        if facts["material"]:
            primary["label"] = f"{facts['material']} {primary['category']}"
            batch["label"] = primary["label"]
        enriched += 1
        print(f"{batch['id']}: {facts['material']} / {facts['visible_condition']}", flush=True)
    return enriched


def main(argv: list[str] | None = None) -> None:
    parser = argparse.ArgumentParser()
    parser.add_argument("--scene", help="Scene slug; default = all scene fixture dirs")
    args = parser.parse_args(argv)

    if not has_api_key():
        raise SystemExit("Set DASHSCOPE_API_KEY before running enrichment")

    if args.scene:
        scene = get_scene(args.scene)
        targets = [(scene.fixture_dir, scene.crop_dir)]
    else:
        targets = []
        if SCENES_DIR.exists():
            for scene_dir in sorted(SCENES_DIR.iterdir()):
                if scene_dir.is_dir():
                    targets.append((scene_dir, RUNS / scene_dir.name / "crops"))
        if not targets:
            targets = [(FIXTURE_DIR, RUNS / "hotel_room" / "crops")]

    total = 0
    for fixture_dir, crop_dir in targets:
        detections_path = fixture_dir / "detections.json"
        batches_path = fixture_dir / "batches.json"
        if not detections_path.exists() or not batches_path.exists():
            print(f"skip missing fixtures in {fixture_dir}", flush=True)
            continue
        detections = json.loads(detections_path.read_text(encoding="utf-8"))
        batches = json.loads(batches_path.read_text(encoding="utf-8"))
        enriched = _enrich_scene(detections, batches, crop_dir)
        detections_path.write_text(json.dumps(detections, ensure_ascii=False, indent=2), encoding="utf-8")
        batches_path.write_text(json.dumps(batches, ensure_ascii=False, indent=2), encoding="utf-8")
        total += enriched
        print(f"updated {enriched} batches in {fixture_dir.name}", flush=True)
    print(f"enriched {total} crops total", flush=True)


if __name__ == "__main__":
    main()
