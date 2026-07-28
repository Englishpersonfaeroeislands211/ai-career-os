from uuid import UUID

from sqlalchemy import select
from sqlalchemy.ext.asyncio import AsyncSession

from app.models import Job, MatchAnalysis


async def _latest_analyses_by_job(
    db: AsyncSession,
    profile_id: UUID,
) -> dict[UUID, MatchAnalysis]:
    """Most recent analysis per job for a profile — single query, no N+1."""
    result = await db.execute(
        select(MatchAnalysis)
        .where(MatchAnalysis.profile_id == profile_id)
        .order_by(MatchAnalysis.created_at.desc())
    )
    latest: dict[UUID, MatchAnalysis] = {}
    for analysis in result.scalars().all():
        if analysis.job_id not in latest:
            latest[analysis.job_id] = analysis
    return latest


async def queue_batch_match_analyses(
    db: AsyncSession,
    profile_id: UUID,
    *,
    job_ids: list[UUID] | None = None,
    skip_existing: bool = True,
) -> tuple[list[MatchAnalysis], list[UUID]]:
    """Create pending match analyses for jobs that need scoring.

    Returns queued analyses and job IDs skipped because they already have a
    pending or completed analysis (when skip_existing is True).
    """
    if job_ids:
        result = await db.execute(
            select(Job).where(Job.id.in_(job_ids)).order_by(Job.created_at.desc())
        )
        jobs = list(result.scalars().all())
        found_ids = {job.id for job in jobs}
        missing = [job_id for job_id in job_ids if job_id not in found_ids]
        if missing:
            msg = f"Job(s) not found: {', '.join(str(job_id) for job_id in missing)}"
            raise ValueError(msg)
    else:
        result = await db.execute(select(Job).order_by(Job.created_at.desc()))
        jobs = list(result.scalars().all())

    latest_by_job = await _latest_analyses_by_job(db, profile_id) if skip_existing else {}

    queued: list[MatchAnalysis] = []
    skipped_job_ids: list[UUID] = []

    for job in jobs:
        if skip_existing:
            latest = latest_by_job.get(job.id)
            if latest and latest.status in {"pending", "completed"}:
                skipped_job_ids.append(job.id)
                continue

        analysis = MatchAnalysis(
            profile_id=profile_id,
            job_id=job.id,
            status="pending",
        )
        db.add(analysis)
        queued.append(analysis)

    if queued:
        await db.commit()
        for analysis in queued:
            await db.refresh(analysis)
    else:
        await db.commit()

    return queued, skipped_job_ids
