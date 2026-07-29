from datetime import UTC, datetime

from sqlalchemy.ext.asyncio import AsyncSession

from app.models import Job
from app.prompts import load_prompt
from app.schemas.company_research import (
    MAX_AGENT_SEARCHES,
    MAX_AGENT_STEPS,
    MAX_SEARCH_RESULTS_PER_QUERY,
    CompanyBrief,
    CompanyBriefContent,
    ResearchAgentStep,
    SearchResult,
)
from app.services.llm import Message, get_llm_client
from app.services.matcher import _format_job
from app.services.search import SearchClient, get_search_client
from app.services.search.tracing import AgentStepTrace, log_agent_step


def _format_job_for_research(job: Job) -> str:
    parts = [_format_job(job)]
    if job.url:
        parts.append(f"\nJob URL: {job.url}")
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


def build_research_agent_user_message(
    job: Job,
    search_results: list[SearchResult],
    *,
    step: int,
    max_steps: int,
    searches_done: int,
    max_searches: int,
) -> str:
    return "\n\n".join(
        [
            f"Research step {step} of {max_steps}.",
            f"Searches used: {searches_done}/{max_searches}.",
            f"Target job:\n\n{_format_job_for_research(job)}",
            (
                f"Results collected so far:\n\n{_format_search_results(search_results)}"
                if search_results
                else "No search results yet."
            ),
            (
                "Choose action=search with one new query, or action=synthesize "
                "if you have enough evidence for the brief."
            ),
        ]
    )


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


async def _run_agent_search_loop(
    llm,
    search_client: SearchClient,
    job: Job,
) -> list[SearchResult]:
    collected: list[SearchResult] = []
    searches_done = 0

    for step in range(1, MAX_AGENT_STEPS + 1):
        agent_step = await llm.generate_structured(
            messages=[
                Message(role="system", content=load_prompt("company_research_agent")),
                Message(
                    role="user",
                    content=build_research_agent_user_message(
                        job,
                        collected,
                        step=step,
                        max_steps=MAX_AGENT_STEPS,
                        searches_done=searches_done,
                        max_searches=MAX_AGENT_SEARCHES,
                    ),
                ),
            ],
            response_model=ResearchAgentStep,
        )

        log_agent_step(
            AgentStepTrace(
                step=step,
                max_steps=MAX_AGENT_STEPS,
                action=agent_step.action,
                query=agent_step.query,
                rationale=agent_step.rationale,
                searches_done=searches_done,
                total_results=len(collected),
            )
        )

        if agent_step.action == "synthesize":
            break

        if searches_done >= MAX_AGENT_SEARCHES:
            break

        query = (agent_step.query or "").strip()
        if not query:
            continue

        batch = await search_client.search(query, max_results=MAX_SEARCH_RESULTS_PER_QUERY)
        collected = _dedupe_search_results([*collected, *batch])
        searches_done += 1

    return collected


async def _synthesize_brief(
    llm, job: Job, search_results: list[SearchResult]
) -> CompanyBriefContent:
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
    return content


async def research_company(
    db: AsyncSession,
    job: Job,
    *,
    search_client: SearchClient | None = None,
) -> CompanyBrief:
    llm = await get_llm_client(db)
    client = search_client or await get_search_client(db)

    search_results = await _run_agent_search_loop(llm, client, job)
    content = await _synthesize_brief(llm, job, search_results)

    return CompanyBrief(
        **content.model_dump(),
        sources=search_results,
        researched_at=datetime.now(UTC),
    )


def company_brief_to_storage(brief: CompanyBrief) -> dict:
    return brief.model_dump(mode="json")


def company_brief_from_payload(payload: dict) -> CompanyBrief:
    return CompanyBrief.model_validate(payload)
