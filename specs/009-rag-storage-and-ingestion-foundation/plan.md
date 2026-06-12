# Implementation Plan: RAG Storage and Ingestion Foundation

**Branch**: `009-rag-storage-and-ingestion-foundation` | **Date**: 2026-06-12 | **Spec**: [spec.md](./spec.md)

**Input**: Feature specification from `/specs/009-rag-storage-and-ingestion-foundation/spec.md`

## Summary

Build foundational RAG storage and ingestion. This allows authorized agency staff to upload policy PDFs, persist document metadata and ingestion outbox events atomically, break documents into page-level parent chunks with overlap and FastCDC child chunks, generate vector embeddings with Azure OpenAI, store vectors using pgvector, and cache pages and original documents securely in MinIO, all strongly isolated by tenant.

## Technical Context

**Language/Version**: Python 3.11 for backend/admin; TypeScript ^5.5.0 for React apps

**Primary Dependencies**: FastAPI, React, Streamlit, PostgreSQL + pgvector, Redis, MinIO; `pymupdf` for PDF parsing, `fastcdc` for Content-Defined Child Chunking.

**Storage**: PostgreSQL + pgvector for metadata/search/vector data; MinIO for blobs/text; Redis for cache/queue/rate limit/token blacklist

**Testing**: Service unit tests, API integration tests, transaction behavior tests, RBAC tenant-isolation tests, and RAG ingestion tests when RAG changes

**Target Platform**: local Docker Compose

**Project Type**: Modular monolith web platform with background workers

**Performance Goals**: Keep uploads non-blocking by moving ingestion work to background workers and paginate RAG document list responses.

**Constraints**: No buyer-to-agency real-time chat; tenant isolation for agency data/RAG/tool calls; provider logic behind interfaces; all secrets read from HashiCorp Vault.

**Scale/Scope**: Multi-tenant agency platform covering user app, agency dashboard, platform admin, AI search/RAG, leads, and viewings.

## Constitution Check

- **Fixed stack**: Uses React + TypeScript, Streamlit + Python, FastAPI + Python, PostgreSQL + pgvector, Redis, MinIO, and background workers. PyMuPDF chosen based on agent recommendation; FastCDC chosen to satisfy Constitution Principle VI.
- **Architecture**: Preserves the modular monolith and feature folders; does not introduce microservices or duplicate DAO/repository layers. Uses `rag/` domain.
- **Product boundaries**: Scope strictly adds PDF foundation, no querying UI or chat in this phase.
- **Tenant/RBAC**: Enforces tenant ID and role permissions for data access and RAG chunks. MinIO paths prefixed with tenant_id.
- **RAG/search**: Keeps PostgreSQL as RAG metadata source of truth, MinIO as blob/text storage, pgvector for embeddings.
- **Reliability/security/performance**: Upload creates RAG document metadata and an ingestion outbox event in one database transaction. Idempotent workers consume the outbox event for PDF ingestion, avoiding blocking API load. RAG document list endpoints use page-based pagination.
- **Testing/quality**: Includes required unit, integration, RAG, and RBAC tests.

## Project Structure

### Documentation (this feature)

```text
specs/009-rag-storage-and-ingestion-foundation/
├── plan.md
├── research.md
├── data-model.md
├── quickstart.md
└── contracts/
    └── rag-endpoints.md
```

### Source Code (repository root)

```text
backend/
├── app/
│   └── rag/
│       ├── router.py
│       ├── service.py
│       ├── repository.py
│       ├── schemas.py
│       └── models.py
└── tests/
    └── integration/
        ├── test_rag_upload.py
        └── test_rag_download_api.py

apps/
└── agency/
    └── src/
        └── pages/
            └── rag/

workers/
├── handlers/
│   └── rag.py
└── tests/
    └── test_rag_ingestion.py
```

## Complexity Tracking

| Violation | Why Needed | Simpler Alternative Rejected Because |
|-----------|------------|-------------------------------------|
| None | N/A | N/A |
