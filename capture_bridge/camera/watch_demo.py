from __future__ import annotations

import time
from pathlib import Path

from PIL import Image

from capture_bridge.camera.base import CameraBackend, CameraInfo, RawCapture
from capture_bridge.camera.errors import BridgeError


class WatchDemoBackend(CameraBackend):
    """Pragmatic backend while Camera SDK is only available via CameraSDKDemo.exe.

    Flow:
      1. Client calls POST /capture/start
      2. Operator uses Demo: 拍照 → 10 拍照并下载 → save into watch_dir
      3. Bridge detects a new/changed .jpg, copies it, returns preview_ready

    Set CAPTURE_BRIDGE_BACKEND=watch to use this mode.
    """

    name = "watch"

    def __init__(
        self,
        watch_dir: Path,
        timeout_sec: float = 180.0,
        poll_sec: float = 1.0,
    ) -> None:
        self.watch_dir = watch_dir
        self.timeout_sec = timeout_sec
        self.poll_sec = poll_sec

    def health(self) -> CameraInfo:
        exists = self.watch_dir.exists()
        return CameraInfo(
            connected=exists,
            model="X4 Air (via CameraSDKDemo)",
            firmware=None,
            detail=(
                f"Watching {self.watch_dir} for new JPG from Demo. "
                "USB must be in Android mode; enable in-camera photo stitch."
                if exists
                else f"Watch dir missing: {self.watch_dir}"
            ),
        )

    def capture_photo(self, dest_dir: Path, capture_id: str) -> RawCapture:
        self.watch_dir.mkdir(parents=True, exist_ok=True)
        dest_dir.mkdir(parents=True, exist_ok=True)

        before = self._snapshot()
        deadline = time.monotonic() + self.timeout_sec

        while time.monotonic() < deadline:
            time.sleep(self.poll_sec)
            after = self._snapshot()
            newcomers = [
                path
                for path, mtime in after.items()
                if path not in before or mtime > before[path] + 0.01
            ]
            if not newcomers:
                continue

            # Prefer the newest file
            newest = max(newcomers, key=lambda p: after[p])
            # Wait briefly for Demo write to finish
            stable = self._wait_stable(newest)
            if stable is None:
                continue

            try:
                with Image.open(stable) as img:
                    width, height = img.size
                    img.verify()
            except Exception as exc:  # noqa: BLE001 — surface as download error
                raise BridgeError(
                    "DOWNLOAD_FAILED",
                    f"Downloaded file is not a readable image: {stable} ({exc})",
                ) from exc

            # reopen after verify()
            with Image.open(stable) as img:
                width, height = img.size

            target = dest_dir / f"{capture_id}.jpg"
            target.write_bytes(stable.read_bytes())
            return RawCapture(
                local_path=target,
                width=width,
                height=height,
                camera_file=stable.name,
                in_camera_stitch=True,
            )

        raise BridgeError(
            "CAMERA_NOT_FOUND",
            (
                f"No new JPG in {self.watch_dir} within {int(self.timeout_sec)}s. "
                "Run CameraSDKDemo, take a panorama, download into that folder."
            ),
        )

    def _snapshot(self) -> dict[Path, float]:
        result: dict[Path, float] = {}
        for path in self.watch_dir.glob("*.jpg"):
            try:
                result[path] = path.stat().st_mtime
            except OSError:
                continue
        for path in self.watch_dir.glob("*.JPG"):
            try:
                result[path] = path.stat().st_mtime
            except OSError:
                continue
        return result

    def _wait_stable(self, path: Path, checks: int = 3, interval: float = 0.4) -> Path | None:
        last_size = -1
        stable_count = 0
        for _ in range(checks * 3):
            try:
                size = path.stat().st_size
            except OSError:
                return None
            if size > 0 and size == last_size:
                stable_count += 1
                if stable_count >= checks:
                    return path
            else:
                stable_count = 0
                last_size = size
            time.sleep(interval)
        return None
