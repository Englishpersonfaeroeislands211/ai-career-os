import copy

from app.schemas.resume_optimization import ResumeSuggestion


def _skill_exists(skills: list[str], skill: str) -> bool:
    normalized = skill.strip().lower()
    return any(existing.strip().lower() == normalized for existing in skills)


def _replace_highlight(highlights: list[str], current: str, suggested: str) -> bool:
    for index, highlight in enumerate(highlights):
        if current in highlight or highlight.strip() == current.strip():
            highlights[index] = suggested
            return True
    return False


def _append_experience_highlight(structured: dict, suggested: str, target_label: str) -> None:
    experience = structured.setdefault("experience", [])
    if not isinstance(experience, list):
        return

    company_hint = target_label.split("—")[0].strip().lower() if "—" in target_label else ""
    for entry in experience:
        if not isinstance(entry, dict):
            continue
        company = str(entry.get("company", "")).lower()
        if company_hint and company_hint not in company:
            continue
        highlights = entry.setdefault("highlights", [])
        if isinstance(highlights, list) and suggested not in highlights:
            highlights.append(suggested)
            return

    if experience and isinstance(experience[0], dict):
        highlights = experience[0].setdefault("highlights", [])
        if isinstance(highlights, list) and suggested not in highlights:
            highlights.append(suggested)


def _append_project_highlight(structured: dict, suggested: str, target_label: str) -> None:
    projects = structured.setdefault("projects", [])
    if not isinstance(projects, list):
        return

    name_hint = target_label.split("—")[0].strip().lower() if "—" in target_label else ""
    for entry in projects:
        if not isinstance(entry, dict):
            continue
        name = str(entry.get("name", "")).lower()
        if name_hint and name_hint not in name:
            continue
        highlights = entry.setdefault("highlights", [])
        if isinstance(highlights, list) and suggested not in highlights:
            highlights.append(suggested)
            return

    if projects and isinstance(projects[0], dict):
        highlights = projects[0].setdefault("highlights", [])
        if isinstance(highlights, list) and suggested not in highlights:
            highlights.append(suggested)


def apply_suggestions(
    resume_text: str,
    structured_data: dict | None,
    headline: str | None,
    suggestions: list[ResumeSuggestion],
) -> tuple[str, dict | None, str | None]:
    """Apply selected suggestions. Returns (resume_text, structured_data, headline)."""
    updated_text = resume_text
    updated_headline = headline
    updated_structured = copy.deepcopy(structured_data) if structured_data else None

    for suggestion in suggestions:
        if suggestion.action in {"rewrite", "emphasize"} and suggestion.current_text:
            if suggestion.current_text in updated_text:
                updated_text = updated_text.replace(
                    suggestion.current_text,
                    suggestion.suggested_text,
                    1,
                )

        if not updated_structured:
            if suggestion.section == "headline" and suggestion.action in {
                "rewrite",
                "emphasize",
                "add",
            }:
                updated_headline = suggestion.suggested_text
            continue

        if suggestion.section == "headline":
            updated_structured["headline"] = suggestion.suggested_text
            updated_headline = suggestion.suggested_text
            continue

        if suggestion.section == "skills":
            skills = updated_structured.setdefault("skills", [])
            if not isinstance(skills, list):
                skills = []
                updated_structured["skills"] = skills
            if suggestion.action == "add" and not _skill_exists(skills, suggestion.suggested_text):
                skills.append(suggestion.suggested_text)
            continue

        if suggestion.section == "experience":
            experience = updated_structured.get("experience", [])
            if not isinstance(experience, list):
                continue
            if suggestion.action in {"rewrite", "emphasize"} and suggestion.current_text:
                for entry in experience:
                    if not isinstance(entry, dict):
                        continue
                    highlights = entry.get("highlights", [])
                    if isinstance(highlights, list) and _replace_highlight(
                        highlights,
                        suggestion.current_text,
                        suggestion.suggested_text,
                    ):
                        break
            elif suggestion.action == "add":
                _append_experience_highlight(
                    updated_structured,
                    suggestion.suggested_text,
                    suggestion.target_label,
                )
            continue

        if suggestion.section == "projects":
            projects = updated_structured.get("projects", [])
            if not isinstance(projects, list):
                continue
            if suggestion.action in {"rewrite", "emphasize"} and suggestion.current_text:
                for entry in projects:
                    if not isinstance(entry, dict):
                        continue
                    highlights = entry.get("highlights", [])
                    if isinstance(highlights, list) and _replace_highlight(
                        highlights,
                        suggestion.current_text,
                        suggestion.suggested_text,
                    ):
                        break
            elif suggestion.action == "add":
                _append_project_highlight(
                    updated_structured,
                    suggestion.suggested_text,
                    suggestion.target_label,
                )

    return updated_text, updated_structured, updated_headline
