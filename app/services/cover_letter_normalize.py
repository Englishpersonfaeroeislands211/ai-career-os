from app.schemas.cover_letter import COVER_LETTER_MAX_BODY_CHARS


def cap_cover_letter_body(body: str, *, max_chars: int = COVER_LETTER_MAX_BODY_CHARS) -> str:
    body = body.strip()
    if len(body) <= max_chars:
        return body

    truncated = body[:max_chars].rstrip()
    if " " in truncated:
        truncated = truncated.rsplit(" ", 1)[0].rstrip(".,;:")
    return truncated


def normalize_cover_letter_draft_payload(payload: dict) -> dict:
    if isinstance(payload.get("body"), str):
        payload = {**payload, "body": cap_cover_letter_body(payload["body"])}
    return payload


def normalize_cover_letter_result_payload(payload: dict) -> dict:
    if isinstance(payload.get("body"), str):
        payload = {**payload, "body": cap_cover_letter_body(payload["body"])}
    return payload
