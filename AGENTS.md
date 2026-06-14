<!-- SPECKIT START -->
For additional context about technologies to be used, project structure,
shell commands, and other important information, read the current plan
at specs/010-rag-retrieval-area-search/plan.md
<!-- SPECKIT END -->

## Session Summary

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
