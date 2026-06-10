# PLAN.md — Akarai MVP Phased Implementation Plan

## Purpose

This file is the main implementation handoff for **Akarai**, an AI-first multi-tenant real estate platform for Lebanon.

It is written for **Spec Kit / spec-driven development** and must be used to generate clean `tasks.md` phases. The agent must **not** collapse the full app into Phase 1. Phase 1 is infrastructure/foundation only.

---

## 0. Non-Negotiable Implementation Rules

### 0.1 Phase Discipline

The implementation must be divided into phases.

**Do not put the whole app in Phase 1.**

Phase 1 must only include infrastructure, repo setup, Docker Compose, service bootstrapping, and health checks.

Feature implementation starts only after infrastructure and backend foundation are working.

### 0.2 Architecture Style

Use:

```text
modular monolith + background workers
```

Do **not** start with full microservices.

Use feature-based backend folders:

```text
backend/app/
  auth/
  users/
  agencies/
  listings/
  media/
  leads/
  viewings/
  search/
  rag/
  ai/
  notifications/
  analytics/
  audit/
  common/
```

Each feature should use:

```text
router.py        # FastAPI endpoints
service.py       # business logic
repository.py    # database CRUD
schemas.py       # request/response schemas
models.py        # ORM models
query_service.py # only where lightweight CQRS helps
```

Use `repository.py`. Do **not** create both DAO and repository layers.

### 0.3 Fixed Tech Stack

Use this stack unless the user explicitly changes it:

```text
User app: React + TypeScript
Agency dashboard: React + TypeScript
Platform admin: Streamlit + Python
Backend: FastAPI + Python
Database: PostgreSQL + pgvector
Vector search: pgvector
Cache/queue/rate limiting/token blacklist: Redis
Blob storage: MinIO
Connection pooling: PgBouncer
RAG reranking: Cohere rerankers where useful
Architecture: modular monolith + background workers
```

### 0.4 Ask User if Unspecified

If any exact provider/library is not specified, the agent must mark it as:

```text
NEEDS CLARIFICATION
```

and ask the user before choosing.

Unspecified decisions include:

```text
exact LLM provider
exact embedding model
exact STT provider
exact TTS provider
exact OCR provider
exact email provider
exact React UI library
exact background worker library
exact auth helper library
exact deployment target
exact image moderation model
exact image quality model
exact ML spam classifier implementation
exact NLP Hot/Normal classifier implementation
```

---

## 1. Product Scope Summary

Akarai is a multi-tenant real estate platform with:

1. User-facing property search and listing experience.
2. Agency dashboard for agencies and support employees.
3. Platform admin dashboard for marketplace-level insights.
4. AI features for search, listing page assistance, RAG, lead handling, media processing, and insights.

### 1.1 Product Boundaries

The app must not include buyer-to-agency real-time chat.

Allowed communication patterns:

```text
User ↔ AI
Agency Admin ↔ AI
Support Employee ↔ AI
Platform Admin ↔ Admin Dashboard
```

Structured outputs:

```text
User inquiry → Lead
Viewing booking → ScheduledViewing
```

Viewing bookings are **not leads**.

### 1.2 Removed / Out of Scope

Do not implement:

```text
buyer-to-agency real-time chat
property match score
generic amenities as core MVP field
reported listing AI review
listing quality checker based on missing fields
AI persona / renter personality profile
manual editing of policy text inside the app
full microservices
DAO layer
BPMN runtime engine
```

---

## 2. User Flow Requirements

### 2.1 Homepage

Homepage includes:

```text
manual search
AI text search
AI voice search
microphone button
featured listings
agency cards
About/Help link
```

Homepage AI is **search-only**.

It must not answer listing-specific or agency-specific questions.

### 2.2 Manual Search

Flow:

```text
User fills filters
↓
Backend runs database query
↓
Listings page opens with paginated results
```

### 2.3 AI Text Search

Flow:

```text
User enters natural-language query
↓
LLM extracts hard filters
↓
If location is vague, area/neighborhood RAG expands location
↓
Frontend shows editable confirmation panel
↓
User confirms or edits
↓
Backend runs database query
↓
Listings page opens
```

Example vague location queries:

```text
house around Beirut
calm area near Beirut
family area close to Beirut
quiet apartment near Beirut
```

### 2.4 AI Voice Search

Flow:

```text
User records voice
↓
STT converts speech to text
↓
LLM extracts filters
↓
Optional area RAG expands vague location
↓
Frontend shows editable confirmation panel
↓
User confirms
↓
Listings page opens
↓
Optional TTS response can summarize result
```

### 2.5 Listings Page

Listings page includes:

```text
paginated listing cards
filters
sorting
save listing
add to compare
open listing
```

Listings page has **no chatbot**.

No match score.

### 2.6 Comparison Page

User can compare up to four listings.

Comparison page includes:

```text
side-by-side structured fields
AI comparison summary
remove from comparison
open listing
```

Core fields may include:

```text
title
agency
price
location
purpose: rent/sale
property type
bedrooms
bathrooms
sqm
parking
floor
furnished status
available viewing dates
```

Do not include generic `amenities` as a core MVP field.

### 2.7 Listing Detail Page

Listing page includes:

```text
photos
full specs
description
price
location
parking
floor
furnished status
available viewing dates
agency preview
unified AI widget
```

### 2.8 Unified Listing AI Widget

The listing AI widget can handle:

```text
listing questions
agency policy questions
create inquiry
schedule viewing
unclear request clarification
```

Context allowed:

```text
selected listing structured data
selected agency public policy RAG
available viewing slots
current user basic profile
controlled backend tools
```

It cannot access another agency's data.

### 2.9 Inquiry Flow

Flow:

```text
User asks to contact/send inquiry
↓
AI creates professional inquiry preview
↓
User edits or confirms
↓
Structured Lead is created
↓
Agency sees lead in dashboard
```

No real-time chat is opened.

### 2.10 Viewing Scheduling Flow

Viewing can be manual or through AI.

Flow:

```text
User selects/asks for viewing slot
↓
System checks selected listing viewing slots
↓
User confirms
↓
ScheduledViewing is created
↓
User sees it in Scheduled Viewings tab
↓
Agency admin/support employee sees it in Viewing Schedules page
```

Viewing bookings are not leads.

### 2.11 User Profile

User profile includes:

```text
name
email
phone
preferred language
saved listings
submitted inquiries
scheduled viewings
```

Do not include:

```text
default budget
preferred areas
buy/rent preference
AI persona classifier
```

---

## 3. Agency Flow Requirements

### 3.1 Roles

Roles:

```text
Agency Admin
Support Employee
```

Agency Admin can:

```text
manage agency profile
upload/delete/re-ingest policy documents
create listings
manage listings
view leads
view spam leads
view reviewed leads
view scheduled viewings
manage support employees
view agency dashboard
use agency assistant
```

Support Employee can:

```text
view/edit listings where allowed
view leads
view spam leads
open lead details
use AI suggested reply
open WhatsApp/email with draft
mark leads reviewed
view scheduled viewings
use agency support assistant
```

Support Employee cannot:

```text
create listings
manage employees
edit agency profile settings
upload/delete policy documents
access platform-wide data
```

### 3.2 Agency Profile Settings

Agency Admin manages:

```text
agency name
email
phone
office location
working hours
```

No profile picture required.
No AI bio generation.

### 3.3 Policy Documents / RAG Knowledge Base

Agency policies are uploaded as documents.

The app must not manually edit policy text records.

Allowed actions:

```text
upload document
view uploaded documents
view ingestion status
delete document
re-ingest document
```

Policy documents power:

```text
listing page policy questions
agency support employee assistant
agency admin assistant where useful
```

### 3.4 Create Listing

Only Agency Admin creates listings.

Create listing page supports:

```text
manual form entry
AI listing generator
OCR specs extraction
listing photo upload
NSFW image rejection
low-quality image warning
WebP optimization
available viewing slots
```

Human confirmation is required before saving/publishing AI-filled fields.

### 3.5 OCR Specs Extraction

Flow:

```text
Agency uploads scanned paper/document
↓
OCR extracts raw text
↓
LLM extracts listing specs
↓
Admin reviews/edits fields
↓
Confirmed fields fill listing form
```

The scanned paper is not listing media.
It is only used to extract specs.

### 3.6 Listing Image Pipeline

Flow:

```text
Agency uploads image
↓
NSFW/inappropriate content classifier
↓
If fail: reject image
↓
If pass: image quality check
↓
If quality poor: accept image but show yellow warning
↓
Convert/store optimized WebP version
↓
Save photo metadata
```

NSFW images cannot be uploaded/published.

Low-quality images are allowed with warning.

### 3.7 My Listings Page

Accessible by Agency Admin and Support Employee.

Columns:

```text
title
location
price
purpose
published yes/no
available viewing dates
created date
actions
```

Status values:

```text
Published
Not Published
```

### 3.8 Leads Page

Lead processing:

```text
Structured lead created from user side
↓
ML spam detector checks spam/not spam
↓
If spam: move to Spam Leads
↓
If not spam: NLP classifies Hot or Normal
↓
Lead appears in Leads page
```

Leads page filters:

```text
Hot
Normal
Reviewed
Not Reviewed
```

Separate section:

```text
Spam Leads
```

Lead table columns:

```text
client name
email
phone
listing
intent rent/sale
budget
lead level Hot/Normal
reviewed yes/no
reviewed by
created date
actions
```

### 3.9 Lead Detail Page

Includes:

```text
lead details
AI spam/level classification
one suggested reply
WhatsApp external draft action
Email external draft action
mark as reviewed
```

External reply rule:

```text
App opens WhatsApp/email page with drafted reply.
Support employee sends externally.
Reply is not sent automatically inside app.
```

### 3.10 Reviewed Leads

When marked reviewed, store:

```text
reviewed = true
reviewed_by_employee_id
reviewed_by_employee_name
reviewed_at
```

### 3.11 Viewing Schedules Page

Accessible by:

```text
Agency Admin
Support Employee
```

Purpose:

```text
See and filter all scheduled viewings for agency listings.
```

Filters:

```text
date
listing
client name
status
upcoming/past
today/this week
```

Statuses:

```text
Scheduled
Confirmed
Cancelled
Completed
No-show
```

Actions:

```text
view listing
view user/contact info
confirm
cancel
mark completed
mark no-show
```

### 3.12 Agency Dashboard

Agency Admin dashboard includes:

```text
forecasted possible sales next month
reviewed leads today
reviewed leads this week
lead distribution: Hot / Normal / Spam
```

No listing performance section unless added later.
No response/review activity explanation unless added later.

### 3.13 Support Employees Page

Agency Admin can:

```text
add support employee
edit support employee
deactivate support employee
reset password
```

Add fields:

```text
full name
email
first login password
role = support_employee
```

---

## 4. Platform Admin Requirements

Platform admin must be built with:

```text
Streamlit + Python
```

Platform Admin can view:

```text
marketplace demand insights
popular searched areas
popular budgets
popular property types
demand/supply gaps
search volume trends
AI audit logs
role/permission overview if needed
```

Platform admin should not be implemented as React unless user changes decision.

---

## 5. RAG Architecture Requirements

### 5.1 RAG Types

The app uses three RAG contexts:

```text
agency policy RAG
agency support assistant RAG
area/neighborhood search RAG
```

Area RAG uses platform-owned data and tenant:

```text
tenant_id = company_internal
```

Agency RAG uses actual agency tenant IDs.

### 5.2 Storage Responsibilities

Use:

```text
MinIO = original documents + extracted page text
Postgres = metadata + blob links + vector IDs + hashes
pgvector = embeddings + minimal filter metadata
```

Metadata source of truth is Postgres, not blob metadata JSON.

### 5.3 MinIO Paths

Original document:

```text
rag-vault/{tenant_id}/{document_id}/original/original.pdf
```

Extracted page text:

```text
rag-vault/{tenant_id}/{document_id}/pages/page_001.txt
rag-vault/{tenant_id}/{document_id}/pages/page_002.txt
```

Public property images should use a separate bucket/prefix:

```text
property-media/{agency_id}/{listing_id}/photos/{photo_id}.webp
```

### 5.4 Postgres RAG Tables

Required conceptual tables:

```text
rag_documents
rag_pages
rag_chunks
rag_retrieval_logs
area_knowledge_documents
```

`rag_documents` stores:

```text
id
tenant_id
document_type
original_filename
doc_source
mime_type
uploaded_by
status
version
created_at
updated_at
```

`rag_pages` stores:

```text
id
tenant_id
document_id
page_number
page_source
text_hash
has_previous_page_overlap
overlap_chars_from_previous_page
created_at
updated_at
```

`rag_chunks` stores:

```text
id
tenant_id
document_id
page_id
page_number
chunk_index
chunk_hash
vector_id
chunking_strategy
embedding_model
created_at
updated_at
```

Chunk metadata must link to document source and page source through:

```text
rag_chunks → rag_pages → rag_documents
```

### 5.5 Page Parent-Child Chunking

Large PDFs are processed page-by-page.

For a 100-page PDF:

```text
page_001.txt
page_002.txt
...
page_100.txt
```

Each page is a parent context block stored in MinIO.

Child chunks are generated from the page and embedded into pgvector.

### 5.6 Previous-Page Overlap

When needed, use an overlap buffer:

```text
last ~200 characters from previous page + current page text
```

This prevents broken meaning between page boundaries.

### 5.7 CDC / fastcdc Child Chunking

Ingestion must use CDC/fastcdc child chunks.

Flow:

```text
PDF page extracted
↓
previous-page overlap added when needed
↓
parent page text stored in MinIO
↓
CDC/fastcdc creates child chunks
↓
chunk hashes generated
↓
new/changed chunks embedded
↓
unchanged chunks skipped
```

### 5.8 Deletion Handling for Removed Policy Text

When a policy is removed from a document:

```text
Document is re-ingested
↓
CDC re-scans updated document
↓
Deleted text no longer generates hashes
↓
Backend gathers new hashes for document_id
↓
Backend queries old hashes from Postgres rag_chunks
↓
orphaned_hashes = old_hashes - new_hashes
↓
Batch delete orphaned vectors from pgvector
↓
Delete orphaned rows from rag_chunks
↓
Upsert new/changed chunks
↓
Keep unchanged chunks
```

CDC is used for both chunking and deletion/change detection.

### 5.9 Retrieval Flow

Flow:

```text
User/employee query
↓
Determine RAG context and tenant_id
↓
Embed query
↓
pgvector search with tenant/document_type metadata filtering
↓
Return matching child chunks
↓
Cohere reranker reranks where useful
↓
Backend uses page_id/document_id to get page_source from Postgres
↓
Fetch full parent page from MinIO
↓
LLM answers using parent context
```

### 5.9a RAG Quality Evaluation

RAG features must ship with evaluation, not just manual testing.

Use RAGAS or equivalent evaluation tooling for:

```text
retrieval precision/recall where measurable
faithfulness
answer relevance
context relevance
groundedness regressions
```

RAG evaluation requires:

```text
representative eval dataset
baseline scores before release
repeatable local/CI eval command
tracked regressions when chunking, retrieval, reranking, or prompts change
```

Do not call RAG production-ready until eval coverage exists for the relevant RAG context.

### 5.10 Area/Neighborhood RAG Document Shape

Reference shape:

```json
{
  "area_name": "Baabda",
  "parent_district": "Baabda District",
  "driving_time_to_beirut": {
    "normal_mins": 15,
    "rush_hour_mins": 40
  },
  "tags": ["calm", "residential", "mountain_view", "green"],
  "vibe_description": "A very quiet and secure residential area located in the hills overlooking Beirut. It features less traffic, cleaner air, and a peaceful atmosphere perfect for families."
}
```

This structure is a reference and may change later.

---

## 6. AI Provider and AI Workflow Rules

### 6.1 Provider Interfaces

Use interfaces for:

```text
chat/completion provider
embedding provider
reranking provider
OCR provider
STT provider
TTS provider
image moderation provider
image quality provider
spam classifier provider
lead classifier provider
```

Support multiple AI providers for fallback-ready design.

First implementation may use one primary provider.

Do not hardcode provider logic inside feature services.

### 6.2 Cohere Reranking

Use Cohere rerankers where useful for:

```text
agency policy RAG
support assistant RAG
area/neighborhood RAG
```

Do not use reranking for normal database search.

### 6.3 AI Workflows

Must support:

```text
LLM search filter extraction
area RAG location expansion
STT voice search
optional TTS voice reply
listing widget intent routing
listing question answering
agency policy question answering
inquiry preview generation
scheduled viewing assistant flow
AI comparison summary
AI listing generator
OCR specs extraction
NSFW image check
image quality check
ML spam detection
NLP Hot/Normal lead classifier
AI suggested reply generation
agency support assistant
agency dashboard summarization
platform demand insight summarization
```

### 6.4 Guardrails and Streaming

Chatbot-style AI flows must use a guardrail layer before production release.

Use NeMo Guardrails or equivalent for:

```text
input policy checks
output policy checks
unsafe request handling
tenant/agency boundary constraints
fallback behavior when guardrails trigger
```

AI chat/widget responses should support HTTP streaming where the UX benefits from it.

Streaming implementation must include:

```text
chunked HTTP response transport
client-side incremental rendering
cancel handling
timeout handling
partial-response recovery
safe logging without storing raw sensitive text by default
```

Do not implement full-buffered chatbot responses as the final production path.

---

## 7. Reliability, Events, Queues

### 7.1 Redis Usage

Use Redis for:

```text
cache
rate limiting
queues/background jobs
token blacklist/session invalidation
scheduled reminders
```

### 7.2 Background Jobs

Use workers for:

```text
OCR
RAG ingestion
image moderation
image quality checking
WebP image optimization
email sending
scheduled viewing reminders
AI-heavy jobs
```

Exact worker library is TBD unless already chosen by the user.

### 7.3 Outbox/Inbox Pattern

Use outbox/inbox where reliability matters:

```text
lead.created
viewing.scheduled
viewing.cancelled
rag.document_uploaded
listing.image_uploaded
email.notification_requested
```

Queue delivery is at-least-once.

Workers must be idempotent.

### 7.4 Pub/Sub

Use pub/sub only where multiple modules need the same event.

Example useful events:

```text
lead.created → notifications + analytics + future time-series event store
viewing.scheduled → email + reminders + analytics
rag.document_uploaded → ingestion worker + audit log
listing.image_uploaded → image worker + audit log
```

Do not use pub/sub everywhere.

### 7.5 Transactions

Use all-or-nothing transactions for:

```text
lead creation
scheduled viewing creation
listing publish
RAG metadata writes
outbox event creation
reviewed lead update
viewing status update
```

### 7.6 Worker Reliability

Background workers must be production reliable before handling user-visible or AI-heavy workflows.

Worker reliability includes:

```text
bounded concurrency
retry policy with exponential backoff
dead-letter state and visibility
idempotency keys per job/event
job timeout handling
poison-message handling
operational metrics
structured worker logs
replay/recovery procedure
```

Outbox-backed jobs must be at-least-once and idempotent by design.

### 7.7 Semantic Cache

Semantic caching may be added only after the source-of-truth search/RAG behavior is correct.

Use Redis vector search or equivalent for semantic cache when AI/search traffic justifies it.

Semantic cache requirements:

```text
separate cache from source-of-truth database results
tenant-aware cache keys and metadata
vector similarity lookup
TTL policy
explicit invalidation policy
cache hit/miss metrics
guardrail-aware cache reads for AI responses
```

Do not use semantic cache to bypass tenant isolation, RAG freshness, or moderation/guardrail checks.

---

## 8. Security and Performance Rules

### 8.1 Auth

Use:

```text
JWT access token
JWT refresh token
JWT invalidation
```

JWT invalidation must support:

```text
logout
password reset
employee deactivation
suspicious session revocation
```

Use Redis for blacklist/session invalidation where needed.

### 8.2 RBAC and Tenant Isolation

Every protected query and AI tool call must enforce:

```text
actor_id
role
tenant_id
permissions
```

Tenant isolation is mandatory for:

```text
listings
leads
scheduled viewings
policy documents
RAG chunks
AI tool calls
audit logs
agency metrics
```

### 8.3 Rate Limiting

Use rate limiting by IP/session/user for:

```text
login
registration
AI endpoints
search
file uploads
lead creation
viewing booking
```

### 8.4 PII Redaction

Use Presidio or equivalent where PII may enter:

```text
AI logs
AI prompts
RAG logs
audit logs
```

### 8.5 Pagination

Use pagination for:

```text
listings
leads
scheduled viewings
saved listings
RAG documents
AI audit logs
platform admin tables
agency employees
```

### 8.6 PgBouncer

Use PgBouncer for PostgreSQL connection pooling.

### 8.7 Cache Invalidation

Use cache invalidation for:

```text
listing search
agency dashboard metrics
RAG retrieval cache
platform demand insights
```

### 8.8 UI Loading

React user and agency apps must use skeleton loading for slow pages.

---

# 9. Phased Implementation Plan

## Phase 0 — Spec Kit Preparation and Guardrails

Purpose: Make sure Spec Kit has clear constraints before generating work.

Deliverables:

```text
constitution.md reviewed
spec.md generated
clarifications resolved
PLAN.md accepted
tasks.md must be phase-based
```

Rules:

```text
Do not implement app features here.
Do not generate all implementation work into Phase 1.
```

Stop gate:

```text
User confirms constitution/spec/plan are accepted.
```

---

## Phase 1 — Infrastructure and Docker Compose Foundation

Purpose: Start all required services locally before app features.

Include only:

```text
repo structure
Docker Compose
PostgreSQL with pgvector
Redis
MinIO
PgBouncer
backend container skeleton
user React container skeleton
agency React container skeleton
Streamlit admin container skeleton
worker container skeleton
.env.example
health checks
basic README/quickstart
```

Acceptance criteria:

```text
docker compose up starts all services
Postgres reachable through PgBouncer
pgvector extension enabled
Redis reachable
MinIO reachable
FastAPI health endpoint works
React apps boot
Streamlit boots
worker boots and can connect to Redis
```

Do not implement:

```text
auth
listings
RAG
AI
leads
viewings
```

---

## Phase 2 — Backend Core Foundation

Purpose: Build backend foundation before domain features.

Implement:

```text
FastAPI app structure
central config/settings module
lifespan startup/shutdown
async DB session
Redis client
MinIO client
PgBouncer connection config
Alembic migrations setup
base exception handling
logging
request ID middleware
pagination helpers
transaction helper/unit of work
base repository pattern
background worker entrypoint
outbox/inbox base tables
email service interface
AI provider interfaces only, no provider logic yet
```

Acceptance criteria:

```text
backend starts cleanly
migrations run
settings load from env
DB/Redis/MinIO clients connect
base tests pass
```

---

## Phase 3 — Auth, RBAC, and Tenant Isolation

Purpose: Secure app before multi-tenant domain work.

Implement:

```text
users
roles
permissions
agencies base tenant model
agency employees
password hashing
login
JWT access token
refresh token
logout
JWT invalidation/token blacklist
password reset flow skeleton
employee deactivation
role guards
tenant context middleware
tenant-aware repository helper
rate limiting base
```

Acceptance criteria:

```text
user can login/refresh/logout
invalidated tokens stop working
employee deactivation blocks access
role guards work
tenant context is available in services
rate limits apply to auth endpoints
```

---

## Phase 4 — Core Domain Database and CRUD APIs

Purpose: Create core tables and CRUD APIs without AI.

Implement domain models/repositories/services/routes for:

```text
agency profile
agency employees management
listings
listing photos metadata
listing viewing slots
scheduled viewings
scheduled viewing status history
saved listings
comparison sessions/items
leads
lead spam result table
lead level result table
lead suggested replies
reviewed lead records
notifications
search logs
domain event/transaction logs
```

Acceptance criteria:

```text
migrations create all core domain tables
CRUD works for agencies/listings/viewing slots/leads/viewings
tenant isolation tests pass
support employee restrictions enforced
pagination works on list endpoints
```

No AI yet.
No RAG yet.
No image processing yet.

---

## Phase 5 — User App Core UI Without AI

Purpose: Build user-facing browsing flows before AI integration.

Implement React pages:

```text
homepage manual search
filter form
listings page
listing cards
sorting/filtering
pagination
save listing
comparison selection
comparison page basic table
listing detail page
inquiry form placeholder
manual viewing booking flow
profile page
saved listings tab
submitted inquiries tab
scheduled viewings tab
skeleton loading states
```

Acceptance criteria:

```text
user can search manually
user can browse listings
user can open listing
user can save listing
user can compare up to four listings
user can book viewing manually
user can see scheduled viewings
```

Do not add listings page chatbot.
Do not add match score.

---

## Phase 6 — Agency Dashboard Core UI Without AI

Purpose: Build agency operations UI before AI integration.

Implement React pages:

```text
agency profile settings
support employees management
create listing manual form
my listings page
listing viewing slots manager
leads page
spam leads section placeholder
lead detail page
reviewed leads page
viewing schedules page
agency dashboard basic cards
policy document upload page placeholder
skeleton loading states
```

Enforce:

```text
Agency Admin permissions
Support Employee restrictions
```

Acceptance criteria:

```text
agency admin can manage profile/employees/listings
support employee cannot create listing or manage employees
agency admin and support employee can view scheduled viewings
viewing schedules filters work
lead review tracking works
```

---

## Phase 7 — Media Pipeline and Listing Image Processing

Purpose: Add MinIO media upload and image processing before AI listing workflows.

Implement:

```text
listing photo upload to MinIO
property-media bucket/prefix
image metadata table updates
upload validation
file type/size limits
NSFW provider interface
image quality provider interface
worker job for listing.image_uploaded
NSFW rejection flow
low-quality warning flow
WebP optimization
image derivative storage strategy
signed URL or CDN-ready access strategy
image upload audit logs
```

Acceptance criteria:

```text
safe image uploads successfully
invalid files are rejected before storage
NSFW image is rejected
low-quality image is accepted with warning
WebP optimized image is stored
photo metadata has blob path and status
media URLs are access-controlled or explicitly public-safe
```

If exact image moderation/quality libraries are unknown, mark NEEDS CLARIFICATION.

---

## Phase 8 — RAG Storage and Ingestion Foundation

Purpose: Build RAG infrastructure before AI assistants use it.

Implement:

```text
rag_documents table
rag_pages table
rag_chunks table
rag_retrieval_logs table
area_knowledge_documents table
MinIO rag-vault paths
document upload service
PDF page extraction
page text storage in MinIO
page metadata in Postgres
previous-page overlap buffer
CDC/fastcdc child chunking
chunk hashing
pgvector embedding storage
old hash vs new hash comparison
orphan chunk deletion
RAG ingestion worker
rag.document_uploaded outbox event
RAG ingestion status API
```

Acceptance criteria:

```text
policy PDF uploads to MinIO
pages are extracted and stored
chunks are generated and hashed
embeddings are stored in pgvector
re-ingestion skips unchanged chunks
removed text deletes orphaned chunks
metadata is stored in Postgres, not MinIO metadata files
```

---

## Phase 9 — RAG Retrieval, Cohere Reranking, and Area Search RAG

Purpose: Enable retrieval for policies and area search.

Implement:

```text
query embedding
pgvector retrieval with tenant_id filtering
parent page fetch from MinIO
Cohere reranker provider interface/integration
agency policy RAG retrieval
support assistant RAG retrieval
area/neighborhood RAG retrieval
company_internal tenant for area docs
area metadata filtering
doc_source/page_source resolution via Postgres joins
RAG retrieval logs
RAGAS evaluation dataset
RAGAS evaluation command
baseline retrieval/answer-quality metrics
semantic cache design spike only if retrieval load justifies it
```

Acceptance criteria:

```text
agency RAG retrieves only selected agency docs
support assistant RAG retrieves only employee agency docs
area RAG expands vague locations like around Beirut
retrieval fetches parent page from MinIO after child match
Cohere reranking works where configured
RAGAS evaluation runs and records baseline quality
retrieval changes can be regression-tested
```

---

## Phase 10 — Search, AI Text Search, and Voice Search

Purpose: Add AI search on top of stable DB search and RAG.

Implement:

```text
LLM filter extraction provider
AI search endpoint
editable confirmation panel integration
area RAG expansion for vague locations
manual DB search final query
STT provider interface/integration
voice search endpoint
optional TTS provider interface/integration
search logs
rate limiting on search/AI search
```

Acceptance criteria:

```text
manual search works
AI text search extracts filters
vague area queries use area RAG
voice search converts speech to text and extracts filters
user confirms filters before search
```

No match score.

---

## Phase 11 — Listing AI Widget and User AI Flows

Purpose: Add contextual listing AI after listing/search/RAG are ready.

Implement:

```text
listing widget UI
listing widget API
HTTP streaming response endpoint
client-side streaming renderer
cancel/timeout handling
NeMo Guardrails or equivalent guardrail layer
guardrail fallback UI
intent router
listing_question flow
agency_policy_question flow
create_inquiry flow
schedule_viewing flow
unclear_request flow
inquiry preview generation
viewing confirmation flow
controlled tool calls
AI audit logs
PII redaction where needed
semantic cache integration only for safe repeat AI/RAG responses
```

Acceptance criteria:

```text
widget answers listing questions from listing data
widget answers policy questions from selected agency RAG
widget streams responses with cancel/timeout behavior
guardrails block unsafe or out-of-scope requests
widget creates structured Lead only after user confirmation
widget creates ScheduledViewing only after user confirmation
widget cannot access wrong agency data
no buyer-agency chat is created
semantic cache never bypasses tenant isolation or guardrails
```

---

## Phase 12 — Agency AI Workflows

Purpose: Add agency AI features after core agency UI and RAG work.

Implement:

```text
AI listing generator
OCR specs extraction
agency support assistant
lead suggested reply generator
agency assistant provider layer
AI comparison summary
agency dashboard summarization if needed
```

Acceptance criteria:

```text
admin can generate listing copy
admin reviews before save
OCR extracts specs from scanned docs
support assistant answers from agency RAG
lead detail shows one suggested reply
WhatsApp/email opens externally with draft
```

---

## Phase 13 — Lead Processing Pipeline

Purpose: Add spam and Hot/Normal lead classification.

Implement:

```text
lead.created outbox event
ML spam classifier provider
spam result storage
Spam Leads section integration
NLP Hot/Normal classifier provider
lead level result storage
lead list filters
reviewed lead actions
analytics/domain event storage for time-series model
```

Acceptance criteria:

```text
new lead is checked for spam first
spam lead goes to Spam Leads
non-spam lead gets Hot/Normal classification
support employee can mark reviewed
review metadata is stored
```

---

## Phase 14 — Scheduled Viewings Pipeline and Notifications

Purpose: Make scheduled viewings operational and notify users/agencies.

Implement:

```text
viewing.scheduled event
viewing.cancelled event
email notification service
viewing reminders
scheduled jobs/queues
viewing status transitions
agency viewing filters
user scheduled viewings tab updates
idempotent notification worker
worker retry/backoff policy
worker concurrency limits
dead-letter visibility for failed notification/reminder jobs
job timeout handling
```

Acceptance criteria:

```text
viewing booking creates ScheduledViewing
user sees scheduled viewing
agency admin/support employee sees scheduled viewing
status transitions work
emails/reminders are queued and idempotent
failed jobs retry with backoff and become visible when dead-lettered
duplicate events do not create duplicate notifications
```

---

## Phase 15 — Platform Admin Streamlit

Purpose: Add platform admin dashboard after event/search data exists.

Implement Streamlit app:

```text
platform admin login/session handling
marketplace demand insights
popular searched areas
popular budgets
popular property types
demand gaps
search volume trends
AI audit logs viewer
role/permission overview if needed
```

Acceptance criteria:

```text
Streamlit admin boots
admin can view demand insights
admin can view AI audit logs
admin cannot mutate agency data unless endpoint explicitly allows it
```

---

## Phase 16 — Observability, Security Hardening, and Compliance

Purpose: Add professional reliability/security polish.

Implement:

```text
AI audit logs
tool call logs
RAG retrieval logs
request/error logs
distributed request tracing
security event visibility
metrics and alerts
worker/job monitoring
dead-letter dashboards or admin visibility
semantic cache hit/miss metrics where enabled
RAGAS scheduled or CI regression evaluation
Presidio or equivalent PII redaction
rate limit coverage
JWT invalidation tests
tenant isolation tests
RBAC tests
outbox/inbox idempotency tests
worker retry/dead-letter/idempotency tests
RAG deletion/hash tests
RAGAS quality regression tests
cache invalidation tests
```

Acceptance criteria:

```text
sensitive AI flows are logged safely
PII redaction applied where needed
unauthorized tenant access is blocked
queue jobs are idempotent
worker failures are observable and recoverable
critical metrics and alerts exist for API, workers, RAG, and AI flows
RAG quality regressions are caught before release
critical tests pass
```

---

## Phase 17 — Demo Data, Integration Testing, and MVP Validation

Purpose: Prepare final demo and validate all flows.

Implement:

```text
seed users
seed agencies
seed agency admins
seed support employees
seed listings
seed viewing slots
seed leads
seed scheduled viewings
seed area knowledge docs
seed agency policy docs
seed search logs
seed dashboard metrics
end-to-end happy path tests
final acceptance checklist
```

Happy paths to validate:

```text
user AI search around Beirut → area RAG → listings
user opens listing → asks policy question → selected agency RAG answer
user creates inquiry → lead pipeline → agency sees Hot/Normal or Spam
user schedules viewing → user tab + agency Viewing Schedules page
agency uploads policy doc → RAG ingestion works
agency uploads listing image → NSFW/quality/WebP pipeline works
support employee replies externally and marks lead reviewed
platform admin sees demand insights
```

---

# 10. Final Spec Kit Task Generation Instruction

When generating `tasks.md`, the agent must follow this phase structure.

The agent must not combine all app work into Phase 1.

Each phase must have:

```text
phase name
purpose
dependent previous phases
tasks
deliverables
acceptance criteria
stop gate
```

Use `[P]` only for tasks that can safely run in parallel without touching the same files.

Do not generate tasks for removed/out-of-scope features.

---

# 11. Recommended Task Phase Order

Use this exact order:

```text
Phase 0: Spec Kit Preparation and Guardrails
Phase 1: Infrastructure and Docker Compose Foundation
Phase 2: Backend Core Foundation
Phase 3: Auth, RBAC, and Tenant Isolation
Phase 4: Core Domain Database and CRUD APIs
Phase 5: User App Core UI Without AI
Phase 6: Agency Dashboard Core UI Without AI
Phase 7: Media Pipeline and Listing Image Processing
Phase 8: RAG Storage and Ingestion Foundation
Phase 9: RAG Retrieval, Cohere Reranking, and Area Search RAG
Phase 10: Search, AI Text Search, and Voice Search
Phase 11: Listing AI Widget and User AI Flows
Phase 12: Agency AI Workflows
Phase 13: Lead Processing Pipeline
Phase 14: Scheduled Viewings Pipeline and Notifications
Phase 15: Platform Admin Streamlit
Phase 16: Observability, Security Hardening, and Compliance
Phase 17: Demo Data, Integration Testing, and MVP Validation
```

---

# 12. Production Readiness Definition

The implementation is production-ready when:

```text
all apps boot locally through Docker Compose
backend has stable modular monolith structure
auth/RBAC/tenant isolation work
manual and AI search work
area RAG handles vague Beirut-area queries
listing page AI widget works with selected listing + selected agency RAG
inquiries create leads
viewings create ScheduledViewing records, not leads
agency dashboard handles listings/leads/viewings/policies/employees
RAG ingestion/retrieval/deletion works
RAGAS or equivalent RAG quality evaluation exists
NeMo Guardrails or equivalent guardrails protect chatbot-style AI flows
HTTP streaming works for chatbot-style responses
semantic cache, where enabled, is tenant-safe and observable
images go through NSFW/quality/WebP pipeline
media uploads enforce validation and access strategy
platform admin Streamlit shows demand insights and audit logs
workers have retry/backoff, idempotency, dead-letter visibility, and monitoring
observability covers API, workers, RAG, AI, security, and critical user journeys
critical tests pass
seed demo data exists
```
