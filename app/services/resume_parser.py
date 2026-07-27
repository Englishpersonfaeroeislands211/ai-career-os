from io import BytesIO

from pypdf import PdfReader


class ResumeParseError(ValueError):
    pass


def extract_text_from_pdf(content: bytes) -> str:
    try:
        reader = PdfReader(BytesIO(content))
    except Exception as exc:
        raise ResumeParseError("Invalid or corrupted PDF file") from exc

    if reader.is_encrypted:
        raise ResumeParseError("Password-protected PDFs are not supported")

    pages: list[str] = []
    for page in reader.pages:
        text = page.extract_text()
        if text:
            pages.append(text.strip())

    resume_text = "\n\n".join(pages).strip()
    if not resume_text:
        raise ResumeParseError("No text could be extracted. The PDF may be scanned/image-only.")

    return resume_text


def guess_name_headline(resume_text: str) -> tuple[str | None, str | None]:
    """Best-effort hints from the first lines — user confirms on review screen."""
    lines = [line.strip() for line in resume_text.splitlines() if line.strip()]
    if not lines:
        return None, None

    name = lines[0] if len(lines[0]) <= 80 else None
    headline = lines[1] if len(lines) > 1 and len(lines[1]) <= 200 else None
    return name, headline
