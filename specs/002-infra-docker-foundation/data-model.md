# Data Model: Infrastructure and Docker Compose Foundation

Phase 1 has no domain data model. The records below describe configuration and
validation concepts used by the local foundation.

## Local Foundation

**Purpose**: Coordinated local environment that starts every required Phase 1
service and app skeleton.

**Fields**:
- `name`: Human-readable environment name, fixed to local development.
- `services`: Required service skeletons and backing services.
- `configuration_source`: Local configuration placeholder file.
- `status`: `not_started`, `starting`, `healthy`, `degraded`, or `failed`.

**Relationships**:
- Has many `Service Skeleton` records.
- Uses many `Configuration Placeholder` records.
- Produces many `Health Check` results.

**Validation Rules**:
- Must include data store, connection proxy, cache/queue, object store, backend
  skeleton, user app skeleton, agency app skeleton, admin skeleton, and worker
  skeleton.
- Must not include domain behavior for auth, listings, RAG, AI, leads, or
  viewings.

## Service Skeleton

**Purpose**: Minimal process that proves startup and readiness without domain
behavior.

**Fields**:
- `service_name`: Unique local service name.
- `service_type`: `backing_service`, `backend`, `frontend`, `admin`, or
  `worker`.
- `startup_signal`: Observable proof that the process started.
- `dependency_checks`: Required dependencies to verify for the service.
- `status`: `not_started`, `starting`, `healthy`, `degraded`, or `failed`.

**Relationships**:
- Belongs to one `Local Foundation`.
- Has zero or more `Health Check` records.

**Validation Rules**:
- Backend skeleton must expose a health signal.
- Worker skeleton must verify cache/queue connectivity.
- App skeletons must boot without requiring domain data.

## Configuration Placeholder

**Purpose**: Documented local setting required to start and verify Phase 1.

**Fields**:
- `key`: Configuration variable name.
- `description`: What the value controls.
- `is_secret`: Must be false for committed placeholders.
- `example_value`: Non-secret sample or bootstrap placeholder.
- `required_for`: Services that consume the value.

**Relationships**:
- Used by one or more `Service Skeleton` records.

**Validation Rules**:
- Committed placeholders must not contain real secret values.
- Vault-related placeholders may contain only minimum bootstrap information.
- Missing required values must produce clear startup or validation failure.

## Health Check

**Purpose**: Repeatable verification that a service is running or dependency
ready.

**Fields**:
- `check_name`: Unique check name.
- `target_service`: Service being checked.
- `check_type`: `process`, `dependency`, `connectivity`, or `capability`.
- `expected_result`: Observable success condition.
- `status`: `pending`, `passed`, or `failed`.

**Relationships**:
- Belongs to one `Service Skeleton` or backing service.

**Validation Rules**:
- PostgreSQL check must run through PgBouncer.
- Vector capability check must confirm pgvector is enabled.
- Cache/queue and object storage checks must prove reachability.
- Failed checks must identify the service or dependency that failed.

## Quickstart

**Purpose**: Contributor-facing validation guide for Phase 1.

**Fields**:
- `prerequisites`: Required local tools.
- `configuration_steps`: How to prepare local configuration placeholders.
- `startup_steps`: How to start the foundation.
- `verification_steps`: Checks for each acceptance criterion.
- `shutdown_steps`: How to stop services.
- `reset_steps`: How to clear local persistent state when needed.

**Relationships**:
- References `Local Foundation`, `Service Skeleton`, and `Health Check`.

**Validation Rules**:
- Must be sufficient for a new contributor to start, verify, stop, and reset
  the foundation without undocumented commands.
