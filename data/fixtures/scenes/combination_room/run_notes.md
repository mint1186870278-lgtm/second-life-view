# Pipeline B perception run — Combination Room

- Scene slug: `combination_room`
- Image: Combination Room, 8192x4096, CC0, Poly Haven.
- Source page: https://polyhaven.com/a/combination_room
- Detector: yolov8s-worldv2 on CUDA. Classes: chair, door, table, window.
- Detections: 26. Batches: 18. Elapsed: 17.5s.
- Semantic crops enriched: 18.
- Enrichment: qwen-vl-plus via Bailian compatible API.
- Pathway assessment: rule engine on 18 batches (no VLM pathway choice).
- Primary pathway distribution: DIRECT_REUSE=4, KEEP_IN_PLACE=9, REFURBISH=5.
- Raw clusters are not in the JSON. Frontend should read component_batches.
