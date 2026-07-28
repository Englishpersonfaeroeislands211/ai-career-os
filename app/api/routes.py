import asyncio
from uuid import UUID

from fastapi import APIRouter, BackgroundTasks, Depends, File, HTTPException, UploadFile, status
from sqlalchemy import select
from sqlalchemy.ext.asyncio import AsyncSession

from app.db.session import get_db
from app.logging_config import get_logger
from app.models import Job, MatchAnalysis, Profile
from app.schemas import (
    JobCreate,
    JobCreateRead,
    JobParseRead,
    JobParseRequest,
    JobRead,
    JobUpdate,
    MatchAnalysisCreate,
    MatchAnalysisRead,
    ProfileCreate,
    ProfileRead,
    ProfileUpdate,
    ResumeParseRead,
)
from app.services.job_paste_parser import JobPasteParseError, prepare_job_post_text
from app.services.job_structurer import structure_job
from app.services.llm.base import LLMConfigurationError, LLMError
from app.services.matcher import run_match_analysis
from app.services.resume_parser import ResumeParseError, extract_text_from_pdf
from app.services.resume_structurer import structure_resume
from app.services.screening_card import attach_screening_card_to_metadata

logger = get_logger(__name__)

router = APIRouter()


# ---------------------------------------------------------------------------
# Profiles
# ---------------------------------------------------------------------------


@router.post("/profiles", response_model=ProfileRead, status_code=status.HTTP_201_CREATED)
async def create_profile(body: ProfileCreate, db: AsyncSession = Depends(get_db)):
    profile = Profile(**body.model_dump())
    db.add(profile)
    await db.commit()
    await db.refresh(profile)
    return profile


@router.get("/profiles", response_model=list[ProfileRead])
async def list_profiles(db: AsyncSession = Depends(get_db)):
    result = await db.execute(select(Profile).order_by(Profile.created_at.desc()))
    return result.scalars().all()


@router.post("/profiles/parse-resume", response_model=ResumeParseRead)
async def parse_resume(
    file: UploadFile = File(...),
    db: AsyncSession = Depends(get_db),
):
    filename = file.filename or "upload.pdf"
    content_type = file.content_type or "unknown"
    logger.info("Parsing resume upload: %s (%s)", filename, content_type)

    if not filename.lower().endswith(".pdf"):
        raise HTTPException(status_code=400, detail="Only PDF files are supported")

    content = await file.read()
    if not content:
        raise HTTPException(status_code=400, detail="Empty file")

    if not content.startswith(b"%PDF"):
        raise HTTPException(status_code=400, detail="File does not appear to be a valid PDF")

    if len(content) > 10 * 1024 * 1024:
        raise HTTPException(status_code=400, detail="File must be under 10 MB")

    logger.info("Extracting text from %s (%.1f KB)", filename, len(content) / 1024)

    try:
        resume_text = await asyncio.to_thread(extract_text_from_pdf, content)
    except ResumeParseError as exc:
        logger.warning("Resume parse failed for %s: %s", filename, exc)
        raise HTTPException(status_code=422, detail=str(exc)) from exc

    logger.info("Structuring resume from %s (%d chars)", filename, len(resume_text))

    try:
        extraction = await structure_resume(db, resume_text)
    except LLMConfigurationError as exc:
        logger.warning("Resume structuring skipped — provider not configured: %s", exc)
        raise HTTPException(status_code=422, detail=str(exc)) from exc
    except LLMError as exc:
        logger.error("Resume structuring failed for %s: %s", filename, exc)
        raise HTTPException(status_code=502, detail=str(exc)) from exc

    logger.info(
        "Structured %s — name=%r, skills=%d, experience=%d",
        filename,
        extraction.name,
        len(extraction.skills),
        len(extraction.experience),
    )
    return ResumeParseRead(
        name=extraction.name,
        headline=extraction.headline,
        resume_text=resume_text,
        structured_data=extraction,
    )


@router.get("/profiles/{profile_id}", response_model=ProfileRead)
async def get_profile(profile_id: UUID, db: AsyncSession = Depends(get_db)):
    profile = await db.get(Profile, profile_id)
    if not profile:
        raise HTTPException(status_code=404, detail="Profile not found")
    return profile


@router.patch("/profiles/{profile_id}", response_model=ProfileRead)
async def update_profile(profile_id: UUID, body: ProfileUpdate, db: AsyncSession = Depends(get_db)):
    profile = await db.get(Profile, profile_id)
    if not profile:
        raise HTTPException(status_code=404, detail="Profile not found")

    for field, value in body.model_dump(exclude_unset=True).items():
        setattr(profile, field, value)

    await db.commit()
    await db.refresh(profile)
    return profile


@router.delete("/profiles/{profile_id}", status_code=status.HTTP_204_NO_CONTENT)
async def delete_profile(profile_id: UUID, db: AsyncSession = Depends(get_db)):
    profile = await db.get(Profile, profile_id)
    if not profile:
        raise HTTPException(status_code=404, detail="Profile not found")
    await db.delete(profile)
    await db.commit()


# ---------------------------------------------------------------------------
# Jobs
# ---------------------------------------------------------------------------


@router.post("/jobs", response_model=JobCreateRead, status_code=status.HTTP_201_CREATED)
async def create_job(
    body: JobCreate,
    background_tasks: BackgroundTasks,
    db: AsyncSession = Depends(get_db),
):
    profile_id = body.profile_id
    payload = body.model_dump(exclude={"profile_id"})
    job = Job(**payload)
    db.add(job)
    await db.flush()
    job.raw_metadata = attach_screening_card_to_metadata(job.raw_metadata, job)

    match_analysis_id: UUID | None = None
    if profile_id:
        profile = await db.get(Profile, profile_id)
        if not profile:
            raise HTTPException(status_code=404, detail="Profile not found")
        analysis = MatchAnalysis(
            profile_id=profile_id,
            job_id=job.id,
            status="pending",
        )
        db.add(analysis)
        await db.flush()
        match_analysis_id = analysis.id

    await db.commit()
    await db.refresh(job)

    if match_analysis_id:
        background_tasks.add_task(run_match_analysis, match_analysis_id)
        logger.info(
            "Queued match analysis %s for new job %s profile=%s",
            match_analysis_id,
            job.id,
            profile_id,
        )

    return JobCreateRead(
        **JobRead.model_validate(job).model_dump(),
        match_analysis_id=match_analysis_id,
    )


@router.get("/jobs", response_model=list[JobRead])
async def list_jobs(db: AsyncSession = Depends(get_db)):
    result = await db.execute(select(Job).order_by(Job.created_at.desc()))
    return result.scalars().all()


@router.post("/jobs/parse-text", response_model=JobParseRead)
async def parse_job_text(body: JobParseRequest, db: AsyncSession = Depends(get_db)):
    logger.info("Parsing pasted job posting (%d chars)", len(body.text))

    try:
        job_text = await asyncio.to_thread(prepare_job_post_text, body.text)
    except JobPasteParseError as exc:
        logger.warning("Job paste parse failed: %s", exc)
        raise HTTPException(status_code=422, detail=str(exc)) from exc

    logger.info("Structuring job posting (%d chars after normalize)", len(job_text))

    try:
        extraction = await structure_job(db, job_text)
    except LLMConfigurationError as exc:
        logger.warning("Job structuring skipped — provider not configured: %s", exc)
        raise HTTPException(status_code=422, detail=str(exc)) from exc
    except LLMError as exc:
        logger.error("Job structuring failed: %s", exc)
        raise HTTPException(status_code=502, detail=str(exc)) from exc

    logger.info(
        "Structured job posting — title=%r, company=%r, requirements=%d",
        extraction.title,
        extraction.company,
        len(extraction.requirements),
    )
    return JobParseRead(job_text=job_text, structured_data=extraction)


@router.get("/jobs/{job_id}", response_model=JobRead)
async def get_job(job_id: UUID, db: AsyncSession = Depends(get_db)):
    job = await db.get(Job, job_id)
    if not job:
        raise HTTPException(status_code=404, detail="Job not found")
    return job


@router.patch("/jobs/{job_id}", response_model=JobRead)
async def update_job(job_id: UUID, body: JobUpdate, db: AsyncSession = Depends(get_db)):
    job = await db.get(Job, job_id)
    if not job:
        raise HTTPException(status_code=404, detail="Job not found")

    for field, value in body.model_dump(exclude_unset=True).items():
        setattr(job, field, value)

    job.raw_metadata = attach_screening_card_to_metadata(job.raw_metadata, job)
    await db.commit()
    await db.refresh(job)
    return job


@router.delete("/jobs/{job_id}", status_code=status.HTTP_204_NO_CONTENT)
async def delete_job(job_id: UUID, db: AsyncSession = Depends(get_db)):
    job = await db.get(Job, job_id)
    if not job:
        raise HTTPException(status_code=404, detail="Job not found")
    await db.delete(job)
    await db.commit()


# ---------------------------------------------------------------------------
# Match Analyses
# ---------------------------------------------------------------------------


@router.post(
    "/match-analyses",
    response_model=MatchAnalysisRead,
    status_code=status.HTTP_201_CREATED,
)
async def create_match_analysis(
    body: MatchAnalysisCreate,
    background_tasks: BackgroundTasks,
    db: AsyncSession = Depends(get_db),
):
    profile = await db.get(Profile, body.profile_id)
    if not profile:
        raise HTTPException(status_code=404, detail="Profile not found")

    job = await db.get(Job, body.job_id)
    if not job:
        raise HTTPException(status_code=404, detail="Job not found")

    analysis = MatchAnalysis(
        profile_id=body.profile_id,
        job_id=body.job_id,
        status="pending",
    )
    db.add(analysis)
    await db.commit()
    await db.refresh(analysis)

    background_tasks.add_task(run_match_analysis, analysis.id)
    logger.info("Queued match analysis %s for profile=%s job=%s", analysis.id, profile.id, job.id)
    return analysis


@router.get("/match-analyses", response_model=list[MatchAnalysisRead])
async def list_match_analyses(db: AsyncSession = Depends(get_db)):
    result = await db.execute(select(MatchAnalysis).order_by(MatchAnalysis.created_at.desc()))
    return result.scalars().all()


@router.get("/match-analyses/{analysis_id}", response_model=MatchAnalysisRead)
async def get_match_analysis(analysis_id: UUID, db: AsyncSession = Depends(get_db)):
    analysis = await db.get(MatchAnalysis, analysis_id)
    if not analysis:
        raise HTTPException(status_code=404, detail="Match analysis not found")
    return analysis
