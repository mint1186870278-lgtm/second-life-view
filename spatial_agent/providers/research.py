"""Evidence-oriented research tools for the Spatial Agent.

The hackathon demo must work without credentials or network access, so the
research layer is local-first.  Curated JSON records act as a tiny RAG corpus;
an optional DuckDuckGo HTML adapter can add web leads when explicitly enabled.
Every returned source carries a provenance label so a UI can distinguish a
curated fact, a search lead, and an opportunity that still needs confirmation.
"""
from __future__ import annotations

import html
import json
import re
from hashlib import sha1
from pathlib import Path
from typing import Any
from urllib.parse import parse_qs, unquote, urlencode, urlparse

import httpx

from spatial_agent.config import Settings
from spatial_agent.models import LocalOpportunity, ResearchResult, SearchSource


class ResearchClient:
    def __init__(self, settings: Settings, root: Path | None = None):
        self.settings = settings
        self.root = root or Path(__file__).resolve().parents[2]
        self.knowledge_path = self.root / "data" / "knowledge" / "material_reuse.json"
        self.opportunity_path = self.root / "data" / "knowledge" / "local_opportunities.json"

    @staticmethod
    def _read_json(path: Path) -> list[dict[str, Any]]:
        try:
            value = json.loads(path.read_text(encoding="utf-8"))
        except (FileNotFoundError, json.JSONDecodeError):
            return []
        return value if isinstance(value, list) else []

    @staticmethod
    def _tokens(text: str) -> set[str]:
        # Keep Chinese text intact while also matching English material names.
        words = set(re.findall(r"[\u4e00-\u9fff]{2,}|[a-z0-9_]{3,}", text.lower()))
        return words

    def _local_sources(self, query: str, categories: list[str], region: str | None) -> list[SearchSource]:
        query_tokens = self._tokens(" ".join([query, *categories]))
        scored_knowledge: list[tuple[int, dict[str, Any]]] = []
        for item in self._read_json(self.knowledge_path):
            haystack = " ".join(str(item.get(k, "")) for k in ("title", "text", "keywords"))
            score = len(query_tokens & self._tokens(haystack))
            scored_knowledge.append((score, item))
        sources: list[SearchSource] = []
        # Always return the best curated record. This keeps the RAG contract
        # useful for Chinese queries whose inflection may not exactly match a
        # keyword (for example ``旧木柜`` versus ``木柜``).
        for score, item in sorted(scored_knowledge, key=lambda pair: pair[0], reverse=True)[:3]:
            if score or not query_tokens or not sources:
                sources.append(SearchSource(
                    title=str(item.get("title", "材料再利用知识")),
                    url=str(item.get("url", "kb://circular-construction")),
                    snippet=str(item.get("text", "")),
                    source_type="knowledge_base",
                    confidence=min(0.98, 0.82 + score * 0.04),
                    provenance="verified",
                ))
        scored_opportunities: list[tuple[int, dict[str, Any], str]] = []
        for item in self._read_json(self.opportunity_path):
            item_region = str(item.get("region", ""))
            haystack = " ".join(str(item.get(k, "")) for k in ("name", "materials", "services"))
            if region and item_region and region not in item_region:
                continue
            score = len(query_tokens & self._tokens(haystack))
            # Return a small local shortlist even when no keyword matched; all
            # records are marked to_confirm because availability is live data.
            scored_opportunities.append((score, item, haystack))
        for score, item, item_haystack in sorted(scored_opportunities, key=lambda pair: pair[0], reverse=True)[:3]:
            if score or len(sources) < 2:
                name = str(item.get("name", "本地再利用机会"))
                sources.append(SearchSource(
                    title=name,
                    url=str(item.get("url", "local://opportunities")),
                    snippet=str(item.get("text", item_haystack)),
                    source_type="local_opportunity",
                    confidence=min(0.8, 0.45 + score * 0.08),
                    provenance="to_confirm",
                ))
        return sources

    async def _web_sources(self, query: str, limit: int = 5) -> list[SearchSource]:
        if not query.strip():
            return []
        endpoint = "https://html.duckduckgo.com/html/?" + urlencode({"q": query})
        try:
            async with httpx.AsyncClient(timeout=15, trust_env=False, headers={"User-Agent": "second-life-view/0.1"}) as client:
                response = await client.get(endpoint)
                response.raise_for_status()
        except Exception:
            return []
        text = response.text
        sources: list[SearchSource] = []
        pattern = re.compile(
            r'<a[^>]+class="result__a"[^>]+href="([^"]+)"[^>]*>(.*?)</a>(.*?)(?=<a[^>]+class="result__a"|</body>)',
            re.I | re.S,
        )
        for match in pattern.finditer(text):
            raw_url, raw_title, block = match.groups()
            parsed = urlparse(html.unescape(raw_url))
            # DDG sometimes wraps the real URL in /l/?uddg=...
            url = unquote(parse_qs(parsed.query).get("uddg", [raw_url])[0])
            title = re.sub(r"<[^>]+>", "", html.unescape(raw_title)).strip()
            snippet_match = re.search(r'class="result__snippet"[^>]*>(.*?)</', block, re.I | re.S)
            snippet = re.sub(r"<[^>]+>", "", html.unescape(snippet_match.group(1) if snippet_match else block)).strip()
            if title and url.startswith(("http://", "https://")):
                sources.append(SearchSource(title=title, url=url, snippet=snippet[:500], source_type="web", confidence=0.55, provenance="inferred"))
            if len(sources) >= limit:
                break
        return sources

    async def retrieve(self, query: str, categories: list[str] | None = None, *, region: str | None = None, include_web: bool | None = None) -> list[SearchSource]:
        categories = categories or []
        sources = self._local_sources(query, categories, region)
        use_web = self.settings.research_web_enabled if include_web is None else include_web
        if use_web:
            sources.extend(await self._web_sources(" ".join([query, *categories])))
        return sources[:12]

    @staticmethod
    def _provider_type(text: str) -> str:
        normalized = text.lower()
        refurbish = any(token in normalized for token in ("翻新", "维修", "修复", "再制造"))
        recycle = any(token in normalized for token in ("回收", "分拣", "拆除"))
        if refurbish and recycle:
            return "mixed"
        if refurbish:
            return "refurbisher"
        if recycle:
            return "recycler"
        if "再利用" in normalized or "reuse" in normalized:
            return "reuse"
        return "unknown"

    @staticmethod
    def _extract_price(text: str) -> tuple[float | None, float | None, str | None, str | None]:
        match = re.search(r"[¥￥]\s*(\d+(?:\.\d+)?)\s*(?:[-~至]\s*[¥￥]?\s*(\d+(?:\.\d+)?))?\s*(/[^，。；,\s]+)?", text)
        if not match:
            return None, None, None, None
        minimum = float(match.group(1))
        maximum = float(match.group(2)) if match.group(2) else minimum
        return minimum, maximum, "CNY", "quote"

    def _normalize_opportunity(self, source: SearchSource, region: str | None) -> LocalOpportunity:
        source_id = sha1(f"{source.source_type}|{source.url}|{source.title}".encode("utf-8")).hexdigest()[:16]
        price_min, price_max, currency, price_unit = self._extract_price(" ".join([source.title, source.snippet]))
        opportunity = LocalOpportunity(
            id=f"opp_{source_id}",
            name=source.title,
            description=source.snippet,
            source_url=source.url,
            source_type="web" if source.source_type == "web" else "local_opportunity",
            provenance=source.provenance,
            provider_type=self._provider_type(" ".join([source.title, source.snippet])),
            region=region,
            price_min=price_min,
            price_max=price_max,
            currency=currency,
            price_unit=price_unit,
            distance_km=None,
        )
        source.opportunity_id = opportunity.id
        return opportunity

    async def retrieve_with_opportunities(
        self,
        query: str,
        categories: list[str] | None = None,
        *,
        region: str | None = None,
        include_web: bool | None = None,
    ) -> ResearchResult:
        """Return knowledge sources plus explicit, provenance-labelled service leads."""
        categories = categories or []
        local_sources = self._local_sources(query, categories, region)
        knowledge_sources = [source for source in local_sources if source.source_type == "knowledge_base"]
        fallback_sources = [source for source in local_sources if source.source_type == "local_opportunity"]
        use_web = self.settings.research_web_enabled if include_web is None else include_web
        web_sources: list[SearchSource] = []
        if use_web:
            web_sources = await self._web_sources(" ".join([query, *categories]))
        opportunity_sources = web_sources if web_sources else fallback_sources
        opportunities = [self._normalize_opportunity(source, region) for source in opportunity_sources]
        return ResearchResult(
            sources=[*knowledge_sources, *opportunity_sources][:12],
            opportunities=opportunities[:6],
            web_attempted=use_web,
            web_results_count=len(web_sources),
            used_fallback=bool(use_web and not web_sources),
        )
