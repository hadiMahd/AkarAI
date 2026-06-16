# Data Model: Agency AI Workflows

## New Request/Response Entities

### `AgencyAIJob`

Trackable job record for OCR and longer AI generation flows.

- `id` (UUID)
- `job_type` (Enum: `ocr_extraction`, `listing_draft`, `lead_reply_draft`, `comparison_summary`)
- `status` (Enum: `queued`, `processing`, `completed`, `blocked`, `failed`)
- `tenant_id` (UUID, nullable for user comparison jobs that are not tenant-scoped)
- `actor_user_id` (UUID)
- `source_reference_id` (UUID, optional)
- `result_payload` (JSON, optional, sanitized)
- `error_message` (String, optional, sanitized)
- `created_at` (DateTime)
- `started_at` (DateTime, optional)
- `completed_at` (DateTime, optional)
- `expires_at` (DateTime, optional)

### `ListingSpecExtractionRequest`

Temporary OCR extraction request initiated from the agency listing form.

- `source_filename` (String)
- `content_type` (String)
- `actor_user_id` (UUID)
- `agency_tenant_id` (UUID)
- `status` (Enum: `uploaded`, `extracting`, `review_ready`, `failed`)
- `provider` (String: `azure_computer_vision_read`)
- `fallback_reason` (String, optional)
- `warnings` (List of strings)

### `ExtractedListingSpecs`

Reviewable fields extracted from the uploaded property spec sheet before any field is applied to the listing form.

- `property_type` (String, optional)
- `listing_purpose` (String, optional)
- `bedrooms` (Integer, optional)
- `bathrooms` (Integer, optional)
- `parking` (Integer, optional)
- `floor` (Integer, optional)
- `area_size` (Number, optional)
- `area_unit` (String, optional)
- `furnishing` (String, optional)
- `address` (String, optional)
- `city` (String, optional)
- `location_text` (String, optional)
- `raw_text_excerpt` (String, optional, bounded)
- `field_confidence` (Map of field key -> `high|medium|low`)
- `source_snippets` (Map of field key -> short supporting text)

### `ListingDraftRequest`

Request to generate listing copy from the current form state and optionally extracted specs.

- `listing_id` (UUID, optional for existing listings)
- `agency_tenant_id` (UUID)
- `actor_user_id` (UUID)
- `listing_context` (Structured listing fields from the form)
- `extracted_specs` (`ExtractedListingSpecs`, optional)
- `status` (Enum: `requested`, `generated`, `blocked`, `failed`)
- `blocked_reason` (String, optional)

### `ListingDraftResult`

Reviewable AI-generated listing copy returned to the form.

- `title` (String)
- `description` (String)
- `highlights` (List of short strings, optional)
- `guardrail_status` (Enum/string)
- `generation_provider` (String, optional)

### `AgencyAssistantToolInvocation`

Normalized record of one approved read-only operational tool call made during an assistant turn.

- `tool_name` (Enum/string: `get_listing`, `search_listings`, `get_lead`, `list_recent_leads`, `list_leads_by_date`)
- `actor_user_id` (UUID)
- `agency_tenant_id` (UUID)
- `input_summary` (Sanitized JSON)
- `output_summary` (Sanitized JSON)
- `status` (Enum: `used`, `refused`, `failed`)
- `failure_reason` (String, optional)

### `LeadReplyDraft`

Reviewable suggested reply for a specific lead and outbound channel.

- `lead_id` (UUID)
- `agency_tenant_id` (UUID)
- `actor_user_id` (UUID)
- `channel` (Enum: `whatsapp`, `email`)
- `draft_text` (String)
- `subject` (String, optional for email)
- `guardrail_status` (Enum/string)
- `generation_provider` (String, optional)
- `blocked_reason` (String, optional)

### `ComparisonSummaryRequest`

User-initiated comparison summary over selected compare-page listings.

- `user_id` (UUID)
- `listing_ids` (List of UUID, min 2, max 4)
- `listing_snapshot` (Derived server-side from current listing records)
- `status` (Enum: `requested`, `generated`, `blocked`, `failed`)
- `fallback_reason` (String, optional)

### `ComparisonSummaryResult`

AI summary returned to the protected user compare page.

- `summary` (Markdown-capable string)
- `key_differences` (List of strings)
- `best_fit_notes` (List of strings, optional)
- `generation_provider` (String, optional)
- `guardrail_status` (Enum/string)

### `AgencyAIActionAudit`

Persistent AI action audit event stored through the existing audit log system.

- `action` (String, e.g. `agency_ai.ocr_requested`, `agency_ai.draft_completed`)
- `resource_type` (String)
- `resource_id` (String)
- `result` (String)
- `metadata` (Sanitized JSON, includes job type, status, and redacted summaries)

## Existing Entities Reused

### `Listing`

Source of truth for agency listing form inputs, AI draft generation context, and user comparison summary source data.

### `Lead`

Source of truth for lead-detail reply drafting and approved assistant lead lookups.

### `RagChatThread` / `RagChatMessage`

Existing durable assistant thread model reused for the broadened agency assistant.

### `RagDocument` / `RagChunk` / `RagRetrievalLog`

Existing policy grounding and retrieval diagnostics reused for policy-backed assistant answers.

## Validation Rules

- OCR uploads must accept only allowed document/image content types and bounded file size.
- Temporary OCR files must not be stored as durable tenant attachments in this phase.
- Extracted spec fields must remain review-only until the human explicitly applies them to the listing form.
- Listing draft generation must not auto-save or auto-publish a listing.
- OCR extraction and longer generation flows must be represented as jobs with visible queued/processing/completed/failed states.
- Agency assistant tool calls must remain read-only, tenant-scoped, and role-checked.
- Support employees may use the assistant but must not gain listing-management or document-management permissions through it.
- Comparison summaries must require at least 2 listing IDs and must cap at the current comparison max of 4.
- User comparison summaries must be built from server-fetched listing data, not trusted client text blobs.
- Lead reply drafts must never send messages directly; they only prepare content for external launch.
- All prompts, outputs, tool payloads, cached artifacts, and audit metadata must pass through existing redaction and guardrail controls.

## State Transitions

- **Spec extraction**: `uploaded` → `queued` → `processing` → `review_ready` or `failed` → `discarded`
- **Listing draft**: `requested` → `queued` → `processing` → `generated` or `blocked/failed`
- **Assistant turn with tools**: `user_message_saved` → `policy_retrieval` + optional `tool_invocation` → `generated` or `blocked/fallback`
- **Lead reply draft**: `requested` → `queued` → `processing` → `generated` or `blocked/failed`
- **Comparison summary**: `requested` → `queued` → `processing` → `generated` or `blocked/failed`
