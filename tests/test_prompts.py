from app.prompts.loader import load_prompt


def test_load_resume_extraction_prompt():
    prompt = load_prompt("resume_extraction")
    assert "ResumeExtraction schema" in prompt
    assert '"experience"' in prompt
    assert "experience_items" in prompt
