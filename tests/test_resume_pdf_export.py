from types import SimpleNamespace
from unittest.mock import patch

import pytest

from app.services.resume_pdf_export import (
    ResumePdfExportError,
    build_profile_resume_pdf,
    content_disposition_attachment,
    resolve_font_paths,
    resume_pdf_filename,
)


def test_resume_pdf_filename_slugifies_name():
    assert resume_pdf_filename("Jane Doe") == "jane_doe_resume.pdf"
    assert resume_pdf_filename("Semir Turğay") == "semir_turay_resume.pdf"


def test_content_disposition_attachment_is_latin1_safe():
    header = content_disposition_attachment("semir_turay_resume.pdf")
    header.encode("latin-1")

    unicode_header = content_disposition_attachment("semir_turğay_resume.pdf")
    unicode_header.encode("latin-1")
    assert "filename*=" in unicode_header


def test_build_profile_resume_pdf_returns_valid_pdf():
    try:
        resolve_font_paths()
    except ResumePdfExportError:
        pytest.skip("No Unicode font available in this environment")

    profile = SimpleNamespace(
        name="Jane Doe",
        headline="Senior Backend Engineer",
        resume_text="Jane Doe\n\nBuilt Python APIs at Acme Corp.",
        structured_data={
            "name": "Jane Doe",
            "headline": "Senior Backend Engineer",
            "email": "jane@example.com",
            "phone": None,
            "skills": ["Python", "FastAPI"],
            "experience": [
                {
                    "title": "Senior Engineer",
                    "company": "Acme",
                    "duration": "2020–2024",
                    "highlights": ["Built payment APIs with Python and FastAPI."],
                }
            ],
            "education": [],
            "projects": [],
        },
    )

    pdf_bytes = build_profile_resume_pdf(profile)

    assert pdf_bytes.startswith(b"%PDF")
    assert len(pdf_bytes) > 500


def test_build_profile_resume_pdf_falls_back_to_raw_text():
    try:
        resolve_font_paths()
    except ResumePdfExportError:
        pytest.skip("No Unicode font available in this environment")

    profile = SimpleNamespace(
        name="Jane Doe",
        headline=None,
        resume_text="Plain resume text without structured data.",
        structured_data=None,
    )

    pdf_bytes = build_profile_resume_pdf(profile)

    assert pdf_bytes.startswith(b"%PDF")


def test_build_profile_resume_pdf_raises_when_no_font():
    profile = SimpleNamespace(
        name="Jane Doe",
        headline=None,
        resume_text="Resume",
        structured_data=None,
    )

    with patch(
        "app.services.resume_pdf_export.resolve_font_paths",
        side_effect=ResumePdfExportError("missing font"),
    ):
        with pytest.raises(ResumePdfExportError):
            build_profile_resume_pdf(profile)
