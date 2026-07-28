# AI Career OS

[![CI](https://img.shields.io/github/actions/workflow/status/semirturgay/ai-career-os/ci.yml?branch=main&label=CI&logo=githubactions&logoColor=white)](https://github.com/semirturgay/ai-career-os/actions/workflows/ci.yml)
[![License: MIT](https://img.shields.io/badge/License-MIT-blue.svg)](LICENSE)

**An open-source AI operating system for career management** — starting with explainable job matching, not black-box auto-apply bots.

Upload a resume PDF, extract structured profile data with an LLM you control, review it, paste job descriptions, and get **automatic explainable match analysis** — score, strengths, gaps, and evidence-backed recommendations.

---

## Table of contents

- [Why this exists](#why-this-exists)
- [Features](#features)
- [How it works](#how-it-works)
- [Tech stack](#tech-stack)
- [Quick start](#quick-start)
- [Configuration](#configuration)
- [Local LLM setup (LM Studio)](#local-llm-setup-lm-studio)
- [Development](#development)
- [Project structure](#project-structure)
- [API overview](#api-overview)
- [Roadmap](#roadmap)
- [Documentation](#documentation)
- [Contributing](#contributing)

---

## Why this exists

Most career tools tell you *what* to do. This project focuses on **why** — structured LLM outputs, human review, and auditable match results.

Built as a learning-friendly codebase for developers who want to understand:

- Provider-agnostic LLM integration (cloud + local)
- Native structured outputs (JSON schema → Pydantic)
- Prompt versioning as plain files
- Human-in-the-loop before data is saved

Long-term vision: an autonomous career assistant that discovers jobs, explains fit with evidence, and helps you act — always with transparency. See [docs/vision.md](docs/vision.md).

---

## Features

- **PDF resume ingestion** — deterministic text extraction with `pypdf`
- **LLM structured extraction** — skills, experience, education, projects into a typed schema
- **Bring your own model** — OpenAI, Anthropic, Groq, Mistral, Together, Azure OpenAI, or **local** (Ollama / LM Studio)
- **Model picker** — fetches available models from your provider
- **Human review** — edit extracted fields before saving
- **Job paste intake** — LLM extracts title, company, requirements from pasted text
- **Match on save** — full detailed analysis runs automatically when you add a job
- **Job pipeline** — home dashboard ranks jobs by match score with polling
- **Explainable match analysis** — LLM compares profile ↔ job with score, strengths, gaps, and evidence
- **Resume optimization** — gap-driven rewrite suggestions from job detail, apply to profile
- **Export resume PDF** — download your profile as a formatted PDF from the profile page
- **Re-analyze** — manual retry on job detail when profile or job changes
- **Version-controlled prompts** — prompts live in `app/prompts/`, not buried in code
- **Eval harness** — golden fixtures for resume extraction and match analysis regression tests

---

## How it works

```mermaid
flowchart LR
    A[PDF upload] --> B[pypdf text]
    B --> C[LLM structured extraction]
    C --> D[Review and edit]
    D --> E[(Profile)]
    F[Paste job] --> G[LLM job extraction]
    G --> H[Save and analyze]
    E --> H
    H --> I[Full match analysis]
    I --> J[Pipeline: ranked jobs + detail view]
```

1. **Extract text** from PDF (no LLM — fast, deterministic)
2. **Structure** resume with your configured LLM (`ResumeExtraction`)
3. **Review** on onboarding — fix anything the model got wrong
4. **Save** profile with raw text + structured JSONB snapshot
5. **Add a job** — paste JD → extract fields → **Save & analyze match**
6. **Match runs in background** — full `MatchResult` (score 0–100, recommendation, strengths/gaps with evidence)
7. **Home pipeline** — jobs ranked by score; job detail for deep dive or Re-analyze

---

## Tech stack

| Layer | Technology |
|-------|------------|
| API | FastAPI (async) |
| Database | PostgreSQL 16 |
| ORM | SQLAlchemy 2.0 (async) |
| Migrations | Alembic |
| Validation | Pydantic v2 |
| PDF | pypdf |
| LLM client | httpx (OpenAI-compatible + structured output) |
| Frontend | Vite, React, TypeScript, Tailwind CSS |
| Package managers | [uv](https://docs.astral.sh/uv/) (Python), [Bun](https://bun.sh) (frontend) |

---

## Quick start

### Prerequisites

- Python 3.12+
- [uv](https://docs.astral.sh/uv/getting-started/installation/)
- Docker (for PostgreSQL)
- Node.js 20+ and [Bun](https://bun.sh) (frontend)
- An LLM provider — cloud API key **or** local LM Studio / Ollama

### 1. Clone and configure

```bash
git clone https://github.com/semirturgay/ai-career-os.git
cd ai-career-os
cp .env.example .env
```

### 2. Start PostgreSQL

```bash
docker compose up db -d
```

### 3. Backend

```bash
uv sync
uv run alembic upgrade head
uv run uvicorn app.main:app --reload
```

API: http://127.0.0.1:8000  
OpenAPI docs: http://127.0.0.1:8000/docs

### 4. Frontend

```bash
cd frontend
bun install
bun run dev
```

App: http://127.0.0.1:5173

### 5. First run

1. Open the app → choose **Local** (LM Studio) or a cloud provider
2. Upload a PDF resume
3. Wait for extraction (local models can take 30–60s)
4. Review structured fields → save profile
5. Add a job — paste description → **Save & analyze match**
6. View ranked pipeline on home; open job detail for strengths, gaps, evidence

> **Note:** Use `127.0.0.1` instead of `localhost` for API URLs on macOS — the Vite proxy and DB URL are configured this way to avoid IPv6 hangs.

### Fresh database / reset migrations

If you had an older dev database from pre-release migrations:

```bash
docker compose down -v
docker compose up db -d
uv run alembic upgrade head
```

---

## Configuration

Environment variables (see [`.env.example`](.env.example)):

| Variable | Default | Description |
|----------|---------|-------------|
| `DATABASE_URL` | `postgresql+asyncpg://career:career@127.0.0.1:5432/ai_career_os` | Async Postgres connection |
| `OPENAI_API_KEY` | — | Optional fallback if not set in Settings UI |
| `ANTHROPIC_API_KEY` | — | Optional fallback |
| Other `*_API_KEY` | — | Provider-specific env fallbacks |

**API keys** entered in the Settings UI are stored server-side in PostgreSQL — never returned to the browser.

Provider and model selection is persisted in the `app_settings` singleton table.

---

## Local LLM setup (LM Studio)

1. Download a model (e.g. Qwen 3.5 9B)
2. Start the **OpenAI-compatible server** in LM Studio (default port `1234`)
3. In onboarding, select **Local** → **LM Studio** preset
4. Base URL: `http://127.0.0.1:1234/v1`
5. Pick your loaded model from the dropdown

Ollama works the same way with the Ollama preset (`http://127.0.0.1:11434/v1`).

Local models may return JSON with non-standard field names — the backend normalizes common variants before validation.

---

## Development

### Tests

```bash
uv run pytest
```

Eval fixtures live in `tests/evals/fixtures/` (resume extraction, job extraction, match analysis, resume optimization). CI runs golden-response checks on every push.

```bash
# Offline golden evals (no API key)
uv run python scripts/run_evals.py

# Optional live LLM evals (configured provider + Postgres)
RUN_LIVE_LLM=1 uv run python scripts/run_evals.py --live
```

See [docs/ai-engineering.md](docs/ai-engineering.md) for the full AI engineering guide.

### Lint

Fast Python linting with [Ruff](https://docs.astral.sh/ruff/) — covers pyflakes, isort import
sorting, pyupgrade, and bugbear in one tool (no separate pylint/isort install needed):

```bash
uv run ruff check app tests scripts alembic
uv run ruff format app tests scripts alembic          # auto-fix formatting
uv run ruff format --check app tests scripts alembic  # CI mode
```

### Pre-commit

Install git hooks to run ruff + tests before each commit:

```bash
uv sync
uv run pre-commit install
uv run pre-commit run --all-files   # verify setup
```

### Frontend build

```bash
cd frontend && bun run build
```

### Docker (API + DB)

```bash
docker compose up --build
```

---

## Project structure

```
ai-career-os/
├── app/
│   ├── api/              # FastAPI routes
│   ├── db/               # SQLAlchemy session
│   ├── models/           # ORM models
│   ├── prompts/          # Version-controlled LLM prompts (.txt)
│   ├── schemas/          # Pydantic models (API + ResumeExtraction + MatchResult)
│   └── services/
│       ├── llm/          # Provider abstraction + generate_structured() client
│       ├── resume_parser.py
│       ├── resume_structurer.py
│       ├── matcher.py
│       └── match_analysis_normalize.py
├── alembic/              # Database migrations (single init migration)
├── frontend/             # Vite + React SPA
├── docs/                 # Architecture, milestones, vision
└── tests/
```

---

## API overview

Base path: `/api/v1`

| Method | Path | Description |
|--------|------|-------------|
| POST | `/profiles/parse-resume` | Upload PDF → text + LLM structured extraction |
| POST | `/profiles` | Create profile |
| GET | `/profiles` | List profiles |
| GET | `/profiles/{id}` | Get profile |
| PATCH | `/profiles/{id}` | Update profile |
| GET | `/profiles/{id}/resume.pdf` | Download profile as PDF |
| DELETE | `/profiles/{id}` | Delete profile |
| POST | `/jobs/parse-text` | Paste JD → structured `JobExtraction` |
| POST | `/jobs` | Create job; optional `profile_id` queues match analysis |
| GET | `/jobs` | List jobs |
| GET | `/jobs/{id}` | Get job |
| PATCH | `/jobs/{id}` | Update job |
| DELETE | `/jobs/{id}` | Delete job |
| POST | `/match-analyses` | Manual re-analyze (background LLM matcher) |
| POST | `/match-analyses/{id}/resume-optimization` | Gap-driven resume suggestions |
| POST | `/match-analyses/{id}/cover-letter` | 3-pass cover letter generation |
| GET | `/match-analyses/{id}` | Get analysis status + result |
| GET | `/match-analyses` | List analyses |
| GET | `/settings` | Get LLM provider config |
| PUT | `/settings` | Update LLM provider config |
| POST | `/llm/models` | List models from configured provider |
| GET | `/health` | Health check |

Full interactive docs: http://127.0.0.1:8000/docs

---

## Roadmap

| Milestone | Status | Description |
|-----------|--------|-------------|
| **M0** Resume extraction | Done | PDF → LLM structured output → review → save |
| **M1** Explain the match | Done | Evidence-based match analysis with eval harness |
| **M2** Job intake | Done | Paste JD → structured extraction → review |
| **M3** Match on job insert | Done | Full analysis automatically when a job is saved |
| **M4** Resume optimization | Done | Gap-driven suggestions with review before apply |
| **M5** Progressive match + cover letter | Done | Fast screen at intake; 3-pass cover letter chain |
| **M6** Company research | **Next** | Employer context via tool calling |

Details: [docs/milestones/](docs/milestones/README.md) · Current state: [docs/project-status.md](docs/project-status.md)

### Design notes

- **JSONB first** for LLM output while schemas evolve; promote to relational tables when query patterns stabilize
- **No LangChain** — thin `LLMClient` protocol + httpx adapters
- **Prompts as files** — `app/prompts/*.txt`, loaded via `load_prompt()`

---

## Documentation

| Doc | Contents |
|-----|----------|
| [docs/ai-engineering.md](docs/ai-engineering.md) | **Evals, tracing, structured outputs, patterns** |
| [docs/vision.md](docs/vision.md) | Long-term product vision |
| [docs/architecture.md](docs/architecture.md) | System design and data model |
| [docs/project-status.md](docs/project-status.md) | Current state and what's next |
| [docs/milestones/m3-match-on-intake.md](docs/milestones/m3-match-on-intake.md) | M3 spec (current product flow) |
| [docs/milestones/README.md](docs/milestones/README.md) | Full roadmap |

---

## Contributing

Contributions welcome — especially around:

- LLM provider adapters (Anthropic native structured output, Google Gemini)
- Extraction and match quality — eval fixtures (sample resumes/jobs + expected fields)
- Resume optimization and cover letter (M4–M5)
- Documentation and DX improvements

### Commit messages

Use [Conventional Commits](https://www.conventionalcommits.org/):

```
<type>(<scope>): <short description>

[optional body explaining why]
```

Common types: `feat`, `fix`, `docs`, `test`, `refactor`, `chore`, `ci`

Examples:

```
feat(matcher): add explainable match analysis with eval harness
docs(readme): update roadmap for completed M1
fix(api): poll match analysis until terminal status
```

1. Fork the repo
2. Create a feature branch
3. Run `uv run pytest` and `uv run ruff check app tests`
4. Open a pull request with a clear description

Please do not commit `.env` files or API keys.

---

## License

[MIT](LICENSE) — Copyright (c) 2026 Semir Turğay
