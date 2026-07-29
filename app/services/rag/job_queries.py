"""Build retrieval queries from job data."""

from __future__ import annotations

from app.models import Job


def job_retrieval_queries(job: Job) -> list[str]:
    """Prefer structured requirements; fall back to the full formatted job."""
    metadata = job.raw_metadata or {}
    requirements = metadata.get("requirements")
    if isinstance(requirements, list):
        cleaned = [str(item).strip() for item in requirements if str(item).strip()]
        if cleaned:
            return cleaned

    match_summary = metadata.get("match_summary")
    if isinstance(match_summary, str) and match_summary.strip():
        return [match_summary.strip()]

    from app.services.match.formatters import format_job

    return [format_job(job)]
