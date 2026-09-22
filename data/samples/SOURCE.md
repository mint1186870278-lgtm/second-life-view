# Sample media layout

```text
data/samples/
  panoramas/                 # ERP inputs (committed, CC0)
    hotel_room.jpg
    lythwood_lounge.jpg
    en_suite.jpg
    old_room.jpg
    combination_room.jpg
  runs/                      # pipeline outputs (gitignored)
    <slug>/
      views/                 # perspective slices
      annotated/             # boxes drawn
      crops/                 # batch primary crops
```

JSON fixtures live separately under `data/fixtures/` (not here).

## Panorama sources (CC0 / Poly Haven)

| Slug | File | Page |
|---|---|---|
| `hotel_room` | `panoramas/hotel_room.jpg` | https://polyhaven.com/a/hotel_room |
| `lythwood_lounge` | `panoramas/lythwood_lounge.jpg` | https://polyhaven.com/a/lythwood_lounge |
| `en_suite` | `panoramas/en_suite.jpg` | https://polyhaven.com/a/en_suite |
| `old_room` | `panoramas/old_room.jpg` | https://polyhaven.com/a/old_room |
| `combination_room` | `panoramas/combination_room.jpg` | https://polyhaven.com/a/combination_room |

Regenerate runs:

```bash
python pipeline/run_demo.py --all
```
