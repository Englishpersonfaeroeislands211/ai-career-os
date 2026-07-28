import pytest

from app.services.job_paste_parser import JobPasteParseError, html_to_text, prepare_job_post_text


def test_prepare_job_post_text_accepts_plain_text():
    text = prepare_job_post_text("Senior Engineer at Acme.\n" + ("Build APIs. " * 20))
    assert "Senior Engineer" in text


def test_prepare_job_post_text_strips_pasted_html():
    html = """
    <html><body><nav>Skip</nav><main>
    <h1>Senior Backend Engineer</h1>
    <p>Build Python APIs with FastAPI and PostgreSQL for production systems.</p>
    <p>Collaborate with product teams and own services end to end.</p>
    </main></body></html>
    """
    text = prepare_job_post_text(html)
    assert "Skip" not in text
    assert "Senior Backend Engineer" in text


def test_html_to_text_collapses_whitespace():
    text = html_to_text("<p>Hello</p><p>World</p>")
    assert "Hello" in text
    assert "World" in text


def test_prepare_job_post_text_rejects_empty():
    with pytest.raises(JobPasteParseError, match="empty"):
        prepare_job_post_text("   ")
