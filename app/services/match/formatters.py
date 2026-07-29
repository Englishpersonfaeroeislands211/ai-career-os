import json

from app.models import Job, Profile
from app.schemas.screening_card import ScreeningCard
from app.services.screening_card import build_screening_card


def format_profile(profile: Profile) -> str:
    if profile.structured_data:
        return json.dumps(profile.structured_data, indent=2, ensure_ascii=False)
    return profile.resume_text.strip()


def format_job(job: Job) -> str:
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
        f"Structured resume:\n\n{format_profile(profile)}\n\nJob description:\n\n{format_job(job)}"
    )


def build_batch_screen_user_message(profile: Profile, jobs: list[Job]) -> str:
    cards = [_format_screening_card(build_screening_card(job)) for job in jobs]
    return (
        "Structured resume:\n\n"
        f"{format_profile(profile)}\n\n"
        "Job screening cards (return one match entry per job_id):\n\n" + "\n\n---\n\n".join(cards)
    )
