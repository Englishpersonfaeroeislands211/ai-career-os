from sqlalchemy.ext.asyncio import AsyncSession

from app.models import Job, Profile
from app.prompts import load_prompt
from app.schemas.match_analysis import MatchResult
from app.schemas.resume_optimization import ResumeOptimizationResult
from app.services.llm import Message, get_llm_client
from app.services.match.formatters import format_job, format_profile
from app.services.resume_optimization_normalize import normalize_resume_optimization_payload


def build_resume_optimization_user_message(
    profile: Profile,
    job: Job,
    match_result: MatchResult,
) -> str:
    gaps_block = "\n".join(f"- [{g.severity}] {g.evidence}" for g in match_result.gaps)
    return (
        "Structured resume:\n\n"
        f"{format_profile(profile)}\n\n"
        "Raw resume text:\n\n"
        f"{profile.resume_text.strip()}\n\n"
        "Target job:\n\n"
        f"{format_job(job)}\n\n"
        "Match analysis summary:\n\n"
        f"{match_result.summary}\n\n"
        "Gaps to address:\n\n"
        f"{gaps_block}"
    )


async def optimize_resume_for_match(
    db: AsyncSession,
    profile: Profile,
    job: Job,
    match_result: MatchResult,
) -> ResumeOptimizationResult:
    if not match_result.gaps:
        raise ValueError("Match analysis has no gaps to optimize against")

    client = await get_llm_client(db)
    return await client.generate_structured(
        messages=[
            Message(role="system", content=load_prompt("resume_optimization")),
            Message(
                role="user",
                content=build_resume_optimization_user_message(profile, job, match_result),
            ),
        ],
        response_model=ResumeOptimizationResult,
        transform_payload=normalize_resume_optimization_payload,
    )
