from __future__ import annotations

from typing import Any

from app.schemas.cover_letter import COVER_LETTER_MAX_BODY_CHARS, CoverLetterResult


def evaluate_cover_letter(
    result: CoverLetterResult,
    expected: dict[str, Any],
    *,
    case_name: str,
) -> list[str]:
    failures: list[str] = []

    max_chars = expected.get("max_body_chars", COVER_LETTER_MAX_BODY_CHARS)
    if len(result.body) > max_chars:
        failures.append(
            f"[{case_name}] body length {len(result.body)} exceeds max {max_chars} characters"
        )

    body = result.body.casefold()
    for term in expected.get("must_include_terms", []):
        if term.casefold() not in body:
            failures.append(f"[{case_name}] expected body to mention {term!r}")

    company = expected.get("must_include_company")
    if company and company.casefold() not in body:
        failures.append(f"[{case_name}] expected body to mention company {company!r}")

    min_highlights = expected.get("min_highlights", 0)
    if len(result.highlights_used) < min_highlights:
        failures.append(
            f"[{case_name}] expected at least {min_highlights} highlights, "
            f"got {len(result.highlights_used)}"
        )

    if expected.get("critique_summary_not_empty") and not result.critique_summary.strip():
        failures.append(f"[{case_name}] expected critique_summary to be present")

    allowed_tones = expected.get("allowed_tones")
    if allowed_tones and result.tone not in allowed_tones:
        failures.append(f"[{case_name}] tone {result.tone!r} not in allowed {allowed_tones!r}")

    return failures
