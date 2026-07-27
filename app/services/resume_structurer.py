from sqlalchemy.ext.asyncio import AsyncSession

from app.prompts import load_prompt
from app.schemas.resume_extraction import ResumeExtraction
from app.services.llm import Message, get_llm_client
from app.services.resume_extraction_normalize import normalize_resume_payload


async def structure_resume(db: AsyncSession, resume_text: str) -> ResumeExtraction:
    client = await get_llm_client(db)
    return await client.complete_structured(
        messages=[
            Message(role="system", content=load_prompt("resume_extraction")),
            Message(role="user", content=f"Resume text:\n\n{resume_text}"),
        ],
        response_model=ResumeExtraction,
        transform_payload=normalize_resume_payload,
    )
