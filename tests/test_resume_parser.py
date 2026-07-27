from io import BytesIO

import pytest
from pypdf import PdfWriter

from app.services.resume_parser import (
    ResumeParseError,
    extract_text_from_pdf,
    guess_name_headline,
)


def test_guess_name_headline_from_lines():
    text = "Jane Doe\nSenior Backend Engineer\n\nExperience..."
    name, headline = guess_name_headline(text)
    assert name == "Jane Doe"
    assert headline == "Senior Backend Engineer"


def test_guess_name_headline_empty():
    assert guess_name_headline("") == (None, None)


def test_extract_text_from_empty_pdf():
    writer = PdfWriter()
    writer.add_blank_page(width=612, height=792)
    buf = BytesIO()
    writer.write(buf)
    with pytest.raises(ResumeParseError, match="No text could be extracted"):
        extract_text_from_pdf(buf.getvalue())
