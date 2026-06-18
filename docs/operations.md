# Operations

## Local runtime

Primary local services:

- backend API: `http://localhost:8000`
- user app: `http://localhost:3000`
- agency app: `http://localhost:3001`
- Streamlit admin: `http://localhost:8501`
- PgBouncer: `localhost:6432`
- PostgreSQL: `localhost:5432`
- Redis: `localhost:6379`
- MinIO API: `localhost:9000`
- MinIO console: `http://localhost:9001`

## Boot flow

The system expects centralized settings in `backend/app/common/config.py` and loads secrets through the startup path. The FastAPI lifespan hook initializes logging, attempts Redis connectivity, and disposes shared resources on shutdown.

## Environment and config philosophy

Important patterns:

- one central settings object
- explicit env-backed toggles for providers and rate limits
- Vault-loaded secrets for sensitive credentials
- explicit CORS allowlist
- runtime flags for guardrails and tracing

## Security controls

### Auth/session model

- short-lived JWT access tokens
- refresh token rotation
- Redis-backed token blacklisting
- user-session invalidation markers
- logout, password reset, and suspicious-session revocation support

### Request protections

- RBAC dependencies on protected routes
- tenant fail-closed behavior
- rate limits by flow
- sanitized logging for user-provided AI/search content

## Rate limiting

The project applies Redis-backed rate limits to:

- login / refresh / logout / password reset flows
- manual search
- AI text search
- voice search
- inquiry creation
- viewing booking
- agency AI drafting / OCR routes

This is important because the product has both classic abuse surfaces and cost-bearing AI endpoints.

## Caching and invalidation

Redis-backed caching is used selectively, especially for:

- listing-search responses
- platform dashboard read models

Invalidation is explicit when writes change public-search or marketplace-insight inputs.

## Async processing and delivery guarantees

The worker model is based on durable outbox polling.

Operationally relevant behaviors:

- pending events are claimed with row locking
- retries use exponential backoff with jitter
- exhausted retries land in dead-letter state
- handlers are invoked with bounded payload contracts

This gives the project at-least-once delivery semantics with explicit persistence.

## Media operations

Listing-photo processing behavior:

- originals stored privately
- NSFW moderation is fail-closed
- blur scores can downgrade accepted images to warning state
- public-safe WebP derivatives are generated for delivery
- processing outcomes are recorded in media audit logs

## RAG operations

RAG ingestion behavior:

- PDFs are validated before acceptance
- original documents and page text live in MinIO
- replacements reuse chunks where hashes remain stable
- stale chunks are orphaned rather than silently mixed into active retrieval

RAG evaluation behavior:

- deterministic code quality runs in standard CI
- live RAG evals are opt-in locally and supported in GitHub workflows
- blocking mode uses a smaller suite
- manual mode runs a larger suite

## CI/CD and quality

The repo’s quality model intentionally separates deterministic checks from provider-dependent evals.

Deterministic merge gates:

- `make quality-precommit`
- `make quality-backend`
- `make quality-user`
- `make quality-agency`
- `make quality-admin`
- `make quality-workers`
- `make quality-model-service`

Live eval entry point:

- `make quality-rag-eval`

Reference:

- [quality-pipeline.md](quality-pipeline.md)

## Platform-admin operations

The Streamlit app is not a database client. It is a read-only HTTP consumer of backend-owned platform routes.

That gives three operational benefits:

- one place for redaction logic
- one place for authorization logic
- no duplicate read path that can drift from backend policy

## Notable implementation choices worth calling out

- outbox and inbox tables exist from the backend foundation, even where inbox use is still lighter than outbox use today
- email notification events are scaffolded through event names and schemas, which keeps notification work compatible with the same eventing approach
- the project prefers async I/O on network and database paths
- the docs, specs, and test structure are phase-based, which helps explain how the system grew without collapsing into one giant feature drop
