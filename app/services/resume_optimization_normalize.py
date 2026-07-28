from typing import Any

_VALID_SECTIONS = {"headline", "skills", "experience", "projects"}
_VALID_ACTIONS = {"rewrite", "add", "emphasize"}


def _as_str(value: Any) -> str | None:
    if value is None:
        return None
    text = str(value).strip()
    return text or None


def normalize_resume_optimization_payload(data: dict[str, Any]) -> dict[str, Any]:
    suggestions_raw = data.get("suggestions")
    if not isinstance(suggestions_raw, list):
        suggestions_raw = []

    suggestions: list[dict[str, Any]] = []
    for item in suggestions_raw:
        if not isinstance(item, dict):
            continue
        section = _as_str(item.get("section")) or "experience"
        if section not in _VALID_SECTIONS:
            section = "experience"
        action = _as_str(item.get("action")) or "rewrite"
        if action not in _VALID_ACTIONS:
            action = "rewrite"

        gap_evidence = _as_str(item.get("gap_evidence"))
        suggested_text = _as_str(item.get("suggested_text"))
        target_label = _as_str(item.get("target_label"))
        rationale = _as_str(item.get("rationale"))
        if not gap_evidence or not suggested_text or not target_label or not rationale:
            continue

        suggestions.append(
            {
                "gap_evidence": gap_evidence,
                "section": section,
                "action": action,
                "target_label": target_label,
                "current_text": _as_str(item.get("current_text")),
                "suggested_text": suggested_text,
                "rationale": rationale,
            }
        )

    summary = _as_str(data.get("summary")) or "Resume tailoring suggestions for this job."
    return {"summary": summary, "suggestions": suggestions}
