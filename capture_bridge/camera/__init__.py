from __future__ import annotations

"""Camera backends for Capture Bridge.

- mock: synthetic JPEG (no hardware)
- watch: wait for CameraSDKDemo download into captures_raw
- sdk: reserved for future ctypes/C++ binding to CameraSDK.dll
"""

from capture_bridge.camera.base import CameraBackend
from capture_bridge.camera.demo_auto import DemoAutoBackend
from capture_bridge.camera.mock import MockCameraBackend
from capture_bridge.camera.sdk_import import SdkImportBackend
from capture_bridge.camera.watch_demo import WatchDemoBackend

__all__ = [
    "CameraBackend",
    "DemoAutoBackend",
    "MockCameraBackend",
    "SdkImportBackend",
    "WatchDemoBackend",
]
