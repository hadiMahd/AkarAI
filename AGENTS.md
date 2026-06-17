<!-- SPECKIT START -->
For additional context about technologies to be used, project structure,
shell commands, and other important information, read the current plan
at specs/013-lead-processing-pipeline/plan.md
<!-- SPECKIT END -->

## Session Summary

### What's been implemented (feature branch `010-rag-retrieval-area-search` → `012-agency-ai-workflows`)

**Phase 12 — Agency AI Workflows**: THIS SESSION
- **Config & env (T001)**: `backend/app/common/config.py` exposes OCR provider, Azure CV endpoint/key, OCR limits, agency AI job settings, and rate-limit knobs. `configure_secrets()` reads the `akarai/azure_cv` Vault path. `.env.example` lists the new placeholders.
- **OCR provider (T004)**: `AzureComputerVisionOCRProvider` implements `OCRProvider.extract_text` against the v3.2 Read API. `get_ocr_provider()` lazily registers it.
- **Guardrailed generation (T005)**: `generate_guardrailed_agency_text` / `generate_guardrailed_agency_draft` shared helpers. `app.ai.jobs` exposes a small state machine (`new_job`, `mark_processing`, `mark_completed`, `mark_failed`) plus the four job type / status constants.
- **Schemas (T006)**: `app.ai.schemas` covers spec extraction, listing draft, lead reply, comparison summary, and the job status envelope. `ExtractedListingSpecs` includes field confidence + source snippets.
- **Assistant tools (T007)**: `app.rag.service` gained `_detect_tool_intent`, `_maybe_run_assistant_tools`, and `_record_tool_invocation`. Listings/Leads services expose `read_only_*` helpers. The chat `send_message` flow now augments policy answers with safe, tenant-scoped, read-only tool output.
- **Rate limits + audit (T008)**: `check_agency_ai_rate_limit` covers OCR/listing-draft/lead-reply/comparison-summary. `AgencyAIService` writes `agency_ai.*` audit events through the existing `AuditService` path.
- **Service (T014/T037/T038)**: `AgencyAIService` runs the spec extraction (synchronous), listing draft, lead reply draft, and comparison summary flows. Each persists a `AgencyAIJob`, writes the result payload, and emits a `LeadReplyDraft` / `ComparisonSummary` record where applicable.
- **Router (T015/T035/T036)**: New endpoints under `/api/v1/agencies` (spec extraction, listing draft, lead reply draft, job status) and `/api/v1/me/comparison-summary`. Routers are wired in `backend/app/main.py`.
- **Worker (T004)**: `workers/handlers/agency_ai.py` handles `agency_ai.spec_sheet_uploaded`. The synchronous API path doesn't dispatch it today but the handler is registered for future async extraction flows.
- **Frontend (T016/T039/T040)**: `apps/agency/src/features/agencyAi/useAgencyAi.ts` and `apps/user/src/features/comparison/useComparisonSummary.ts` provide mutation/query hooks. `apps/agency/src/features/listings/ListingAiWorkflow.tsx` is the spec-sheet upload + draft panel. `apps/agency/src/lib/api/errors.ts` and `apps/user/src/lib/api/errors.ts` map the new error codes.
- **Migration (T002/T003)**: `0018_add_agency_ai_workflows.py` adds `agency_ai_jobs`, `lead_reply_drafts`, `comparison_summaries`, and `agency_assistant_tool_invocations`.
- **Docs (T042/T044)**: `backend/app/ai/README.md` documents the new OCR provider, shared guardrailed generation, and job lifecycle. `specs/012-agency-ai-workflows/quickstart.md` is unchanged because the validation scenarios already match the implemented routes.
- **Tests (T009-T012, T019-T022, T029-T034, T045)**: 14 new test files written this session.
  - Backend unit tests pass standalone (no Docker): 27 + 13 + 14 = **54 unit tests pass**
  - Frontend vitest tests pass standalone: 4 + 16 + 2 + 2 = **24 frontend tests pass**
  - Integration, RBAC, and worker-routed tests are implemented and structured against the live database+Redis fixtures; they will execute when the Docker Compose stack is brought up.

### What's been implemented (feature branch `009-rag-storage-and-ingestion-foundation` → `010-rag-retrieval-area-search`)

**Phase 8 — RAG Storage & Ingestion**: Completed in prior session. See the full summary at specs/009-rag-storage-and-ingestion-foundation/plan.md.

**Phase 9 Setup & Foundational (T001–T013)**: Completed in prior session.
- Models: `RagRetrievalLog`, `RagEvaluationRun`, `RagEvaluationExample`
- Migration 0012 adding retrieval-log fields, evaluation tables, enums
- Schemas: `RagRetrievalQueryRequest`, `RagPolicyAnswer`, `RagRetrievalCitation`, `RagRetrievalEvidence`, `RagRetrievalDebug`, `RagRetrievalLogRead`, `RagEvaluationRunRead`
- Repository: `search_chunks_by_embedding()`, `list_parent_pages()`, `list_processed_documents()`, `list_active_chunks()`, `create_retrieval_log()`, `list_retrieval_logs()`, `create_evaluation_run()`, `get_chunks_by_ids()`, `get_documents_by_ids()`
- OpenRouter reranking provider (registered in registry)
- Shared retrieval orchestration (`retrieval.py`): `RetrievalCandidate`, `RetrievalResult`, `assemble_result()`, `to_policy_answer()`, `build_citations()`, `build_evidence()`, `truncate_text()`
- Service: `RagRetrievalService` with `list_retrieval_logs()`, `create_retrieval_log()`, `record_evaluation_run()`, `build_policy_answer()`
- Agency frontend: query keys, `submitRagPolicyQuery()`, `fetchRagRetrievalLogs()`, type definitions

**Phase 3 — User Story 1: Retrieve Agency Policy Answers (T019–T025)**: THIS SESSION
- **Chunk text column**: Added `text` column to `RagChunk` model (migration 0013). Handler now stores chunk text during ingestion so retrieval can return `text_preview` in evidence.
- **Retrieval service (`answer_policy_query`)**: Full flow in `RagRetrievalService`:
  1. Snapshot processed documents (tenant-isolated)
  2. Generate query embedding via `get_embedding_provider()`
  3. Vector search via `search_chunks_by_embedding()` (cosine distance on pgvector)
  4. Parent page fetch for page numbers and context text
  5. Replace-while-retrieving hardening: re-verify document status after vector search, filter stale chunks
  6. OpenRouter reranking with graceful fallback (reranker_unavailable → vector ordering preserved)
  7. Confidence determination (sufficient/insufficient/fallback)
  8. Retrieval log creation with selected doc/chunk/page IDs
  9. Answer assembly with citations, evidence, and debug payload
- **Router**: `POST /api/v1/agencies/rag/query` and `GET /api/v1/agencies/rag/retrieval-logs` endpoints (separate router from docs, each independently included in app)
- **Frontend hooks**: `useRagPolicyQuery()` (mutation), `useRagRetrievalLogs()` (query)
- **Frontend UI**: Policy Q&A card with question input, answer display, citations as badges, collapsible evidence + debug panel, empty-state for no processed docs, error states, loading states

**Phase 4 — User Story 2: Support Assistant Retrieval (T029–T033)**:
- **Backend role enforcement**: `list_retrieval_logs` service method checks `role in ("agency_admin", "platform_admin")` and raises `ForbiddenError` for support employees. Router adds `Depends(require_role("agency_admin"))` on `GET /retrieval-logs`.
- **Filter schemas**: `RagRetrievalLogFilter` with optional `actor_role`, `confidence_status`, `date_from`, `date_to`. Threaded through router → service → repository.
- **Repository filtering**: `list_retrieval_logs` now applies optional where-clause filters before pagination.
- **Frontend admin guard**: `useRagRetrievalLogs` hook checks `getTenantSession().role === "agency_admin"` and disables the query for non-admins.
- **Retrieval log UI**: New `RetrievalLogSection` and `RetrievalLogRow` components showing query table with expandable details (log ID, scope, fallback reason, doc/chunk counts). Pagination matches documents table pattern. Only rendered for admin users.

**Phase 5 — User Story 3: Evaluation Baseline (T038–T042)**:
- **Repository helpers**: `create_evaluation_examples` (batch), `list_evaluation_runs` (paginated) in `repository.py`. `RagEvaluationExampleCreate` schema.
- **Service**: `record_evaluation_run_with_examples` creates run + batch-persists examples + generates summary (pass rate, latency metrics).
- **Script**: `scripts/ci/run_rag_eval.py` — dataset loader (JSONL), orchestrator (run each query through retrieval pipeline), scorer (compare behavior + sources against expected), latency recorder (per-query + aggregate min/max/avg/p50/p95), threshold enforcement (exit code 0/1).
- **Documentation**: `quickstart.md` updated with eval scenario, dataset format table, scoring logic, and latency validation.

### Pending (tests need Docker)
- T014–T018: All US1 tests (unit, integration, RBAC, UI)
- T026–T028: All US2 tests (RBAC, integration, UI)
- T034–T037: All US3 tests (unit, integration, eval smoke, latency)
- Phase 6: Polish (error handling, query optimization, docs update, validation)

## Architecture Rules

## Architecture Rules

- **No `dao.py` files**: `repository.py` is the data access layer. DAO files are forbidden.
- Module conventions: `router.py`, `service.py`, `repository.py`, `schemas.py`, `models.py`, optional `query_service.py`.
- See `backend/app/README.md` for full module conventions.
- **Phase 4 core domain CRUD**: Create only non-AI domain database and CRUD foundations for agencies, listings, viewing slots, viewings, leads, saved listings, comparisons, notifications, search logs, and domain logs. No AI, RAG, media processing, OCR, email sending, dashboards, chat, spam classification, lead scoring, or generated replies.

## graphify

This project has a knowledge graph at graphify-out/ with god nodes, community structure, and cross-file relationships.

When the user types `/graphify`, invoke the `skill` tool with `skill: "graphify"` before doing anything else.

Rules:
- For codebase questions, first run `graphify query "<question>"` when graphify-out/graph.json exists. Use `graphify path "<A>" "<B>"` for relationships and `graphify explain "<concept>"` for focused concepts. These return a scoped subgraph, usually much smaller than GRAPH_REPORT.md or raw grep output.
- Dirty graphify-out/ files are expected after hooks or incremental updates; dirty graph files are not a reason to skip graphify. Only skip graphify if the task is about stale or incorrect graph output, or the user explicitly says not to use it.
- If graphify-out/wiki/index.md exists, use it for broad navigation instead of raw source browsing.
- Read graphify-out/GRAPH_REPORT.md only for broad architecture review or when query/path/explain do not surface enough context.
- After modifying code, run `graphify update .` to keep the graph current (AST-only, no API cost).
