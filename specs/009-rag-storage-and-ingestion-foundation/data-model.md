# Data Model: RAG Storage and Ingestion Foundation

## Entities

### `RagDocument`
Represents an uploaded policy PDF document.
- `id` (UUID, Primary Key)
- `tenant_id` (UUID, Foreign Key to User/Tenant)
- `filename` (String)
- `status` (Enum: pending, processing, processed, failed)
- `blob_path` (String, e.g. `rag-vault/{tenant_id}/{document_id}/original/original.pdf`)
- `created_at` (DateTime)
- `updated_at` (DateTime)

### `RagPage`
Represents a single extracted page of a document.
- `id` (UUID, Primary Key)
- `document_id` (UUID, Foreign Key to RagDocument)
- `tenant_id` (UUID, Foreign Key to User/Tenant)
- `page_number` (Integer)
- `blob_path` (String, e.g. `rag-vault/{tenant_id}/{document_id}/pages/page_001.txt`)
- `created_at` (DateTime)

### `RagChunk`
Represents a smaller text segment derived from pages using FastCDC (Content-Defined Chunking).
- `id` (UUID, Primary Key)
- `document_id` (UUID, Foreign Key to RagDocument)
- `tenant_id` (UUID, Foreign Key to User/Tenant)
- `page_ids` (Array of UUIDs, Foreign Keys to RagPage)
- `content_hash` (String, SHA256 of text to avoid duplicate ingestion)
- `embedding` (VECTOR, pgvector column)
- `status` (Enum: active, orphaned)
- `created_at` (DateTime)

### `RagRetrievalLog`
Records retrieval usage for a document or chunk (laying groundwork for Phase 9).
- `id` (UUID, Primary Key)
- `tenant_id` (UUID, Foreign Key to User/Tenant)
- `document_id` (UUID, Foreign Key to RagDocument)
- `query` (String)
- `retrieved_at` (DateTime)

## Validation Rules
- `RagDocument` only accepts `.pdf` files.
- Empty PDFs or those with no extractable text raise an error during ingestion, marking status as `failed`.

## State Transitions
- **RagDocument**: `pending` → `processing` → `processed` (or `failed`)
