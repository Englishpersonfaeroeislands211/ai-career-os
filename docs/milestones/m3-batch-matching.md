# Milestone 3: Batch matching + scoring

**Status:** Done  
**Concepts:** Comparative batch prompting, context engineering, background orchestration

## Problem

Users track multiple jobs but must analyze each one individually. Running N separate LLM calls is slow, expensive, and scores are not calibrated relative to each other.

## Solution

**One comparative LLM call per batch** (up to 12 jobs), not one call per job:

```
POST /match-analyses/batch
  → queue pending MatchAnalysis rows (2 SQL queries, no N+1)
  → single background task: run_batch_match_analysis
  → LLM sees resume once + all job_ids in shared context
  → relative score calibration across the batch
  → map results back to each MatchAnalysis row
```

Single-job **Re-analyze** on job detail still uses the deep `match_analysis` prompt.

## API

`POST /api/v1/match-analyses/batch`

```json
{
  "profile_id": "...",
  "job_ids": null,
  "skip_existing": true
}
```

## AI engineering choices

| Approach | Why |
|----------|-----|
| Batch comparative prompt | Model ranks jobs against the same resume in one context — scores are relative, not isolated |
| Chunk size 12 | Keeps context predictable; larger pipelines split into few calls, not N |
| Separate batch prompt | Lighter orchestration rules + job_id mapping; single-job prompt unchanged for deep dives |
| One background task | Avoids N sequential FastAPI background tasks |

## Completed

- [x] `batch_match_analysis.txt` prompt + `BatchMatchResult` schema
- [x] `analyze_matches_batch` / `run_batch_match_analysis`
- [x] N+1 fix: `_latest_analyses_by_job` (one query)
- [x] Home page: Analyze all / new / re-analyze with polling
- [x] Unit tests

## Next

[M3.5 — Tiered matching cascade](m3.5-tiered-matching.md): compress job context, screen all jobs cheaply, full explain on top K only.
