from __future__ import annotations

from typing import Any

from app.schemas.job_extraction import JobExtraction


def evaluate_job_extraction(
    extraction: JobExtraction,
    expected: dict[str, Any],
    *,
    case_name: str,
) -> list[str]:
    failures: list[str] = []

    title_contains = expected.get("title_contains")
    if title_contains and title_contains not in extraction.title:
        failures.append(
            f"[{case_name}] expected title to contain {title_contains!r}, got {extraction.title!r}"
        )

    company_contains = expected.get("company_contains")
    if company_contains and company_contains not in extraction.company:
        failures.append(
            f"[{case_name}] expected company to contain {company_contains!r}, "
            f"got {extraction.company!r}"
        )

    min_description_length = expected.get("min_description_length", 0)
    if len(extraction.description) < min_description_length:
        failures.append(
            f"[{case_name}] expected description length >= {min_description_length}, "
            f"got {len(extraction.description)}"
        )

    min_requirements = expected.get("min_requirements", 0)
    if len(extraction.requirements) < min_requirements:
        failures.append(
            f"[{case_name}] expected at least {min_requirements} requirements, "
            f"got {len(extraction.requirements)}"
        )

    req_text = " ".join(extraction.requirements).casefold()
    for term in expected.get("must_include_requirements", []):
        if term.casefold() not in req_text:
            failures.append(f"[{case_name}] expected requirements to mention {term!r}")

    expected_work_mode = expected.get("work_mode")
    if expected_work_mode and extraction.work_mode != expected_work_mode:
        failures.append(
            f"[{case_name}] expected work_mode={expected_work_mode!r}, got {extraction.work_mode!r}"
        )

    location_contains = expected.get("location_contains")
    if location_contains:
        if not extraction.location or location_contains not in extraction.location:
            failures.append(
                f"[{case_name}] expected location to contain {location_contains!r}, "
                f"got {extraction.location!r}"
            )

    match_summary_contains = expected.get("match_summary_contains")
    if match_summary_contains and match_summary_contains not in extraction.match_summary:
        failures.append(
            f"[{case_name}] expected match_summary to contain {match_summary_contains!r}, "
            f"got {extraction.match_summary!r}"
        )

    return failures
