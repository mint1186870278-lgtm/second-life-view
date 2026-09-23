from __future__ import annotations

from pathlib import Path

from PIL import Image, ImageDraw, ImageFont

from capture_bridge.camera.base import CameraBackend, CameraInfo, RawCapture


class MockCameraBackend(CameraBackend):
    """Generates a 2:1 placeholder JPEG so API can be tested without a camera."""

    name = "mock"

    def __init__(self, width: int = 2048, height: int = 1024) -> None:
        self.width = width
        self.height = height

    def health(self) -> CameraInfo:
        return CameraInfo(
            connected=True,
            model="Mock X4 Air",
            firmware="mock",
            detail="No real camera; returns synthetic ERP JPEG",
        )

    def capture_photo(self, dest_dir: Path, capture_id: str) -> RawCapture:
        dest_dir.mkdir(parents=True, exist_ok=True)
        path = dest_dir / f"{capture_id}.jpg"
        img = Image.new("RGB", (self.width, self.height), color=(32, 48, 64))
        draw = ImageDraw.Draw(img)
        text = f"MOCK CAPTURE\n{capture_id}"
        try:
            font = ImageFont.load_default()
        except OSError:
            font = None
        draw.text((40, 40), text, fill=(220, 220, 220), font=font)
        img.save(path, format="JPEG", quality=90)
        return RawCapture(
            local_path=path,
            width=self.width,
            height=self.height,
            camera_file=f"/mock/{capture_id}.jpg",
            in_camera_stitch=True,
        )
