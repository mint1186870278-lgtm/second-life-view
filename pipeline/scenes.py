"""Curated demo scenes for multi-input Pipeline B runs.

Layout:
  data/samples/panoramas/<slug>.jpg   — ERP inputs (committed)
  data/samples/runs/<slug>/           — views / annotated / crops (gitignored)
  data/fixtures/scenes/<slug>/        — JSON fixtures
"""

from __future__ import annotations

from dataclasses import dataclass
from pathlib import Path

ROOT = Path(__file__).resolve().parents[1]
SAMPLES = ROOT / "data" / "samples"
PANORAMAS = SAMPLES / "panoramas"
RUNS = SAMPLES / "runs"


@dataclass(frozen=True)
class SceneSpec:
    slug: str
    scene_id: str
    panorama_id: str
    image_name: str
    title: str
    page: str
    author: str = "Poly Haven"
    license: str = "CC0"
    order: int = 1

    @property
    def image_path(self) -> Path:
        return PANORAMAS / self.image_name

    @property
    def image_rel(self) -> str:
        return f"data/samples/panoramas/{self.image_name}"

    @property
    def run_dir(self) -> Path:
        return RUNS / self.slug

    @property
    def view_dir(self) -> Path:
        """Perspective views directory (also parent of annotated/)."""
        return self.run_dir / "views"

    @property
    def annotated_dir(self) -> Path:
        return self.run_dir / "annotated"

    @property
    def crop_dir(self) -> Path:
        return self.run_dir / "crops"

    @property
    def fixture_dir(self) -> Path:
        return ROOT / "data" / "fixtures" / "scenes" / self.slug


# Primary demo set: residential / hotel interiors with furniture.
SCENES: list[SceneSpec] = [
    SceneSpec(
        slug="hotel_room",
        scene_id="scene_hotel",
        panorama_id="pano_hotel",
        image_name="hotel_room.jpg",
        title="Hotel Room",
        page="https://polyhaven.com/a/hotel_room",
        order=1,
    ),
    SceneSpec(
        slug="lythwood_lounge",
        scene_id="scene_lounge",
        panorama_id="pano_lounge",
        image_name="lythwood_lounge.jpg",
        title="Lythwood Lounge",
        page="https://polyhaven.com/a/lythwood_lounge",
        order=2,
    ),
    SceneSpec(
        slug="en_suite",
        scene_id="scene_ensuite",
        panorama_id="pano_ensuite",
        image_name="en_suite.jpg",
        title="En Suite",
        page="https://polyhaven.com/a/en_suite",
        order=3,
    ),
    SceneSpec(
        slug="old_room",
        scene_id="scene_old",
        panorama_id="pano_old",
        image_name="old_room.jpg",
        title="Old Room",
        page="https://polyhaven.com/a/old_room",
        order=4,
    ),
    SceneSpec(
        slug="combination_room",
        scene_id="scene_combo",
        panorama_id="pano_combo",
        image_name="combination_room.jpg",
        title="Combination Room",
        page="https://polyhaven.com/a/combination_room",
        order=5,
    ),
]


def get_scene(slug: str) -> SceneSpec:
    for scene in SCENES:
        if scene.slug == slug:
            return scene
    raise KeyError(f"unknown scene slug: {slug}")


def available_scenes() -> list[SceneSpec]:
    return [scene for scene in SCENES if scene.image_path.exists()]
