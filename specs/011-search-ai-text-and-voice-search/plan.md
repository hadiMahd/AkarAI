# Implementation Plan: Search, AI Text Search, and Voice Search

**Branch**: `011-search-ai-text-and-voice-search` | **Date**: 2026-06-14 | **Spec**: [spec.md](./spec.md)

**Input**: Feature specification from `/specs/011-search-ai-text-and-voice-search/spec.md`

## Summary

Build a unified listing search flow where manual filters, AI text search, and Azure Whisper voice transcription all produce the same confirmed search filter contract before listing results are queried. The implementation extends the existing public listing search and search-log foundations with a canonical `SearchIntent`, real supported filters for parking and floor, LLM-based filter extraction behind the existing chat provider interface, Azure Whisper behind the existing STT provider interface, privacy-safe search logs, separate Redis-backed rate limits, and user-app confirmation UI. Area expansion and TTS are intentionally excluded from this phase.

## Technical Context

**Language/Version**: Python 3.11 for backend/admin; TypeScript ^5.5.0 for React apps

**Primary Dependencies**: FastAPI, React, Streamlit, PostgreSQL + pgvector, Redis, MinIO, Azure OpenAI chat via the existing `ChatProvider`, Azure Whisper via the existing `STTProvider`, PII/secret redaction utilities, TanStack Query, existing UI primitives

**Storage**: PostgreSQL for search logs and listing search source data; Redis for listing search cache and separate manual/AI/voice rate-limit keys; MinIO is not used by this feature except as existing listing media storage

**Testing**: Backend service unit tests, API integration tests for search intent/transcription/listing search contracts, rate-limit tests, privacy/redaction tests, and user-app component tests. No e2e browser automation in this phase.

**Target Platform**: local Docker Compose

**Project Type**: Modular monolith web platform with background workers available but not required for this synchronous search flow

**Performance Goals**: Search responses remain paginated and bounded to `page_size <= 100`. Manual, AI text, and voice flows must preserve confirmed filter state, confirmation gating, and clear fallback behavior under local development conditions.

**Constraints**: No buyer-to-agency real-time chat; homepage AI remains search-only; no area expansion in this phase; no TTS/spoken summaries; provider logic stays behind AI provider interfaces; search logs must be redacted and bounded; secrets remain Vault-backed through central settings.

**Scale/Scope**: Public user listing search across active public listings, with manual filters, AI text extraction, voice transcription/extraction, confirmation UI, search logs, and per-mode rate limiting.

## Constitution Check

- **Fixed stack**: Uses React + TypeScript, FastAPI + Python, PostgreSQL, Redis, existing MinIO listing media, Azure OpenAI chat, and Azure Whisper. No new stack component is introduced.
- **Architecture**: Preserves the modular monolith. Search orchestration stays under `backend/app/search/`; listing result queries continue through `backend/app/listings/`; provider-specific STT/chat code stays under `backend/app/ai/`. No DAO layer or service split.
- **Product boundaries**: Adds homepage/listing search features only. Does not add buyer-to-agency chat, listing match scores, persona profiling, generated replies, inquiry creation, or viewing booking.
- **Tenant/RBAC**: Public search only exposes active public listing fields. Search logs avoid tenant-private data and store optional user context only when authenticated. Agency-private policy RAG remains untouched.
- **RAG/search**: Manual search remains direct DB filtering. AI text and voice search produce a confirmed filter object before DB search. Area expansion is excluded and future area RAG remains separate from agency policy RAG. Unresolved vague locations may continue as searches with no location filter.
- **Reliability/security/performance**: Adds separate rate limits for manual, AI text, and voice search. Uses redaction for user-provided text in logs. Keeps result sets paginated and listing cache keys based on confirmed filters.
- **Testing/quality**: Requires service, API, rate-limit, redaction, and user-app component tests. No e2e scope per user direction.

## Project Structure

### Documentation (this feature)

```text
specs/011-search-ai-text-and-voice-search/
├── plan.md
├── research.md
├── data-model.md
├── quickstart.md
├── contracts/
│   └── search-api.md
└── tasks.md
```

### Source Code (repository root)

```text
backend/
├── app/
│   ├── ai/
│   │   ├── providers.py
│   │   ├── registry.py
│   │   └── azure_openai.py
│   ├── search/
│   │   ├── router.py
│   │   ├── service.py
│   │   ├── repository.py
│   │   ├── schemas.py
│   │   └── models.py
│   └── listings/
│       ├── router.py
│       ├── query_service.py
│       └── schemas.py
└── tests/
    ├── unit/
    │   ├── test_search_intent.py
    │   ├── test_ai_search_extraction.py
    │   └── test_voice_search.py
    └── integration/
        └── test_search_api.py

apps/
└── user/
    └── src/
        ├── features/
        │   ├── listings/
        │   └── search/
        └── pages/
            └── listings/
```

**Structure Decision**: Extend the existing `search` module for intent/extraction/logging contracts and keep final listing result execution in the existing `listings` module. The user app owns the search form, AI text entry, voice recorder, confirmation panel, and URL filter state.

## Complexity Tracking

| Violation | Why Needed | Simpler Alternative Rejected Because |
|-----------|------------|-------------------------------------|
| None | N/A | N/A |
