# Security Policy

## Supported versions

Security fixes are applied to the latest code on the `main` branch. There are no
long-term support releases yet — please run a recent commit when deploying.

| Version | Supported |
| ------- | --------- |
| `main`  | Yes       |
| Older tags / forks | No |

## Reporting a vulnerability

**Please do not report security vulnerabilities in public GitHub issues.**

If you discover a security issue, report it privately using one of these channels:

1. **[GitHub Security Advisories](https://github.com/semirturgay/ai-career-os/security/advisories/new)** (preferred)
2. Email: [semir.turgay@gmail.com](mailto:semir.turgay@gmail.com) with subject
   `AI Career OS security`

Include:

- Description of the vulnerability and potential impact
- Steps to reproduce (proof of concept if available)
- Affected components (API route, frontend, dependency, etc.)
- Your environment (version/commit, deployment setup) if relevant

You should receive an acknowledgment within **72 hours**. We will work with you
on validation, fix timeline, and coordinated disclosure when appropriate.

## Scope

In scope:

- Authentication, authorization, or data exposure bugs in this repository
- Injection, SSRF, or unsafe deserialization in API handlers
- Secrets leakage via logs, responses, or committed files
- Dependency vulnerabilities with a demonstrable exploit path in this app

Out of scope:

- Denial-of-service against a local dev instance without broader impact
- Social engineering or physical attacks
- Issues in third-party LLM providers, job boards, or search engines
- Missing security headers on a local-only development setup
- Vulnerabilities in dependencies with no practical exploit in our usage (still
  welcome — we may track them separately)

## Security practices for contributors

- API keys entered in the Settings UI are stored server-side and must never be
  returned to the browser or logged.
- Do not commit `.env`, credentials, or real user documents.
- Use parameterized queries / ORM patterns — no raw SQL with untrusted input.
- Treat LLM outputs as untrusted when rendering in the UI.
- Run `uv sync` and keep lockfiles updated; report supply-chain concerns promptly.

## Safe harbor

We appreciate responsible disclosure. We will not pursue legal action against
researchers who report issues in good faith and follow this policy.
