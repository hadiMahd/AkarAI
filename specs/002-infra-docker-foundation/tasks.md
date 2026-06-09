# Tasks: Infrastructure and Docker Compose Foundation

**Input**: Design docs from `/specs/002-infra-docker-foundation/`

**Scope**: Phase 1 only. No auth, listings, RAG, AI, leads, or viewings.

## Phase 1: Repository and Project Structure

- [X] T001 Create the Phase 1 root scaffold and placeholder directories
  Files: `backend/`, `apps/user/`, `apps/agency/`, `admin/`, `workers/`, `specs/002-infra-docker-foundation/`
  Dependencies: none
  Parallel: no

- [X] T002 [P] Update `.gitignore` for Python, Node, Streamlit, Docker, coverage, and local env artifacts
  Files: `.gitignore`
  Dependencies: none
  Parallel: yes

- [X] T003 [P] Refresh `.env.example` with Phase 1 non-secret runtime values and Vault bootstrap placeholders
  Files: `.env.example`
  Dependencies: none
  Parallel: yes

- [X] T004 [P] Align `README.md` with the Phase 1 service list, startup flow, and repository layout
  Files: `README.md`
  Dependencies: none
  Parallel: yes

## Phase 1: Docker Compose Infrastructure

- [X] T005 Create the root `docker-compose.yml` with PostgreSQL + pgvector, PgBouncer, Redis, MinIO, backend, worker, user app, agency app, and Streamlit admin services
  Files: `docker-compose.yml`
  Dependencies: T001
  Parallel: no

- [X] T006 Extend `docker-compose.yml` with persistent volumes, service dependencies, exposed ports, restart policies, and environment-variable wiring
  Files: `docker-compose.yml`
  Dependencies: T005
  Parallel: no

- [X] T007 Add MinIO bootstrap in `docker-compose.yml` so `rag-vault` and `property-media` buckets are created on local startup
  Files: `docker-compose.yml`
  Dependencies: T006
  Parallel: no

- [X] T008 Add container health checks and readiness wiring in `docker-compose.yml` for PostgreSQL, PgBouncer, Redis, MinIO, backend, worker, user app, agency app, and Streamlit admin
  Files: `docker-compose.yml`
  Dependencies: T006
  Parallel: no

## Phase 1: Backend FastAPI Skeleton

- [X] T009 Create the backend app entrypoint and factory in `backend/app/main.py` and `backend/app/common/lifespan.py`
  Files: `backend/app/main.py`, `backend/app/common/lifespan.py`
  Dependencies: T001
  Parallel: no

- [X] T010 [P] Add central config/settings parsing for non-secret runtime values in `backend/app/common/config.py`
  Files: `backend/app/common/config.py`
  Dependencies: T001
  Parallel: yes

- [X] T011 [P] Add base logging and exception handling in `backend/app/common/logging.py` and `backend/app/common/exceptions.py`
  Files: `backend/app/common/logging.py`, `backend/app/common/exceptions.py`
  Dependencies: T001
  Parallel: yes

- [X] T012 [P] Add async client placeholders for PostgreSQL, Redis, and MinIO in `backend/app/common/database.py`, `backend/app/common/redis.py`, `backend/app/common/minio.py`, and `backend/app/common/dependencies.py`
  Files: `backend/app/common/database.py`, `backend/app/common/redis.py`, `backend/app/common/minio.py`, `backend/app/common/dependencies.py`
  Dependencies: T010
  Parallel: yes

- [X] T013 Create the backend health route and wire `/health` and `/ready` in `backend/app/main.py` and `backend/app/common/health.py`
  Files: `backend/app/main.py`, `backend/app/common/health.py`
  Dependencies: T009, T012
  Parallel: no

- [X] T014 [P] Create placeholder backend feature folders and empty module stubs in `backend/app/auth/`, `backend/app/users/`, `backend/app/agencies/`, `backend/app/listings/`, `backend/app/media/`, `backend/app/search/`, `backend/app/leads/`, `backend/app/viewings/`, `backend/app/rag/`, `backend/app/ai/`, `backend/app/notifications/`, `backend/app/analytics/`, `backend/app/audit/`, and `backend/app/common/`
  Files: `backend/app/auth/`, `backend/app/users/`, `backend/app/agencies/`, `backend/app/listings/`, `backend/app/media/`, `backend/app/search/`, `backend/app/leads/`, `backend/app/viewings/`, `backend/app/rag/`, `backend/app/ai/`, `backend/app/notifications/`, `backend/app/analytics/`, `backend/app/audit/`, `backend/app/common/`
  Dependencies: T001
  Parallel: yes

## Phase 1: Database and Migrations

- [X] T015 Initialize the backend database layer and Alembic scaffolding in `backend/alembic.ini`, `backend/alembic/env.py`, and `backend/alembic/versions/0001_enable_pgvector.py`
  Files: `backend/alembic.ini`, `backend/alembic/env.py`, `backend/alembic/versions/0001_enable_pgvector.py`
  Dependencies: T012
  Parallel: no

- [X] T016 [P] Add the backend test framework scaffold in `backend/pytest.ini`, `backend/tests/conftest.py`, `backend/tests/unit/__init__.py`, `backend/tests/integration/__init__.py`, `backend/tests/rbac/__init__.py`, and `backend/tests/smoke/__init__.py`
  Files: `backend/pytest.ini`, `backend/tests/conftest.py`, `backend/tests/unit/__init__.py`, `backend/tests/integration/__init__.py`, `backend/tests/rbac/__init__.py`, `backend/tests/smoke/__init__.py`
  Dependencies: T001
  Parallel: yes

- [X] T017 [P] Add a PostgreSQL through PgBouncer connectivity smoke test in `backend/tests/smoke/test_database_connectivity.py`
  Files: `backend/tests/smoke/test_database_connectivity.py`
  Dependencies: T015, T016
  Parallel: yes

- [X] T018 [P] Add a backend health endpoint smoke test in `backend/tests/smoke/test_health.py`
  Files: `backend/tests/smoke/test_health.py`
  Dependencies: T013, T016
  Parallel: yes

- [X] T019 [P] Add a Redis connectivity smoke test in `backend/tests/smoke/test_redis.py`
  Files: `backend/tests/smoke/test_redis.py`
  Dependencies: T012, T016
  Parallel: yes

- [X] T020 [P] Add a MinIO connectivity and bucket-existence smoke test in `backend/tests/smoke/test_minio.py`
  Files: `backend/tests/smoke/test_minio.py`
  Dependencies: T007, T016
  Parallel: yes

- [X] T021 [P] Add a pgvector extension smoke test in `backend/tests/smoke/test_pgvector.py`
  Files: `backend/tests/smoke/test_pgvector.py`
  Dependencies: T015, T016
  Parallel: yes

## Phase 1: React User App Skeleton

- [X] T022 Create the React + TypeScript user app skeleton in `apps/user/` with routing, API client placeholder, env wiring, base layout, and skeleton loading component
  Files: `apps/user/`
  Dependencies: T001
  Parallel: no

- [X] T023 [P] Add the user app placeholder landing/status page and startup smoke check in `apps/user/`
  Files: `apps/user/src/`, `apps/user/tests/`
  Dependencies: T022
  Parallel: yes

## Phase 1: React Agency Dashboard Skeleton

- [X] T024 Create the React + TypeScript agency dashboard skeleton in `apps/agency/` with routing, API client placeholder, env wiring, base layout, and skeleton loading component
  Files: `apps/agency/`
  Dependencies: T001
  Parallel: no

- [X] T025 [P] Add the agency dashboard placeholder landing/status page and startup smoke check in `apps/agency/`
  Files: `apps/agency/src/`, `apps/agency/tests/`
  Dependencies: T024
  Parallel: yes

## Phase 1: Streamlit Admin Skeleton

- [X] T026 Create the Streamlit admin skeleton in `admin/` with env wiring, backend health display, and a placeholder home page
  Files: `admin/`
  Dependencies: T001, T013
  Parallel: no

## Phase 1: Worker Skeleton

- [X] T027 Create the worker skeleton in `workers/` with entrypoint, Redis connection, logging, graceful startup/shutdown, and a placeholder job registry
  Files: `workers/`
  Dependencies: T012
  Parallel: no

- [X] T028 [P] Add worker startup/connectivity smoke verification in `workers/tests/test_startup.py`
  Files: `workers/tests/test_startup.py`
  Dependencies: T027, T019
  Parallel: yes

## Phase 1: Documentation and Verification

- [X] T029 Update `specs/002-infra-docker-foundation/quickstart.md` with startup, verification, shutdown, and reset commands for the Phase 1 foundation
  Files: `specs/002-infra-docker-foundation/quickstart.md`
  Dependencies: T005, T013, T015, T022, T024, T026, T027
  Parallel: no

- [X] T030 [P] Add service ports and environment-variable notes to `README.md`
  Files: `README.md`
  Dependencies: T003, T004
  Parallel: yes

- [X] T031 Run the full Phase 1 verification flow: `docker compose up`, backend `/health`, backend `/ready`, PostgreSQL through PgBouncer, Redis, MinIO, `rag-vault` and `property-media` buckets, user app boot, agency app boot, Streamlit boot, worker boot, Alembic initialization, `.env.example` presence, and base tests
  Files: `docker-compose.yml`, `backend/tests/smoke/`, `apps/user/tests/`, `apps/agency/tests/`, `workers/tests/`, `.env.example`
  Dependencies: T006, T007, T008, T017, T018, T019, T020, T021, T023, T025, T028, T029, T030
  Parallel: no

## Dependencies & Execution Order

1. Start with repository structure and local config/docs: T001-T004.
2. Build the local foundation in Docker Compose: T005-T008.
3. Stand up backend skeleton and shared clients: T009-T014.
4. Initialize database/migrations and smoke tests: T015-T021.
5. Build the frontend/admin/worker skeletons: T022-T028.
6. Finish quickstart and README alignment: T029-T030.
7. Execute the full Phase 1 verification gate: T031.

## Parallel Opportunities

- T002, T003, and T004 can run in parallel.
- T010, T011, T012, and T014 can run in parallel after T009 is in place.
- T017, T018, T019, T020, and T021 can run in parallel after the test scaffold exists.
- T023 and T025 can run in parallel with the backend/database work because they touch different app folders.
- T028, T029, and T030 can be split across contributors once the skeletons are in place.

## Implementation Strategy

1. Get `docker-compose.yml`, backend `/health`, and dependency wiring stable first.
2. Add the database/migration foundation and smoke tests next.
3. Stand up each app skeleton with a single placeholder page and startup check.
4. Finish documentation, then run the full Phase 1 verification gate once.
5. Stop at Phase 1. Do not add auth, listings, RAG, AI, leads, or viewings.
