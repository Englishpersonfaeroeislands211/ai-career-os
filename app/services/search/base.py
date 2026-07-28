from typing import Protocol

from app.schemas.company_research import SearchResult


class SearchError(Exception):
    """Raised when a web search request fails."""


class SearchConfigurationError(SearchError):
    """Raised when search is not configured or unavailable."""


class SearchClient(Protocol):
    async def search(self, query: str, *, max_results: int = 5) -> list[SearchResult]: ...
