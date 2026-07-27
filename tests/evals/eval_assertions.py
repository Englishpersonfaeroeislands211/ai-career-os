from __future__ import annotations

import json
from pathlib import Path
from typing import Any

from app.schemas.resume_extraction import ResumeExtraction

BAD_NAME_HINTS = frozenset({"contact", "unknown", "resume", "n/a"})


def load_json(path: Path) -> dict[str, Any]:
    return json.loads(path.read_text(encoding="utf-8"))


def evaluate_extraction(
    extraction: ResumeExtraction,
    expected: dict[str, Any],
    *,
    case_name: str,
) -> list[str]:
    failures: list[str] = []

    name = extraction.name.strip()
    if not name:
        failures.append(f"[{case_name}] name is empty")

    name_contains = expected.get("name_contains")
    if name_contains and name_contains not in name:
        failures.append(f"[{case_name}] expected name to contain {name_contains!r}, got {name!r}")

    for forbidden in expected.get("name_not", []):
        if name.casefold() == str(forbidden).casefold():
            failures.append(f"[{case_name}] name must not be {forbidden!r}")

    if name.casefold() in BAD_NAME_HINTS:
        failures.append(f"[{case_name}] name looks like a parser placeholder: {name!r}")

    min_skills = expected.get("min_skills", 0)
    if len(extraction.skills) < min_skills:
        failures.append(
            f"[{case_name}] expected at least {min_skills} skills, got {len(extraction.skills)}"
        )

    skill_set = {skill.casefold() for skill in extraction.skills}
    for skill in expected.get("must_include_skills", []):
        if skill.casefold() not in skill_set:
            failures.append(f"[{case_name}] missing required skill {skill!r}")

    min_experience = expected.get("min_experience", 0)
    if len(extraction.experience) < min_experience:
        failures.append(
            f"[{case_name}] expected at least {min_experience} experience entries, "
            f"got {len(extraction.experience)}"
        )

    companies = " ".join(entry.company for entry in extraction.experience)
    for fragment in expected.get("experience_companies_contain", []):
        if fragment not in companies:
            failures.append(f"[{case_name}] expected an experience company containing {fragment!r}")

    min_education = expected.get("min_education", 0)
    if len(extraction.education) < min_education:
        failures.append(
            f"[{case_name}] expected at least {min_education} education entries, "
            f"got {len(extraction.education)}"
        )

    email_contains = expected.get("email_contains")
    if email_contains:
        email = extraction.email or ""
        if email_contains not in email:
            failures.append(
                f"[{case_name}] expected email to contain {email_contains!r}, got {email!r}"
            )

    if expected.get("phone_not_empty") and not (extraction.phone or "").strip():
        failures.append(f"[{case_name}] expected phone to be present")

    if expected.get("headline_not_empty") and not (extraction.headline or "").strip():
        failures.append(f"[{case_name}] expected headline to be present")

    return failures
