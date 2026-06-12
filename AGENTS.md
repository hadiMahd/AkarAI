<!-- SPECKIT START -->
For additional context about technologies to be used, project structure,
shell commands, and other important information, read the current plan
at specs/008-media-pipeline-and-listing-image-processing/plan.md
<!-- SPECKIT END -->

## Session Summary

### What's been implemented (feature branch `008-media-pipeline-and-listing-image-processing`)

**HF token vault flow** — Worker reads `hf_token` from Vault path `akarai/ai` via `configure_secrets()`. Vault seed script writes token from `.env`. Worker `_load_secrets()` runs at startup before handler imports. Fail-closed: missing/misconfigured token rejects with 401.

**Agency listing 2-step create flow** — No draft/publish/edit language in UI. Submit creates listing (inactive) + uploads staged photos → explicit publish confirmation → "Confirm Publish" sets active. Edit mode simplified to Save Changes + optional Publish button. Media manager supports staged multi-file selection with per-file preflight checking.

**Media UX fix** — 
- Backend: `preview_url` on agency photo listing (derivative preferred, original fallback). `thumbnail_url` on `PublicListingResponse`. Batch-efficient `build_thumbnail_map()` (2 queries for N listings).
- Agency frontend: edit mode multi-file staged upload (multi-select, preflight, batch "Upload All"). Current Photos renders actual image previews from `preview_url`, processing placeholder when null.
- User frontend: `ListingCard` has fixed image area with `thumbnail_url` or muted placeholder. `ListingDetailPage` shows full media gallery from `/listings/{id}/media` endpoint, falls back to single thumbnail.

### Verification
- Backend: 276 pass (4 pre-existing unrelated failures)
- Agency frontend: 23/23 tests, `tsc --noEmit` clean, build succeeds
- User frontend: 57/57 tests, `tsc --noEmit` clean, build succeeds

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
