from datetime import UTC, datetime

from sqlalchemy.ext.asyncio import AsyncSession

from app.models import Job
from app.prompts import load_prompt
from app.schemas.company_research import (
    MAX_RESEARCH_QUERIES,
    MAX_SEARCH_RESULTS_PER_QUERY,
    CompanyBrief,
    CompanyBriefContent,
    ResearchPlan,
    SearchResult,
)
from app.services.llm import Message, get_llm_client
from app.services.matcher import _format_job
from app.services.search import SearchClient, get_search_client


def _format_job_for_research(job: Job) -> str:
    parts = [_format_job(job)]
    if job.url:
        parts.append(f"\nJob posting URL: {job.url}")
    return "\n".join(parts)


def _format_search_results(results: list[SearchResult]) -> str:
    if not results:
        return "No search results returned."

    blocks: list[str] = []
    for index, result in enumerate(results, start=1):
        blocks.append(
            "\n".join(
                [
                    f"[{index}] {result.title}",
                    f"URL: {result.url}",
                    f"Snippet: {result.snippet}",
                ]
            )
        )
    return "\n\n".join(blocks)


def build_research_plan_user_message(job: Job) -> str:
    return f"Target job:\n\n{_format_job_for_research(job)}"


def build_research_synthesize_user_message(job: Job, search_results: list[SearchResult]) -> str:
    return "\n\n".join(
        [
            f"Target job:\n\n{_format_job_for_research(job)}",
            f"Web search results:\n\n{_format_search_results(search_results)}",
        ]
    )


def _dedupe_search_results(results: list[SearchResult]) -> list[SearchResult]:
    seen_urls: set[str] = set()
    unique: list[SearchResult] = []
    for result in results:
        key = result.url.casefold()
        if key in seen_urls:
            continue
        seen_urls.add(key)
        unique.append(result)
    return unique


async def _run_searches(search_client: SearchClient, plan: ResearchPlan) -> list[SearchResult]:
    collected: list[SearchResult] = []
    for query in plan.queries[:MAX_RESEARCH_QUERIES]:
        query = query.strip()
        if not query:
            continue
        batch = await search_client.search(query, max_results=MAX_SEARCH_RESULTS_PER_QUERY)
        collected.extend(batch)
    return _dedupe_search_results(collected)


async def research_company(
    db: AsyncSession,
    job: Job,
    *,
    search_client: SearchClient | None = None,
) -> CompanyBrief:
    llm = await get_llm_client(db)
    client = search_client or await get_search_client(db)

    plan = await llm.generate_structured(
        messages=[
            Message(role="system", content=load_prompt("company_research_plan")),
            Message(role="user", content=build_research_plan_user_message(job)),
        ],
        response_model=ResearchPlan,
    )

    search_results = await _run_searches(client, plan)

    content = await llm.generate_structured(
        messages=[
            Message(role="system", content=load_prompt("company_research_synthesize")),
            Message(
                role="user",
                content=build_research_synthesize_user_message(job, search_results),
            ),
        ],
        response_model=CompanyBriefContent,
    )

    if content.company.strip().casefold() != job.company.strip().casefold():
        content = content.model_copy(update={"company": job.company})

    return CompanyBrief(
        **content.model_dump(),
        sources=search_results,
        researched_at=datetime.now(UTC),
    )


def company_brief_to_storage(brief: CompanyBrief) -> dict:
    return brief.model_dump(mode="json")


def company_brief_from_payload(payload: dict) -> CompanyBrief:
    return CompanyBrief.model_validate(payload)
