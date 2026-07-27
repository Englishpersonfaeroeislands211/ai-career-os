from __future__ import annotations

from typing import Any

from app.schemas.match_analysis import MatchResult


def evaluate_match_result(
    result: MatchResult,
    expected: dict[str, Any],
    *,
    case_name: str,
) -> list[str]:
    failures: list[str] = []

    min_score = expected.get("min_score")
    if min_score is not None and result.score < min_score:
        failures.append(f"[{case_name}] expected score >= {min_score}, got {result.score}")

    max_score = expected.get("max_score")
    if max_score is not None and result.score > max_score:
        failures.append(f"[{case_name}] expected score <= {max_score}, got {result.score}")

    expected_recommendation = expected.get("recommendation")
    if expected_recommendation and result.recommendation != expected_recommendation:
        failures.append(
            f"[{case_name}] expected recommendation {expected_recommendation!r}, "
            f"got {result.recommendation!r}"
        )

    min_strengths = expected.get("min_strengths", 0)
    if len(result.strengths) < min_strengths:
        failures.append(
            f"[{case_name}] expected at least {min_strengths} strengths, "
            f"got {len(result.strengths)}"
        )

    min_gaps = expected.get("min_gaps", 0)
    if len(result.gaps) < min_gaps:
        failures.append(f"[{case_name}] expected at least {min_gaps} gaps, got {len(result.gaps)}")

    strength_text = " ".join(item.evidence for item in result.strengths).casefold()
    for term in expected.get("must_include_strength_terms", []):
        if term.casefold() not in strength_text:
            failures.append(f"[{case_name}] expected strengths to mention {term!r}")

    gap_text = " ".join(item.evidence for item in result.gaps).casefold()
    for term in expected.get("must_include_gap_terms", []):
        if term.casefold() not in gap_text:
            failures.append(f"[{case_name}] expected gaps to mention {term!r}")

    if expected.get("summary_not_empty") and not result.summary.strip():
        failures.append(f"[{case_name}] expected summary to be present")

    return failures
