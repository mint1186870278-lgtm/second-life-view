from __future__ import annotations

import json
import os
import subprocess
from pathlib import Path

from capture_bridge.camera.base import CameraBackend, CameraInfo, RawCapture
from capture_bridge.camera.errors import BridgeError


class SdkImportBackend(CameraBackend):
    """Import photos the user already took on the camera body.

    Calls a native helper that wraps Camera SDK:
      GetCameraFilesList → pick newest JPG → DownloadCameraFile

    Helper path: CAPTURE_BRIDGE_IMPORT_HELPER
      default: tools/insta360/bin/import_latest.exe
    """

    name = "sdk_import"

    def __init__(self, helper_path: Path, timeout_sec: float = 120.0) -> None:
        self.helper_path = helper_path
        self.timeout_sec = timeout_sec

    def health(self) -> CameraInfo:
        if not self.helper_path.exists():
            return CameraInfo(
                connected=False,
                model="X4 Air",
                detail=(
                    f"Import helper missing: {self.helper_path}. "
                    "Build tools/insta360/import_latest (see README). "
                    "Product flow: shoot on camera, then import — no Demo CLI."
                ),
            )
        try:
            proc = subprocess.run(
                [str(self.helper_path), "--health"],
                capture_output=True,
                text=True,
                timeout=30,
                check=False,
            )
        except OSError as exc:
            return CameraInfo(
                connected=False,
                detail=f"Failed to run import helper: {exc}",
            )
        if proc.returncode != 0:
            return CameraInfo(
                connected=False,
                detail=(proc.stderr or proc.stdout or "helper --health failed").strip(),
            )
        try:
            data = json.loads(proc.stdout.strip() or "{}")
        except json.JSONDecodeError:
            return CameraInfo(connected=False, detail="helper --health returned invalid JSON")
        return CameraInfo(
            connected=bool(data.get("camera_connected")),
            model=data.get("camera_model") or "X4 Air",
            firmware=data.get("firmware"),
            detail=data.get("detail") or "sdk_import helper ready",
        )

    def capture_photo(self, dest_dir: Path, capture_id: str) -> RawCapture:
        """Name kept for CameraBackend; behavior is import-from-camera, not TakePhoto."""
        if not self.helper_path.exists():
            raise BridgeError(
                "SDK_INIT_FAILED",
                f"Import helper not found: {self.helper_path}. "
                "Cannot pull photos from camera until the native helper is built.",
            )

        dest_dir.mkdir(parents=True, exist_ok=True)
        out_path = dest_dir / f"{capture_id}.jpg"

        try:
            proc = subprocess.run(
                [
                    str(self.helper_path),
                    "--download-latest",
                    "--out",
                    str(out_path),
                ],
                capture_output=True,
                text=True,
                timeout=self.timeout_sec,
                check=False,
            )
        except subprocess.TimeoutExpired as exc:
            raise BridgeError("DOWNLOAD_FAILED", "Import helper timed out") from exc
        except OSError as exc:
            raise BridgeError("SDK_INIT_FAILED", f"Failed to run import helper: {exc}") from exc

        if proc.returncode != 0:
            err = (proc.stderr or proc.stdout or "").strip()
            code = "NO_NEW_FILE" if "NO_NEW_FILE" in err else "DOWNLOAD_FAILED"
            if "CAMERA_NOT_FOUND" in err:
                code = "CAMERA_NOT_FOUND"
            raise BridgeError(code, err or "import helper failed")

        try:
            payload = json.loads(proc.stdout.strip() or "{}")
        except json.JSONDecodeError as exc:
            raise BridgeError("DOWNLOAD_FAILED", "helper returned invalid JSON") from exc

        path = Path(payload.get("local_path") or out_path)
        if not path.exists():
            raise BridgeError("DOWNLOAD_FAILED", f"helper reported success but file missing: {path}")

        width = int(payload.get("width") or 0)
        height = int(payload.get("height") or 0)
        if width <= 0 or height <= 0:
            from PIL import Image

            with Image.open(path) as img:
                width, height = img.size

        return RawCapture(
            local_path=path,
            width=width,
            height=height,
            camera_file=payload.get("camera_file"),
            in_camera_stitch=bool(payload.get("in_camera_stitch", True)),
        )


def default_helper_path(repo_root: Path) -> Path:
    env = os.environ.get("CAPTURE_BRIDGE_IMPORT_HELPER")
    if env:
        return Path(env)
    return repo_root / "tools" / "insta360" / "bin" / "import_latest.exe"
