# Data Model: Backend Core Foundation

## Conventions

- IDs are UUIDs unless a later implementation decision explicitly changes
  this.
- Mutable records include `created_at` and `updated_at`.
- Records that should be deactivated rather than removed include `deleted_at`
  or status fields.
- Tenant-aware future records must carry `tenant_id`; Phase 2 only prepares
  foundations and does not add business tenant tables.
- Business entities for listings, leads, scheduled viewings, RAG documents,
  RAG pages, RAG chunks, agency profiles, and media are out of scope.

## Entities

### Role

Purpose: Approved project role for future RBAC checks.

Fields:
- `id` primary key
- `name` unique role name: User, Agency Admin, Support Employee, Platform Admin
- `slug` unique stable identifier
- `scope`: user, agency, or platform
- `description`
- `created_at`
- `updated_at`

Foreign keys: None.

Unique constraints: `name`, `slug`.

Indexes: `scope`.

Soft delete: Not required for fixed MVP roles.

State transitions: None.

### Permission

Purpose: Named capability that can be assigned to roles.

Fields:
- `id` primary key
- `key` unique permission key
- `scope`: user, agency, platform, system
- `description`
- `created_at`
- `updated_at`

Foreign keys: None.

Unique constraints: `key`.

Indexes: `scope`.

Soft delete: Not required for foundation records.

State transitions: None.

### RolePermission

Purpose: Association that grants permissions to roles.

Fields:
- `role_id` foreign key to Role
- `permission_id` foreign key to Permission
- `created_at`

Primary key: Composite of `role_id` and `permission_id`.

Foreign keys: `role_id`, `permission_id`.

Unique constraints: Composite primary key prevents duplicate grants.

Indexes: `role_id`, `permission_id`.

Soft delete: Not required.

State transitions: None.

### User

Purpose: Minimal base actor identity used for auth utility and future profile
foundation. This is not the full user profile feature.

Fields:
- `id` primary key
- `email` unique normalized email
- `password_hash`
- `name`
- `phone`
- `preferred_language`
- `is_active`
- `last_login_at`
- `created_at`
- `updated_at`
- `deleted_at`

Foreign keys: None in Phase 2.

Unique constraints: `email`.

Indexes: `is_active`, `created_at`.

Soft delete: `deleted_at`.

State transitions: `active -> inactive`; `active -> deleted`.

### RefreshSession

Purpose: Foundation record for refresh-token/session invalidation behavior.

Fields:
- `id` primary key
- `user_id` foreign key to User
- `token_hash`
- `family_id`
- `issued_at`
- `expires_at`
- `revoked_at`
- `revocation_reason`
- `replaced_by_session_id`
- `ip_address`
- `user_agent`
- `created_at`
- `updated_at`

Foreign keys: `user_id`, optional self-reference `replaced_by_session_id`.

Unique constraints: `token_hash`.

Indexes: `user_id`, `family_id`, `expires_at`, `revoked_at`.

Soft delete: Not required; revocation is explicit.

State transitions: `active -> revoked`; `active -> replaced`; `active ->
expired`.

### AuditLog

Purpose: Base security and operational event record.

Fields:
- `id` primary key
- `request_id`
- `actor_user_id` optional foreign key to User
- `tenant_id` optional UUID for future tenant-scoped records
- `action`
- `resource_type`
- `resource_id`
- `result`: success, failure, warning
- `metadata`
- `ip_address`
- `user_agent`
- `created_at`

Foreign keys: Optional `actor_user_id`.

Unique constraints: None.

Indexes: `request_id`, `actor_user_id`, `tenant_id`, `action`, `created_at`.

Soft delete: No. Audit logs should remain append-only.

State transitions: Append-only.

### OutboxEvent

Purpose: Reliable async event waiting for worker dispatch.

Fields:
- `id` primary key
- `event_name`
- `aggregate_type`
- `aggregate_id`
- `idempotency_key`
- `payload`
- `status`: pending, processing, delivered, failed, dead_letter
- `available_at`
- `processed_at`
- `retry_count`
- `max_retries`
- `last_error`
- `created_at`
- `updated_at`

Foreign keys: None in Phase 2.

Unique constraints: `idempotency_key`.

Indexes: `event_name`, `status`, `available_at`, `aggregate_type`,
`aggregate_id`, `created_at`.

Soft delete: No; status tracks lifecycle.

State transitions: `pending -> processing -> delivered`; `pending -> failed`;
`failed -> pending`; `failed -> dead_letter`.

Prepared future event names:
- `lead.created`
- `viewing.scheduled`
- `viewing.cancelled`
- `rag.document_uploaded`
- `listing.image_uploaded`
- `email.notification_requested`

### InboxEvent

Purpose: Duplicate-consumption protection for at-least-once worker delivery.

Fields:
- `id` primary key
- `event_id`
- `consumer_name`
- `idempotency_key`
- `status`: processing, consumed, failed
- `received_at`
- `processed_at`
- `last_error`
- `created_at`
- `updated_at`

Foreign keys: Optional relationship to OutboxEvent if processed from local
outbox.

Unique constraints: Composite unique `consumer_name` + `idempotency_key`.

Indexes: `event_id`, `consumer_name`, `status`, `received_at`.

Soft delete: No.

State transitions: `processing -> consumed`; `processing -> failed`; `failed
-> processing`.

### Notification

Purpose: Base outbound notification record for future email and reminder
flows. Phase 2 does not send notifications.

Fields:
- `id` primary key
- `recipient_user_id` optional foreign key to User
- `tenant_id` optional UUID for future tenant-scoped notifications
- `channel`: email, system
- `template_key`
- `payload`
- `status`: pending, queued, sent, failed, cancelled
- `outbox_event_id` optional foreign key to OutboxEvent
- `created_at`
- `updated_at`
- `sent_at`

Foreign keys: Optional `recipient_user_id`, optional `outbox_event_id`.

Unique constraints: None by default.

Indexes: `recipient_user_id`, `tenant_id`, `channel`, `status`, `created_at`.

Soft delete: Not required.

State transitions: `pending -> queued -> sent`; `pending -> cancelled`;
`queued -> failed`; `failed -> queued`.

## Non-Persistent Foundation Objects

### TenantContext

Purpose: Runtime context for future tenant-aware operations.

Fields:
- `actor_id`
- `role`
- `permissions`
- `tenant_id`
- `request_id`
- `source`

Validation: Future tenant-scoped operations must receive tenant context rather
than raw loose tenant IDs.

### PaginationRequest

Purpose: Validated list request bounds.

Fields:
- `page`
- `page_size`

Validation: Page must be positive. Page size must use a configured default and
maximum.

### PaginationResult

Purpose: Bounded list response metadata.

Fields:
- `items`
- `page`
- `page_size`
- `total`
- `has_next`
- `has_previous`

### ProviderContract

Purpose: Interface boundary for future providers.

Provider types:
- chat/completion
- embedding
- reranking
- OCR
- STT
- TTS
- image moderation
- image quality
- spam classifier
- lead classifier
- email

Validation: Concrete providers remain `TBD_ASK_USER`.
