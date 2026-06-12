# Feature Specification: RAG Storage and Ingestion Foundation

**Feature Branch**: 009-rag-storage-and-ingestion-foundation

**Created**: 2026-06-12

**Status**: Implemented

**Input**: User description: "phase 8, ask before taking any decision/detail dont assume anything"

## User Scenarios & Testing *(mandatory)*

### User Story 1 - Upload Policy PDFs (Priority: P1)

Agency staff upload policy PDFs so the platform can prepare them for later retrieval and AI use.

**Why this priority**: Policy documents are the source material for all later RAG features.

**Independent Test**: Can be tested by uploading a policy PDF and verifying that the document is accepted, stored, and assigned a visible ingestion status.

**Acceptance Scenarios**:

1. **Given** an authorized agency user has a policy PDF, **When** they upload it, **Then** the document is accepted and recorded as a RAG document for that tenant.
2. **Given** a user uploads a non-PDF file or a scanned image-only file, **When** validation runs, **Then** the upload is rejected with a clear reason and no document is accepted.

---

### User Story 2 - Ingest Pages and Chunks (Priority: P2)

The system breaks each accepted policy PDF into page records and smaller searchable chunks so the document can be prepared for later retrieval.

**Why this priority**: Page and chunk storage is the core foundation for later RAG behavior.

**Independent Test**: Can be tested by uploading a valid policy PDF and verifying that page records, chunk records, and chunk status are created.

**Acceptance Scenarios**:

1. **Given** a valid policy PDF is accepted, **When** ingestion completes, **Then** the system stores page-level text and chunk records for that document.
2. **Given** a policy PDF contains unchanged text on re-ingestion, **When** it is processed again, **Then** unchanged chunks are reused rather than duplicated.

---

### User Story 3 - Track Ingestion State (Priority: P3)

Agency staff can see whether a policy PDF is pending, processed, failed, or needs attention.

**Why this priority**: Staff need confidence that uploaded policy content is ready before later RAG features rely on it.

**Independent Test**: Can be tested by uploading a document and observing its status move through the ingestion lifecycle.

**Acceptance Scenarios**:

1. **Given** a policy PDF is still being processed, **When** staff view its status, **Then** they see a pending or processing state.
2. **Given** ingestion fails or orphaned content is removed, **When** staff review the document later, **Then** the system shows a final failure or updated state rather than silent success.
3. **Given** many RAG documents exist for a tenant, **When** staff view the document list, **Then** results are paginated so they can browse them in bounded pages.

### Edge Cases

- A PDF uploads successfully but page extraction fails.
- The same policy PDF is uploaded again after the text changes.
- A document is re-ingested after part of its earlier content was removed.
- A tenant uploads a document that belongs to another tenant.
- A file looks like a PDF but cannot be parsed as readable policy text.

## Requirements *(mandatory)*

### Functional Requirements

- **FR-001**: System MUST allow authorized agency users to upload policy PDFs for their own tenant.
- **FR-002**: System MUST reject non-PDF files and unreadable PDF uploads before they become accepted documents.
- **FR-003**: System MUST store each accepted policy document with tenant-scoped metadata and an ingestion status.
- **FR-004**: System MUST extract page content from each accepted policy PDF and store the page records separately from the uploaded file.
- **FR-005**: System MUST divide page content into smaller chunks suitable for later retrieval.
- **FR-006**: System MUST store hashes or equivalent change markers so unchanged chunks can be reused on re-ingestion.
- **FR-007**: System MUST remove orphaned chunks when a document changes and the old chunk content is no longer present.
- **FR-008**: System MUST create and persist embeddings for ingested chunks using the project-selected embedding provider.
- **FR-009**: System MUST track ingestion progress and final state for each document.
- **FR-010**: System MUST keep document metadata, page metadata, chunk metadata, and retrieval log records in the platform's primary database.
- **FR-011**: System MUST keep source files and extracted page text in object storage using tenant-scoped paths.
- **FR-012**: System MUST preserve tenant isolation for document uploads, extracted pages, chunks, embeddings, and ingestion logs.
- **FR-013**: System MUST record whether a document is pending, processed, failed, or unchanged after re-ingestion.
- **FR-014**: System MUST paginate RAG document list responses.

### Key Entities

- RAG Document: A policy PDF uploaded by a tenant, with status and ownership metadata.
- RAG Page: A single extracted page of a document, including page order and stored text.
- RAG Chunk: A smaller text segment derived from one or more pages, with a content hash and embedding reference.
- RAG Retrieval Log: A record of later retrieval usage for a document or chunk.

### Constitution Alignment *(mandatory)*

- Product Boundary: This phase covers policy document storage and ingestion only. It does not add buyer-to-agency chat, listing AI answers, search UI, or area-knowledge content.
- Tenant/RBAC Impact: Authorized agency users can upload their own tenant's policy PDFs. Tenant isolation must cover document metadata, pages, chunks, and logs.
- AI/RAG Scope: This phase adds the storage and ingestion foundation for later retrieval. It does not add user-facing retrieval, reranking, or voice search yet.
- Reliability/Security/Performance: Uploads must be validated before ingestion, re-ingestion must avoid duplicate chunks, failed ingestion must be visible, document lists must be paginated, and all secrets remain Vault-backed.
- Unknowns to Clarify: None.

## Success Criteria *(mandatory)*

### Measurable Outcomes

- SC-001: 100% of non-PDF or unreadable policy uploads are rejected before becoming accepted documents.
- SC-002: 100% of accepted policy PDFs are stored with page records and chunk records.
- SC-003: Re-ingesting an unchanged policy PDF does not create duplicate chunks.
- SC-004: Removing text from a policy and re-ingesting it results in orphaned chunks being removed.
- SC-005: 100% of uploaded documents remain tenant-isolated in metadata, storage paths, and ingestion logs.

## Assumptions

- Policy PDFs are text-based PDFs only in this phase.
- OCR fallback is out of scope for this phase.
- Azure OpenAI with `text-embedding-3-small` is the embeddings provider for chunk embeddings in this phase.
- Existing authentication, tenant isolation, object storage, worker, and database foundations are reused.
- Retrieval features will be defined in a later phase and are not part of this spec.
