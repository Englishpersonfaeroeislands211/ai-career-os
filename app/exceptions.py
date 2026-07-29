"""Domain errors raised by services — mapped to HTTP responses in app.api.exception_handlers."""


class SettingsValidationError(ValueError):
    """Invalid LLM provider settings (missing API key, base URL, etc.)."""


class ModelListError(Exception):
    """Failed to list models from a provider."""

    def __init__(self, message: str, *, status_code: int = 502) -> None:
        super().__init__(message)
        self.message = message
        self.status_code = status_code
