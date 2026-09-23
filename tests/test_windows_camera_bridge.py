from __future__ import annotations

import importlib
import sys
from pathlib import Path

from fastapi.testclient import TestClient


def load_gateway(monkeypatch, tmp_path: Path):
    """Import the Windows-only service with harmless test configuration."""
    monkeypatch.setenv("CAMERA_BRIDGE_EXECUTABLE", str(tmp_path / "camera_bridge_cli.exe"))
    monkeypatch.setenv("CAMERA_BRIDGE_OUTPUT_DIR", str(tmp_path / "captures"))
    monkeypatch.setenv("CAMERA_BRIDGE_TOKEN", "gateway-test-token")
    monkeypatch.setenv(
        "LINUX_CAMERA_INGEST_URL",
        "https://linux.example.test/api/v1/camera/ingest",
    )
    monkeypatch.setenv("LINUX_CAMERA_INGEST_TOKEN", "linux-ingest-test-token")
    monkeypatch.setenv("CAMERA_BRIDGE_ALLOWED_WEB_ORIGIN", "https://app.example.test")
    sys.modules.pop("windows_camera_bridge.app", None)
    return importlib.import_module("windows_camera_bridge.app")


def test_local_erp_file_is_forwarded_without_detection_boxes(monkeypatch, tmp_path):
    gateway = load_gateway(monkeypatch, tmp_path)
    image = gateway.settings.output_dir / "erp" / "room.jpg"
    image.parent.mkdir(parents=True)
    image.write_bytes(b"jpeg")
    forwarded: dict = {}

    async def fake_post(path, payload, *, gateway_result=None):
        forwarded["path"] = path
        forwarded["payload"] = payload
        forwarded["gateway_result"] = gateway_result
        return {"asset": {"frame_id": "linux-frame"}, "yolo": {}, "run": {}}

    monkeypatch.setattr(gateway, "post_artifact_to_linux", fake_post)
    response = TestClient(gateway.app).post(
        "/v1/local-file/ingest",
        headers={"Authorization": "Bearer gateway-test-token"},
        json={
            "filename": "erp/room.jpg",
            "metadata": {"frame_id": "x5-001", "site": "lobby"},
            # Unknown client-side detector data is ignored; it is never part
            # of the model forwarded to Linux.
            "detections": [{"class": "cabinet"}],
        },
    )

    assert response.status_code == 200
    assert forwarded["path"] == image
    assert forwarded["payload"].metadata == {"frame_id": "x5-001", "site": "lobby"}
    assert not hasattr(forwarded["payload"], "detections")
    assert response.json()["gateway"] == {
        "source": "windows_local_file",
        "filename": "room.jpg",
        "frame_id": "linux-frame",
    }


def test_capture_and_ingest_preserves_sdk_metadata_and_requires_stitched_jpeg(monkeypatch, tmp_path):
    gateway = load_gateway(monkeypatch, tmp_path)
    image = gateway.settings.output_dir / "stitched.jpg"
    image.parent.mkdir(parents=True, exist_ok=True)
    image.write_bytes(b"jpeg")
    forwarded: dict = {}

    async def fake_invoke(command, *, arguments=None):
        assert command == "capture"
        assert "--stitch" in arguments
        return {
            "ok": True,
            "frame_id": "x5-capture-001",
            "artifact_path": str(image),
            "stitched": True,
            "remote_paths": ["/DCIM/100MEDIA/IMG_001.insp"],
            "camera": {"camera_name": "Insta360 X5", "serial": "X5-TEST"},
        }

    async def fake_post(path, payload, *, gateway_result=None):
        forwarded["path"] = path
        forwarded["payload"] = payload
        forwarded["gateway_result"] = gateway_result
        return {"asset": {}, "yolo": {}, "run": {}}

    monkeypatch.setattr(gateway, "invoke_cli", fake_invoke)
    monkeypatch.setattr(gateway, "post_artifact_to_linux", fake_post)
    response = TestClient(gateway.app).post(
        "/v1/capture-and-ingest",
        headers={"Authorization": "Bearer gateway-test-token"},
        json={"stitch": True, "metadata": {"site": "lobby"}},
    )

    assert response.status_code == 200
    assert forwarded["path"] == image
    assert forwarded["gateway_result"]["frame_id"] == "x5-capture-001"
    assert forwarded["gateway_result"]["camera"]["serial"] == "X5-TEST"
    assert response.json()["gateway"]["remote_paths"] == ["/DCIM/100MEDIA/IMG_001.insp"]


def test_browser_capture_route_allows_only_configured_web_origin(monkeypatch, tmp_path):
    gateway = load_gateway(monkeypatch, tmp_path)

    async def fake_capture(payload):
        assert payload.stitch is True
        return {"asset": {"image_url": "https://linux.example.test/camera.jpg"}, "yolo": {}, "run": {}}

    monkeypatch.setattr(gateway, "capture_and_ingest", fake_capture)
    client = TestClient(gateway.app)
    headers = {
        "Origin": "https://app.example.test",
        "X-Second-Life-Client": "capture-ui-v1",
    }

    preflight = client.options(
        "/v1/browser/capture-and-ingest",
        headers={
            "Origin": "https://app.example.test",
            "Access-Control-Request-Method": "POST",
            "Access-Control-Request-Headers": "content-type,x-second-life-client",
        },
    )
    assert preflight.status_code == 204
    assert preflight.headers["access-control-allow-origin"] == "https://app.example.test"
    assert preflight.headers["access-control-allow-private-network"] == "true"

    allowed = client.post(
        "/v1/browser/capture-and-ingest",
        headers=headers,
        json={"stitch": True, "metadata": {"scene_label": "大厅"}},
    )
    assert allowed.status_code == 200
    assert allowed.headers["access-control-allow-origin"] == "https://app.example.test"
    assert allowed.json()["asset"]["image_url"].endswith("camera.jpg")

    blocked = client.post(
        "/v1/browser/capture-and-ingest",
        headers={**headers, "Origin": "https://untrusted.example.test"},
        json={"stitch": True},
    )
    assert blocked.status_code == 403

    detection_boxes = client.post(
        "/v1/browser/capture-and-ingest",
        headers=headers,
        json={"stitch": True, "detections": [{"class": "cabinet"}]},
    )
    assert detection_boxes.status_code == 422
