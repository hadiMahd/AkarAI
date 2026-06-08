# Data Model: Akarai MVP

## Conventions

- Every tenant-owned entity includes `tenant_id`.
- Every mutable entity includes `created_at`, `updated_at`, and where useful
  `deleted_at`.
- IDs are UUIDs unless a later plan chooses otherwise.
- Money values store currency and amount separately.
- Status changes that matter to users or agencies get history records.

## Entities

### User

Fields: `id`, `name`, `email`, `phone`, `preferred_language`, `password_hash`
or external auth reference, `is_active`, timestamps.

Relationships: Has saved listings, comparison sessions, submitted leads, and
scheduled viewings.

Validation: Email unique. Phone format validated for supported markets.
Profile fields remain limited to name, email, phone, preferred language, saved
listings, submitted inquiries, and scheduled viewings.

### Agency

Fields: `id`, `name`, `slug`, `description`, `logo_object_key`, `public_phone`,
`public_email`, `address`, `is_active`, timestamps.

Relationships: Owns employees, listings, leads, scheduled viewings, policy
documents, RAG documents, RAG chunks, dashboard metrics, and audit logs.

Validation: Slug unique. Agency is the tenant boundary.

### AgencyEmployee

Fields: `id`, `tenant_id`, `user_id`, `role_id`, `display_name`, `email`,
`phone`, `status`, `deactivated_at`, timestamps.

Relationships: Belongs to agency and role. Reviews leads. May be referenced in
audit logs.

Validation: Support employees cannot create listings, manage employees, edit
agency profile settings, upload/delete policy documents, or access platform
data.

State transitions: `active -> deactivated`; deactivation invalidates sessions.

### Role

Fields: `id`, `name`, `scope` (`user`, `agency`, `platform`), `description`.

Relationships: Has permissions; assigned to agency employees or platform
admins.

Validation: MVP roles are User, Agency Admin, Support Employee, and Platform
Admin.

### Permission

Fields: `id`, `key`, `description`, `scope`.

Relationships: Many-to-many with roles.

Validation: Permission checks must include tenant scope where applicable.

### Listing

Fields: `id`, `tenant_id`, `title`, `description`, `property_type`, `purpose`,
`price_amount`, `price_currency`, `area`, `city`, `neighborhood`, `address`,
`bedrooms`, `bathrooms`, `size_sqm`, `parking_spaces`, `floor`, `is_furnished`,
`status`, `published_at`, timestamps.

Relationships: Belongs to agency. Has photos, viewing slots, saved listings,
comparison items, leads, scheduled viewings, and audit records.

Validation: Generic amenities are not a core MVP field. Listing publish uses an
all-or-nothing transaction.

State transitions: `draft -> pending_media_checks -> published -> archived`.

### ListingPhoto

Fields: `id`, `tenant_id`, `listing_id`, `object_key_original`,
`object_key_webp`, `display_order`, `nsfw_status`, `quality_status`,
`quality_warning`, `processing_status`, timestamps.

Relationships: Belongs to listing.

Validation: NSFW photos are rejected. Low-quality photos may be accepted with a
warning. Accepted photos are optimized to WebP.

State transitions: `uploaded -> checking -> accepted | rejected`.

### ListingViewingSlot

Fields: `id`, `tenant_id`, `listing_id`, `starts_at`, `ends_at`, `capacity`,
`status`, timestamps.

Relationships: Belongs to listing. Can produce scheduled viewings.

Validation: Slots must belong to the listing tenant.

### ScheduledViewing

Fields: `id`, `tenant_id`, `listing_id`, `user_id`, `client_name`,
`client_email`, `client_phone`, `starts_at`, `ends_at`, `status`, `notes`,
`created_by_ai`, timestamps.

Relationships: Belongs to listing, agency, and user. Has status history.

Validation: Created only after user confirmation. Must not create a Lead.

State transitions: `Scheduled -> Confirmed -> Completed`; `Scheduled ->
Cancelled`; `Confirmed -> Cancelled`; `Scheduled -> No-show`; `Confirmed ->
No-show`.

### ScheduledViewingStatusHistory

Fields: `id`, `tenant_id`, `scheduled_viewing_id`, `from_status`,
`to_status`, `changed_by_user_id`, `changed_by_employee_id`, `changed_at`,
`reason`.

Relationships: Belongs to scheduled viewing.

Validation: Every status change records actor and timestamp.

### SavedListing

Fields: `id`, `user_id`, `listing_id`, `saved_at`.

Relationships: Belongs to user and listing.

Validation: Unique per user/listing.

### ComparisonSession

Fields: `id`, `user_id`, `status`, `created_at`, `updated_at`, `expires_at`.

Relationships: Has comparison items.

Validation: Maximum four active items.

### ComparisonItem

Fields: `id`, `comparison_session_id`, `listing_id`, `position`, timestamps.

Relationships: Belongs to comparison session and listing.

Validation: Unique listing per session. Position is 1 through 4.

### Lead

Fields: `id`, `tenant_id`, `listing_id`, `user_id`, `client_name`,
`client_email`, `client_phone`, `message`, `source`, `status`,
`is_spam`, `level`, timestamps.

Relationships: Belongs to agency, listing, and user. Has spam result, level
result, suggested reply, and review record.

Validation: Created only after user confirmation. Viewing bookings do not
create leads.

State transitions: `new -> classified -> reviewed`; spam leads stay in spam
queue.

### LeadSpamResult

Fields: `id`, `tenant_id`, `lead_id`, `is_spam`, `score`, `model_name`,
`reason`, `created_at`.

Relationships: Belongs to lead.

Validation: Spam leads are separated from valid leads.

### LeadLevelResult

Fields: `id`, `tenant_id`, `lead_id`, `level` (`Hot`, `Normal`), `score`,
`model_name`, `reason`, `created_at`.

Relationships: Belongs to lead.

Validation: Applies only to non-spam leads.

### LeadSuggestedReply

Fields: `id`, `tenant_id`, `lead_id`, `reply_text`, `channel_hint`,
`model_name`, `created_at`.

Relationships: Belongs to lead.

Validation: One suggested reply is shown in MVP. Reply is not sent inside the
app.

### ReviewedLeadRecord

Fields: `id`, `tenant_id`, `lead_id`, `reviewer_employee_id`,
`reviewer_name_snapshot`, `reviewed_at`, `notes`.

Relationships: Belongs to lead and employee.

Validation: Reviewer ID, reviewer name, and timestamp are required.

### AgencyPolicyDocument

Fields: `id`, `tenant_id`, `title`, `document_type`, `status`,
`original_object_key`, `uploaded_by_employee_id`, timestamps.

Relationships: Belongs to agency. Creates RAG document/pages/chunks.

Validation: Uploaded by Agency Admin only. Stored as document source, not
manual text record.

State transitions: `uploaded -> processing -> indexed -> failed -> archived`.

### RAGDocument

Fields: `id`, `tenant_id`, `source_type`, `source_id`, `title`, `status`,
`original_blob_link`, `content_hash`, timestamps.

Relationships: Has pages and chunks. Source may be agency policy document or
platform area knowledge document.

Validation: Original document path:
`rag-vault/{tenant_id}/{document_id}/original/original.pdf`.

### RAGPage

Fields: `id`, `tenant_id`, `rag_document_id`, `page_number`,
`page_text_blob_link`, `page_hash`, `char_count`, timestamps.

Relationships: Belongs to RAG document. Parent context for child chunks.

Validation: Page path:
`rag-vault/{tenant_id}/{document_id}/pages/page_001.txt`.

### RAGChunk

Fields: `id`, `tenant_id`, `rag_document_id`, `rag_page_id`, `chunk_index`,
`chunk_text_preview`, `chunk_hash`, `vector_id`, `metadata`, `is_active`,
timestamps.

Relationships: Belongs to document/page. Referenced by retrieval logs.

Validation: Child chunks are embedded. Hashes are compared on re-ingestion.
Orphan hashes are batch deleted from pgvector and Postgres.

### RAGRetrievalLog

Fields: `id`, `tenant_id`, `conversation_id`, `query_text_redacted`,
`retrieved_chunk_ids`, `reranked_chunk_ids`, `latency_ms`, `created_at`.

Relationships: May belong to AI conversation.

Validation: Logs must avoid raw PII where redaction applies.

### AreaKnowledgeDocument

Fields: `id`, `tenant_id`, `area_name`, `title`, `status`, `source_notes`,
timestamps.

Relationships: Creates RAG document/pages/chunks.

Validation: Tenant is `company_internal`.

### AIConversation

Fields: `id`, `tenant_id`, `user_id`, `employee_id`, `listing_id`, `scope`,
`status`, timestamps.

Relationships: Has messages and audit logs.

Validation: Homepage scope is search-only. Listing scope can use listing
context, agency policy RAG, viewing slots, and controlled tools.

### AIMessage

Fields: `id`, `tenant_id`, `conversation_id`, `role`, `content_redacted`,
`tool_name`, `tool_result_summary`, timestamps.

Relationships: Belongs to AI conversation.

Validation: PII redaction required where personal data may appear.

### AIAuditLog

Fields: `id`, `tenant_id`, `actor_type`, `actor_id`, `scope`, `action`,
`prompt_redacted`, `response_redacted`, `tool_name`, `allowed`, `reason`,
timestamps.

Relationships: Linked to conversation/message where applicable.

Validation: Platform admin can view audit logs without crossing tenant rules.

### OutboxEvent

Fields: `id`, `tenant_id`, `event_type`, `aggregate_type`, `aggregate_id`,
`payload`, `status`, `attempt_count`, `next_attempt_at`, timestamps.

Relationships: Created inside critical transactions.

Validation: Event recording shares transaction with source write.

State transitions: `pending -> processing -> published -> failed`.

### InboxEvent

Fields: `id`, `tenant_id`, `source_event_id`, `consumer_name`, `status`,
`processed_at`, timestamps.

Relationships: Tracks idempotent worker consumption.

Validation: Unique per source event and consumer.

### Notification

Fields: `id`, `tenant_id`, `recipient_user_id`, `recipient_employee_id`,
`channel`, `template_key`, `status`, `payload`, timestamps.

Relationships: May originate from outbox event.

Validation: Used for signup, password reset, lead received, viewing booked,
viewing cancelled, and reminders.

### SearchLog

Fields: `id`, `user_id`, `tenant_id`, `query_text_redacted`, `search_type`,
`filters_extracted`, `result_count`, `created_at`.

Relationships: Feeds demand metrics.

Validation: Area RAG uses `company_internal` tenant knowledge.

### MarketplaceDemandMetric

Fields: `id`, `period_start`, `period_end`, `area`, `budget_range`,
`property_type`, `demand_gap_score`, `search_count`, timestamps.

Relationships: Derived from search logs and listing inventory.

Validation: Platform admin only.

### AgencyDashboardMetric

Fields: `id`, `tenant_id`, `period_start`, `period_end`,
`forecasted_possible_sales_next_month`, `reviewed_leads_count`,
`hot_leads_count`, `normal_leads_count`, `spam_leads_count`, timestamps.

Relationships: Belongs to agency.

Validation: Tenant-scoped.

### DomainEventTransaction

Fields: `id`, `tenant_id`, `event_type`, `aggregate_type`, `aggregate_id`,
`occurred_at`, `payload`, `time_series_ready`.

Relationships: May mirror outbox events.

Validation: Stores domain event/transaction facts for future time-series model.
