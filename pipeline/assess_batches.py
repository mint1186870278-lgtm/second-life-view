"""Fill ComponentBatch.assessment from primary-object facts.

Usage:
    python pipeline/assess_batches.py

Reads data/fixtures/detections.json + batches.json, writes assessment back,
updates run_notes.md, and refreshes analysis.json via build_analysis.
"""

from __future__ import annotations

import json
import sys
from collections import Counter
from pathlib import Path

ROOT = Path(__file__).resolve().parents[1]
if str(ROOT) not in sys.path:
    sys.path.insert(0, str(ROOT))

from pipeline.assessment import assess_batch
from pipeline.build_analysis import main as build_analysis_main

FIXTURE_DIR = ROOT / "data" / "fixtures"


def apply_assessments(detections: dict, batches: dict) -> Counter:
    by_id = {obj["id"]: obj for obj in detections["objects"]}
    counts: Counter = Counter()
    for batch in batches["component_batches"]:
        assessment = assess_batch(batch, by_id)
        batch["assessment"] = assessment
        primary = assessment["system_recommendation"]["primary_pathway"]
        counts[primary or "NO_PRIMARY_YET"] += 1
    return counts


def main() -> None:
    detections = json.loads((FIXTURE_DIR / "detections.json").read_text(encoding="utf-8"))
    batches = json.loads((FIXTURE_DIR / "batches.json").read_text(encoding="utf-8"))
    counts = apply_assessments(detections, batches)
    (FIXTURE_DIR / "batches.json").write_text(
        json.dumps(batches, ensure_ascii=False, indent=2), encoding="utf-8"
    )

    assessed = len(batches["component_batches"])
    dist = ", ".join(f"{name}={counts[name]}" for name in sorted(counts))
    notes_path = FIXTURE_DIR / "run_notes.md"
    notes = notes_path.read_text(encoding="utf-8") if notes_path.exists() else ""
    lines = [
        line
        for line in notes.splitlines()
        if not line.startswith("- Assessment")
        and not line.startswith("- Pathway assessment")
        and not line.startswith("- Primary pathway distribution")
    ]
    while lines and lines[-1] == "":
        lines.pop()
    lines.extend(
        [
            f"- Pathway assessment: rule engine on {assessed} batches (no VLM pathway choice).",
            f"- Primary pathway distribution: {dist}.",
            "",
        ]
    )
    notes_path.write_text("\n".join(lines), encoding="utf-8")

    for batch in batches["component_batches"]:
        primary = batch["assessment"]["system_recommendation"]["primary_pathway"]
        print(f"{batch['id']}: {primary}", flush=True)
    print(f"assessed {assessed} batches ({dist})", flush=True)
    build_analysis_main()


if __name__ == "__main__":
    main()
