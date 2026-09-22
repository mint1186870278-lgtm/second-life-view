# Pipeline B perception run — Hotel Room

- Scene slug: `hotel_room`
- Image: Hotel Room, 8192x4096, CC0, Poly Haven.
- Source page: https://polyhaven.com/a/hotel_room
- Detector: yolov8s-worldv2 on CUDA. Classes: cabinet, chair, door, table, window.
- Detections: 25. Batches: 14. Elapsed: 18.2s.
- Semantic crops enriched: 14.
- Enrichment: qwen-vl-plus via Bailian compatible API.
- Pathway assessment: rule engine on 14 batches (no VLM pathway choice).
- Primary pathway distribution: DIRECT_REUSE=11, KEEP_IN_PLACE=3.
- Raw clusters are not in the JSON. Frontend should read component_batches.
