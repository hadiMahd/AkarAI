<!--
Sync Impact Report
Version change: 2.0.0 -> 3.0.0
Modified principles: I. Fixed Technology Stack; VI. RAG Ingestion and Retrieval; XII. AI Provider Interfaces
Added sections: None
Removed sections: None
Templates requiring updates:
- updated: .specify/templates/plan-template.md
- updated: .specify/templates/spec-template.md
- updated: .specify/templates/tasks-template.md
- not present: .specify/templates/commands/*.md
- updated: AGENTS.md
Follow-up TODOs: Align RAG planning artifacts with provider-agnostic reranking language
-->
# AkarAI Constitution

## Core Principles

### I. Fixed Technology Stack
The implementation MUST use React and TypeScript for the user app and agency
dashboard, Streamlit and Python for the platform admin, FastAPI and Python for
the backend, PostgreSQL with pgvector for persistence and vector search, Redis
for cache, queue, rate limiting, and token blacklist duties, and MinIO for
blob/object storage. RAG reranking MUST go through provider interfaces and MAY
use any user-approved provider where useful. The backend MUST start as a
modular monolith with background workers. If any
required library, package, model, or service provider is unspecified, the agent
MUST ask the user before choosing. Rationale: fixed choices prevent accidental
stack drift and keep the final project buildable.

### II. Modular Monolith Architecture
The app MUST start as a modular monolith, not full microservices. Backend code
MUST be organized by feature folders for users, agencies, listings, leads,
viewings, rag, ai, auth, and notifications. Each feature MUST use `router.py`
for HTTP endpoints, `service.py` for business logic, `repository.py` for
database CRUD, `schemas.py` for request/response schemas, `models.py` for ORM
models, and `query_service.py` only when CQRS/read optimization is useful. The
project MUST NOT create both DAO and repository layers; `repository.py` is the
data access layer. Rationale: the system needs clear ownership without the
operational overhead of microservices.

### III. Product Boundary Integrity
The product MUST NOT include buyer-to-agency real-time chat. Allowed
communication flows are user to AI, agency admin/support employee to AI, and
platform admin to the admin dashboard. User inquiries MUST create structured
leads. Viewing bookings MUST create scheduled viewing records and MUST NOT be
modeled as leads. Homepage AI MUST be search-only and MUST NOT answer
listing-specific or agency-specific questions. Listing page AI MUST answer only
from selected listing context, selected agency public policy RAG, allowed
viewing slots, and controlled backend tools. Rationale: clear boundaries avoid
scope creep and keep lead/viewing semantics reliable.

### IV. Roles and Tenant Isolation
Every agency is a tenant. Tenant isolation is mandatory for listings, leads,
scheduled viewings, policy documents, RAG chunks, AI tool calls, audit logs, and
agency metrics. The only roles are User, Agency Admin, Support Employee, and
Platform Admin. Support employees MUST NOT create listings, manage employees,
edit agency profile settings, or access platform-wide data. AI tool calls MUST
enforce role permissions and tenant ID. Rationale: real estate agency data is
tenant-scoped and must not leak across agencies.

### V. RAG Source of Truth
RAG metadata MUST use PostgreSQL as the source of truth. MinIO stores
files/text only, using paths like
`rag-vault/{tenant_id}/{document_id}/original/original.pdf` and
`rag-vault/{tenant_id}/{document_id}/pages/page_001.txt`. PostgreSQL MUST store
document metadata, page metadata, chunk metadata, blob links, vector IDs, and
chunk hashes. pgvector MUST store embeddings and minimal filter metadata. Policy
documents MUST be uploaded and ingested, not manually edited as text records
inside the app. Rationale: metadata belongs in transactional storage while
objects remain replaceable blobs.

### VI. RAG Ingestion and Retrieval
RAG ingestion MUST include document upload to MinIO, page-level parent chunking,
previous-page overlap buffer when needed, CDC/fastcdc child chunking, chunk
hashing, old-hash versus new-hash comparison, orphan chunk deletion, tenant
metadata filtering, parent page fetch from MinIO during retrieval, and
provider-based reranking where useful. Rationale: retrieval quality and tenant
safety depend on deterministic ingestion, metadata filters, and auditable chunk
updates.

### VII. Search Flow Separation
Manual search MUST use direct database filters. AI text/voice search MUST use
LLM filter extraction, optional area/neighborhood RAG for vague location terms,
and database search. Area RAG applies to queries such as `house around Beirut`,
`calm area near Beirut`, and `family area close to Beirut`. Area RAG MUST use
platform-owned area knowledge, not agency policy documents. No match score is
required because filtered database search already returns matching listings.
Rationale: database filters remain authoritative while AI helps translate vague
natural language.

### VIII. Reliability and Async Work
All-or-nothing database transactions MUST cover lead creation, viewing booking,
listing publish, RAG document metadata writes, and outbox event creation.
Redis/background workers MUST handle image processing, OCR, RAG ingestion,
email sending, scheduled reminders, and AI-heavy jobs. Outbox/inbox MUST be
used where reliable async events are needed. Events MUST be idempotent because
queue delivery is at-least-once. Pub/Sub MAY be used only when multiple parts
of the system need the same domain event. Rationale: user-facing workflows must
not partially commit or duplicate side effects.

### IX. Security and Privacy
Authentication MUST use JWT access tokens and refresh tokens. Access tokens
MUST be short-lived, while refresh tokens MUST allow users/employees to stay
logged in. JWT invalidation MUST support logout, password reset, employee
deactivation, and suspicious session revocation. Rate limiting MUST cover
login, registration, AI endpoints, search, file uploads, lead creation, and
viewing booking. Presidio or equivalent redaction MUST be used where PII may
enter AI logs or prompts. All secrets MUST be read from HashiCorp Vault through
a central settings/config module. Secret values MUST NOT be committed, embedded
in code, or treated as ordinary environment configuration. Environment
variables MAY contain only non-secret runtime configuration and the minimum
bootstrap information required to reach Vault. Rationale: AI and multi-tenant
workflows increase the blast radius of weak auth, weak rate limits, or leaked
PII.

### X. Performance Standards
Pagination MUST be used for listings, leads, scheduled viewings, saved
listings, audit logs, RAG documents, and admin tables. PostgreSQL connection
pooling MUST use PgBouncer. FastAPI code MUST be async/non-blocking where I/O
is involved. Cache invalidation MUST be explicit for listing search, agency
dashboard metrics, RAG retrieval cache, and platform demand insights. Listing
images MUST be optimized to WebP for storage efficiency. Rationale: predictable
latency and bounded payloads are required for search, dashboards, and RAG.

### XI. UI Boundaries
React user and agency interfaces MUST use skeleton loading for slow pages. The
platform admin MUST be Streamlit, not React. The user profile MUST stay limited
to name, email, phone, preferred language, saved listings, submitted inquiries,
and scheduled viewings. The app MUST NOT add AI persona profiling, default
budget, preferred areas, or buy/rent preference unless the user explicitly
requests it later. Rationale: the UI exposes useful state without
inventing personal profiling or expanding scope silently.

### XII. AI Provider Interfaces
AI providers MUST be accessed through provider interfaces. The system MUST NOT
hardcode provider-specific logic into feature services. Provider interfaces MUST
exist for chat/completion, embedding, reranking, STT, TTS, and OCR providers.
The first implementation MAY use one primary provider, but the design MUST
support fallback providers. If a provider is unspecified, the agent MUST ask the
user. Rationale: feature code must survive provider changes and fallback
needs.

### XIII. Testing, Quality, and Unknowns
Each feature MUST include service-level unit tests where practical, integration
tests for important API routes, transaction behavior tests for critical flows,
RAG ingestion tests for chunk/hash deletion logic when RAG changes, and RBAC
tests for tenant isolation. The implementation MUST prefer clear, maintainable
code over clever abstractions. The project MUST NOT add unused architecture
patterns just to look advanced. If a required decision is not specified in the
plan/spec, the agent MUST ask the user instead of inventing it, including exact
AI provider, email provider, OCR provider, STT/TTS provider, auth library,
React UI library, background worker library, deployment target, and any future
payment/billing behavior. Rationale: tests and explicit unknown handling keep
the implementation verifiable.

## Development Workflow

Feature specs MUST identify affected product boundaries, tenant/role behavior,
AI/RAG scope, critical transactions, and provider or library unknowns. Plans
MUST pass the Constitution Check before Phase 0 research and again after Phase
1 design. Tasks MUST group work by independently testable user stories and MUST
include required tests and security/reliability work in the relevant story or
foundational phase.

Implementation MUST follow the fixed stack and modular monolith structure
unless this constitution is amended first. Any exception MUST be documented in
the feature plan's Complexity Tracking table with the simpler alternative and
the reason it was rejected.

## Governance

This constitution supersedes conflicting project conventions, templates, and
generated plans. Amendments require an explicit constitution update, a Sync
Impact Report, and review of dependent templates and runtime guidance. Plans,
specs, tasks, code reviews, and implementation work MUST treat constitution
violations as blocking until the artifact or constitution is corrected.

Versioning follows semantic versioning. MAJOR changes remove or redefine
governance or principles in a backward-incompatible way. MINOR changes add a
principle, section, or materially expanded guidance. PATCH changes clarify
wording without changing meaning.

Compliance review MUST happen during `/speckit-plan`, `/speckit-tasks`,
`/speckit-analyze`, and before implementation completion. Any required decision
not resolved in a spec or plan MUST be escalated to the user, not silently
filled by the agent.

**Version**: 3.0.0 | **Ratified**: 2026-06-08 | **Last Amended**: 2026-06-12
