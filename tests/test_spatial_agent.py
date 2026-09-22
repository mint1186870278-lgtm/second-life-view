import pytest
from fastapi.testclient import TestClient
from spatial_agent.app import app

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
