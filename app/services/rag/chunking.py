"""Split structured resumes into retrieval-friendly chunks."""

from __future__ import annotations

import re

from pydantic import ValidationError

from app.schemas.rag import ResumeChunk
from app.schemas.resume_extraction import ResumeExtraction


def chunk_resume(
    structured_data: dict | None,
    *,
    resume_text: str | None = None,
) -> list[ResumeChunk]:
    """Turn profile resume content into atomic, citeable chunks.

    Structured profiles are split by section (skills, bullets, etc.). Plain-text
    profiles fall back to paragraph chunks so RAG still works without extraction.
    """
    if structured_data:
        try:
            extraction = ResumeExtraction.model_validate(structured_data)
        except ValidationError:
            pass
        else:
            return _chunk_structured_resume(extraction)

    if resume_text and resume_text.strip():
        return _chunk_plain_resume(resume_text.strip())

    return []


def _chunk_structured_resume(extraction: ResumeExtraction) -> list[ResumeChunk]:
    chunks: list[ResumeChunk] = []

    if extraction.headline:
        chunks.append(
            ResumeChunk(
                id="headline-0",
                text=extraction.headline.strip(),
                section="headline",
            )
        )

    for index, skill in enumerate(extraction.skills):
        skill_text = skill.strip()
        if not skill_text:
            continue
        chunks.append(
            ResumeChunk(
                id=f"skill-{index}",
                text=skill_text,
                section="skill",
            )
        )

    for exp_index, entry in enumerate(extraction.experience):
        for hl_index, highlight in enumerate(entry.highlights):
            highlight_text = highlight.strip()
            if not highlight_text:
                continue
            chunks.append(
                ResumeChunk(
                    id=f"exp-{exp_index}-hl-{hl_index}",
                    text=f"{entry.title} at {entry.company}: {highlight_text}",
                    section="experience",
                    company=entry.company,
                    title=entry.title,
                )
            )

    for edu_index, entry in enumerate(extraction.education):
        base = f"{entry.degree} at {entry.school}"
        if entry.duration:
            base = f"{base} ({entry.duration})"
        chunks.append(
            ResumeChunk(
                id=f"edu-{edu_index}",
                text=base,
                section="education",
            )
        )
        for hl_index, highlight in enumerate(entry.highlights):
            highlight_text = highlight.strip()
            if not highlight_text:
                continue
            chunks.append(
                ResumeChunk(
                    id=f"edu-{edu_index}-hl-{hl_index}",
                    text=f"{entry.degree} at {entry.school}: {highlight_text}",
                    section="education",
                )
            )

    for proj_index, entry in enumerate(extraction.projects):
        if entry.description and entry.description.strip():
            chunks.append(
                ResumeChunk(
                    id=f"proj-{proj_index}",
                    text=f"{entry.name}: {entry.description.strip()}",
                    section="project",
                )
            )
        for hl_index, highlight in enumerate(entry.highlights):
            highlight_text = highlight.strip()
            if not highlight_text:
                continue
            chunks.append(
                ResumeChunk(
                    id=f"proj-{proj_index}-hl-{hl_index}",
                    text=f"{entry.name}: {highlight_text}",
                    section="project",
                )
            )

    return chunks


def _chunk_plain_resume(resume_text: str) -> list[ResumeChunk]:
    paragraphs = [part.strip() for part in re.split(r"\n\s*\n", resume_text) if part.strip()]
    if not paragraphs:
        paragraphs = [resume_text]

    return [
        ResumeChunk(
            id=f"resume_text-{index}",
            text=paragraph,
            section="resume_text",
        )
        for index, paragraph in enumerate(paragraphs)
    ]
