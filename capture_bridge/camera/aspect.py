from __future__ import annotations

from capture_bridge.camera.errors import BridgeError


def assert_erp_aspect(width: int, height: int, tolerance: float = 0.05) -> None:
    """Require approximately 2:1 equirectangular aspect ratio."""
    if height <= 0:
        raise BridgeError("NOT_ERP_ASPECT", "Invalid image height")
    ratio = width / height
    if abs(ratio - 2.0) > tolerance * 2.0:
        raise BridgeError(
            "NOT_ERP_ASPECT",
            f"Expected ~2:1 panorama, got {width}x{height} (ratio={ratio:.3f}). "
            "Enable in-camera photo stitch and retake.",
        )
