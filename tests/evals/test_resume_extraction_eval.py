from __future__ import annotations

from pathlib import Path
from unittest.mock import AsyncMock, patch

import pytest

from app.schemas.resume_extraction import ResumeExtraction
from app.services.resume_extraction_normalize import normalize_resume_payload
from app.services.resume_structurer import structure_resume
from tests.evals.eval_assertions import evaluate_extraction, load_json

FIXTURES_DIR = Path(__file__).parent / "fixtures"


def _iter_eval_cases() -> list[tuple[str, Path]]:
    cases: list[tuple[str, Path]] = []
    for case_dir in sorted(FIXTURES_DIR.iterdir()):
        if not case_dir.is_dir():
            continue
        if not (case_dir / "expected.json").exists():
            continue
        cases.append((case_dir.name, case_dir))
    return cases


@pytest.mark.parametrize("case_name,case_dir", _iter_eval_cases())
def test_golden_llm_response_meets_expectations(case_name: str, case_dir: Path):
    llm_response = load_json(case_dir / "llm_response.json")
    expected = load_json(case_dir / "expected.json")

    normalized = normalize_resume_payload(llm_response)
    extraction = ResumeExtraction.model_validate(normalized)

    failures = evaluate_extraction(extraction, expected, case_name=case_name)
    assert not failures, "\n".join(failures)


@pytest.mark.parametrize("case_name,case_dir", _iter_eval_cases())
@pytest.mark.asyncio
async def test_structure_resume_pipeline_with_mocked_llm(case_name: str, case_dir: Path):
    resume_text = (case_dir / "resume.txt").read_text(encoding="utf-8").strip()
    llm_response = load_json(case_dir / "llm_response.json")
    expected = load_json(case_dir / "expected.json")

    assert len(resume_text) >= 100, f"[{case_name}] resume fixture looks too short"

    golden = ResumeExtraction.model_validate(normalize_resume_payload(llm_response))
    mock_client = AsyncMock()
    mock_client.complete_structured.return_value = golden

    with patch(
        "app.services.resume_structurer.get_llm_client",
        new=AsyncMock(return_value=mock_client),
    ):
        extraction = await structure_resume(db=None, resume_text=resume_text)

    mock_client.complete_structured.assert_awaited_once()
    call_kwargs = mock_client.complete_structured.await_args.kwargs
    assert call_kwargs["response_model"] is ResumeExtraction
    assert resume_text in call_kwargs["messages"][-1].content

    failures = evaluate_extraction(extraction, expected, case_name=case_name)
    assert not failures, "\n".join(failures)


@pytest.mark.live_llm
@pytest.mark.asyncio
async def test_live_llm_extraction_backend_engineer():
    """Optional live eval — run with: RUN_LIVE_LLM=1 uv run pytest -m live_llm"""
    import os

    if os.getenv("RUN_LIVE_LLM") != "1":
        pytest.skip("Set RUN_LIVE_LLM=1 to run live LLM extraction evals")

    pytest.importorskip("asyncpg")
    from sqlalchemy.ext.asyncio import AsyncSession, async_sessionmaker, create_async_engine

    from app.config import settings

    case_dir = FIXTURES_DIR / "backend_engineer"
    resume_text = (case_dir / "resume.txt").read_text(encoding="utf-8").strip()
    expected = load_json(case_dir / "expected.json")

    engine = create_async_engine(settings.database_url)
    session_factory = async_sessionmaker(engine, class_=AsyncSession, expire_on_commit=False)

    try:
        async with session_factory() as db:
            extraction = await structure_resume(db, resume_text)
    finally:
        await engine.dispose()

    failures = evaluate_extraction(extraction, expected, case_name="live:backend_engineer")
    assert not failures, "\n".join(failures)
