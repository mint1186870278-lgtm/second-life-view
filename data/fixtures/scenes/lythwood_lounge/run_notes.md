# Pipeline B perception run — Lythwood Lounge

- Scene slug: `lythwood_lounge`
- Image: Lythwood Lounge, 8192x4096, CC0, Poly Haven.
- Source page: https://polyhaven.com/a/lythwood_lounge
- Detector: yolov8s-worldv2 on CUDA. Classes: cabinet, chair, door, table, window.
- Detections: 86. Batches: 51. Elapsed: 47.4s.
- Semantic crops enriched: 51.
- Enrichment: qwen-vl-plus via Bailian compatible API.
- Pathway assessment: rule engine on 51 batches (no VLM pathway choice).
- Primary pathway distribution: DIRECT_REUSE=29, KEEP_IN_PLACE=7, MATERIAL_RECOVERY=2, REFURBISH=13.
- Raw clusters are not in the JSON. Frontend should read component_batches.
