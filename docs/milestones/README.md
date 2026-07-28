# Milestones

Incremental build plan. Each milestone adds one capability and is validated before moving on.

## Roadmap

| # | Milestone | AI concepts | Status |
|---|-----------|-------------|--------|
| 1 | [Explain the Match](m1-explain-the-match.md) | Structured outputs, prompt engineering, evals | **Done** |
| 2 | [Job structuring from paste](m2-job-intake.md) | Structured outputs, prompt engineering | **Done** |
| 3 | Batch matching + scoring | Context engineering, model routing | **Next** |
| 4 | Resume optimization | Reflection, iterative refinement | Planned |
| 5 | Cover letter generation | Tone control, template + generation hybrid | Planned |
| 6 | Company research | Tool calling, web search | Planned |
| 7 | Job discovery | Official APIs, user-provided data (no scraping) | Planned |
| 8 | Memory + feedback loop | Long-term memory, learning from feedback | Planned |
| 9 | Interview preparation | Multi-step planning, structured curricula | Planned |
| 10 | Application automation | Human-in-the-loop, guardrails | Planned |

Milestones 2–9 are directional, not committed. Each depends on eval results from the previous milestone.

## Milestone selection criteria

A milestone is ready to start when:

1. The previous milestone has a working eval harness
2. Eval results show where the current approach plateaus
3. The new concept solves a **measured** problem, not a hypothetical one

## Completed work (pre-M1)

- [x] Project scaffolding (FastAPI, PostgreSQL, Alembic, Docker)
- [x] CRUD for Profile, Job, MatchAnalysis
- [x] Documentation structure
