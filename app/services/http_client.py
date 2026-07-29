"""Shared httpx client lifecycle — one connection pool per app process."""

import httpx

DEFAULT_TIMEOUT = 120.0
MODEL_LIST_TIMEOUT = 15.0

_client: httpx.AsyncClient | None = None


def get_http_client() -> httpx.AsyncClient:
    if _client is None:
        raise RuntimeError("HTTP client is not initialized")
    return _client


async def init_http_client() -> None:
    global _client
    if _client is not None:
        return
    _client = httpx.AsyncClient(timeout=DEFAULT_TIMEOUT)


async def close_http_client() -> None:
    global _client
    if _client is not None:
        await _client.aclose()
        _client = None
