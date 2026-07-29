from app.schemas.match_analysis import BatchScreeningResult, MatchResult
from app.services.match_analysis_normalize import (
    normalize_batch_screen_payload,
    normalize_match_payload,
)


def test_normalize_match_score_from_fraction():
    payload = normalize_match_payload(
        {
            "match_score": 0.885,
            "recommendation": "apply",
            "strengths": [],
            "gaps": [],
            "summary": "Strong match.",
        }
    )
    assert payload["score"] == 88.5


def test_normalize_recommendation_aliases():
    payload = normalize_match_payload(
        {
            "score": 55,
            "recommendation": "skip",
            "strengths": [],
            "gaps": [],
            "summary": "Weak match.",
        }
    )
    assert payload["recommendation"] == "do not apply"


def test_normalize_strength_with_string_point():
    payload = normalize_match_payload(
        {
            "score": 80,
            "recommendation": "apply",
            "strengths": [{"point": "Strong Python backend experience."}],
            "gaps": [],
            "summary": "Good match.",
        }
    )
    assert payload["strengths"][0]["evidence"] == "Strong Python backend experience."
    assert payload["strengths"][0]["point"] == 7.0


def test_match_result_validation():
    normalized = normalize_match_payload(
        {
            "score": 91.5,
            "recommendation": "apply",
            "strengths": [{"point": 9.0, "evidence": "8 years of Python experience."}],
            "gaps": [
                {
                    "point": 4.0,
                    "severity": "blocker",
                    "evidence": "No AWS experience mentioned.",
                }
            ],
            "summary": "Strong match overall.",
        }
    )
    result = MatchResult.model_validate(normalized)
    assert result.score == 91.5
    assert result.gaps[0].severity == "high"


def test_normalize_batch_screen_payload():
    payload = normalize_batch_screen_payload(
        {
            "matches": [
                {
                    "job_id": "550e8400-e29b-41d4-a716-446655440000",
                    "score": 0.75,
                    "recommendation": "apply",
                    "reason": "Strong Python fit.",
                }
            ]
        }
    )
    result = BatchScreeningResult.model_validate(payload)
    assert result.matches[0].score == 75.0
    assert result.matches[0].reason == "Strong Python fit."
