# EXTRA_PHASES.md — Post-Core Feature Track

## Purpose

This file tracks additional feature phases that should be implemented after the current core planned phases.

These phases are intentionally kept separate from the main `specs/` track so the core roadmap stays clean while extra work remains spec-driven and branch-scoped.

## Execution Strategy

Keep this simple:

1. Build quality gates first.
2. Add the listing-page user agent on top of the existing lead and viewing flows.
3. Add streaming for chatbot and RAG surfaces.
4. Add semantic caching only after AI behavior and eval baselines are stable.

## Extra Phase Order

### 001 — Quality Pipeline

- Branch: `extra/001-quality-pipeline`
- Directory: `extra-specs/001-quality-pipeline/`
- Scope:
  - CI/CD
  - `pre-commit`
  - deterministic test/lint/type gates
  - RAGAS eval runner integration
  - split deterministic CI checks from optional/live AI evals

### 002 — Listing Page User Agent

- Branch: `extra/002-listing-page-user-agent`
- Directory: `extra-specs/002-listing-page-user-agent/`
- Scope:
  - user-facing AI agent on listing detail page
  - assist with inquiry submission
  - assist with viewing booking
  - reuse existing lead and viewing APIs
  - explicit user confirmation before any mutation
  - user-app cleanup so profile identity details stay on the profile page instead of leaking into inquiry and viewing activity surfaces

### 003 — Streaming AI Responses

- Branch: `extra/003-streaming-ai-responses`
- Directory: `extra-specs/003-streaming-ai-responses/`
- Scope:
  - stream answer output for RAG and chatbot-style surfaces
  - apply to existing agency RAG chat first
  - keep a reusable backend/frontend pattern for future chat surfaces like the listing-page user agent
  - preserve citations, debug data, and guardrail behavior while streaming
  - do not block ordinary non-streaming fallbacks

### 004 — Semantic Cache

- Branch: `extra/004-semantic-cache`
- Directory: `extra-specs/004-semantic-cache/`
- Scope:
  - Redis-backed semantic cache
  - vector similarity lookup
  - TTL and invalidation policy
  - clear separation between semantic cache and source-of-truth DB results
  - cache only AI/retrieval behavior, never transactional truth

## Rules

- Each extra phase gets its own branch.
- Each extra phase is implemented from its own `extra-specs/<phase>/` directory.
- Each extra phase keeps at least:
  - `plan.md`
  - `tasks.md`
- Do not merge streaming or semantic caching work into earlier feature branches.
- Do not let the listing-page user agent create a parallel source of truth for leads or viewings.
- Do not let RAGAS or semantic caching hide regressions in uncached retrieval/generation behavior.
