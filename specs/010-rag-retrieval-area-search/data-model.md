# Data Model: RAG Retrieval and Reranking

## Entities

### `RagRetrievalLog`
Records one retrieval attempt.
- `id` (UUID, Primary Key)
- `tenant_id` (UUID, required)
- `actor_user_id` (UUID, required when authenticated)
- `actor_role` (String)
- `query` (Text)
- `retrieval_scope` (Enum: agency_policy)
- `selected_document_ids` (Array of UUIDs)
- `selected_chunk_ids` (Array of UUIDs)
- `selected_page_ids` (Array of UUIDs)
- `reranker_used` (Boolean)
- `reranker_provider` (String, nullable)
- `fallback_reason` (String, nullable)
- `confidence_status` (Enum: sufficient, insufficient, fallback)
- `created_at` (DateTime)

### `RagRetrievalEvidence`
Represents one ranked piece of evidence returned to callers and optionally persisted for audit/debug.
- `chunk_id` (UUID)
- `document_id` (UUID)
- `page_ids` (Array of UUIDs)
- `document_filename` (String)
- `page_numbers` (Array of Integer)
- `chunk_text_preview` (Text)
- `parent_page_text` (Text, bounded for response)
- `vector_rank` (Integer)
- `vector_score` (Float)
- `rerank_rank` (Integer, nullable)
- `rerank_score` (Float, nullable)
- `source_label` (String)

### `RagPolicyAnswer`
Represents the retrieval-backed answer returned to agency staff.
- `answer` (Text)
- `citations` (List of source references)
- `evidence` (List of ranked evidence)
- `debug` (Provider, confidence, fallback, and scoring metadata)
- `status` (Enum: answered, insufficient_evidence, fallback)

### `RagEvaluationExample`
Represents one evaluation case.
- `id` (String or UUID)
- `query` (Text)
- `tenant_fixture` (String)
- `expected_behavior` (Enum: answer, refuse, insufficient_evidence)
- `expected_source_labels` (List of String)
- `notes` (Text)

### `RagEvaluationRun`
Represents one completed retrieval evaluation run.
- `id` (UUID)
- `run_label` (String)
- `started_at` (DateTime)
- `completed_at` (DateTime)
- `total_examples` (Integer)
- `passed_examples` (Integer)
- `failed_examples` (Integer)
- `summary` (JSON-compatible structured metrics)

## Existing Entities Reused

### `RagDocument`
Processed policy PDF metadata. Retrieval uses only documents with `status = processed`.

### `RagPage`
Parent page metadata and page text reference. Retrieval fetches parent page text after child chunk selection.

### `RagChunk`
Child chunk metadata, content hash, embedding, tenant scope, and active/orphaned status. Retrieval uses only `active` chunks.

## Validation Rules

- Retrieval requires authenticated agency context.
- Retrieval must reject missing tenant context.
- Retrieval must only read `processed` documents and `active` chunks.
- Support employees can retrieve policy evidence but cannot perform admin-only actions through the retrieval flow.
- Returned evidence must be bounded by configured top-k limits.
- Debug output must not include secrets, raw tokens, or unnecessary personal data.
- Area search RAG entities are out of scope for this phase.

## State Transitions

- **RagPolicyAnswer**: `answered` when evidence is sufficient; `insufficient_evidence` when evidence is too weak; `fallback` when reranking or answer generation degrades gracefully.
- **RagEvaluationRun**: `started` → `completed`; failed examples are recorded inside the run summary.
