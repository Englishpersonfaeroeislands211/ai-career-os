from uuid import UUID

from fastapi import Depends, HTTPException
from sqlalchemy.ext.asyncio import AsyncSession

from app.db.session import get_db
from app.models import Job, MatchAnalysis, Profile


async def get_profile_or_404(
    profile_id: UUID,
    db: AsyncSession = Depends(get_db),
) -> Profile:
    profile = await db.get(Profile, profile_id)
    if not profile:
        raise HTTPException(status_code=404, detail="Profile not found")
    return profile


async def get_job_or_404(
    job_id: UUID,
    db: AsyncSession = Depends(get_db),
) -> Job:
    job = await db.get(Job, job_id)
    if not job:
        raise HTTPException(status_code=404, detail="Job not found")
    return job


async def get_match_analysis_or_404(
    analysis_id: UUID,
    db: AsyncSession = Depends(get_db),
) -> MatchAnalysis:
    analysis = await db.get(MatchAnalysis, analysis_id)
    if not analysis:
        raise HTTPException(status_code=404, detail="Match analysis not found")
    return analysis
