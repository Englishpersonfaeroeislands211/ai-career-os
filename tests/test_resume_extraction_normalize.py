import json

from app.schemas.resume_extraction import ResumeExtraction
from app.services.resume_extraction_normalize import normalize_resume_payload


def test_normalize_qwen_style_payload():
    raw = {
        "name": "Semir Turğay",
        "contact": {
            "email": "semir.turgay@gmail.com",
            "phone": "+46761138196",
            "linkedin": "www.linkedin.com/in/semirturgay",
        },
        "skills_top": ["Crowdfunding", "Payment Solutions", "Docker"],
        "skills_general": ["Python", "FastAPI", "GraphQL"],
        "experience_items": [
            {
                "title": "Senior Software Engineer",
                "company": "Invisible Technologies Inc.",
                "duration": "June 2022 - July 2026 (4 years 2 months)",
                "location": "New York, United States",
                "highlights": ["Built backend platforms"],
            }
        ],
        "education_items": [
            {
                "school": "Eskişehir Osmangazi Üniversitesi",
                "degree": "Bilgisayar Mühendisi, Bilgisayar Mühendisliği",
                "duration": "2009 - 2014",
            }
        ],
        "projects_items": [],
    }

    normalized = normalize_resume_payload(raw)
    parsed = ResumeExtraction.model_validate(normalized)

    assert parsed.name == "Semir Turğay"
    assert parsed.email == "semir.turgay@gmail.com"
    assert parsed.phone == "+46761138196"
    assert "Python" in parsed.skills
    assert "Crowdfunding" in parsed.skills
    assert len(parsed.experience) == 1
    assert parsed.experience[0].company == "Invisible Technologies Inc."
    assert len(parsed.education) == 1


def test_normalize_qwen_style_payload_end_to_end_json_string():
    content = json.dumps(
        {
            "name": "Semir Turğay",
            "contact": {"email": "semir.turgay@gmail.com", "phone": "+46761138196"},
            "skills_general": ["Python"],
            "experience_items": [
                {
                    "title": "Senior Software Engineer",
                    "company": "Invisible Technologies Inc.",
                    "duration": "June 2022 - July 2026",
                    "highlights": [],
                }
            ],
            "education_items": [],
            "projects_items": [],
        }
    )
    data = json.loads(content)
    parsed = ResumeExtraction.model_validate(normalize_resume_payload(data))
    assert parsed.email == "semir.turgay@gmail.com"
    assert parsed.skills == ["Python"]
