# Research: Core Domain Database and CRUD APIs

## Decision: Keep Phase 4 Backend-Only for Domain CRUD

Rationale: Phase 4 acceptance criteria are migrations, CRUD APIs, tenant isolation, support-employee restrictions, pagination, and local validation. React user/agency UI screens start in Phases 5 and 6.

Alternatives considered:
- Build UI with APIs now: rejected because it blends Phase 4 with later UI phases.
- Add only tables, no APIs: rejected because acceptance criteria require CRUD behavior.

## Decision: Use Existing Modular Monolith Modules

Rationale: The project constitution and backend README require feature modules with `router.py`, `service.py`, `repository.py`, `schemas.py`, and `models.py`. Domain records map naturally to existing modules: agencies, listings, leads, viewings, notifications, and search.

Alternatives considered:
- Create a generic domain module: rejected because it weakens ownership and makes later phases harder to extend.
- Create DAO files: rejected by constitution and project rules.

## Decision: Store All Phase 4 Domain State in PostgreSQL

Rationale: Phase 4 is core domain data and CRUD. PostgreSQL provides transactional guarantees for tenant-owned records, status history, comparison constraints, duplicate saved-listing prevention, and domain logs.

Alternatives considered:
- Store search logs or notification state in Redis: rejected because logs and notifications need durable records for later analytics and retries.
- Store photo metadata in MinIO metadata: rejected because Phase 4 only stores metadata references and the constitution favors PostgreSQL as durable metadata source for structured state.

## Decision: Reuse Phase 3 Tenant Context and RBAC Guards

Rationale: Phase 3 created roles, permissions, membership, tenant context, and fail-closed authorization. Phase 4 should build on those guardrails rather than define a parallel access model.

Alternatives considered:
- Add ad hoc tenant filters in each route: rejected because it increases leakage risk.
- Add platform admin bypass for all CRUD: rejected because Phase 4 does not require platform data mutation.

## Decision: Use Clarified Status Sets

Rationale: The spec clarification fixed status sets that affect migrations, schemas, validation, and tests:
- Listing: `active`, `inactive`, `archived`
- Lead: `new`, `reviewed`, `closed`
- Scheduled viewing: `scheduled`, `cancelled_by_user`, `cancelled_by_agency`, `completed`, `no_show`

Alternatives considered:
- More detailed listing review status: rejected because moderation/review workflow is not Phase 4.
- More detailed lead sales pipeline: rejected because Phase 4 needs basic review tracking, not CRM pipeline depth.
- Viewing approval flow: rejected because Phase 4 manually books available slots without approval workflow.

## Decision: Manual Listing Search Only

Rationale: Phase 4 needs direct database-backed filters and search logs. Clarified filters are location text, price range, bedrooms, bathrooms, property type, listing purpose, furnishing, area size, and sort options. Sort options are newest, price low to high, price high to low, area size low to high, and area size high to low.

Alternatives considered:
- AI filter extraction: rejected because Phase 10 owns AI text and voice search.
- Area/neighborhood expansion: rejected because Phase 9/10 own area RAG.
- Full-text ranking beyond simple location text: deferred unless needed in implementation without expanding scope.

## Decision: Apply Explicit Rate Limits to Search, Inquiry, and Viewing Booking

Rationale: The constitution explicitly requires rate limiting for search, lead creation, and viewing booking. Phase 4 needs these flows to reject over-limit requests before partial domain writes occur.

Alternatives considered:
- Defer rate limits to a later hardening phase: rejected because the constitution marks this as mandatory now.
- Add generic app-wide throttling only: rejected because Phase 4 needs endpoint-specific protection for the exposed public flows.

## Decision: Use Explicit Listing Search Cache Invalidation

Rationale: The constitution explicitly requires listing-search cache invalidation. Listing status changes and searchable field changes must invalidate affected cached search results so public listing search cannot return stale data.

Alternatives considered:
- Disable caching entirely: rejected because the constitution specifically requires explicit cache invalidation, implying cached search results remain an expected platform concern.
- Time-based expiry only: rejected because it allows stale public search results after listing mutations.

## Decision: Atomic Booking Creates Viewing and Initial History

Rationale: Scheduled viewings require a reliable current state plus auditable status history. Creating both in one transaction prevents orphaned bookings or missing history.

Alternatives considered:
- Create history asynchronously: rejected because initial status history is part of the core booking invariant.
- Store current status only: rejected because Phase 4 requires status history.

## Decision: Lead Result Tables Are Placeholders Only

Rationale: The plan lists lead spam result, lead level result, and suggested reply tables in Phase 4, but classifiers/generators are later phases. Phase 4 should create durable containers that remain empty or manually/external-test populated.

Alternatives considered:
- Implement spam/Hot-Normal logic now: rejected because Phase 13 owns lead processing.
- Drop result tables until Phase 13: rejected because PLAN.md includes them in Phase 4 domain database scope.

## Decision: Notifications Persist, Delivery Deferred

Rationale: Notification records are part of Phase 4 domain storage. Email delivery, reminders, queues, and idempotent notification workers are Phase 14.

Alternatives considered:
- Send emails on notification creation: rejected because email sending is explicitly out of scope.
- Skip notification records: rejected because PLAN.md includes notifications in Phase 4.

## Decision: Domain Logs Supplement Existing Outbox/Audit Foundations

Rationale: Phase 2 created outbox/inbox/audit foundations. Phase 4 should record critical domain changes for later analytics and async workflows while avoiding actual downstream processing.

Alternatives considered:
- Only use generic audit logs: rejected because domain logs/search logs need queryable business context for later dashboard and analytics phases.
- Trigger all later workflows now: rejected because AI, lead processing, email, and dashboards are out of scope.
