# Milestone 3: Match on job insert

**Status:** Done  
**Concepts:** Background orchestration, intake-time matching, context compression (screening cards)

## Problem

Users add jobs one at a time. Matching is the reason they paste a JD — it should happen **immediately**, not as a separate “Analyze all” step on the home page.

Bulk batch matching (comparative scoring across many jobs) and tiered cascades (cheap screen → deep analyze top K) made sense at high volume but added UX and engineering complexity for the common case: paste one job, want one explanation.

## Solution

**Full detailed match when the job is saved:**

```
Paste JD → extract fields → Save & analyze match
                                ↓
              POST /jobs { profile_id, title, company, description, ... }
                                ↓
              MatchAnalysis row (pending) + background run_match_analysis
                                ↓
              Home pipeline + job detail show score, strengths, gaps
```

## API

`POST /api/v1/jobs`

```json
{
  "title": "Senior Backend Engineer",
  "company": "Acme",
  "description": "...",
  "profile_id": "uuid-of-active-profile",
  "raw_metadata": {
    "match_summary": "Senior backend role building Python APIs at scale.",
    "requirements": []
  }
}
```

Response (`JobCreateRead`) includes `match_analysis_id` when match was queued.

Manual re-analyze remains available:

`POST /api/v1/match-analyses` with `{ "profile_id", "job_id" }`

## Product choices

| Decision | Rationale |
|----------|-----------|
| Full `match_analysis` at intake | One job at a time; user expects depth, not a cheap screen |
| No bulk “Analyze all” | Profile exists before add-job; match is part of save |
| Screening card at extract | Compresses JD context for future cost optimizations without changing UX |
| Re-analyze on job detail | Profile updates or legacy jobs without analysis |

## Completed

- [x] `profile_id` on `JobCreate` → auto-queue full match
- [x] `JobCreateRead.match_analysis_id`
- [x] Screening card + `match_summary` in job extraction
- [x] JobNewPage: requires active profile, “Save & analyze match”
- [x] Home pipeline: ranked jobs, poll pending analyses (no bulk buttons)
- [x] Job detail: hide analyze while pending; Re-analyze / Retry otherwise
- [x] Removed `POST /match-analyses/batch` from API

## Not done (follow-ups)

- [ ] Re-analyze automatically when job description is updated
- [ ] Eval fixtures for match-at-intake golden path
- [ ] Prune unused batch/cascade code in `matcher.py` / `batch_matcher.py`

## Next

[M4 — Resume optimization](../milestones/README.md#m4--resume-optimization-next): turn match gaps into suggested resume improvements.
