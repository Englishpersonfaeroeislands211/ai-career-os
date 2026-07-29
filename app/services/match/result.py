from app.schemas.match_analysis import MatchResult
from app.schemas.rag import ScoredChunk


def full_result_payload(
    result: MatchResult,
    *,
    rag_chunks: list[ScoredChunk] | None = None,
) -> dict:
    payload = {"depth": "full", **result.model_dump()}
    if rag_chunks:
        payload["retrieved_chunks"] = [
            {
                "id": item.chunk.id,
                "score": round(item.score, 4),
                "text": item.chunk.text,
                "section": item.chunk.section,
            }
            for item in rag_chunks
        ]
    return payload


def match_result_from_analysis_payload(result: dict) -> MatchResult:
    """Build MatchResult from persisted analysis JSON (may include depth/reason extras)."""
    payload = {key: result[key] for key in MatchResult.model_fields if key in result}
    return MatchResult.model_validate(payload)


def match_result_for_cover_letter(result: dict) -> MatchResult:
    if result.get("depth") == "screen":
        raise ValueError("Full match analysis required for cover letter generation")
    return match_result_from_analysis_payload(result)
