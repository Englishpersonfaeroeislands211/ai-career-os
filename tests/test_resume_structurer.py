from unittest.mock import AsyncMock, patch

import pytest

from app.schemas.resume_extraction import ExperienceEntry, ResumeExtraction
from app.services.llm.base import LLMConfigurationError
from app.services.resume_structurer import structure_resume


@pytest.mark.asyncio
async def test_structure_resume_calls_llm_client():
    extraction = ResumeExtraction(
        name="Jane Doe",
        headline="Backend Engineer",
        skills=["Python"],
        experience=[
            ExperienceEntry(
                title="Engineer",
                company="Acme",
                duration="2020-2024",
                highlights=["Built APIs"],
            )
        ],
    )
    mock_client = AsyncMock()
    mock_client.generate_structured.return_value = extraction

    with patch(
        "app.services.resume_structurer.get_llm_client",
        new=AsyncMock(return_value=mock_client),
    ):
        result = await structure_resume(db=None, resume_text="Jane Doe\nBackend Engineer")

    assert result.name == "Jane Doe"
    mock_client.generate_structured.assert_awaited_once()


@pytest.mark.asyncio
async def test_structure_resume_propagates_configuration_error():
    with patch(
        "app.services.resume_structurer.get_llm_client",
        new=AsyncMock(side_effect=LLMConfigurationError("not configured")),
    ):
        with pytest.raises(LLMConfigurationError, match="not configured"):
            await structure_resume(db=None, resume_text="Resume text")
