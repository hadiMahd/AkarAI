# Research: Infrastructure and Docker Compose Foundation

## Decision: Use root Docker Compose for the local foundation

**Rationale**: The repository already has a root `docker-compose.yml`, and the
Phase 1 goal is a single local command that starts all required services and app
skeletons. A root compose file keeps startup discoverable and matches the
feature scope.

**Alternatives considered**:
- `infra/docker-compose.yml`: More nested, but the current root file exists and
  the requested phase is repository foundation work.
- Separate compose files per app: Adds coordination overhead before any domain
  feature exists.

## Decision: Keep Phase 1 skeleton-only

**Rationale**: The plan explicitly excludes auth, listings, RAG, AI, leads, and
viewings. Skeletons only prove local startup, service health, and dependency
reachability.

**Alternatives considered**:
- Add starter auth or listing endpoints: Rejected because it violates the Phase
  1 stop gate and would mix later phases into infrastructure.
- Add provider integrations: Rejected because AI/RAG/provider behavior is out
  of scope.

## Decision: Verify PostgreSQL through PgBouncer

**Rationale**: The constitution requires PgBouncer for PostgreSQL connection
pooling, and the Phase 1 acceptance criteria require PostgreSQL to be reachable
through PgBouncer. Verification must use the same path later app code will use.

**Alternatives considered**:
- Verify direct PostgreSQL only: Rejected because it can pass while the required
  connection proxy is broken.
- Skip database verification until migrations: Rejected because Phase 1 must
  prove the local data foundation starts.

## Decision: Enable and verify pgvector during infrastructure startup

**Rationale**: Later RAG/search phases depend on vector support, and Phase 1
acceptance requires the extension to be enabled. Verifying it early prevents
late discovery of an incompatible local database image.

**Alternatives considered**:
- Enable pgvector in a later RAG phase: Rejected because it is explicitly part
  of Phase 1 acceptance.
- Treat vector support as documentation-only: Rejected because acceptance must
  be verifiable.

## Decision: Use health/readiness checks as the Phase 1 contract

**Rationale**: Phase 1 has no domain workflows. The meaningful external
contract is whether the local foundation starts and reports process/dependency
readiness consistently.

**Alternatives considered**:
- Full domain API contracts: Rejected because auth/listings/RAG/AI/leads/viewings
  are out of scope.
- Manual-only verification: Rejected because repeatable checks are needed for
  contributors and later CI smoke validation.

## Decision: Store only non-secret configuration placeholders in `.env.example`

**Rationale**: The constitution requires secrets to come from HashiCorp Vault and
allows environment variables only for non-secret runtime configuration plus the
minimum bootstrap data needed to reach Vault.

**Alternatives considered**:
- Put local passwords/tokens directly in `.env.example`: Rejected because it
  normalizes committed secret values.
- Omit configuration placeholders entirely: Rejected because Phase 1 must be
  reproducible for new contributors.
