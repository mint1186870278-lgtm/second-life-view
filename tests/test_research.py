import asyncio

from fastapi.testclient import TestClient

from spatial_agent.app import app
from spatial_agent.config import Settings
from spatial_agent.models import SearchSource
from spatial_agent.providers.research import ResearchClient


def test_local_fallback_returns_structured_opportunity_and_unknown_live_fields():
    client = ResearchClient(Settings(research_web_enabled=False))
    result = asyncio.run(client.retrieve_with_opportunities(
        "旧木柜翻新和回收", ["wood_cabinet"], region="本地", include_web=False
    ))

    assert result.used_fallback is False  # web was not requested
    assert result.opportunities
    opportunity = result.opportunities[0]
    assert opportunity.provider_type in {"refurbisher", "recycler", "mixed", "reuse", "unknown"}
    assert opportunity.source_type == "local_opportunity"
    assert opportunity.provenance == "to_confirm"
    # The fixture intentionally has no live quote/geocode; null prevents an
    # unverified demo value from being shown as a price or distance.
    assert opportunity.price_min is None
    assert opportunity.distance_km is None
    assert any(source.opportunity_id == opportunity.id for source in result.sources)


def test_web_leads_are_normalized_and_local_opportunity_is_fallback(monkeypatch):
    client = ResearchClient(Settings(research_web_enabled=False))

    async def fake_web(query: str, limit: int = 5):
        return [
            SearchSource(
                title="城市家具维修中心",
                url="https://example.test/repair",
                snippet="提供木柜维修，起价 ¥300/件，上海浦东。",
                source_type="web",
                confidence=0.55,
                provenance="inferred",
            )
        ]

    monkeypatch.setattr(client, "_web_sources", fake_web)
    result = asyncio.run(client.retrieve_with_opportunities(
        "木柜维修", ["木柜"], region="上海", include_web=True
    ))

    assert result.web_attempted is True
    assert result.web_results_count == 1
    assert result.used_fallback is False
    assert len(result.opportunities) == 1
    item = result.opportunities[0]
    assert item.source_type == "web"
    assert item.provenance == "inferred"
    assert item.price_min == 300
    assert item.price_max == 300
    assert item.currency == "CNY"
    assert item.price_unit == "quote"
    assert item.region == "上海"


def test_empty_web_results_set_fallback_flag(monkeypatch):
    client = ResearchClient(Settings(research_web_enabled=False))

    async def no_results(query: str, limit: int = 5):
        return []

    monkeypatch.setattr(client, "_web_sources", no_results)
    result = asyncio.run(client.retrieve_with_opportunities("门窗回收", ["门窗"], include_web=True))

    assert result.web_attempted is True
    assert result.web_results_count == 0
    assert result.used_fallback is True
    assert result.opportunities
    assert all(item.source_type == "local_opportunity" for item in result.opportunities)


def test_research_api_exposes_opportunities_and_query_hints():
    client = TestClient(app)
    created = client.post("/api/v1/runs", json={"enable_design": False})
    run_id = created.json()["run_id"]
    response = client.post(
        "/api/v1/research",
        json={
            "run_id": run_id,
            "query": "回收",
            "furniture_type": "木柜",
            "location": "本地",
            "radius_km": 10,
            "include_web": False,
        },
    )
    assert response.status_code == 200
    body = response.json()
    assert body["opportunities"]
    assert body["research"]["used_fallback"] is False
    assert all("source_url" in item and "provenance" in item for item in body["opportunities"])
