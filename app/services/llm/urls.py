def normalize_openai_base_url(base_url: str) -> str:
    """Ensure OpenAI-compatible base URLs use 127.0.0.1 and end with /v1."""
    url = base_url.strip().rstrip("/")
    url = url.replace("://localhost:", "://127.0.0.1:")
    if url.endswith("://localhost"):
        url = f"{url[: -len('localhost')]}127.0.0.1"
    if not url.endswith("/v1"):
        url = f"{url}/v1"
    return url
