# Quickstart: Akarai MVP Validation

This guide describes how to validate the MVP once implementation tasks exist.
Commands are placeholders until dependencies are selected and scaffolded.

## Prerequisites

- Python 3.11+
- Node.js 20+
- Docker and Docker Compose
- HashiCorp Vault reachable for secrets
- Local services for PostgreSQL + pgvector, Redis, MinIO, and PgBouncer

## Local Setup

1. Install backend dependencies:

   ```bash
   cd backend
   uv sync
   ```

2. Install user app dependencies:

   ```bash
   cd apps/user
   npm install
   ```

3. Install agency app dependencies:

   ```bash
   cd apps/agency
   npm install
   ```

4. Configure non-secret environment variables and Vault bootstrap settings:

   ```bash
   cp .env.example .env
   ```

   Required secret values must be stored in HashiCorp Vault, not `.env`.

5. Start local services:

   ```bash
   docker compose up -d postgres redis minio pgbouncer vault
   ```

6. Run migrations and seed demo data:

   ```bash
   cd backend
   uv run alembic upgrade head
   uv run python scripts/seed_demo_data.py
   ```

## Run Apps

1. Backend API:

   ```bash
   cd backend
   uv run uvicorn app.main:app --reload
   ```

2. User app:

   ```bash
   cd apps/user
   npm run dev
   ```

3. Agency dashboard:

   ```bash
   cd apps/agency
   npm run dev
   ```

4. Platform admin:

   ```bash
   cd admin
   uv run streamlit run app.py
   ```

5. Workers:

   ```bash
   cd workers
   uv run python -m workers.runner
   ```

## Validation Scenarios

### User Search and Compare

1. Open the user app.
2. Run a manual search and verify paginated results.
3. Run AI text search for "calm area near Beirut".
4. Run voice search and verify extracted filters.
5. Save one listing.
6. Add four listings to comparison.
7. Verify the fifth comparison add is rejected.
8. Open comparison and verify structured fields plus AI summary.

Expected outcome: search, save, comparison limit, and summary all work without
showing a match score.

### Listing AI Widget

1. Open a listing detail page.
2. Verify photos, specs, description, price, location, parking, floor,
   furnished status, viewing dates, agency preview, and one unified AI widget.
3. Ask a listing question.
4. Ask an agency policy question.
5. Ask to create an inquiry and cancel confirmation.
6. Ask to create an inquiry and confirm.
7. Ask to schedule a viewing and confirm.

Expected outcome: cancelled actions create nothing; confirmed inquiry creates a
Lead; confirmed viewing creates a ScheduledViewing, not a Lead.

### Agency Leads and Viewings

1. Login as Agency Admin.
2. Upload a policy document and verify ingestion status.
3. Create a listing with photos.
4. Verify NSFW photos are rejected and low-quality photos show a warning.
5. Open leads page and verify valid/spam separation.
6. Open lead detail and verify Hot/Normal/Spam classification and one suggested
   reply.
7. Mark the lead reviewed.
8. Open viewing schedules and filter by date, listing, client, status,
   upcoming/past, today, and week.

Expected outcome: agency workflows stay tenant-scoped and review metadata is
stored.

### Support Employee RBAC

1. Login as Support Employee.
2. Verify allowed listing view/edit behavior.
3. Verify create listing is forbidden.
4. Verify employee management is forbidden.
5. Verify agency profile editing is forbidden.
6. Verify upload/delete policy document is forbidden.
7. Verify platform admin data is forbidden.

Expected outcome: every forbidden action returns an authorization failure and
does not mutate state.

### RAG Re-Ingestion

1. Upload an agency policy PDF.
2. Verify original document path:
   `rag-vault/{tenant_id}/{document_id}/original/original.pdf`.
3. Verify page text path:
   `rag-vault/{tenant_id}/{document_id}/pages/page_001.txt`.
4. Re-upload an edited version of the document.
5. Verify old and new chunk hashes are compared.
6. Verify orphaned chunks are batch deleted.
7. Ask the support assistant a policy question.

Expected outcome: retrieval uses tenant filtering, child chunk retrieval, parent
page context, and reranking where useful.

### Platform Admin

1. Open the platform admin dashboard.
2. Verify marketplace demand insights: popular areas, budgets, property types,
   demand gaps, and trends.
3. Verify AI audit logs are visible.
4. Verify role/permission management is available if enabled for MVP.

Expected outcome: platform admin is separate from agency tenant workflows.

## Test Commands

```bash
cd backend
uv run pytest
```

```bash
cd apps/user
npm test
```

```bash
cd apps/agency
npm test
```

## Expected Contract

The API surface is defined in [contracts/openapi.yaml](./contracts/openapi.yaml).
The data model is defined in [data-model.md](./data-model.md).
