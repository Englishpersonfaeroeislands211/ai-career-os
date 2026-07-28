from app.models import Job
from app.schemas.screening_card import ScreeningCard

TOP_REQUIREMENTS_LIMIT = 5
FALLBACK_SUMMARY_CHARS = 200


def _fallback_summary(description: str) -> str:
    text = description.strip()
    if len(text) <= FALLBACK_SUMMARY_CHARS:
        return text
    return text[: FALLBACK_SUMMARY_CHARS - 1].rstrip() + "…"


def _top_requirements(raw_metadata: dict | None) -> list[str]:
    if not raw_metadata:
        return []
    requirements = raw_metadata.get("requirements")
    if not isinstance(requirements, list):
        return []
    return [str(item).strip() for item in requirements if str(item).strip()][
        :TOP_REQUIREMENTS_LIMIT
    ]


def build_screening_card(job: Job) -> ScreeningCard:
    """Build a Tier-1 screening card from a saved job."""
    raw_metadata = job.raw_metadata or {}
    match_summary = raw_metadata.get("match_summary")
    if isinstance(match_summary, str) and match_summary.strip():
        summary = match_summary.strip()
    else:
        summary = _fallback_summary(job.description)

    return ScreeningCard(
        job_id=job.id,
        title=job.title,
        company=job.company,
        location=job.location,
        top_requirements=_top_requirements(raw_metadata),
        summary=summary,
    )


def attach_screening_card_to_metadata(
    raw_metadata: dict | None,
    job: Job,
) -> dict:
    """Merge a fresh screening_card into job raw_metadata."""
    metadata = dict(raw_metadata or {})
    metadata["screening_card"] = build_screening_card(job).model_dump(mode="json")
    return metadata
