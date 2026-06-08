# Tasks: Akarai MVP

**Input**: Design documents from `specs/001-akarai-mvp/`

**Prerequisites**: plan.md, spec.md, research.md, data-model.md, contracts/openapi.yaml, quickstart.md

**Tests**: Required by constitution and planning brief. Write tests before implementation for service behavior, API routes, RBAC/tenant isolation, transactions, RAG ingestion, queue idempotency, and UI smoke coverage.

**Organization**: Tasks are dependency-ordered by shared foundation first, then independently testable user stories.

## Format: `[ID] [P?] [Story] Description`

- **[P]**: Can run in parallel because it touches different files and does not depend on an incomplete task.
- **[Story]**: Used only in user-story phases: [US1], [US2], [US3], [US4].
- Every task includes an exact file path.

## Phase 1: Project Foundation

**Purpose**: Create the repository skeleton, local services, config, and base test harness.

- [ ] T001 Create root project README with local architecture summary in README.md
- [ ] T002 Create backend Python project config in backend/pyproject.toml
- [ ] T003 Create backend package skeleton in backend/app/main.py
- [ ] T004 Create FastAPI lifespan resource wiring in backend/app/core/lifespan.py
- [ ] T005 Create central settings module with HashiCorp Vault bootstrap in backend/app/core/settings.py
- [ ] T006 Create Vault client wrapper in backend/app/core/vault.py
- [ ] T007 Create async database session setup in backend/app/core/database.py
- [ ] T008 Create Redis client setup in backend/app/core/redis.py
- [ ] T009 Create MinIO client setup in backend/app/core/storage.py
- [ ] T010 Create PgBouncer-compatible SQLAlchemy configuration in backend/app/core/database.py
- [ ] T011 Create Alembic configuration in backend/alembic.ini
- [ ] T012 Create initial Alembic env file in backend/alembic/env.py
- [ ] T013 Create structured logging setup in backend/app/core/logging.py
- [ ] T014 Create backend test configuration in backend/pytest.ini
- [ ] T015 [P] Create backend unit test package in backend/tests/unit/__init__.py
- [ ] T016 [P] Create backend integration test package in backend/tests/integration/__init__.py
- [ ] T017 [P] Create backend RBAC test package in backend/tests/rbac/__init__.py
- [ ] T018 [P] Create backend RAG test package in backend/tests/rag/__init__.py
- [ ] T019 [P] Create user React app package config in apps/user/package.json
- [ ] T020 [P] Create agency React app package config in apps/agency/package.json
- [ ] T021 [P] Create Streamlit admin project config in admin/pyproject.toml
- [ ] T022 Create Docker Compose services for postgres, pgvector, redis, minio, pgbouncer, and vault in infra/docker-compose.yml
- [ ] T023 Create non-secret environment example in .env.example
- [ ] T024 Create base CI test command documentation in docs/dev-commands.md

---

## Phase 2: Auth, RBAC, and Tenant Isolation

**Purpose**: Blocking identity, tenant, permissions, and rate-limit infrastructure.

- [ ] T025 [P] Create auth models for users, sessions, refresh tokens, and password resets in backend/app/auth/models.py
- [ ] T026 [P] Create role and permission models in backend/app/auth/models.py
- [ ] T027 [P] Create agency employee auth model links in backend/app/agencies/models.py
- [ ] T028 Create auth schemas for login, refresh, logout, and password reset in backend/app/auth/schemas.py
- [ ] T029 Create auth repository for users, refresh tokens, and sessions in backend/app/auth/repository.py
- [ ] T030 Create token service for short-lived access tokens and refresh tokens in backend/app/auth/service.py
- [ ] T031 Create Redis token blacklist/session invalidation service in backend/app/auth/session_store.py
- [ ] T032 Create logout and password reset flows in backend/app/auth/service.py
- [ ] T033 Create employee deactivation session revocation flow in backend/app/agencies/service.py
- [ ] T034 Create auth router endpoints from contract in backend/app/auth/router.py
- [ ] T035 Create tenant context middleware in backend/app/core/tenant.py
- [ ] T036 Create RBAC permission dependency helpers in backend/app/auth/dependencies.py
- [ ] T037 Create role-based route protection utilities in backend/app/auth/permissions.py
- [ ] T038 Create rate-limit middleware by IP/session/user in backend/app/core/rate_limit.py
- [ ] T039 Register auth, tenant, and rate-limit middleware in backend/app/main.py
- [ ] T040 [P] Create unit tests for token service in backend/tests/unit/test_auth_tokens.py
- [ ] T041 [P] Create integration tests for auth routes in backend/tests/integration/test_auth_routes.py
- [ ] T042 [P] Create JWT invalidation tests in backend/tests/integration/test_jwt_invalidation.py
- [ ] T043 [P] Create RBAC route protection tests in backend/tests/rbac/test_role_permissions.py
- [ ] T044 [P] Create tenant isolation tests for agency-scoped access in backend/tests/rbac/test_tenant_isolation.py
- [ ] T045 [P] Create rate-limit tests for login, search, uploads, leads, and viewings in backend/tests/integration/test_rate_limits.py

---

## Phase 3: Core Domain Models and API Shells

**Purpose**: Shared database entities and feature module skeletons used by all user stories.

- [ ] T046 Create users feature files in backend/app/users/router.py
- [ ] T047 Create users models, schemas, repository, and service in backend/app/users/models.py
- [ ] T048 Create agencies feature files in backend/app/agencies/router.py
- [ ] T049 Create agencies schemas, repository, service, and employee permissions in backend/app/agencies/schemas.py
- [ ] T050 Create listings feature files in backend/app/listings/router.py
- [ ] T051 Create listing, listing photo, and viewing slot models in backend/app/listings/models.py
- [ ] T052 Create listing schemas, repository, service, and search query service in backend/app/listings/schemas.py
- [ ] T053 Create leads feature files in backend/app/leads/router.py
- [ ] T054 Create lead, spam result, level result, suggested reply, and review models in backend/app/leads/models.py
- [ ] T055 Create leads schemas, repository, service, and list query service in backend/app/leads/schemas.py
- [ ] T056 Create viewings feature files in backend/app/viewings/router.py
- [ ] T057 Create scheduled viewing and status history models in backend/app/viewings/models.py
- [ ] T058 Create viewings schemas, repository, service, and schedule query service in backend/app/viewings/schemas.py
- [ ] T059 Create comparison models in backend/app/listings/comparison_models.py
- [ ] T060 Create saved listing models in backend/app/users/saved_listing_models.py
- [ ] T061 Create notifications feature files in backend/app/notifications/router.py
- [ ] T062 Create notification models, schemas, repository, and service in backend/app/notifications/models.py
- [ ] T063 Create audit feature files in backend/app/audit/router.py
- [ ] T064 Create AI audit and tool call log models in backend/app/audit/models.py
- [ ] T065 Create metrics feature files in backend/app/metrics/router.py
- [ ] T066 Create marketplace and agency dashboard metric models in backend/app/metrics/models.py
- [ ] T067 Create domain event transaction model in backend/app/metrics/domain_events.py
- [ ] T068 Create initial migration for auth and core domain tables in backend/alembic/versions/001_core_domain.py
- [ ] T069 [P] Create repository tests for users and agencies in backend/tests/integration/test_users_agencies_repositories.py
- [ ] T070 [P] Create repository tests for listings and photos in backend/tests/integration/test_listings_repositories.py
- [ ] T071 [P] Create repository tests for leads and viewings in backend/tests/integration/test_leads_viewings_repositories.py
- [ ] T072 [P] Create repository tests for notifications and metrics in backend/tests/integration/test_notifications_metrics_repositories.py

---

## Phase 4: RAG Infrastructure

**Purpose**: Build tenant-aware knowledge ingestion and retrieval before AI-heavy user stories.

- [ ] T073 Create RAG feature files in backend/app/rag/router.py
- [ ] T074 Create RAG document, page, chunk, retrieval log, and area knowledge models in backend/app/rag/models.py
- [ ] T075 Create RAG schemas for documents, pages, chunks, and ingestion status in backend/app/rag/schemas.py
- [ ] T076 Create RAG repository for metadata, pages, chunks, hashes, and logs in backend/app/rag/repository.py
- [ ] T077 Create MinIO RAG storage service with original document path in backend/app/rag/storage_service.py
- [ ] T078 Create MinIO page text path helper in backend/app/rag/storage_service.py
- [ ] T079 Create PDF page extraction service in backend/app/rag/extraction_service.py
- [ ] T080 Create previous-page overlap buffer logic around 200 characters in backend/app/rag/chunking.py
- [ ] T081 Create page-level parent context builder in backend/app/rag/chunking.py
- [ ] T082 Create CDC/fastcdc child chunker adapter in backend/app/rag/chunking.py
- [ ] T083 Create chunk hashing service in backend/app/rag/hash_service.py
- [ ] T084 Create pgvector embedding repository methods in backend/app/rag/vector_repository.py
- [ ] T085 Create tenant/document_type metadata filtering in backend/app/rag/retrieval_service.py
- [ ] T086 Create child chunk retrieval then parent page fetch flow in backend/app/rag/retrieval_service.py
- [ ] T087 Create old-hash versus new-hash re-ingestion comparison in backend/app/rag/ingestion_service.py
- [ ] T088 Create orphan chunk batch deletion from pgvector and Postgres in backend/app/rag/ingestion_service.py
- [ ] T089 Create Cohere reranking adapter usage in backend/app/rag/rerank_service.py
- [ ] T090 Create agency policy RAG retrieval service in backend/app/rag/policy_retrieval.py
- [ ] T091 Create support assistant RAG retrieval service in backend/app/rag/support_retrieval.py
- [ ] T092 Create area RAG retrieval using tenant_id company_internal in backend/app/rag/area_retrieval.py
- [ ] T093 Create RAG ingestion status endpoints in backend/app/rag/router.py
- [ ] T094 Create migration for RAG tables and vector indexes in backend/alembic/versions/002_rag.py
- [ ] T095 [P] Create RAG chunk/hash deletion tests in backend/tests/rag/test_rag_reingestion_hashes.py
- [ ] T096 [P] Create RAG tenant filtering tests in backend/tests/rag/test_rag_tenant_filtering.py
- [ ] T097 [P] Create RAG parent page fetch tests in backend/tests/rag/test_rag_parent_fetch.py

---

## Phase 5: AI Provider Layer

**Purpose**: Define fallback-ready interfaces and explicit clarification tasks for unresolved provider choices.

- [ ] T098 NEEDS CLARIFICATION: choose exact LLM provider and model in specs/001-akarai-mvp/provider-decisions.md
- [ ] T099 NEEDS CLARIFICATION: choose exact embedding model in specs/001-akarai-mvp/provider-decisions.md
- [ ] T100 NEEDS CLARIFICATION: choose exact STT provider in specs/001-akarai-mvp/provider-decisions.md
- [ ] T101 NEEDS CLARIFICATION: choose exact TTS provider in specs/001-akarai-mvp/provider-decisions.md
- [ ] T102 NEEDS CLARIFICATION: choose exact OCR provider in specs/001-akarai-mvp/provider-decisions.md
- [ ] T103 NEEDS CLARIFICATION: choose exact email provider in specs/001-akarai-mvp/provider-decisions.md
- [ ] T104 NEEDS CLARIFICATION: choose exact React UI library in specs/001-akarai-mvp/provider-decisions.md
- [ ] T105 NEEDS CLARIFICATION: choose exact worker library in specs/001-akarai-mvp/provider-decisions.md
- [ ] T106 NEEDS CLARIFICATION: choose exact auth library in specs/001-akarai-mvp/provider-decisions.md
- [ ] T107 NEEDS CLARIFICATION: choose exact deployment target in specs/001-akarai-mvp/provider-decisions.md
- [ ] T108 Create AI provider interface package in backend/app/ai/providers/base.py
- [ ] T109 Create chat/completion provider interface in backend/app/ai/providers/chat.py
- [ ] T110 Create embedding provider interface in backend/app/ai/providers/embedding.py
- [ ] T111 Create reranking provider interface in backend/app/ai/providers/reranking.py
- [ ] T112 Create OCR provider interface in backend/app/ai/providers/ocr.py
- [ ] T113 Create STT provider interface in backend/app/ai/providers/stt.py
- [ ] T114 Create TTS provider interface in backend/app/ai/providers/tts.py
- [ ] T115 Create image moderation provider interface in backend/app/ai/providers/image_moderation.py
- [ ] T116 Create image quality provider interface in backend/app/ai/providers/image_quality.py
- [ ] T117 Create spam classifier provider interface in backend/app/ai/providers/spam_classifier.py
- [ ] T118 Create lead classifier provider interface in backend/app/ai/providers/lead_classifier.py
- [ ] T119 Create provider fallback registry in backend/app/ai/providers/registry.py
- [ ] T120 [P] Create provider interface unit tests in backend/tests/unit/test_ai_provider_interfaces.py

---

## Phase 6: Async Events, Queues, and Outbox/Inbox

**Purpose**: Reliable async processing for image, RAG, email, reminder, and AI-heavy jobs.

- [ ] T121 Create workers project entrypoint in workers/runner.py
- [ ] T122 Create Redis queue setup in workers/core/queue.py
- [ ] T123 Create outbox event model integration in backend/app/notifications/models.py
- [ ] T124 Create inbox event model integration in backend/app/notifications/models.py
- [ ] T125 Create event publishing service in backend/app/notifications/event_service.py
- [ ] T126 Create idempotent worker handling base class in workers/core/idempotency.py
- [ ] T127 Create retry handling and dead-letter logging in workers/core/retry.py
- [ ] T128 Create lead.created event handler in workers/notifications/lead_created.py
- [ ] T129 Create viewing.scheduled event handler in workers/reminders/viewing_scheduled.py
- [ ] T130 Create viewing.cancelled event handler in workers/reminders/viewing_cancelled.py
- [ ] T131 Create rag.document_uploaded event handler in workers/rag_ingestion/document_uploaded.py
- [ ] T132 Create listing.image_uploaded event handler in workers/image_processing/image_uploaded.py
- [ ] T133 Create email.notification_requested event handler in workers/notifications/email_requested.py
- [ ] T134 Create scheduled viewing reminder worker in workers/reminders/scheduled_viewing_reminders.py
- [ ] T135 Create migration for outbox and inbox tables in backend/alembic/versions/003_outbox_inbox.py
- [ ] T136 [P] Create queue idempotency tests in backend/tests/integration/test_queue_idempotency.py
- [ ] T137 [P] Create transaction rollback tests for outbox writes in backend/tests/integration/test_outbox_transactions.py

---

## Phase 7: User Story 1 - Search and Compare Listings (Priority: P1) MVP

**Goal**: User can search manually or with AI/voice, browse paginated results, save listings, compare up to four listings, and view an AI comparison summary.

**Independent Test**: Complete quickstart "User Search and Compare" with no match score, no chatbot, and no buyer-agency chat.

### Tests for User Story 1

- [ ] T138 [P] [US1] Create API integration tests for manual and AI search in backend/tests/integration/test_search_routes.py
- [ ] T139 [P] [US1] Create service unit tests for filter extraction orchestration in backend/tests/unit/test_search_service.py
- [ ] T140 [P] [US1] Create area RAG location expansion tests in backend/tests/rag/test_area_rag_search.py
- [ ] T141 [P] [US1] Create comparison limit tests in backend/tests/integration/test_comparison_routes.py
- [ ] T142 [P] [US1] Create user app search smoke tests in apps/user/src/__tests__/search-flow.test.tsx

### Implementation for User Story 1

- [ ] T143 [US1] Implement manual search endpoint in backend/app/listings/router.py
- [ ] T144 [US1] Implement listing search query service with filters/sorting/pagination in backend/app/listings/query_service.py
- [ ] T145 [US1] Implement AI search filter extraction orchestration in backend/app/ai/search_service.py
- [ ] T146 [US1] Implement voice search orchestration with STT provider interface in backend/app/ai/voice_search_service.py
- [ ] T147 [US1] Implement area RAG expansion call for vague locations in backend/app/rag/area_retrieval.py
- [ ] T148 [US1] Implement saved listing endpoints in backend/app/users/router.py
- [ ] T149 [US1] Implement comparison session and item endpoints in backend/app/listings/router.py
- [ ] T150 [US1] Implement AI comparison summary service in backend/app/ai/comparison_service.py
- [ ] T151 [US1] Implement homepage manual search UI in apps/user/src/pages/HomePage.tsx
- [ ] T152 [US1] Implement AI text search UI in apps/user/src/features/search/AiTextSearch.tsx
- [ ] T153 [US1] Implement AI voice search UI in apps/user/src/features/search/AiVoiceSearch.tsx
- [ ] T154 [US1] Implement editable filter confirmation panel in apps/user/src/features/search/FilterConfirmationPanel.tsx
- [ ] T155 [US1] Implement paginated listings page in apps/user/src/pages/ListingsPage.tsx
- [ ] T156 [US1] Implement listing filters and sorting controls in apps/user/src/features/listings/ListingFilters.tsx
- [ ] T157 [US1] Implement save listing control in apps/user/src/features/listings/SaveListingButton.tsx
- [ ] T158 [US1] Implement comparison selection control in apps/user/src/features/comparison/CompareToggle.tsx
- [ ] T159 [US1] Implement comparison page with AI summary placeholder in apps/user/src/pages/ComparisonPage.tsx
- [ ] T160 [US1] Add skeleton loading states for search/listings/comparison in apps/user/src/components/Skeletons.tsx

**Checkpoint**: Stop and validate user search, save, compare, and AI summary placeholder before listing AI work.

---

## Phase 8: User Story 2 - Inspect Listing and Ask AI (Priority: P1)

**Goal**: User can inspect listing detail, ask the unified listing AI widget, and confirm inquiry or viewing creation.

**Independent Test**: Complete quickstart "Listing AI Widget" with cancelled actions creating nothing and confirmed actions creating the correct record type.

### Tests for User Story 2

- [ ] T161 [P] [US2] Create listing detail route tests in backend/tests/integration/test_listing_detail_routes.py
- [ ] T162 [P] [US2] Create listing AI widget intent routing tests in backend/tests/unit/test_listing_ai_intents.py
- [ ] T163 [P] [US2] Create lead creation transaction tests in backend/tests/integration/test_lead_creation_transaction.py
- [ ] T164 [P] [US2] Create scheduled viewing transaction tests in backend/tests/integration/test_viewing_creation_transaction.py
- [ ] T165 [P] [US2] Create user app listing widget smoke tests in apps/user/src/__tests__/listing-ai-widget.test.tsx

### Implementation for User Story 2

- [ ] T166 [US2] Implement listing detail response assembly in backend/app/listings/service.py
- [ ] T167 [US2] Implement available viewing dates retrieval in backend/app/viewings/query_service.py
- [ ] T168 [US2] Implement unified listing AI widget endpoint in backend/app/ai/router.py
- [ ] T169 [US2] Implement listing widget intent routing in backend/app/ai/listing_widget_service.py
- [ ] T170 [US2] Implement listing question answering using listing context in backend/app/ai/listing_qa_service.py
- [ ] T171 [US2] Implement agency policy question answering using tenant RAG in backend/app/ai/policy_qa_service.py
- [ ] T172 [US2] Implement inquiry preview generation before create in backend/app/ai/inquiry_preview_service.py
- [ ] T173 [US2] Implement confirmed Lead creation flow in backend/app/leads/service.py
- [ ] T174 [US2] Implement scheduled viewing assistant preview and confirmation flow in backend/app/ai/viewing_assistant_service.py
- [ ] T175 [US2] Implement confirmed ScheduledViewing creation flow in backend/app/viewings/service.py
- [ ] T176 [US2] Implement listing detail page in apps/user/src/pages/ListingDetailPage.tsx
- [ ] T177 [US2] Implement unified listing AI widget UI in apps/user/src/features/ai/ListingAiWidget.tsx
- [ ] T178 [US2] Implement inquiry confirmation dialog in apps/user/src/features/leads/InquiryConfirmDialog.tsx
- [ ] T179 [US2] Implement scheduled viewing confirmation dialog in apps/user/src/features/viewings/ViewingConfirmDialog.tsx
- [ ] T180 [US2] Implement user profile page with saved listings, submitted inquiries, and scheduled viewings tabs in apps/user/src/pages/ProfilePage.tsx
- [ ] T181 [US2] Add skeleton loading states for listing detail/profile in apps/user/src/components/Skeletons.tsx

**Checkpoint**: Stop and validate listing AI, inquiry confirmation, and scheduled viewing separation.

---

## Phase 9: User Story 3 - Agency Manage Leads and Viewings (Priority: P1)

**Goal**: Agency Admin and Support Employee can operate listings, policy documents, leads, scheduled viewings, dashboard metrics, and support assistant within role limits.

**Independent Test**: Complete quickstart "Agency Leads and Viewings" and "Support Employee RBAC".

### Tests for User Story 3

- [ ] T182 [P] [US3] Create agency policy upload route tests in backend/tests/integration/test_policy_document_routes.py
- [ ] T183 [P] [US3] Create listing photo moderation tests in backend/tests/integration/test_listing_photo_upload.py
- [ ] T184 [P] [US3] Create lead processing flow tests in backend/tests/integration/test_lead_processing_flow.py
- [ ] T185 [P] [US3] Create viewing schedule filter tests in backend/tests/integration/test_viewing_schedule_filters.py
- [ ] T186 [P] [US3] Create support employee restriction tests in backend/tests/rbac/test_support_employee_restrictions.py
- [ ] T187 [P] [US3] Create agency dashboard smoke tests in apps/agency/src/__tests__/agency-dashboard.test.tsx

### Implementation for User Story 3

- [ ] T188 [US3] Implement agency profile settings endpoints in backend/app/agencies/router.py
- [ ] T189 [US3] Implement agency employees management endpoints in backend/app/agencies/router.py
- [ ] T190 [US3] Implement policy document upload and list endpoints in backend/app/rag/router.py
- [ ] T191 [US3] Implement create listing flow with AI generator hook in backend/app/listings/service.py
- [ ] T192 [US3] Implement OCR specs extraction job enqueue in backend/app/listings/service.py
- [ ] T193 [US3] Implement listing image upload checks enqueue in backend/app/listings/service.py
- [ ] T194 [US3] Implement NSFW rejection and low-quality warning persistence in backend/app/listings/service.py
- [ ] T195 [US3] Implement Lead processing flow structured lead to spam to Hot/Normal in backend/app/leads/service.py
- [ ] T196 [US3] Implement AI suggested reply generation service in backend/app/ai/lead_reply_service.py
- [ ] T197 [US3] Implement reviewed lead tracking in backend/app/leads/service.py
- [ ] T198 [US3] Implement WhatsApp/email external draft action response in backend/app/leads/router.py
- [ ] T199 [US3] Implement viewing schedule filters and status actions in backend/app/viewings/router.py
- [ ] T200 [US3] Implement agency dashboard metrics query service in backend/app/metrics/query_service.py
- [ ] T201 [US3] Implement agency support assistant endpoint in backend/app/ai/router.py
- [ ] T202 [US3] Implement agency profile settings page in apps/agency/src/pages/AgencySettingsPage.tsx
- [ ] T203 [US3] Implement policy document upload page in apps/agency/src/pages/PolicyDocumentsPage.tsx
- [ ] T204 [US3] Implement create listing page with AI generator and OCR UI in apps/agency/src/pages/CreateListingPage.tsx
- [ ] T205 [US3] Implement listing image upload UI with NSFW and quality feedback in apps/agency/src/features/listings/ImageUploadPanel.tsx
- [ ] T206 [US3] Implement My Listings page in apps/agency/src/pages/MyListingsPage.tsx
- [ ] T207 [US3] Implement Leads page with valid and spam sections in apps/agency/src/pages/LeadsPage.tsx
- [ ] T208 [US3] Implement Lead Detail page with classification and one suggested reply in apps/agency/src/pages/LeadDetailPage.tsx
- [ ] T209 [US3] Implement external WhatsApp/email draft actions in apps/agency/src/features/leads/ExternalReplyActions.tsx
- [ ] T210 [US3] Implement Viewing Schedules page with filters and status actions in apps/agency/src/pages/ViewingsPage.tsx
- [ ] T211 [US3] Implement agency dashboard metrics page in apps/agency/src/pages/DashboardPage.tsx
- [ ] T212 [US3] Implement support employees management page in apps/agency/src/pages/EmployeesPage.tsx
- [ ] T213 [US3] Implement agency support assistant UI in apps/agency/src/features/ai/SupportAssistant.tsx
- [ ] T214 [US3] Add skeleton loading states for agency dashboard pages in apps/agency/src/components/Skeletons.tsx

**Checkpoint**: Stop and validate Agency Admin and Support Employee flows with RBAC restrictions.

---

## Phase 10: User Story 4 - Platform Admin Marketplace Oversight (Priority: P2)

**Goal**: Platform Admin can inspect demand insights, search trends, AI audit logs, and role/permission overview in Streamlit.

**Independent Test**: Complete quickstart "Platform Admin".

### Tests for User Story 4

- [ ] T215 [P] [US4] Create platform demand insights route tests in backend/tests/integration/test_platform_demand_insights.py
- [ ] T216 [P] [US4] Create AI audit logs route tests in backend/tests/integration/test_ai_audit_logs.py
- [ ] T217 [P] [US4] Create Streamlit smoke tests in admin/tests/test_admin_smoke.py

### Implementation for User Story 4

- [ ] T218 [US4] Implement platform demand insights query service in backend/app/metrics/platform_query_service.py
- [ ] T219 [US4] Implement platform demand insights endpoint in backend/app/metrics/router.py
- [ ] T220 [US4] Implement AI audit logs endpoint in backend/app/audit/router.py
- [ ] T221 [US4] Implement platform role/permission overview endpoint in backend/app/auth/router.py
- [ ] T222 [US4] Create Streamlit app entrypoint in admin/app.py
- [ ] T223 [US4] Implement platform admin auth/session handling in admin/auth.py
- [ ] T224 [US4] Implement marketplace demand insights page in admin/pages/demand_insights.py
- [ ] T225 [US4] Implement search trend charts and tables in admin/pages/search_trends.py
- [ ] T226 [US4] Implement AI audit logs page in admin/pages/ai_audit_logs.py
- [ ] T227 [US4] Implement role/permission overview page in admin/pages/roles_permissions.py

**Checkpoint**: Stop and validate platform admin stays Streamlit-only and separate from tenant agency workflows.

---

## Phase 11: Security, Privacy, Observability, and Cross-Cutting Quality

**Purpose**: Hardening tasks that cut across stories after core flows exist.

- [ ] T228 Create AI audit log write hooks for all AI calls in backend/app/audit/ai_audit_service.py
- [ ] T229 Create tool call log write hooks for AI tool calls in backend/app/audit/tool_call_service.py
- [ ] T230 Create RAG retrieval logging hooks in backend/app/rag/retrieval_log_service.py
- [ ] T231 Create Presidio-compatible PII redaction service in backend/app/ai/pii_redaction.py
- [ ] T232 Wire request logging middleware in backend/app/core/request_logging.py
- [ ] T233 Wire error logging handlers in backend/app/core/error_handlers.py
- [ ] T234 Create cache invalidation helpers for listing search in backend/app/listings/cache.py
- [ ] T235 Create cache invalidation helpers for agency metrics in backend/app/metrics/cache.py
- [ ] T236 Create cache invalidation helpers for RAG retrieval in backend/app/rag/cache.py
- [ ] T237 Create cache invalidation helpers for platform demand insights in backend/app/metrics/platform_cache.py
- [ ] T238 [P] Create AI audit log tests in backend/tests/integration/test_ai_audit_logging.py
- [ ] T239 [P] Create PII redaction tests in backend/tests/unit/test_pii_redaction.py
- [ ] T240 [P] Create request/error logging tests in backend/tests/integration/test_observability.py
- [ ] T241 [P] Create cache invalidation tests in backend/tests/integration/test_cache_invalidation.py
- [ ] T242 [P] Create frontend smoke tests for user app in apps/user/src/__tests__/smoke.test.tsx
- [ ] T243 [P] Create frontend smoke tests for agency app in apps/agency/src/__tests__/smoke.test.tsx

---

## Phase 12: Demo Seed Data and Final MVP Validation

**Purpose**: Seed realistic data and run acceptance checks before implementation is considered complete.

- [ ] T244 Create seed users script in backend/scripts/seed_users.py
- [ ] T245 Create seed agencies and employees script in backend/scripts/seed_agencies.py
- [ ] T246 Create seed listings and viewing slots script in backend/scripts/seed_listings.py
- [ ] T247 Create seed leads and scheduled viewings script in backend/scripts/seed_leads_viewings.py
- [ ] T248 Create seed area knowledge documents script in backend/scripts/seed_area_knowledge.py
- [ ] T249 Create seed agency policy documents script in backend/scripts/seed_policy_documents.py
- [ ] T250 Create seed dashboard metrics script in backend/scripts/seed_dashboard_metrics.py
- [ ] T251 Create combined demo data runner in backend/scripts/seed_demo_data.py
- [ ] T252 Create full MVP happy-path validation script in backend/scripts/validate_mvp.py
- [ ] T253 Update quickstart validation commands in specs/001-akarai-mvp/quickstart.md
- [ ] T254 Create final acceptance checklist in specs/001-akarai-mvp/checklists/final-acceptance.md
- [ ] T255 Run full quickstart validation and record results in specs/001-akarai-mvp/validation-results.md

---

## Dependencies & Execution Order

### Phase Dependencies

- Phase 1 must complete first.
- Phase 2 depends on Phase 1 and blocks user story work.
- Phase 3 depends on Phase 2 and creates domain shells for all stories.
- Phase 4 depends on Phase 3 and blocks policy/area RAG work.
- Phase 5 can run after Phase 1, but concrete adapters wait on provider decisions.
- Phase 6 depends on Phases 2 and 3 and supports async side effects.
- Phase 7 (US1) depends on Phases 1-6 enough for search, area RAG, and comparison.
- Phase 8 (US2) depends on Phase 7 for listings/search and Phase 4 for policy RAG.
- Phase 9 (US3) depends on Phases 3-6 and can proceed in parallel with Phase 8 after shared dependencies.
- Phase 10 (US4) depends on metrics/audit foundations from Phases 3 and 11 service hooks.
- Phase 11 depends on story implementation surfaces but individual tests can start earlier.
- Phase 12 depends on all MVP user stories and cross-cutting checks.

### User Story Dependencies

- **US1 Search and Compare Listings**: MVP first. Independent after foundational search/RAG/provider scaffolding.
- **US2 Inspect Listing and Ask AI**: Depends on listing detail, RAG, lead, and viewing foundations; integrates with US1 listing access.
- **US3 Agency Manage Leads and Viewings**: Depends on auth/RBAC, listings, leads, viewings, RAG, AI provider interfaces, and queues.
- **US4 Platform Admin Marketplace Oversight**: Depends on audit and metrics foundations; can be delivered after core data starts flowing.

### Stop Points

- Stop after Phase 2 to verify auth, RBAC, tenant context, Vault config, and rate limits.
- Stop after Phase 7 to demo the MVP-first user search/compare slice.
- Stop after Phase 8 to verify inquiry and ScheduledViewing separation.
- Stop after Phase 9 to validate agency operations and support employee restrictions.
- Stop after Phase 12 before claiming MVP completion.

## Parallel Opportunities

- Phase 1 app skeleton tasks T019-T021 can run in parallel with backend test package tasks T015-T018.
- Phase 2 tests T040-T045 can be authored in parallel after auth interfaces are drafted.
- Phase 3 repository tests T069-T072 can run in parallel after model/repository files exist.
- Phase 4 RAG tests T095-T097 can be authored in parallel with RAG services.
- Phase 5 provider interfaces T109-T118 can be implemented in parallel after base interface T108.
- Phase 7 tests T138-T142 can run in parallel before US1 implementation.
- Phase 8 tests T161-T165 can run in parallel before US2 implementation.
- Phase 9 tests T182-T187 can run in parallel before US3 implementation.
- Phase 10 tests T215-T217 can run in parallel before US4 implementation.
- Phase 11 tests T238-T243 can run in parallel by file area.

## Parallel Example: US1

```bash
Task: "T138 [P] [US1] Create API integration tests for manual and AI search in backend/tests/integration/test_search_routes.py"
Task: "T139 [P] [US1] Create service unit tests for filter extraction orchestration in backend/tests/unit/test_search_service.py"
Task: "T140 [P] [US1] Create area RAG location expansion tests in backend/tests/rag/test_area_rag_search.py"
Task: "T142 [P] [US1] Create user app search smoke tests in apps/user/src/__tests__/search-flow.test.tsx"
```

## Parallel Example: US3

```bash
Task: "T182 [P] [US3] Create agency policy upload route tests in backend/tests/integration/test_policy_document_routes.py"
Task: "T184 [P] [US3] Create lead processing flow tests in backend/tests/integration/test_lead_processing_flow.py"
Task: "T185 [P] [US3] Create viewing schedule filter tests in backend/tests/integration/test_viewing_schedule_filters.py"
Task: "T187 [P] [US3] Create agency dashboard smoke tests in apps/agency/src/__tests__/agency-dashboard.test.tsx"
```

## Implementation Strategy

### MVP First

1. Complete Phase 1 and Phase 2.
2. Complete only the Phase 3 entities needed by US1 plus RAG/provider scaffolding needed for area search.
3. Complete Phase 7.
4. Stop and demo user search, paginated listings, save listing, comparison, and AI summary placeholder.

### Incremental Delivery

1. Add Phase 8 to validate listing detail AI, inquiries, and scheduled viewings.
2. Add Phase 9 to validate agency admin/support employee operations.
3. Add Phase 10 to validate platform admin.
4. Add Phases 11 and 12 to harden and validate the full MVP.

## Explicitly Excluded Tasks

- No buyer-to-agency real-time chat tasks.
- No match score tasks.
- No full microservices tasks.
- No BPMN runtime engine tasks.
- No DAO layer tasks.
- No generic amenities as a core MVP field.
- No manually edited policy text record tasks.
