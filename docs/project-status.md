# Project Status

Last updated: 2026-07-26

## Overview

AI Career OS is in early development. The CRUD foundation is in place; the AI matching layer is next.

## Implemented

### Stack

- Python 3.12, FastAPI (async), uv (dependency management)
- Vite + React + Tailwind (Match Explorer UI)
- PostgreSQL 16, SQLAlchemy 2.0 (async), Alembic
- Pydantic v2, Docker Compose

### Data model

```
Profile ──┐
          ├── MatchAnalysis (status: pending → completed | failed)
Job ──────┘
```

### API (`/api/v1/`)

| Resource | Endpoints |
|----------|-----------|
| Profiles | CRUD |
| Jobs | CRUD |
| Match analyses | Create, list, get |

`POST /api/v1/match-analyses` creates a record with `status: "pending"`. LLM integration is not yet wired.

### Repository layout

```
ai-career-os/
├── app/
│   ├── main.py
│   ├── config.py
│   ├── db/session.py
│   ├── models/__init__.py       # Profile, Job, MatchAnalysis
│   ├── schemas/__init__.py
│   └── api/routes.py
├── frontend/                    # Vite + React Match Explorer
├── alembic/
├── docs/
├── docker-compose.yml
├── Dockerfile
├── pyproject.toml
└── uv.lock
```

## In progress

| Component | Status |
|-----------|--------|
| Match output schema | Draft (see below) |
| Matcher service (`app/services/matcher.py`) | Not started |
| LLM provider integration | Not started |
| Eval harness | Not started |

## Open questions

- [ ] LLM provider: OpenAI, Anthropic, or local (Ollama)?
- [ ] Final shape of `MatchAnalysis.result` JSON schema
- [ ] Sync vs async execution for match analysis (BackgroundTasks recommended for M1)

## Draft match result schema

Starting point for `MatchAnalysis.result`:

```json
{
  "match_score": 0.72,
  "recommendation": "apply",
  "strengths": [
    {
      "point": "13+ years backend experience exceeds 8+ year requirement",
      "evidence": "Resume: 'Senior Backend Engineer, 2012–present'"
    }
  ],
  "gaps": [
    {
      "point": "No direct Kubernetes production experience mentioned",
      "severity": "minor"
    }
  ],
  "summary": "Strong backend match with minor infra gap. Recommend applying."
}
```

Field definitions:

| Field | Type | Description |
|-------|------|-------------|
| `match_score` | float (0–1) | Overall fit score |
| `recommendation` | enum | `apply`, `maybe`, or `skip` |
| `strengths` | array | Matching points with resume evidence |
| `gaps` | array | Missing or weak areas with severity |
| `summary` | string | Human-readable conclusion |

## Deferred

These are intentionally out of scope until the core matching loop is proven:

- Agent frameworks
- Vector DB / RAG
- Multi-agent orchestration
- Fine-tuning
- Auto-apply
- Job scraping
- Authentication

## Next steps

1. Finalize `MatchAnalysis.result` schema as a Pydantic model
2. Implement matcher service with structured LLM outputs
3. Wire matcher into `POST /api/v1/match-analyses` via background task
4. Add eval harness with 5–10 labeled test cases

See [M1: Explain the Match](milestones/m1-explain-the-match.md) for the full plan.
