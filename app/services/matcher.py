import json
from typing import Literal
from uuid import UUID

from sqlalchemy import select
from sqlalchemy.ext.asyncio import AsyncSession

from app.db.session import async_session
from app.logging_config import get_logger
from app.models import Job, MatchAnalysis, Profile
from app.prompts import load_prompt
from app.schemas.match_analysis import (
    BatchMatchResult,
    BatchScreeningResult,
    MatchResult,
    ScreeningJobMatchResult,
)
from app.schemas.screening_card import ScreeningCard
from app.services.llm import Message, get_llm_client
from app.services.llm.base import LLMConfigurationError, LLMError
from app.services.match_analysis_normalize import (
    normalize_batch_match_payload,
    normalize_batch_screen_payload,
    normalize_match_payload,
)
from app.services.screening_card import build_screening_card

# Max jobs per LLM call — keeps context size predictable; large batches are chunked.
BATCH_MATCH_CHUNK_SIZE = 12
DEFAULT_DEEP_ANALYZE_TOP_K = 3

MatchBatchMode = Literal["cascade", "screen_only", "full"]

logger = get_logger(__name__)


def _format_profile(profile: Profile) -> str:
    if profile.structured_data:
        return json.dumps(profile.structured_data, indent=2, ensure_ascii=False)
    return profile.resume_text.strip()


def _format_job(job: Job) -> str:
    parts = [
        f"Title: {job.title}",
        f"Company: {job.company}",
    ]
    if job.location:
        parts.append(f"Location: {job.location}")
    parts.append("")
    parts.append("Description:")
    parts.append(job.description.strip())
    return "\n".join(parts)


def _format_screening_card(card: ScreeningCard) -> str:
    lines = [
        f"job_id: {card.job_id}",
        f"Title: {card.title}",
        f"Company: {card.company}",
    ]
    if card.location:
        lines.append(f"Location: {card.location}")
    if card.top_requirements:
        lines.append(f"Requirements: {', '.join(card.top_requirements)}")
    lines.append(f"Summary: {card.summary}")
    return "\n".join(lines)


def build_match_user_message(profile: Profile, job: Job) -> str:
    return (
        "Structured resume:\n\n"
        f"{_format_profile(profile)}\n\n"
        "Job description:\n\n"
        f"{_format_job(job)}"
    )


def build_batch_match_user_message(profile: Profile, jobs: list[Job]) -> str:
    job_blocks = []
    for job in jobs:
        job_blocks.append(
            f"--- job_id: {job.id} ---\n{_format_job(job)}",
        )
    return (
        "Structured resume:\n\n"
        f"{_format_profile(profile)}\n\n"
        "Job postings to evaluate (return one match entry per job_id):\n\n"
        + "\n\n".join(job_blocks)
    )


def build_batch_screen_user_message(profile: Profile, jobs: list[Job]) -> str:
    cards = [_format_screening_card(build_screening_card(job)) for job in jobs]
    return (
        "Structured resume:\n\n"
        f"{_format_profile(profile)}\n\n"
        "Job screening cards (return one match entry per job_id):\n\n" + "\n\n---\n\n".join(cards)
    )


def _chunk_jobs(jobs: list[Job], size: int) -> list[list[Job]]:
    return [jobs[i : i + size] for i in range(0, len(jobs), size)]


def _screen_result_payload(match: ScreeningJobMatchResult) -> dict:
    return {
        "depth": "screen",
        "score": match.score,
        "recommendation": match.recommendation,
        "reason": match.reason,
        "summary": match.reason,
        "strengths": [],
        "gaps": [],
    }


def _full_result_payload(result: MatchResult) -> dict:
    return {"depth": "full", **result.model_dump()}


async def analyze_match(db: AsyncSession, profile: Profile, job: Job) -> MatchResult:
    client = await get_llm_client(db)
    return await client.generate_structured(
        messages=[
            Message(role="system", content=load_prompt("match_analysis")),
            Message(role="user", content=build_match_user_message(profile, job)),
        ],
        response_model=MatchResult,
        transform_payload=normalize_match_payload,
    )


async def analyze_matches_batch(
    db: AsyncSession,
    profile: Profile,
    jobs: list[Job],
) -> BatchMatchResult:
    """Score multiple jobs in one LLM call for relative calibration (full JDs)."""
    if not jobs:
        raise ValueError("At least one job is required for batch match analysis")

    client = await get_llm_client(db)
    return await client.generate_structured(
        messages=[
            Message(role="system", content=load_prompt("batch_match_analysis")),
            Message(role="user", content=build_batch_match_user_message(profile, jobs)),
        ],
        response_model=BatchMatchResult,
        transform_payload=normalize_batch_match_payload,
    )


async def analyze_matches_screen(
    db: AsyncSession,
    profile: Profile,
    jobs: list[Job],
) -> BatchScreeningResult:
    """Tier 1: fast screening using compressed screening cards."""
    if not jobs:
        raise ValueError("At least one job is required for batch screen analysis")

    client = await get_llm_client(db)
    return await client.generate_structured(
        messages=[
            Message(role="system", content=load_prompt("batch_screen_match")),
            Message(role="user", content=build_batch_screen_user_message(profile, jobs)),
        ],
        response_model=BatchScreeningResult,
        transform_payload=normalize_batch_screen_payload,
    )


async def run_match_analysis(analysis_id: UUID) -> None:
    async with async_session() as db:
        analysis = await db.get(MatchAnalysis, analysis_id)
        if not analysis or analysis.status != "pending":
            return

        profile = await db.get(Profile, analysis.profile_id)
        job = await db.get(Job, analysis.job_id)
        if not profile or not job:
            analysis.status = "failed"
            analysis.error = "Profile or job not found"
            await db.commit()
            return

        try:
            result = await analyze_match(db, profile, job)
            analysis.status = "completed"
            analysis.result = _full_result_payload(result)
            analysis.error = None
            logger.info(
                "Match analysis completed: id=%s score=%.1f recommendation=%s",
                analysis_id,
                result.score,
                result.recommendation,
            )
        except (LLMConfigurationError, LLMError) as exc:
            analysis.status = "failed"
            analysis.error = str(exc)
            logger.warning("Match analysis failed for %s: %s", analysis_id, exc)
        except Exception as exc:
            analysis.status = "failed"
            analysis.error = str(exc)
            logger.exception("Unexpected match analysis failure for %s", analysis_id)

        await db.commit()


async def run_batch_match_analysis(analysis_ids: list[UUID]) -> None:
    """Legacy M3: full JD batch matching."""
    if not analysis_ids:
        return

    async with async_session() as db:
        pending: list[MatchAnalysis] = []
        for analysis_id in analysis_ids:
            analysis = await db.get(MatchAnalysis, analysis_id)
            if analysis and analysis.status == "pending":
                pending.append(analysis)

        if not pending:
            return

        profile = await db.get(Profile, pending[0].profile_id)
        if not profile:
            for analysis in pending:
                analysis.status = "failed"
                analysis.error = "Profile not found"
            await db.commit()
            return

        job_ids = [analysis.job_id for analysis in pending]
        jobs_result = await db.execute(select(Job).where(Job.id.in_(job_ids)))
        jobs_by_id = {job.id: job for job in jobs_result.scalars().all()}
        analyses_by_job = {analysis.job_id: analysis for analysis in pending}
        ordered_jobs = [jobs_by_id[jid] for jid in job_ids if jid in jobs_by_id]

        for analysis in pending:
            if analysis.job_id not in jobs_by_id:
                analysis.status = "failed"
                analysis.error = "Job not found"

        try:
            for chunk in _chunk_jobs(ordered_jobs, BATCH_MATCH_CHUNK_SIZE):
                batch_result = await analyze_matches_batch(db, profile, chunk)
                results_by_job = {match.job_id: match for match in batch_result.matches}

                for job in chunk:
                    analysis = analyses_by_job[job.id]
                    if analysis.status != "pending":
                        continue

                    match = results_by_job.get(job.id)
                    if not match:
                        analysis.status = "failed"
                        analysis.error = "Batch response missing this job_id"
                        continue

                    analysis.status = "completed"
                    analysis.result = _full_result_payload(
                        MatchResult.model_validate(match.model_dump(exclude={"job_id"}))
                    )
                    analysis.error = None
        except (LLMConfigurationError, LLMError) as exc:
            logger.warning("Batch match analysis failed: %s", exc)
            for analysis in pending:
                if analysis.status == "pending":
                    analysis.status = "failed"
                    analysis.error = str(exc)
        except Exception as exc:
            logger.exception("Unexpected batch match analysis failure")
            for analysis in pending:
                if analysis.status == "pending":
                    analysis.status = "failed"
                    analysis.error = str(exc)

        await db.commit()


async def _run_screen_pass(
    db: AsyncSession,
    profile: Profile,
    ordered_jobs: list[Job],
    analyses_by_job: dict[UUID, MatchAnalysis],
) -> list[tuple[Job, ScreeningJobMatchResult]]:
    """Tier 1 screen all jobs; return successful matches for ranking."""
    screened: list[tuple[Job, ScreeningJobMatchResult]] = []

    for chunk in _chunk_jobs(ordered_jobs, BATCH_MATCH_CHUNK_SIZE):
        batch_result = await analyze_matches_screen(db, profile, chunk)
        results_by_job = {match.job_id: match for match in batch_result.matches}

        for job in chunk:
            analysis = analyses_by_job[job.id]
            if analysis.status != "pending":
                continue

            match = results_by_job.get(job.id)
            if not match:
                analysis.status = "failed"
                analysis.error = "Screen batch missing this job_id"
                continue

            analysis.status = "completed"
            analysis.result = _screen_result_payload(match)
            analysis.error = None
            screened.append((job, match))
            logger.info(
                "Screen match completed: id=%s job=%s score=%.1f",
                analysis.id,
                job.id,
                match.score,
            )

    return screened


async def run_screen_batch_match_analysis(analysis_ids: list[UUID]) -> None:
    """Tier 1 only — screen all jobs using screening cards."""
    if not analysis_ids:
        return

    async with async_session() as db:
        pending, profile, jobs_by_id, analyses_by_job = await _load_pending_in_session(
            db, analysis_ids
        )
        if not pending or not profile:
            await db.commit()
            return

        ordered_jobs = [jobs_by_id[jid] for jid in [a.job_id for a in pending] if jid in jobs_by_id]

        try:
            await _run_screen_pass(db, profile, ordered_jobs, analyses_by_job)
        except (LLMConfigurationError, LLMError) as exc:
            logger.warning("Screen batch match failed: %s", exc)
            for analysis in pending:
                if analysis.status == "pending":
                    analysis.status = "failed"
                    analysis.error = str(exc)
        except Exception as exc:
            logger.exception("Unexpected screen batch failure")
            for analysis in pending:
                if analysis.status == "pending":
                    analysis.status = "failed"
                    analysis.error = str(exc)

        await db.commit()


async def _load_pending_in_session(
    db: AsyncSession,
    analysis_ids: list[UUID],
) -> tuple[list[MatchAnalysis], Profile | None, dict[UUID, Job], dict[UUID, MatchAnalysis]]:
    pending: list[MatchAnalysis] = []
    for analysis_id in analysis_ids:
        analysis = await db.get(MatchAnalysis, analysis_id)
        if analysis and analysis.status == "pending":
            pending.append(analysis)

    if not pending:
        return [], None, {}, {}

    profile = await db.get(Profile, pending[0].profile_id)
    if not profile:
        for analysis in pending:
            analysis.status = "failed"
            analysis.error = "Profile not found"
        return pending, None, {}, {}

    job_ids = [analysis.job_id for analysis in pending]
    jobs_result = await db.execute(select(Job).where(Job.id.in_(job_ids)))
    jobs_by_id = {job.id: job for job in jobs_result.scalars().all()}
    analyses_by_job = {analysis.job_id: analysis for analysis in pending}

    for analysis in pending:
        if analysis.job_id not in jobs_by_id:
            analysis.status = "failed"
            analysis.error = "Job not found"

    return pending, profile, jobs_by_id, analyses_by_job


async def run_cascade_match_analysis(
    analysis_ids: list[UUID],
    *,
    deep_analyze_top_k: int = DEFAULT_DEEP_ANALYZE_TOP_K,
) -> None:
    """M3.5: Tier 1 screen all jobs, then Tier 2 full analysis on top K."""
    if not analysis_ids:
        return

    top_k = max(0, deep_analyze_top_k)

    async with async_session() as db:
        pending, profile, jobs_by_id, analyses_by_job = await _load_pending_in_session(
            db, analysis_ids
        )
        if not pending or not profile:
            await db.commit()
            return

        ordered_jobs = [jobs_by_id[jid] for jid in [a.job_id for a in pending] if jid in jobs_by_id]

        try:
            screened = await _run_screen_pass(db, profile, ordered_jobs, analyses_by_job)
            screened.sort(key=lambda item: item[1].score, reverse=True)

            for job, _match in screened[:top_k]:
                analysis = analyses_by_job[job.id]
                try:
                    full_result = await analyze_match(db, profile, job)
                    analysis.result = _full_result_payload(full_result)
                    logger.info(
                        "Deep match completed: id=%s job=%s score=%.1f",
                        analysis.id,
                        job.id,
                        full_result.score,
                    )
                except (LLMConfigurationError, LLMError) as exc:
                    logger.warning(
                        "Deep match failed for job=%s, keeping screen result: %s",
                        job.id,
                        exc,
                    )
                    analysis.error = f"Deep analysis failed: {exc}"
                except Exception as exc:
                    logger.exception("Unexpected deep match failure for job=%s", job.id)
                    analysis.error = f"Deep analysis failed: {exc}"

        except (LLMConfigurationError, LLMError) as exc:
            logger.warning("Cascade screen pass failed: %s", exc)
            for analysis in pending:
                if analysis.status == "pending":
                    analysis.status = "failed"
                    analysis.error = str(exc)
        except Exception as exc:
            logger.exception("Unexpected cascade match failure")
            for analysis in pending:
                if analysis.status == "pending":
                    analysis.status = "failed"
                    analysis.error = str(exc)

        await db.commit()


async def run_batch_match_by_mode(
    analysis_ids: list[UUID],
    *,
    mode: MatchBatchMode = "cascade",
    deep_analyze_top_k: int = DEFAULT_DEEP_ANALYZE_TOP_K,
) -> None:
    if mode == "cascade":
        await run_cascade_match_analysis(analysis_ids, deep_analyze_top_k=deep_analyze_top_k)
    elif mode == "screen_only":
        await run_screen_batch_match_analysis(analysis_ids)
    else:
        await run_batch_match_analysis(analysis_ids)
