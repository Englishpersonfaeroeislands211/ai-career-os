from sqlalchemy.ext.asyncio import AsyncSession

from app.models import Job, Profile
from app.prompts import load_prompt
from app.schemas.match_analysis import BatchScreeningResult, MatchResult
from app.services.llm import Message, get_llm_client
from app.services.match.formatters import build_batch_screen_user_message, build_match_user_message
from app.services.match_analysis_normalize import (
    normalize_batch_screen_payload,
    normalize_match_payload,
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


async def analyze_matches_screen(
    db: AsyncSession,
    profile: Profile,
    jobs: list[Job],
) -> BatchScreeningResult:
    """Fast screening using compressed screening cards."""
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
