from __future__ import annotations

from pathlib import Path
from types import SimpleNamespace
from unittest.mock import AsyncMock, patch

import pytest

from app.schemas.company_research import CompanyBriefContent, ResearchPlan, SearchResult
from app.services.company_research import research_company
from tests.evals.company_research_eval_assertions import (
    evaluate_company_brief,
    evaluate_company_brief_content,
)
from tests.evals.eval_assertions import load_json

FIXTURES_DIR = Path(__file__).parent / "fixtures" / "company_research"


def _iter_company_research_cases() -> list[tuple[str, Path]]:
    cases: list[tuple[str, Path]] = []
    for case_dir in sorted(FIXTURES_DIR.iterdir()):
        if not case_dir.is_dir():
            continue
        required = (
            "expected.json",
            "job.json",
            "llm_response_plan.json",
            "llm_response_brief.json",
            "search_results.json",
        )
        if all((case_dir / name).exists() for name in required):
            cases.append((case_dir.name, case_dir))
    return cases


@pytest.mark.parametrize("case_name,case_dir", _iter_company_research_cases())
def test_golden_company_brief_content_meets_expectations(case_name: str, case_dir: Path):
    llm_response = load_json(case_dir / "llm_response_brief.json")
    expected = load_json(case_dir / "expected.json")

    content = CompanyBriefContent.model_validate(llm_response)
    failures = evaluate_company_brief_content(content, expected, case_name=case_name)
    assert not failures, "\n".join(failures)


@pytest.mark.parametrize("case_name,case_dir", _iter_company_research_cases())
@pytest.mark.asyncio
async def test_research_company_pipeline_with_mocked_llm_and_search(
    case_name: str,
    case_dir: Path,
):
    job_data = load_json(case_dir / "job.json")
    plan_response = load_json(case_dir / "llm_response_plan.json")
    brief_response = load_json(case_dir / "llm_response_brief.json")
    search_data = load_json(case_dir / "search_results.json")
    expected = load_json(case_dir / "expected.json")

    job = SimpleNamespace(
        title=job_data["title"],
        company=job_data["company"],
        description=job_data["description"],
        location=job_data.get("location"),
        url=job_data.get("url"),
    )

    plan = ResearchPlan.model_validate(plan_response)
    brief_content = CompanyBriefContent.model_validate(brief_response)
    search_results = [SearchResult.model_validate(item) for item in search_data]

    mock_llm = AsyncMock()
    mock_llm.generate_structured = AsyncMock(side_effect=[plan, brief_content])

    mock_search = AsyncMock()
    mock_search.search = AsyncMock(
        side_effect=[
            search_results[:1],
            search_results[1:],
        ]
    )

    with patch(
        "app.services.company_research.get_llm_client",
        new=AsyncMock(return_value=mock_llm),
    ):
        result = await research_company(
            db=None,
            job=job,
            search_client=mock_search,
        )

    assert mock_llm.generate_structured.await_count == 2
    call_models = [
        call.kwargs["response_model"] for call in mock_llm.generate_structured.await_args_list
    ]
    assert call_models == [ResearchPlan, CompanyBriefContent]
    assert mock_search.search.await_count == len(plan.queries)

    plan_message = mock_llm.generate_structured.await_args_list[0].kwargs["messages"][-1].content
    assert job_data["company"] in plan_message

    synth_message = mock_llm.generate_structured.await_args_list[1].kwargs["messages"][-1].content
    assert search_results[0].url in synth_message

    failures = evaluate_company_brief(
        result,
        {**expected, "min_sources": 1},
        case_name=case_name,
    )
    assert not failures, "\n".join(failures)
