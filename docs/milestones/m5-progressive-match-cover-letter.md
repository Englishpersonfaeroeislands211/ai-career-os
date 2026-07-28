# Milestone 5: Progressive match + cover letter chain

**Status:** Done (MVP)  
**Concepts:** Staged inference, reflection chain, progressive UX

## Problem

Two related gaps after M4:

1. **Latency at intake** — full match analysis takes several seconds; the job board showed nothing useful while pending.
2. **Cover letters** — users still need tailored outreach after understanding fit, but one-shot generation often overclaims or misses strengths.

## Solution

### A — Progressive match (screen → full)

When a job is saved with `profile_id`, match analysis runs in two stages:

```
POST /jobs { profile_id, ... }
  → MatchAnalysis (pending)
  → Tier 1: analyze_matches_screen (screening card, fast)
  → commit screen result (still pending)
  → Tier 2: analyze_match (full strengths/gaps)
  → commit full result (completed)
```

The UI shows the screen score and recommendation while full analysis runs, then upgrades to strengths/gaps when complete.

Manual re-analyze (`POST /match-analyses`) skips the screen pass and runs full analysis only.

If deep analysis fails after a successful screen, the screen result is kept with `status=completed` and an error note.

### B — Cover letter reflection chain

From a **completed full match** on job detail:

```
MatchResult
  → draft (cover_letter_draft.txt)
  → critique (cover_letter_critique.txt)
  → revise (cover_letter_revise.txt)
  → CoverLetterResult
```

Three separate `generate_structured()` calls — each traced independently.

## API

`POST /api/v1/match-analyses/{analysis_id}/cover-letter`

Requires completed full analysis (`depth !== "screen"`). Returns `CoverLetterResult`:

```json
{
  "body": "Dear Acme,\n\n...",
  "tone": "professional",
  "highlights_used": ["Python backend", "FastAPI migration"],
  "critique_summary": "Added missing FastAPI strength; removed unsupported claim."
}
```

## Product choices

| Decision | Rationale |
|----------|-----------|
| Screen only at job insert | Progressive UX where users wait; re-analyze is explicit full refresh |
| Keep pending during screen | Frontend can detect `result.depth === "screen"` + `status === "pending"` |
| Cover letter after full match | Needs strengths/gaps narrative; screen-only is insufficient |
| 3-pass chain vs one prompt | Reflection reduces fabrication and tone drift; observable in traces |
| Resume optimization + cover letter gated on full match | Both depend on gap/strength detail |

## Completed

- [x] `run_progressive_match_analysis()` in `matcher.py`
- [x] Job create routes to progressive match; manual re-analyze stays full-only
- [x] `CoverLetterDraft`, `CoverLetterCritique`, `CoverLetterResult` schemas
- [x] `cover_letter_draft.txt`, `cover_letter_critique.txt`, `cover_letter_revise.txt`
- [x] `generate_cover_letter()` service + API route
- [x] Frontend: screen preview on job board and job detail while pending
- [x] `CoverLetterPanel` on job detail (generate, copy, regenerate)
- [x] Tests: progressive match, cover letter chain, prompt loading

## Not done (follow-ups)

- [ ] Cover letter golden eval fixture
- [ ] Model routing (fast model for screen/draft, slow for full/revise)
- [ ] PDF export of cover letter
- [ ] Prune unused batch/cascade product code

## Next

[M6 — Company research](README.md): tool calling and web search for employer context.
