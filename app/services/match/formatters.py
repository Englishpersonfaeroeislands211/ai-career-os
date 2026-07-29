import json

from app.config import settings
from app.models import Job, Profile
from app.services.rag.match_context import format_rag_resume_section, retrieve_for_match
from app.services.rag.retrieval import EmbeddingProvider, get_embedding_provider


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


def build_match_user_message(
    profile: Profile,
    job: Job,
    *,
    use_rag: bool | None = None,
    embedder: EmbeddingProvider | None = None,
    top_k: int | None = None,
) -> str:
    job_block = format_job(job)
    rag_enabled = settings.match_rag_enabled if use_rag is None else use_rag
    limit = settings.match_rag_top_k if top_k is None else top_k

    if rag_enabled:
        provider = embedder or get_embedding_provider()
        scored = retrieve_for_match(profile, job_block, provider, top_k=limit)
        if scored:
            resume_block = format_rag_resume_section(profile, scored)
        else:
            resume_block = f"Structured resume:\n\n{format_profile(profile)}"
    else:
        resume_block = f"Structured resume:\n\n{format_profile(profile)}"

    return f"{resume_block}\n\nJob description:\n\n{job_block}"
