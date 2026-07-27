from functools import lru_cache
from pathlib import Path

PROMPTS_DIR = Path(__file__).parent


class PromptNotFoundError(FileNotFoundError):
    pass


@lru_cache
def load_prompt(name: str) -> str:
    """Load a prompt template from app/prompts/{name}.txt."""
    path = PROMPTS_DIR / f"{name}.txt"
    if not path.is_file():
        raise PromptNotFoundError(f"Prompt not found: {name} ({path})")
    return path.read_text(encoding="utf-8").strip()
