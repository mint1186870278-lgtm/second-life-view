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
    design = client.post(f"/api/v1/runs/{state['run_id']}/design", json={"brief": "保留结构，换成浅色环保表面"})
    assert design.status_code == 200
    assert design.json()["designs"]

def test_lux3d_domestic_mock_does_not_call_network():
    response = TestClient(app).post("/api/v1/reconstruct", json={"image_url": "https://example.com/object.jpg"})
    assert response.status_code == 200
    assert response.json()["region"] == "cn"
