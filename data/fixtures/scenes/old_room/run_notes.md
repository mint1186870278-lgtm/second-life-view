# Pipeline B perception run — Old Room

- Scene slug: `old_room`
- Image: Old Room, 8192x4096, CC0, Poly Haven.
- Source page: https://polyhaven.com/a/old_room
- Detector: yolov8s-worldv2 on CUDA. Classes: door, window.
- Detections: 16. Batches: 8. Elapsed: 7.9s.
- Semantic crops enriched: 8.
- Enrichment: qwen-vl-plus via Bailian compatible API.
- Pathway assessment: rule engine on 8 batches (no VLM pathway choice).
- Primary pathway distribution: KEEP_IN_PLACE=7, REFURBISH=1.
- Raw clusters are not in the JSON. Frontend should read component_batches.
