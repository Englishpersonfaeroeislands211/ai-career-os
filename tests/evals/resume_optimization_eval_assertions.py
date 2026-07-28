from __future__ import annotations

from typing import Any

from app.schemas.resume_optimization import ResumeOptimizationResult


def evaluate_resume_optimization(
    result: ResumeOptimizationResult,
    expected: dict[str, Any],
    *,
    case_name: str,
) -> list[str]:
    failures: list[str] = []

    min_suggestions = expected.get("min_suggestions", 0)
    if len(result.suggestions) < min_suggestions:
        failures.append(
            f"[{case_name}] expected at least {min_suggestions} suggestions, "
            f"got {len(result.suggestions)}"
        )

    sections = {item.section for item in result.suggestions}
    for section in expected.get("must_include_sections", []):
        if section not in sections:
            failures.append(f"[{case_name}] expected a suggestion in section {section!r}")

    gap_text = " ".join(item.gap_evidence for item in result.suggestions).casefold()
    for term in expected.get("must_include_gap_terms", []):
        if term.casefold() not in gap_text:
            failures.append(f"[{case_name}] expected suggestions to reference gap term {term!r}")

    for suggestion in result.suggestions:
        if not suggestion.suggested_text.strip():
            failures.append(f"[{case_name}] suggestion for {suggestion.target_label!r} is empty")
        if not suggestion.rationale.strip():
            failures.append(
                f"[{case_name}] suggestion for {suggestion.target_label!r} missing rationale"
            )

    if expected.get("summary_not_empty") and not result.summary.strip():
        failures.append(f"[{case_name}] expected summary to be present")

    return failures
