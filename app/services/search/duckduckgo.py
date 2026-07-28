import asyncio
import time

from duckduckgo_search import DDGS

from app.schemas.company_research import SearchResult
from app.services.search.base import SearchError
from app.services.search.tracing import ToolCallTrace, log_tool_call

PROVIDER = "duckduckgo"


class DuckDuckGoSearchClient:
    async def search(self, query: str, *, max_results: int = 5) -> list[SearchResult]:
        started = time.perf_counter()
        try:
            raw = await asyncio.to_thread(_search_sync, query, max_results)
            results = [_to_search_result(item) for item in raw]
            log_tool_call(
                ToolCallTrace(
                    operation="web_search",
                    provider=PROVIDER,
                    query=query,
                    latency_ms=(time.perf_counter() - started) * 1000,
                    result_count=len(results),
                    status="ok",
                )
            )
            return results
        except Exception as exc:
            log_tool_call(
                ToolCallTrace(
                    operation="web_search",
                    provider=PROVIDER,
                    query=query,
                    latency_ms=(time.perf_counter() - started) * 1000,
                    result_count=0,
                    status="error",
                    error=str(exc),
                )
            )
            raise SearchError(f"DuckDuckGo search failed: {exc}") from exc


def _search_sync(query: str, max_results: int) -> list[dict]:
    with DDGS() as ddgs:
        return list(ddgs.text(query, max_results=max_results))


def _to_search_result(item: dict) -> SearchResult:
    title = (item.get("title") or "").strip()
    url = (item.get("href") or item.get("link") or "").strip()
    snippet = (item.get("body") or item.get("snippet") or title).strip()
    if not title or not url:
        raise SearchError("DuckDuckGo returned a result missing title or URL")
    return SearchResult(title=title[:500], url=url[:2048], snippet=snippet[:2000])
