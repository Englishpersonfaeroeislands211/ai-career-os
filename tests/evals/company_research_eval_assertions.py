from __future__ import annotations

from typing import Any

from app.schemas.company_research import CompanyBrief, CompanyBriefContent


def evaluate_company_brief_content(
    content: CompanyBriefContent,
    expected: dict[str, Any],
    *,
    case_name: str,
) -> list[str]:
    failures: list[str] = []

    company = expected.get("must_include_company")
    if company and company.casefold() not in content.company.casefold():
        failures.append(f"[{case_name}] expected company to mention {company!r}")

    summary = content.summary.casefold()
    for term in expected.get("must_include_terms", []):
        if term.casefold() not in summary and term.casefold() not in content.company.casefold():
            combined = " ".join(
                [
                    content.summary,
                    *content.culture_signals,
                    *content.recent_news,
                    *content.interview_signals,
                ]
            ).casefold()
            if term.casefold() not in combined:
                failures.append(f"[{case_name}] expected content to mention {term!r}")

    if expected.get("summary_not_empty") and not content.summary.strip():
        failures.append(f"[{case_name}] expected summary to be present")

    min_culture = expected.get("min_culture_signals", 0)
    if len(content.culture_signals) < min_culture:
        failures.append(
            f"[{case_name}] expected at least {min_culture} culture signals, "
            f"got {len(content.culture_signals)}"
        )

    min_interview = expected.get("min_interview_signals", 0)
    if len(content.interview_signals) < min_interview:
        failures.append(
            f"[{case_name}] expected at least {min_interview} interview signals, "
            f"got {len(content.interview_signals)}"
        )

    return failures


def evaluate_company_brief(
    brief: CompanyBrief,
    expected: dict[str, Any],
    *,
    case_name: str,
) -> list[str]:
    failures = evaluate_company_brief_content(brief, expected, case_name=case_name)

    min_sources = expected.get("min_sources", 0)
    if len(brief.sources) < min_sources:
        failures.append(
            f"[{case_name}] expected at least {min_sources} sources, got {len(brief.sources)}"
        )

    if not brief.researched_at:
        failures.append(f"[{case_name}] expected researched_at timestamp")

    return failures
