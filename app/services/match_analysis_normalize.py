from typing import Any

RECOMMENDATION_ALIASES: dict[str, str] = {
    "apply": "apply",
    "maybe": "maybe apply",
    "maybe_apply": "maybe apply",
    "maybe apply": "maybe apply",
    "skip": "do not apply",
    "do_not_apply": "do not apply",
    "do not apply": "do not apply",
    "pass": "do not apply",
}

SEVERITY_ALIASES: dict[str, str] = {
    "low": "low",
    "minor": "low",
    "medium": "medium",
    "moderate": "medium",
    "high": "high",
    "major": "high",
    "blocker": "high",
    "critical": "high",
}


def _as_float(value: Any, default: float = 5.0) -> float:
    try:
        return float(value)
    except (TypeError, ValueError):
        return default


def _normalize_score(value: Any) -> float:
    score = _as_float(value, default=0.0)
    if 0 <= score <= 1:
        return round(score * 100, 1)
    return max(0.0, min(100.0, score))


def _normalize_recommendation(value: Any) -> str:
    text = str(value or "").strip().casefold()
    return RECOMMENDATION_ALIASES.get(text, "maybe apply")


def _normalize_severity(value: Any) -> str:
    text = str(value or "medium").strip().casefold()
    return SEVERITY_ALIASES.get(text, "medium")


def _normalize_strength(item: Any) -> dict[str, Any] | None:
    if not isinstance(item, dict):
        return None

    evidence = item.get("evidence")
    point = item.get("point")

    if isinstance(point, str) and not evidence:
        evidence = point
        point = 7.0
    elif isinstance(point, str) and evidence:
        point = 7.0

    evidence_text = str(evidence or point or "").strip()
    if not evidence_text:
        return None

    return {
        "point": max(0.0, min(10.0, _as_float(point, default=7.0))),
        "evidence": evidence_text,
    }


def _normalize_gap(item: Any) -> dict[str, Any] | None:
    if not isinstance(item, dict):
        return None

    evidence = item.get("evidence")
    point = item.get("point")

    if isinstance(point, str) and not evidence:
        evidence = point
        point = 5.0
    elif isinstance(point, str) and evidence:
        point = 5.0

    evidence_text = str(evidence or "").strip()
    if not evidence_text:
        return None

    return {
        "point": max(0.0, min(10.0, _as_float(point, default=5.0))),
        "severity": _normalize_severity(item.get("severity")),
        "evidence": evidence_text,
    }


def normalize_match_payload(data: dict[str, Any]) -> dict[str, Any]:
    """Map common model-specific keys onto the MatchResult schema."""
    score = data.get("score", data.get("match_score"))
    strengths = [
        normalized
        for item in data.get("strengths") or []
        if (normalized := _normalize_strength(item)) is not None
    ]
    gaps = [
        normalized
        for item in data.get("gaps") or []
        if (normalized := _normalize_gap(item)) is not None
    ]

    return {
        "score": _normalize_score(score),
        "recommendation": _normalize_recommendation(data.get("recommendation")),
        "strengths": strengths,
        "gaps": gaps,
        "summary": str(data.get("summary") or "").strip() or "No summary provided.",
    }


def normalize_screen_match_payload(data: dict[str, Any]) -> dict[str, Any]:
    """Map a single screening match onto ScreeningJobMatchResult fields."""
    score = data.get("score", data.get("match_score"))
    reason = str(data.get("reason") or data.get("summary") or "").strip()
    return {
        "score": _normalize_score(score),
        "recommendation": _normalize_recommendation(data.get("recommendation")),
        "reason": reason or "No screening reason provided.",
    }


def normalize_batch_screen_payload(data: dict[str, Any]) -> dict[str, Any]:
    """Map batch screen LLM output onto BatchScreeningResult."""
    raw_matches = data.get("matches") or data.get("results") or []
    matches: list[dict[str, Any]] = []
    for item in raw_matches:
        if not isinstance(item, dict):
            continue
        job_id = item.get("job_id")
        if not job_id:
            continue
        matches.append({"job_id": job_id, **normalize_screen_match_payload(item)})
    return {"matches": matches}
