# Milestone 2: Job structuring from pasted text

**Status:** Done  
**Concepts:** Structured outputs, prompt engineering, evals  
**Policy:** No URL fetching or scraping — user paste only

## Problem

Users copy job postings from LinkedIn, Greenhouse, email, etc. Manual field entry is tedious. We need structured job fields without fetching URLs.

## Solution

Mirror M0 resume extraction:

```
User paste (text or copied HTML)
  → normalize locally (job_paste_parser.py)
  → LLM structured extraction (job_structurer.py)
  → review fields on dashboard
  → save Job (+ raw_metadata for requirements, etc.)
```

## API

`POST /api/v1/jobs/parse-text`

```json
{ "text": "Senior Backend Engineer\nFinTech Labs\n..." }
```

Returns `job_text` + `structured_data` (`JobExtraction`).

## Completed

- [x] `JobExtraction` schema
- [x] `job_extraction.txt` prompt
- [x] `job_paste_parser.py` — plain text + pasted HTML normalization (no network)
- [x] `job_structurer.py` — `generate_structured()`
- [x] `POST /jobs/parse-text`
- [x] Dashboard: paste → extract → review → save
- [x] Eval fixtures under `tests/evals/fixtures/job_extraction/`

## Cancelled (policy)

- URL fetch / scrape pipeline — never part of this project

## Next

[M3: Match on job insert](m3-match-on-intake.md) — automatic full match when a job is saved. Then [M4: Resume optimization](../milestones/README.md#m4--resume-optimization-next).
