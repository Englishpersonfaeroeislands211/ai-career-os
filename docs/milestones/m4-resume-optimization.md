# Milestone 4: Resume optimization

**Status:** Done (MVP)  
**Concepts:** Reflection, iterative refinement, human-in-the-loop edits

## Problem

Match analysis surfaces gaps — missing keywords, under-sold experience, weak framing. Users need actionable help closing those gaps, not just a score.

## Solution

From a **completed full match analysis** on job detail:

```
MatchResult.gaps
  → POST /match-analyses/{id}/resume-optimization
  → LLM suggests bullet rewrites / skill additions (honest, no fabrication)
  → user selects suggestions
  → POST /profiles/{id}/apply-resume-suggestions
  → optional Re-analyze match
```

## API

`POST /api/v1/match-analyses/{analysis_id}/resume-optimization`

Requires completed full analysis with at least one gap. Returns `ResumeOptimizationResult`.

`POST /api/v1/profiles/{profile_id}/apply-resume-suggestions`

```json
{
  "suggestions": [
    {
      "gap_evidence": "...",
      "section": "experience",
      "action": "rewrite",
      "target_label": "Acme — Engineer, bullet 1",
      "current_text": "Built APIs with Python.",
      "suggested_text": "Built APIs with Python on AWS.",
      "rationale": "..."
    }
  ]
}
```

Updates `resume_text`, `structured_data`, and `headline` where applicable.

## Product constraints

- Never auto-apply — user selects which suggestions to merge
- Suggestions must be grounded in existing resume content
- No PDF regeneration in M4 optimizer (structured apply only) — **profile PDF export** added separately

## Completed

- [x] `resume_optimization.txt` prompt + `ResumeOptimizationResult` schema
- [x] `optimize_resume_for_match` service
- [x] `apply_suggestions` helper for structured profile updates
- [x] Job detail UI: generate, review, apply, re-analyze
- [x] Unit tests

## Next

- Eval fixtures for optimization quality (golden gap → suggestion pairs)
- Navigate to profile review with pre-filled diff view
- Re-analyze automatically after apply (optional)

## Then

[M5 — Cover letter generation](../milestones/README.md)
