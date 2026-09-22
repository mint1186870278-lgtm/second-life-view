# Pipeline B perception run — En Suite

- Scene slug: `en_suite`
- Image: En Suite, 8192x4096, CC0, Poly Haven.
- Source page: https://polyhaven.com/a/en_suite
- Detector: yolov8s-worldv2 on CUDA. Classes: cabinet, chair, door, table, window.
- Detections: 19. Batches: 13. Elapsed: 12.5s.
- Semantic crops enriched: 13.
- Enrichment: qwen-vl-plus via Bailian compatible API.
- Pathway assessment: rule engine on 13 batches (no VLM pathway choice).
- Primary pathway distribution: DIRECT_REUSE=5, KEEP_IN_PLACE=4, NO_PRIMARY_YET=1, REFURBISH=3.
- Raw clusters are not in the JSON. Frontend should read component_batches.
