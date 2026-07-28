from sqlalchemy.ext.asyncio import AsyncSession

from app.services.search.base import SearchClient
from app.services.search.duckduckgo import DuckDuckGoSearchClient


def create_search_client() -> SearchClient:
    """Return the default search client (DuckDuckGo — no API key required)."""
    return DuckDuckGoSearchClient()


async def get_search_client(_db: AsyncSession) -> SearchClient:
    """Resolve search client from settings. Phase 2 adds Tavily/Serper via app_settings."""
    return create_search_client()
