# Refactor Plan

Last updated: 2026-07-29

Incremental refactor to improve structure and test coverage without changing product behavior. Each phase is one or more small PRs; evals and unit tests must stay green.

## Principles

- Behavior-preserving refactors only
- Thin API/components, logic in services
- Delete dead code before adding abstractions
- Test boundaries (API smoke + golden evals), not every helper

## Phases

| Phase | Status | Scope |
|-------|--------|-------|
| **0 — Baseline** | Done | `tests/conftest.py`, API smoke tests, this doc |
| **1 — Dead code** | Done | Removed batch/cascade matcher, `ResearchPlan`, orphan prompts |
| **2 — Backend layering** | Done | Split API routers, `match/` package, schema layout |
| **3 — Backend quality** | Next | Exception handlers, remove `HTTPException` from services, httpx pooling |
| **4 — Frontend structure** | Planned | Hooks (`usePolling`, `useMatchAnalysis`), `RequireProfile`, split `JobDetailPage` |
| **5 — Types & observability** | Planned | OpenAPI typegen, optional request IDs |
| **6 — Testing pyramid** | Ongoing | Expand API integration tests after route split |

## Phase 0 deliverables

- Shared fixtures: `mock_db_session`, `mock_llm_client`, `api_client`
- Smoke tests: `/health`, list/get endpoints per domain, settings, LLM models
- No production code changes

## Success metrics (after phases 1–4)

- No production module > ~300 lines (except prompts)
- No cross-imports of private `_format_*` helpers
- API routes split by domain; matcher decomposed
- Frontend: one polling hook, one profile guard
- Dead batch/plan code removed

See [project-status.md](project-status.md) for product roadmap (M7+).
