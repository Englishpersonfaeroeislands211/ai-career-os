# Milestones

Incremental build plan. Each milestone adds one capability and is validated before moving on.

## Roadmap

| # | Milestone | AI concepts | Status |
|---|-----------|-------------|--------|
| 0 | Resume extraction | Structured outputs, human review | **Done** |
| 1 | [Explain the match](m1-explain-the-match.md) | Structured outputs, prompt engineering, evals | **Done** |
| 2 | [Job structuring from paste](m2-job-intake.md) | Structured outputs, prompt engineering | **Done** |
| 3 | [Match on job insert](m3-match-on-intake.md) | Background tasks, intake-time matching | **Done** |
| 4 | Resume optimization | Reflection, iterative refinement | **Next** |
| 5 | Cover letter generation | Tone control, template + generation hybrid | Planned |
| 6 | Company research | Tool calling, web search | Planned |
| 7 | Job discovery | Official APIs, user-provided data (no scraping) | Planned |
| 8 | Memory + feedback loop | Long-term memory, learning from feedback | Planned |
| 9 | Interview preparation | Multi-step planning, structured curricula | Planned |
| 10 | Application automation | Human-in-the-loop, guardrails | Planned |

Milestones 4–10 are directional. Each depends on eval results from the previous milestone.

### Archived experiments

| Doc | What it was | Outcome |
|-----|-------------|---------|
| [M3 batch matching (archived)](m3-batch-matching.md) | Bulk “Analyze all” with comparative LLM batching | Built, then **removed from product** — see [M3 match on intake](m3-match-on-intake.md) |

## M4 — Resume optimization (next)

**Problem:** Match analysis surfaces gaps (“no Kubernetes in production”, “missing fintech domain”). Users need actionable help closing them — not just a score.

**Direction:**

```
MatchResult.gaps
  → LLM suggests bullet rewrites / skill framing
  → user reviews diff
  → optional new profile version
```

**Ready when:**

1. Match-at-intake eval fixtures exist for the primary path
2. M1 match quality is stable on golden resume + job pairs

**Not in scope yet:** auto-apply, multi-version A/B testing, PDF re-generation.

## Milestone selection criteria

A milestone is ready to start when:

1. The previous milestone has a working eval harness
2. Eval results show where the current approach plateaus
3. The new concept solves a **measured** problem, not a hypothetical one

## Completed foundation

- [x] Project scaffolding (FastAPI, PostgreSQL, Alembic, Docker)
- [x] CRUD for Profile, Job, MatchAnalysis
- [x] Provider-agnostic LLM client (cloud + local)
- [x] Version-controlled prompts in `app/prompts/`
- [x] Eval harness with golden fixtures
