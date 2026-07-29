# Milestone 6: Company research

**Status:** Done  
**Concepts:** Bounded agent loop, tool use, web search, source-grounded synthesis

## Problem

Match analysis explains fit against the JD, but candidates lack **employer context**: culture, recent news, interview prep angles, and potential red flags. That information lives on the web, not in the resume or job description.

## Solution

User-triggered research on job detail — a **bounded agent loop** in Python (not LangChain/ReAct):

```
Job (company, title, description)
  → loop (max 5 steps, max 5 searches):
      LLM: ResearchAgentStep → search | synthesize
      if search: web_search(query) → accumulate snippets
      if synthesize or limits hit: break
  → LLM: CompanyBriefContent (synthesis from snippets only)
  → attach sources + researched_at in code
  → persist on jobs.company_brief JSONB
```

The agent decides **one query at a time** and can stop early when it has enough evidence. **Sources are never LLM-generated URLs** — they come from search results attached in code.

## API

`POST /api/v1/jobs/{job_id}/company-research`

Runs synchronously (like cover letter). Returns `CompanyBrief` and caches on the job.

`GET /api/v1/jobs/{id}` includes optional `company_brief` on `JobRead`.

## Schema

| Model | Role |
|-------|------|
| `ResearchAgentStep` | LLM output per turn — `search` (with query) or `synthesize` |
| `CompanyBriefContent` | LLM synthesis — summary, signals, news |
| `SearchResult` | Tool output — title, url, snippet |
| `CompanyBrief` | API response — content + sources + `researched_at` |

`ResearchPlan` remains in schema for reference; the product path uses the agent loop.

## Product choices

| Decision | Rationale |
|----------|-----------|
| User-triggered, not on job save | Avoid surprise latency/cost |
| Bounded agent vs fixed plan | Agent can stop early or search again for gaps |
| DuckDuckGo default | No API key for local dev |
| Sources attached in code | Prevent hallucinated URLs |
| Sync POST | Simple UX; research ~5–20s |
| Dedicated `company_brief` column | Separate from intake `raw_metadata` |
| Research tab hidden until full match | Keeps intake focused on fit first |

## Observability

```
agent_step | step=1/5 action=search query="..." rationale="..."
tool_call | operation=web_search provider=duckduckgo ...
LLM call | operation=CompanyBriefContent ...
```

Implementation: `app/services/search/tracing.py`, `app/services/company_research.py`

## Completed

- [x] `SearchClient` protocol + `DuckDuckGoSearchClient`
- [x] `research_company()` bounded agent orchestrator
- [x] Prompts: `company_research_agent.txt`, `company_research_synthesize.txt`
- [x] Migration `002_job_company_brief`
- [x] `POST /jobs/{id}/company-research`
- [x] `CompanyResearchPanel` + job detail tabs
- [x] Golden eval suite with mocked search (`company_research/fintech_labs`)
- [x] Unit tests for agent loop, storage, DuckDuckGo mapping

## Not done (follow-ups)

- [ ] Tavily/Serper in settings (production search provider)
- [ ] Inject company brief into cover letter context
- [ ] Live eval with real search (optional, flaky in CI)
- [ ] Research history (multiple briefs per job)
- [ ] A/B eval: fixed plan vs agent on real search

## Next

[M7 — Job discovery](README.md): official APIs for job feeds — no scraping.
