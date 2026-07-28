# Milestone 3 (archived): Batch matching + scoring

**Status:** Superseded — not part of the current product  
**Superseded by:** [M3: Match on job insert](m3-match-on-intake.md)

> This milestone was implemented and then removed from the product. The code and prompts remain in the repo for reference and experiments. Do not build new features on the batch API — it no longer exists.

## What we built

- Comparative batch prompt (`batch_match_analysis.txt`) — one LLM call for up to 12 jobs
- `POST /match-analyses/batch` + home “Analyze all” UI
- N+1 SQL fix via `_latest_analyses_by_job`

## Why we pivoted away

1. **Product flow changed** — users add jobs one at a time; match runs at save, not in bulk.
2. **Timeout at scale** — 10 full JDs in one batch timed out; led to tiered cascade experiments.
3. **Complexity vs. value** — cascade (screen all → deep analyze top K) solved batch timeouts but the simpler answer was: **full match per job at intake**, which matches how people actually use the app.

## What remains in the codebase

| Artifact | Location | Used by product? |
|----------|----------|------------------|
| Batch match prompt | `app/prompts/batch_match_analysis.txt` | No |
| Screen batch prompt | `app/prompts/batch_screen_match.txt` | No |
| `analyze_matches_batch`, cascade runners | `app/services/matcher.py` | No |
| `batch_matcher.py` | `app/services/batch_matcher.py` | No |
| Unit tests | `tests/test_batch_matcher.py`, `tests/test_matcher.py` | Yes (regression) |

**Cleanup ticket:** prune batch/cascade paths once match-on-intake evals are in place.

## Historical reference — original design

**One comparative LLM call per batch** (up to 12 jobs):

```
POST /match-analyses/batch  [removed]
  → queue pending MatchAnalysis rows
  → run_batch_match_analysis (single background task)
  → relative score calibration across the batch
```

See git history around `feat(jobs): run full match analysis when a job is saved` for the pivot commit.
