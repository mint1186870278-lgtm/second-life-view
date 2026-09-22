# Pipeline B perception (local)

Runs without FastAPI or a frontend. Output is JSON on disk.

## Setup

```bash
pip install ultralytics opencv-python openai
# CLIP is required by YOLO-World (already installed if you followed the project setup)
```

Put the Bailian / DashScope key in the environment when you want semantic enrichment:

```powershell
$env:DASHSCOPE_API_KEY = "sk-..."
```

## Run

From the repo root:

```bash
# One scene (default hotel_room)
python pipeline/run_demo.py
python pipeline/run_demo.py --scene lythwood_lounge

# All available curated scenes (detect → enrich → assess → merge analysis)
python pipeline/run_demo.py --all
python pipeline/run_demo.py --list
```

If fixtures already exist and you only need pathway reassessment on root copies:

```bash
python pipeline/assess_batches.py
```

Or rebuild Analysis Root from `data/fixtures/scenes/*/`:

```bash
python pipeline/build_analysis.py
```

## Outputs

| Path | Content |
|---|---|
| `data/samples/panoramas/*.jpg` | ERP inputs (see `SOURCE.md`) |
| `data/samples/runs/<slug>/views/` | Perspective slices |
| `data/samples/runs/<slug>/annotated/` | Boxes drawn on views |
| `data/samples/runs/<slug>/crops/` | Primary-batch crops for VL |
| `data/fixtures/scenes/<slug>/` | Per-scene detections / batches / run_notes |
| `data/fixtures/analysis.json` | Merged Analysis Root (all scenes) |
| `data/fixtures/scenes_index.json` | Scene slug → paths |

API setup: copy `.env.example` to `.env` and fill in (never commit `.env`):

```text
DASHSCOPE_API_KEY=
DASHSCOPE_BASE_URL=https://<your-workspace>.cn-beijing.maas.aliyuncs.com/compatible-mode/v1
```

Scripts load them automatically. `enrich_crop` uses the OpenAI-compatible endpoint.

Pathway assessment is a local rule engine on category / material / condition. The VLM must not choose pathways.
