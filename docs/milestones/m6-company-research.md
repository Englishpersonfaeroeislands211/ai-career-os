# Milestone 6: Company research

**Status:** Done (MVP)  
**Concepts:** Orchestrated tool use, web search, source-grounded synthesis

## Problem

Match analysis explains fit against the JD, but candidates lack **employer context**: culture, recent news, interview prep angles, and potential red flags. That information lives on the web, not in the resume or job description.

## Solution

User-triggered research on job detail — **orchestrated tool use**, not an open agent:

```
Job (company, title, description)
  → LLM: ResearchPlan (2–3 search queries)
  → web_search tool (DuckDuckGo, max 3 queries × 5 results)
  → LLM: CompanyBriefContent (synthesis from snippets only)
  → attach sources + researched_at in code
  → persist on jobs.company_brief JSONB
```

Python owns the control flow. The LLM plans queries and synthesizes; **sources are never LLM-generated URLs**.

## API

`POST /api/v1/jobs/{job_id}/company-research`

Runs synchronously (like cover letter). Returns `CompanyBrief` and caches on the job.

`GET /api/v1/jobs/{id}` includes optional `company_brief` on `JobRead`.

## Schema

| Model | Role |
|-------|------|
| `ResearchPlan` | LLM output — 2–3 search queries |
| `CompanyBriefContent` | LLM synthesis — summary, signals, news |
| `SearchResult` | Tool output — title, url, snippet |
| `CompanyBrief` | API response — content + sources + `researched_at` |

## Product choices

| Decision | Rationale |
|----------|-----------|
| User-triggered, not on job save | Avoid surprise latency/cost |
| DuckDuckGo default | No API key for local dev |
| Sources attached in code | Prevent hallucinated URLs |
| Sync POST | Simple UX; research ~5–15s |
| Dedicated `company_brief` column | Separate from intake `raw_metadata` |

## Observability

Tool calls log separately from LLM calls:

```
tool_call | operation=web_search provider=duckduckgo query="FinTech Labs culture" latency_ms=842 results=5 status=ok
LLM call | operation=ResearchPlan ...
LLM call | operation=CompanyBriefContent ...
```

Implementation: `app/services/search/tracing.py`

## Completed

- [x] `SearchClient` protocol + `DuckDuckGoSearchClient`
- [x] `research_company()` orchestrator
- [x] Prompts: `company_research_plan.txt`, `company_research_synthesize.txt`
- [x] Migration `002_job_company_brief`
- [x] `POST /jobs/{id}/company-research`
- [x] `CompanyResearchPanel` on job detail
- [x] Golden eval suite with mocked search (`company_research/fintech_labs`)
- [x] Unit tests for pipeline, storage, DuckDuckGo mapping

## Not done (follow-ups)

- [ ] Tavily/Serper in settings (production search provider)
- [ ] Inject company brief into cover letter context
- [ ] Live eval with real search (optional, flaky in CI)
- [ ] Research history (multiple briefs per job)

## Next

[M7 — Job discovery](README.md): official APIs for job feeds — no scraping.
