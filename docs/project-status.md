# Project Status

Last updated: 2026-07-28

## Where we are

AI Career OS has a working **resume → job → explainable match → act** loop. The product is intentionally narrow: paste your data, get evidence-backed fit analysis — no black-box auto-apply.

**Current milestone:** M5 complete. **Next:** M6 — company research.

## Product flow (today)

```mermaid
flowchart LR
    A[Upload resume PDF] --> B[Review extraction]
    B --> C[(Profile)]
    C --> D[Paste job description]
    D --> E[Extract job fields]
    E --> F[Save and analyze match]
    F --> G[Screen match shown quickly]
    G --> H[Full MatchAnalysis completes]
    H --> I[Home pipeline ranked by score]
    H --> J[Job detail: strengths, gaps, resume + cover letter]
```

1. **Onboarding** — PDF → LLM structured extraction → human review → save profile.
2. **Add job** — paste JD → extract fields → **Save & analyze match** (sends `profile_id`).
3. **Progressive match** — fast screen result while pending; full strengths/gaps when complete.
4. **Home pipeline** — jobs ranked by match score; shows screen score during analysis.
5. **Job detail** — deep dive; resume optimization and cover letter (full match only).

## Implemented

| Area | Status |
|------|--------|
| Resume PDF extraction + structured `ResumeExtraction` | Done |
| Profile CRUD + settings (BYOM: cloud + local) | Done |
| Job paste → `JobExtraction` + review UI | Done |
| Explainable match + match on job insert | Done |
| Progressive match (screen → full at intake) | Done |
| Resume optimization (gap → suggestions → apply) | Done |
| Cover letter (draft → critique → revise) | Done |
| Home job pipeline with polling | Done |
| Eval harness (5 suites: resume, job, match, optimization, cover letter) | Done |
| LLM call tracing (latency, tokens, operation) | Done |
| Screening card + `match_summary` at job extract | Done |

## API surface (`/api/v1/`)

| Resource | Key endpoints |
|----------|----------------|
| Profiles | CRUD, `POST /profiles/parse-resume`, `GET /profiles/{id}/resume.pdf` |
| Jobs | CRUD, `POST /jobs/parse-text`, `POST /jobs` (optional `profile_id` → progressive match) |
| Match analyses | `POST /match-analyses` (manual full re-analyze), list, get |
| Match actions | `POST /match-analyses/{id}/resume-optimization`, `POST /match-analyses/{id}/cover-letter` |
| Settings | GET/PUT LLM provider config |
| LLM | `POST /llm/models` |

Interactive docs: http://127.0.0.1:8000/docs

## Pivot history (why docs mention “batch”)

We briefly shipped **bulk batch matching** (one comparative LLM call for many jobs) and explored a **tiered cascade** (cheap screen → full analyze top K). At typical intake volume (one job at a time), bulk UX added complexity without enough benefit.

**Product decision:** run **progressive match when each job is saved** (screen first, then full). Batch/cascade code remains in the repo for experiments but is not exposed in the API or UI.

See [M3: Match on job insert](milestones/m3-match-on-intake.md), [M5: Progressive match + cover letter](milestones/m5-progressive-match-cover-letter.md), and [M3 batch (archived)](milestones/m3-batch-matching.md).

## What's next (M6+)

| Priority | Milestone | Why |
|----------|-----------|-----|
| **Next** | [M6 — Company research](milestones/README.md) | Employer context via tool calling |
| Soon | Re-analyze on job update | JD edits should refresh match without manual retry |
| Soon | Cover letter golden eval fixture | Regression tests for reflection chain |
| Later | Job discovery (M7) | Official APIs only — no scraping |
| Cleanup | Prune unused batch/cascade backend | After evals cover primary paths |

## Intentionally deferred

- Authentication (single-user local dev)
- Vector DB / RAG (resume + JD fit in context today)
- Agent frameworks (except targeted tool use in M6)
- Auto-apply

## References

- [AI engineering patterns](ai-engineering.md)
- [Architecture](architecture.md)
- [Milestones](milestones/README.md)
