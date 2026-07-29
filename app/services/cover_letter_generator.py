import json

from sqlalchemy.ext.asyncio import AsyncSession

from app.models import Job, Profile
from app.prompts import load_prompt
from app.schemas.cover_letter import CoverLetterCritique, CoverLetterDraft, CoverLetterResult
from app.schemas.match_analysis import MatchResult
from app.services.cover_letter_normalize import (
    normalize_cover_letter_draft_payload,
    normalize_cover_letter_result_payload,
)
from app.services.llm import Message, get_llm_client
from app.services.match.formatters import format_job, format_profile


def build_cover_letter_user_message(
    profile: Profile,
    job: Job,
    match_result: MatchResult,
    *,
    draft: CoverLetterDraft | None = None,
    critique: CoverLetterCritique | None = None,
) -> str:
    parts = [
        "Structured resume:\n\n",
        format_profile(profile),
        "\n\nTarget job:\n\n",
        format_job(job),
        "\n\nMatch analysis:\n\n",
        json.dumps(match_result.model_dump(), indent=2, ensure_ascii=False),
    ]
    if draft:
        parts.extend(
            [
                "\n\nDraft cover letter:\n\n",
                draft.body,
                "\n\nDraft tone: ",
                draft.tone,
            ]
        )
    if critique:
        parts.extend(
            [
                "\n\nEditor critique:\n\n",
                json.dumps(critique.model_dump(), indent=2, ensure_ascii=False),
            ]
        )
    return "".join(parts)


async def generate_cover_letter(
    db: AsyncSession,
    profile: Profile,
    job: Job,
    match_result: MatchResult,
) -> CoverLetterResult:
    client = await get_llm_client(db)
    context = build_cover_letter_user_message(profile, job, match_result)

    draft = await client.generate_structured(
        messages=[
            Message(role="system", content=load_prompt("cover_letter_draft")),
            Message(role="user", content=context),
        ],
        response_model=CoverLetterDraft,
        transform_payload=normalize_cover_letter_draft_payload,
    )

    critique = await client.generate_structured(
        messages=[
            Message(role="system", content=load_prompt("cover_letter_critique")),
            Message(
                role="user",
                content=build_cover_letter_user_message(
                    profile,
                    job,
                    match_result,
                    draft=draft,
                ),
            ),
        ],
        response_model=CoverLetterCritique,
    )

    final = await client.generate_structured(
        messages=[
            Message(role="system", content=load_prompt("cover_letter_revise")),
            Message(
                role="user",
                content=build_cover_letter_user_message(
                    profile,
                    job,
                    match_result,
                    draft=draft,
                    critique=critique,
                ),
            ),
        ],
        response_model=CoverLetterResult,
        transform_payload=normalize_cover_letter_result_payload,
    )
    return final
