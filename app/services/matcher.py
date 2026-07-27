import json
from uuid import UUID

from sqlalchemy.ext.asyncio import AsyncSession

from app.db.session import async_session
from app.logging_config import get_logger
from app.models import Job, MatchAnalysis, Profile
from app.prompts import load_prompt
from app.schemas.match_analysis import MatchResult
from app.services.llm import Message, get_llm_client
from app.services.llm.base import LLMConfigurationError, LLMError
from app.services.match_analysis_normalize import normalize_match_payload


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


def build_match_user_message(profile: Profile, job: Job) -> str:
    return (
        "Structured resume:\n\n"
        f"{_format_profile(profile)}\n\n"
        "Job description:\n\n"
        f"{_format_job(job)}"
    )


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


logger = get_logger(__name__)


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
            analysis.result = result.model_dump()
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
