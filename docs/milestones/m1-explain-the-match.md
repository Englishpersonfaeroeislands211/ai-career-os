# Milestone 1: Explain the Match

**Status:** In progress  
**Concepts:** Structured outputs, prompt engineering, context engineering, evals

## Problem

Given a job description and a resume, produce a structured explanation of *why* this job is or isn't a match — with evidence, not vibes.

This is the atomic unit of the entire product. Everything else (scoring, cover letters, interview prep) builds on **explainable matching**.

## Why this first

- Smallest vertical slice with real AI engineering decisions
- Forces structured outputs, prompt design, and eval thinking
- No external dependencies (no job boards, no scraping, no vector DB)
- Testable with real resume + job description data

## Approaches considered

### A. Single LLM call → structured JSON (chosen)

```
Input:  resume text + JD text
Output: { match_score, strengths[], gaps[], recommendation, evidence[] }
```

| Pros | Cons |
|------|------|
| Simple, debuggable | Quality ceiling depends on prompt |
| Fast to iterate | No multi-step reasoning |
| Low cost (~$0.01/request) | |

### B. Chain: extract → compare → synthesize

```
Step 1: Extract requirements from JD
Step 2: Extract skills/experience from resume
Step 3: Compare and explain
```

| Pros | Cons |
|------|------|
| Interpretable intermediate steps | 3x latency/cost |
| Easier to eval each step | Error propagation between steps |

### C. Agent with tools

| Pros | Cons |
|------|------|
| Flexible | Overkill for M1 |
| | Hard to eval |
| | Premature |

### Decision

Start with A and an eval harness from day one. If quality plateaus, eval data will show which step in B would help.

## Completed

- [x] CRUD foundation (Profile, Job, MatchAnalysis)
- [x] `POST /api/v1/match-analyses` creates a pending analysis record
- [x] `MatchAnalysis.result` JSONB column ready for LLM output

## Remaining work

### 1. Output schema

Define the JSON schema for `MatchAnalysis.result`. See [project status](../project-status.md) for the current draft.

### 2. Matcher service

```
app/services/matcher.py
├── analyze_match(profile, job) → MatchResult
├── Uses LLM with structured output
└── Returns validated Pydantic model
```

### 3. API integration

| Approach | When to use |
|----------|-------------|
| Sync on create | Fine for M1 dev; blocks request ~2–5s |
| Background task (FastAPI BackgroundTasks) | Better UX; recommended for M1 |
| Task queue (Celery/ARQ) | When you need retries, rate limiting, scale |

### 4. Eval harness

Even 5–10 hand-labeled (profile, job, expected_quality) pairs enable regression testing on prompt changes.

```
tests/evals/
├── test_match_quality.py
├── fixtures/
│   ├── profile_backend_engineer.txt
│   ├── job_senior_python.json
│   └── job_junior_frontend.json
```

## Design notes

### Structured outputs

Career advice must be parseable, testable, and UI-renderable. Use the provider's native structured output API — don't parse free-form JSON with regex.

### Prompt engineering

Prompts are the API contract with the model. They need an eval set behind them — prompt tuning without measurement doesn't scale.

### Context engineering

What goes *into* the prompt matters more than clever phrasing. Structure resume and JD inputs deliberately rather than dumping raw text.

### Evals

Build the eval harness alongside the first LLM integration, not after. Match quality is the core product metric.

## Open questions

- [ ] LLM provider: OpenAI, Anthropic, or local (Ollama)?
- [ ] Output schema: final field list
- [ ] Sync vs async execution for M1

## References

- [Anthropic: Building Effective Agents](https://www.anthropic.com/research/building-effective-agents)
- [OpenAI: A Practical Guide to Building Agents](https://platform.openai.com/docs/guides/agents)
- [Hamming: LLM Evals FAQ](https://hamming.ai/blog/llm-evals-faq)
