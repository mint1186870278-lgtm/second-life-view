from __future__ import annotations

import os
from pathlib import Path


def repo_root() -> Path:
    return Path(__file__).resolve().parents[1]


def env_path(name: str, default: Path) -> Path:
    raw = os.environ.get(name)
    return Path(raw) if raw else default


HOST = os.environ.get("CAPTURE_BRIDGE_HOST", "127.0.0.1")
PORT = int(os.environ.get("CAPTURE_BRIDGE_PORT", "18765"))
# mock | demo_auto (recommended MVP) | watch | sdk_import
BACKEND = os.environ.get("CAPTURE_BRIDGE_BACKEND", "demo_auto").lower()
SDK_VERSION = os.environ.get("CAPTURE_BRIDGE_SDK_VERSION", "2.2.0")

CAPTURES_RAW = env_path(
    "CAPTURE_BRIDGE_WATCH_DIR",
    repo_root() / "data" / "samples" / "captures_raw",
)
CAPTURE_SESSION_DIR = env_path(
    "CAPTURE_BRIDGE_SESSION_DIR",
    repo_root() / "data" / "samples" / "captures_raw" / "_sessions",
)
WATCH_TIMEOUT_SEC = float(os.environ.get("CAPTURE_BRIDGE_WATCH_TIMEOUT", "240"))
# Demo photo mode list index after「选择模式」; 0 = 普通拍照 (ERP when in-camera stitch on)
DEMO_PHOTO_MODE_INDEX = int(os.environ.get("CAPTURE_BRIDGE_DEMO_PHOTO_MODE_INDEX", "0"))
