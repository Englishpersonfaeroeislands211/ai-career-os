from unittest.mock import patch

import pytest

from app.services.search.base import SearchError
from app.services.search.duckduckgo import DuckDuckGoSearchClient


@pytest.mark.asyncio
async def test_duckduckgo_search_maps_results():
    raw = [
        {
            "title": "Example Corp culture",
            "href": "https://example.com/culture",
            "body": "Remote-first engineering team.",
        }
    ]

    with patch("app.services.search.duckduckgo._search_sync", return_value=raw):
        client = DuckDuckGoSearchClient()
        results = await client.search("Example Corp culture", max_results=5)

    assert len(results) == 1
    assert results[0].title == "Example Corp culture"
    assert results[0].url == "https://example.com/culture"
    assert "Remote-first" in results[0].snippet


@pytest.mark.asyncio
async def test_duckduckgo_search_wraps_failures():
    with patch("app.services.search.duckduckgo._search_sync", side_effect=RuntimeError("blocked")):
        client = DuckDuckGoSearchClient()
        with pytest.raises(SearchError, match="DuckDuckGo search failed"):
            await client.search("test query")
