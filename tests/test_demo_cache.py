from fastapi.testclient import TestClient

import spatial_agent.app as app_module
import spatial_agent.demo as demo_module
from spatial_agent.app import app
from spatial_agent.demo_cache import DemoArtifactStore


def test_artifact_store_reuses_matching_fingerprint_and_rejects_path_escape(tmp_path):
    store = DemoArtifactStore(tmp_path)
    store.save_crop("group/one", "source-v1", b"jpeg")

    assert store.cached_crop("group/one", "source-v1") == b"jpeg"
    assert store.cached_crop("group/one", "source-v2") is None
    assert store.asset_path("../../outside.jpg") is None
    assert store.status()["crops"] == 1


def test_component_preview_returns_retained_asset_before_provider_call(monkeypatch, tmp_path):
    store = DemoArtifactStore(tmp_path)
    monkeypatch.setattr(app_module, "DEMO_ARTIFACTS", store)
    monkeypatch.setattr(demo_module, "DEMO_ARTIFACTS", store)

    group = next(item for item in demo_module.list_demo_component_groups() if item["can_generate_preview"])
    advice = {
        "material": "保留稳定主体，局部补配。",
        "color": "暖白与浅木色。",
        "surface": "清洁后使用低 VOC 水性保护层。",
        "construction": "采用可逆五金连接。",
        "rationale": "用于缓存命中测试。",
    }
    prompt = demo_module.build_demo_component_preview_prompt(group["id"], advice, "南京 · 江苏")
    fingerprint = demo_module.demo_component_fingerprint(group["id"])
    saved = store.save_preview(
        group["id"],
        fingerprint,
        demo_module.demo_component_preview_cache_key(prompt),
        b"cached-jpeg",
        metadata={"provider": "qwen-image-3.0-pro", "prompt": prompt},
    )

    response = TestClient(app).post(
        f"/api/v1/demo/components/{group['id']}/preview",
        json={"region": "南京 · 江苏", "advice": advice},
    )

    assert response.status_code == 200
    body = response.json()
    assert body["cache_hit"] is True
    assert body["image_url"].endswith(store.preview_relative_path(saved))
    image = TestClient(app).get(body["image_url"])
    assert image.status_code == 200
    assert image.content == b"cached-jpeg"
