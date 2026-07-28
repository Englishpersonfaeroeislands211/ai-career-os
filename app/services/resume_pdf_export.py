from __future__ import annotations

import re
from pathlib import Path
from typing import Any
from urllib.parse import quote

from fpdf import FPDF

from app.models import Profile

FONT_DIR = Path(__file__).resolve().parents[1] / "assets" / "fonts"

REGULAR_FONT_CANDIDATES = (
    FONT_DIR / "DejaVuSans.ttf",
    Path("/usr/share/fonts/truetype/dejavu/DejaVuSans.ttf"),
    Path("/usr/share/fonts/TTF/DejaVuSans.ttf"),
    Path("/Library/Fonts/Arial Unicode.ttf"),
    Path("/System/Library/Fonts/Supplemental/Arial.ttf"),
)

BOLD_FONT_CANDIDATES = (
    FONT_DIR / "DejaVuSans-Bold.ttf",
    Path("/usr/share/fonts/truetype/dejavu/DejaVuSans-Bold.ttf"),
    Path("/usr/share/fonts/TTF/DejaVuSans-Bold.ttf"),
    Path("/System/Library/Fonts/Supplemental/Arial Bold.ttf"),
)


class ResumePdfExportError(Exception):
    """Raised when a resume PDF cannot be generated."""


def _first_existing(paths: tuple[Path, ...]) -> Path | None:
    for path in paths:
        if path.is_file():
            return path
    return None


def resolve_font_paths() -> tuple[Path, Path | None]:
    regular = _first_existing(REGULAR_FONT_CANDIDATES)
    if not regular:
        raise ResumePdfExportError(
            "No Unicode font found for PDF export. "
            "Install DejaVu fonts (e.g. fonts-dejavu-core on Linux) or add DejaVuSans.ttf "
            "under app/assets/fonts/."
        )
    bold = _first_existing(BOLD_FONT_CANDIDATES)
    return regular, bold


def resume_pdf_filename(name: str) -> str:
    slug = re.sub(r"[^\w\s-]", "", name, flags=re.UNICODE).strip().lower()
    slug = re.sub(r"[-\s]+", "_", slug)
    # HTTP headers must be latin-1 — use ASCII-only slug for Content-Disposition.
    ascii_slug = re.sub(r"[^a-z0-9_]", "", slug.encode("ascii", "ignore").decode())
    ascii_slug = re.sub(r"_+", "_", ascii_slug).strip("_")
    return f"{ascii_slug or 'resume'}_resume.pdf"


def content_disposition_attachment(filename: str) -> str:
    """Build a Content-Disposition value safe for Starlette (latin-1 headers)."""
    if filename.isascii():
        return f'attachment; filename="{filename}"'
    ascii_fallback = filename.encode("ascii", "ignore").decode() or "resume.pdf"
    encoded = quote(filename, safe="")
    return f"attachment; filename=\"{ascii_fallback}\"; filename*=UTF-8''{encoded}"


class _ResumePdf(FPDF):
    def __init__(self, regular_font: Path, bold_font: Path | None):
        super().__init__(unit="mm", format="A4")
        self.font_family = "ResumeExport"
        self.set_margins(18, 18, 18)
        self.set_auto_page_break(auto=True, margin=18)
        self.add_font(self.font_family, "", str(regular_font))
        if bold_font:
            self.add_font(self.font_family, "B", str(bold_font))
        self.add_page()

    def section_title(self, title: str) -> None:
        self.ln(2)
        self.set_font(self.font_family, "B", 11)
        self.multi_cell(0, 6, title.upper(), new_x="LMARGIN", new_y="NEXT")
        self.set_font(self.font_family, size=10)

    def body_text(self, text: str, *, bold: bool = False) -> None:
        self.set_font(self.font_family, "B" if bold else "", 10)
        self.multi_cell(0, 5.5, text, new_x="LMARGIN", new_y="NEXT")
        self.set_font(self.font_family, size=10)

    def bullet(self, text: str) -> None:
        self.set_font(self.font_family, size=10)
        self.multi_cell(0, 5.5, f"• {text}", new_x="LMARGIN", new_y="NEXT")


def _as_list(value: Any) -> list[Any]:
    return value if isinstance(value, list) else []


def _as_str(value: Any) -> str | None:
    if value is None:
        return None
    text = str(value).strip()
    return text or None


def _render_structured(pdf: _ResumePdf, data: dict[str, Any], profile: Profile) -> None:
    skills = [str(skill).strip() for skill in _as_list(data.get("skills")) if str(skill).strip()]
    if skills:
        pdf.section_title("Skills")
        pdf.body_text(", ".join(skills))

    experience = _as_list(data.get("experience"))
    if experience:
        pdf.section_title("Experience")
        for item in experience:
            if not isinstance(item, dict):
                continue
            title = _as_str(item.get("title")) or "Role"
            company = _as_str(item.get("company")) or "Company"
            duration = _as_str(item.get("duration"))
            line = f"{title} — {company}"
            if duration:
                line = f"{line} ({duration})"
            pdf.body_text(line, bold=True)
            for highlight in _as_list(item.get("highlights")):
                highlight_text = _as_str(highlight)
                if highlight_text:
                    pdf.bullet(highlight_text)
            pdf.ln(1)

    education = _as_list(data.get("education"))
    if education:
        pdf.section_title("Education")
        for item in education:
            if not isinstance(item, dict):
                continue
            degree = _as_str(item.get("degree")) or "Degree"
            school = _as_str(item.get("school")) or "School"
            duration = _as_str(item.get("duration"))
            line = f"{degree} — {school}"
            if duration:
                line = f"{line} ({duration})"
            pdf.body_text(line)

    projects = _as_list(data.get("projects"))
    if projects:
        pdf.section_title("Projects")
        for item in projects:
            if not isinstance(item, dict):
                continue
            name = _as_str(item.get("name")) or "Project"
            pdf.body_text(name, bold=True)
            description = _as_str(item.get("description"))
            if description:
                pdf.body_text(description)
            for highlight in _as_list(item.get("highlights")):
                highlight_text = _as_str(highlight)
                if highlight_text:
                    pdf.bullet(highlight_text)
            pdf.ln(1)

    if not any([skills, experience, education, projects]):
        pdf.body_text(profile.resume_text.strip())


def build_profile_resume_pdf(profile: Profile) -> bytes:
    regular, bold = resolve_font_paths()
    pdf = _ResumePdf(regular, bold)

    pdf.set_font(pdf.font_family, "B", 20)
    pdf.multi_cell(0, 10, profile.name, new_x="LMARGIN", new_y="NEXT", align="C")

    headline = profile.headline
    data = profile.structured_data if isinstance(profile.structured_data, dict) else None
    if not headline and data:
        headline = _as_str(data.get("headline"))
    if headline:
        pdf.set_font(pdf.font_family, size=12)
        pdf.multi_cell(0, 6, headline, new_x="LMARGIN", new_y="NEXT", align="C")

    contact_parts: list[str] = []
    if data:
        email = _as_str(data.get("email"))
        phone = _as_str(data.get("phone"))
        if email:
            contact_parts.append(email)
        if phone:
            contact_parts.append(phone)
    if contact_parts:
        pdf.set_font(pdf.font_family, size=10)
        pdf.multi_cell(0, 5, " · ".join(contact_parts), new_x="LMARGIN", new_y="NEXT", align="C")

    pdf.ln(4)
    pdf.set_font(pdf.font_family, size=10)

    if data:
        _render_structured(pdf, data, profile)
    else:
        pdf.multi_cell(0, 5.5, profile.resume_text.strip(), new_x="LMARGIN", new_y="NEXT")

    return bytes(pdf.output())
