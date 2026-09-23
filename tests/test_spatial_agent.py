import json
from pathlib import Path

import pytest
from fastapi.testclient import TestClient
import spatial_agent.app as app_module
from spatial_agent.app import app
from spatial_agent.models import Detection
from spatial_agent.yolo_service import LiveYoloResult

@pytest.mark.parametrize("path", ["/health", "/api/v1/demo"])
def test_public_endpoints(path):
    response = TestClient(app).get(path)
    assert response.status_code == 200

def test_active_perception_resume_and_design():
    client = TestClient(app)
    created = client.post("/api/v1/runs", json={"user_goal": "评估旧木柜再利用"})
    assert created.status_code == 200
    state = created.json()
    assert state["status"] == "awaiting_evidence"
    action = state["capture_actions"][0]
    resumed = client.post(f"/api/v1/runs/{state['run_id']}/capture/complete", json={"run_id": state["run_id"], "action_id": action["id"], "image_url": "https://example.com/close.jpg"})
    assert resumed.status_code == 200
    assert resumed.json()["status"] == "completed"
    assert resumed.json()["sources"]
    assert any(item["provenance"] == "verified" for item in resumed.json()["sources"])
    design = client.post(f"/api/v1/runs/{state['run_id']}/design", json={"brief": "保留结构，换成浅色环保表面"})
    assert design.status_code == 200
    assert design.json()["designs"]
    assert "研究依据" in design.json()["designs"][0]["prompt"]

def test_lux3d_domestic_mock_does_not_call_network():
    response = TestClient(app).post("/api/v1/reconstruct", json={"image_url": "https://example.com/object.jpg"})
    assert response.status_code == 200
    assert response.json()["region"] == "cn"
    status = TestClient(app).get("/api/v1/reconstruct/mock-lux3d-task")
    assert status.status_code == 200
    assert status.json()["region"] == "cn"


def test_windows_camera_frame_contract_starts_run():
    response = TestClient(app).post(
        "/api/v1/camera/frame",
        json={
            "image_url": "https://example.com/room.jpg",
            "detections": [
                {"class": "wood_cabinet", "bbox": [0.1, 0.2, 0.4, 0.8], "confidence": 0.9}
            ],
            "metadata": {"camera_model": "Insta360 X5", "projection": "equirectangular"},
        },
    )
    assert response.status_code == 200
    state = response.json()
    assert state["image_urls"] == ["https://example.com/room.jpg"]
    assert state["metadata"]["camera"]["camera_model"] == "Insta360 X5"


class FakeWindowsCameraGateway:
    def __init__(self, image: bytes):
        self.image = image
        self.capture_payloads: list[dict] = []
        self.download_payloads: list[dict] = []

    async def status(self) -> dict:
        return {"ok": True, "sdk_version": "2.2.0", "devices": [{"serial": "X5-TEST"}]}

    async def list_files(self) -> dict:
        return {"ok": True, "file_count": 1, "files": ["/DCIM/100MEDIA/TEST.insp"]}

    async def capture(self, payload: dict) -> dict:
        self.capture_payloads.append(payload)
        return self._result("frame/with unsafe chars")

    async def download(self, payload: dict) -> dict:
        self.download_payloads.append(payload)
        return self._result("download-frame")

    async def download_artifact_to(self, artifact_url, destination):
        assert artifact_url == "/v1/artifacts/fake-artifact"
        destination.parent.mkdir(parents=True, exist_ok=True)
        destination.write_bytes(self.image)
        return "image/jpeg"

    @staticmethod
    def _result(frame_id: str) -> dict:
        return {
            "ok": True,
            "frame_id": frame_id,
            "artifact_id": "fake-artifact",
            "artifact_url": "/v1/artifacts/fake-artifact",
            "filename": "stitched-room.jpg",
            "stitched": True,
            "remote_paths": ["/DCIM/100MEDIA/TEST.insp"],
            "camera": {
                "serial": "X5-TEST",
                "camera_name": "Insta360 X5",
                "firmware": "1.0.0",
                "camera_type": 6,
            },
        }


class FakeLiveYolo:
    def __init__(self, detections: list[Detection] | None = None):
        self.detections = detections if detections is not None else [
            Detection(
                id="live_obj_001",
                class_name="cabinet",
                bbox=[12, 18, 160, 240],
                bbox_xyxy=[12, 18, 160, 240],
                confidence=0.94,
                track_id="live_obj_001",
                source="linux:yolov8s-worldv2",
                raw_label="cabinet",
                yaw=4.0,
                pitch=-2.0,
                component_batch_id="live__batch_cabinet_005_-005",
            )
        ]
        self.calls: list[dict] = []

    async def detect(self, image_path: Path, *, artifact_id: str, projection: str, output_dir: Path) -> LiveYoloResult:
        self.calls.append(
            {
                "image_path": image_path,
                "artifact_id": artifact_id,
                "projection": projection,
                "output_dir": output_dir,
            }
        )
        annotated_path = output_dir / f"{artifact_id}-yolo-annotated.jpg"
        detections_path = output_dir / f"{artifact_id}-yolo.json"
        annotated_path.write_bytes(b"annotated")
        detections_path.write_text("{}", encoding="utf-8")
        batches = [
            {
                "id": "live__batch_cabinet_005_-005",
                "category": "cabinet",
                "object_ids": [detection.id for detection in self.detections if detection.id],
                "detected_count": len(self.detections),
            }
        ] if self.detections else []
        return LiveYoloResult(
            detections=self.detections,
            component_batches=batches,
            raw_detection_count=len(self.detections),
            projection=projection,
            annotation_kind="perspective_contact_sheet",
            annotated_path=annotated_path,
            detections_path=detections_path,
            device=0,
        )


def test_windows_gateway_capture_transfers_stitched_frame_and_starts_run(monkeypatch, tmp_path):
    gateway = FakeWindowsCameraGateway(b"\xff\xd8fake-jpeg\xff\xd9")
    detector = FakeLiveYolo()
    monkeypatch.setattr(app_module, "camera_gateway", gateway)
    monkeypatch.setattr(app_module, "live_yolo", detector)
    monkeypatch.setattr(app_module, "CAMERA_ARTIFACT_DIR", tmp_path)

    response = TestClient(app).post(
        "/api/v1/camera/capture",
        json={
            "user_goal": "评估拍摄到的空间",
            "stitch": True,
            "output_width": 4096,
            "output_height": 2048,
            "detections": [
                {"class": "wood_cabinet", "bbox": [0.1, 0.2, 0.4, 0.8], "confidence": 0.91}
            ],
        },
    )

    assert response.status_code == 200
    body = response.json()
    assert gateway.capture_payloads == [
        {
            "raw_type": "off",
            "timeout_ms": 0,
            "stitch": True,
            "output_width": 4096,
            "output_height": 2048,
        }
    ]
    assert body["asset"]["filename"].startswith("frame_with_unsafe_chars-")
    assert body["asset"]["image_url"].endswith(f"/camera-assets/{body['asset']['filename']}")
    assert (tmp_path / body["asset"]["filename"]).read_bytes() == b"\xff\xd8fake-jpeg\xff\xd9"
    assert body["run"]["metadata"]["camera"]["camera_model"] == "Insta360 X5"
    assert body["run"]["metadata"]["camera"]["projection"] == "equirectangular"
    assert body["yolo"]["mode"] == "live"
    assert detector.calls


def test_windows_gateway_download_resumes_pending_capture(monkeypatch, tmp_path):
    gateway = FakeWindowsCameraGateway(b"\xff\xd8fake-jpeg\xff\xd9")
    detector = FakeLiveYolo()
    monkeypatch.setattr(app_module, "camera_gateway", gateway)
    monkeypatch.setattr(app_module, "live_yolo", detector)
    monkeypatch.setattr(app_module, "CAMERA_ARTIFACT_DIR", tmp_path)
    client = TestClient(app)
    created = client.post("/api/v1/runs", json={"user_goal": "评估旧木柜再利用"}).json()
    action_id = created["capture_actions"][0]["id"]

    response = client.post(
        "/api/v1/camera/download",
        json={
            "run_id": created["run_id"],
            "action_id": action_id,
            "remote_path": "/DCIM/100MEDIA/TEST.insp",
            "stitch": True,
        },
    )

    assert response.status_code == 200
    body = response.json()
    assert gateway.download_payloads[0]["remote_path"] == "/DCIM/100MEDIA/TEST.insp"
    assert body["run"]["run_id"] == created["run_id"]
    assert body["run"]["metadata"]["camera"]["camera_serial"] == "X5-TEST"
    assert body["run"]["metadata"]["yolo_source"] == "Linux live YOLO-World"


def test_windows_multipart_ingest_runs_linux_yolo_and_starts_run(monkeypatch, tmp_path):
    detector = FakeLiveYolo()
    monkeypatch.setattr(app_module, "live_yolo", detector)
    monkeypatch.setattr(app_module, "CAMERA_ARTIFACT_DIR", tmp_path)
    monkeypatch.setattr(app_module.settings, "camera_ingest_token", "ingest-test-token")

    response = TestClient(app).post(
        "/api/v1/camera/ingest",
        headers={"Authorization": "Bearer ingest-test-token"},
        files={"file": ("stitched-room.jpg", b"windows-jpeg", "image/jpeg")},
        data={
            "user_goal": "评估来自 Windows 的全景图",
            "metadata": json.dumps(
                {
                    "frame_id": "windows-frame-001",
                    "camera_model": "Insta360 X5",
                    "projection": "equirectangular",
                }
            ),
        },
    )

    assert response.status_code == 200
    body = response.json()
    assert body["asset"]["source"] == "windows_multipart"
    assert (tmp_path / body["asset"]["filename"]).read_bytes() == b"windows-jpeg"
    assert body["yolo"]["source"] == "linux:yolov8s-worldv2"
    assert body["run"]["metadata"]["yolo_mode"] == "live"
    assert body["run"]["objects"][0]["source"] == "linux:yolov8s-worldv2"
    assert detector.calls[0]["projection"] == "equirectangular"


def test_windows_multipart_ingest_resumes_run_and_never_uses_fixture(monkeypatch, tmp_path):
    detector = FakeLiveYolo(detections=[])
    monkeypatch.setattr(app_module, "live_yolo", detector)
    monkeypatch.setattr(app_module, "CAMERA_ARTIFACT_DIR", tmp_path)
    monkeypatch.setattr(app_module.settings, "camera_ingest_token", "ingest-test-token")
    client = TestClient(app)
    created = client.post("/api/v1/runs", json={"user_goal": "需要补拍"}).json()
    action_id = created["capture_actions"][0]["id"]

    response = client.post(
        "/api/v1/camera/ingest",
        headers={"Authorization": "Bearer ingest-test-token"},
        files={"file": ("empty-room.jpg", b"windows-jpeg", "image/jpeg")},
        data={
            "run_id": created["run_id"],
            "action_id": action_id,
            "metadata": json.dumps({"projection": "equirectangular"}),
        },
    )

    assert response.status_code == 200
    body = response.json()
    assert body["run"]["run_id"] == created["run_id"]
    assert body["run"]["status"] == "completed"
    assert body["run"]["objects"] == []
    assert body["run"]["detections"] == []
    assert any(event["action"] == "no_detections" for event in body["run"]["events"])


def test_windows_gateway_status_and_files_are_proxied(monkeypatch):
    gateway = FakeWindowsCameraGateway(b"jpeg")
    monkeypatch.setattr(app_module, "camera_gateway", gateway)
    client = TestClient(app)

    assert client.get("/api/v1/camera/status").json()["devices"][0]["serial"] == "X5-TEST"
    assert client.get("/api/v1/camera/files").json()["files"] == ["/DCIM/100MEDIA/TEST.insp"]


def test_tayli_fixture_is_perception_input():
    client = TestClient(app)
    response = client.post("/api/v1/runs", json={"scene_slug": "hotel_room", "enable_research": False, "enable_design": False})
    assert response.status_code == 200
    state = response.json()
    assert state["metadata"]["yolo_source"] == "TAY-LI Pipeline B"
    assert state["metadata"]["scene_slug"] == "hotel_room"
    assert len(state["objects"]) == 25
    assert all(item["source"] == "tay-li:yolo-world" for item in state["objects"])
    assert any(item["recommended_pathway"] == "DIRECT_REUSE" for item in state["objects"])
    assert state["status"] == "awaiting_evidence"


def test_yolo_scene_catalog_and_world_validation():
    client = TestClient(app)
    scenes = client.get("/api/v1/yolo/scenes").json()["scenes"]
    assert {"hotel_room", "old_room"}.issubset(scenes)
    rejected = client.post("/api/v1/3dgs/reconstruct", json={"resources": ["https://example.com/one.jpg"]})
    assert rejected.status_code == 400
    assert "20 images" in rejected.json()["detail"]


def test_research_returns_provenance_and_local_opportunities():
    client = TestClient(app)
    created = client.post("/api/v1/runs", json={"user_goal": "评估旧木柜再利用", "enable_design": False})
    state = created.json()
    action = state["capture_actions"][0]
    resumed = client.post(
        f"/api/v1/runs/{state['run_id']}/capture/complete",
        json={"run_id": state["run_id"], "action_id": action["id"], "image_url": "https://example.com/close.jpg"},
    )
    assert resumed.status_code == 200
    sources = resumed.json()["sources"]
    assert sources
    assert any(item["source_type"] == "knowledge_base" for item in sources)
    assert any(item["source_type"] == "local_opportunity" for item in sources)
    assert {item["provenance"] for item in sources}.issubset({"verified", "inferred", "to_confirm"})


def test_picture_demo_catalog_and_full_chain():
    client = TestClient(app)
    catalog = client.get("/api/v1/demo/scenes")
    assert catalog.status_code == 200
    scenes = catalog.json()["scenes"]
    assert len(scenes) == 11
    assert all(item["asset_url"].startswith("/demo-assets/") for item in scenes)
    assert all(item["thumbnail_url"].startswith("/api/v1/demo/scenes/") for item in scenes)
    assert all(item["annotated_url"].startswith("/api/v1/demo/scenes/") for item in scenes)
    assert sum(item["group_count"] for item in scenes) == 263

    result = client.post(
        "/api/v1/demo/analyze",
        json={
            "scene_ids": ["hotel_room"],
            "user_goal": "评估酒店客房构件并提出低碳翻新方案",
            "region": "南京 · 江苏",
            "spatial_prompt": "保留布局并升级为明亮低碳客房",
        },
    )
    assert result.status_code == 200
    body = result.json()
    assert body["status"] == "completed"
    assert body["raw_detection_count"] == 26
    assert body["component_count"] == 26
    assert body["pending_evidence_count"] == 0
    assert body["evidence_checked_count"] > 0
    assert body["design"]["title"]
    assert body["spatial_generation"]["provider"] == "aholo-spatial-gen"
    assert {item["agent"] for item in body["events"]} >= {"perception", "evidence", "research", "design"}


def test_demo_picture_asset_is_served():
    response = TestClient(app).get("/demo-assets/hotel_room.jpg")
    assert response.status_code == 200
    assert response.headers["content-type"].startswith("image/jpeg")
    thumbnail = TestClient(app).get("/api/v1/demo/scenes/hotel_room/thumbnail")
    assert thumbnail.status_code == 200
    assert thumbnail.headers["content-type"].startswith("image/jpeg")
    assert len(thumbnail.content) < len(response.content)
    annotated = TestClient(app).get("/api/v1/demo/scenes/hotel_room/annotated")
    assert annotated.status_code == 200
    assert annotated.headers["content-type"].startswith("image/jpeg")
