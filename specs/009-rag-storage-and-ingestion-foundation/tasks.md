# Tasks: RAG Storage and Ingestion Foundation

**Input**: Design documents from `/specs/009-rag-storage-and-ingestion-foundation/`

**Prerequisites**: plan.md, spec.md, research.md, data-model.md, contracts/

**Tests**: Constitution-required tests are included: API integration tests for endpoints, RBAC tenant-isolation tests, and RAG ingestion tests for chunking logic.

**Organization**: Tasks are grouped by user story to enable independent implementation and testing.

## Format: `[ID] [P?] [Story] Description`

- **[P]**: Can run in parallel (different files, no dependencies)
- **[Story]**: Which user story this task belongs to (e.g., US1, US2, US3)
- Include exact file paths in descriptions

## Path Conventions

- Backend: `backend/app/`, `backend/tests/`
- Frontend: `apps/agency/src/`
- Workers: `workers/handlers/`

---

## Phase 1: Setup (Shared Infrastructure)

**Purpose**: Add new dependencies for this feature.

- [X] T001 [P] Add `pymupdf` and `fastcdc` to `backend/requirements.txt`
- [X] T002 [P] Add `azure-identity` and `azure-ai-openai` to `backend/requirements.txt` for embeddings.

---

## Phase 2: Foundational (Blocking Prerequisites)

**Purpose**: Core database models and migrations that MUST be complete before any user story.

- [X] T003 Create `RagDocument`, `RagPage`, `RagChunk`, `RagRetrievalLog` models in `backend/app/rag/models.py`
- [X] T004 Generate and apply initial Alembic migration for the new RAG tables in `backend/alembic/versions/`.
- [X] T005 [P] Implement `pgvector` extension setup in the Alembic migration script.

---

## Phase 3: User Story 1 - Upload Policy PDFs (Priority: P1)

**Goal**: Agency staff can upload policy PDFs, which are accepted and recorded with a `pending` status.

**Independent Test**: Upload a PDF via the API and verify a `RagDocument` record is created for the correct tenant with `pending` status.

### Tests for User Story 1

- [X] T006 [P] [US1] Create API integration test file `backend/tests/integration/test_rag_upload.py`
- [X] T007 [US1] Write test in `test_rag_upload.py` to verify an authorized user can upload a PDF, get a 202 response, and create a RAG ingestion outbox event in the same transaction as the document metadata.
- [X] T008 [US1] Write RBAC test in `test_rag_upload.py` to ensure a user from another tenant cannot access/see the uploaded document.
- [X] T009 [US1] Write validation tests in `test_rag_upload.py` to ensure non-PDF files and unreadable/scanned-image PDFs are rejected with a 400 error before any accepted document is created.

### Implementation for User Story 1

- [X] T010 [P] [US1] Create `RagDocumentCreate`, `RagDocumentRead` schemas in `backend/app/rag/schemas.py`
- [X] T011 [US1] Implement `create_rag_document` in `backend/app/rag/repository.py` to insert document metadata.
- [X] T012 [US1] Implement `upload_rag_document` in `backend/app/rag/service.py`. It should validate the PDF, save the file to MinIO, create the `RagDocument` record, and create a `rag.document.uploaded` ingestion outbox event in the same database transaction.
- [X] T013 [US1] Create `POST /api/v1/agencies/rag/documents` endpoint in `backend/app/rag/router.py`.

---

## Phase 4: User Story 2 - Ingest Pages and Chunks (Priority: P2)

**Goal**: The system processes the uploaded PDF, extracting pages, creating chunks, and generating embeddings.

**Independent Test**: After a PDF is uploaded, verify that the `RagPage` and `RagChunk` tables are populated, embeddings are generated, and old chunks are orphaned on re-ingestion.

### Tests for User Story 2

- [X] T014 [P] [US2] Create worker test file `workers/tests/test_rag_ingestion.py`
- [X] T015 [US2] Write test in `test_rag_ingestion.py` to verify a `pending` document is processed, creating pages and chunks.
- [X] T016 [US2] Write test in `test_rag_ingestion.py` to confirm re-ingesting an unchanged document does not create duplicate chunks.
- [X] T017 [US2] Write test in `test_rag_ingestion.py` to confirm re-ingesting a modified document orphans the old, now-unused chunks.

### Implementation for User Story 2

- [X] T018 [P] [US2] Create `RagPageCreate`, `RagChunkCreate` schemas in `backend/app/rag/schemas.py`
- [X] T019 [US2] Implement `create_pages_and_chunks` logic in a new file `workers/handlers/rag.py`. This handler will consume the `rag.document.uploaded` outbox event and:
    - Fetch the PDF from MinIO.
    - Use `pymupdf` to extract text page by page.
    - Use `fastcdc` to create child chunks from page text.
    - Use Azure OpenAI client to generate embeddings for chunks.
    - Store `RagPage` and `RagChunk` records in the database.
    - Handle content hashing and orphan logic.
- [X] T020 [US2] Register the `rag.py` handler in the worker's main entrypoint.

---

## Phase 5: User Story 3 - Track Ingestion State (Priority: P3)

**Goal**: Agency staff can see the current ingestion status of their documents.

**Independent Test**: Upload a document and poll the API to observe the status change from `pending` to `processing` to `processed` or `failed`.

### Tests for User Story 3

- [X] T021 [P] [US3] Add tests to `backend/tests/integration/test_rag_upload.py` for `GET` endpoints.
- [X] T022 [US3] Write test to list RAG documents for a tenant with page-based pagination.
- [X] T023 [US3] Write test to get a single RAG document by ID and verify its status.

### Implementation for User Story 3

- [X] T024 [P] [US3] Add `get_rag_document` and paginated `list_rag_documents` methods to `backend/app/rag/repository.py`.
- [X] T025 [US3] Add corresponding `get_rag_document` and paginated `list_rag_documents` methods to `backend/app/rag/service.py`.
- [X] T026 [US3] Implement `GET /api/v1/agencies/rag/documents?page=&page_size=` and `GET /api/v1/agencies/rag/documents/{id}` in `backend/app/rag/router.py`.
- [X] T027 [P] [US3] Create a simple UI in `apps/agency/src/pages/rag/` to list paginated documents and show their status.

---

## Phase 6: Polish & Cross-Cutting Concerns

**Purpose**: Final cleanup and integration.

- [X] T028 [P] Review and add error handling for all new services and endpoints.
- [X] T029 [P] Ensure all new database queries are optimized.
- [X] T030 [P] Final documentation review for the new RAG feature.

## Dependencies

- **US1** is the foundational story.
- **US2** depends on **US1** (a document must be uploaded before it can be ingested).
- **US3** depends on **US1** and **US2** (status tracking requires a document and an ingestion process).

## Parallel Execution

- Within each user story, tasks marked with **[P]** can often be done in parallel. For example, in US1, the tests can be written at the same time as the schemas.
- Foundational DB work (Phase 2) can be done in parallel with writing tests for US1.

## Implementation Strategy

The feature will be delivered incrementally, following the user story phases. User Story 1 provides the core upload capability; subsequent stories build on this foundation to add ingestion and status tracking.
