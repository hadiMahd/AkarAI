# Backend App Module Conventions

## Feature Module Structure

Every feature domain (e.g. auth, users, listings) follows this layout:

```
backend/app/<feature>/
├── __init__.py
├── router.py          # FastAPI APIRouter with route handlers
├── service.py         # Business logic, orchestrates repositories
├── repository.py      # Data access layer (SQLAlchemy sessions)
├── schemas.py         # Pydantic request/response models
├── models.py          # SQLAlchemy ORM models
└── query_service.py   # (Optional) Read-optimized queries for CQRS
```

## Module Responsibilities

- **router.py**: HTTP route definitions, request parsing, response serialization. Delegates to `service.py` for business logic. No direct database access.
- **service.py**: Business logic and transaction orchestration. Calls repositories, handles validation beyond schema checks, coordinates side effects. No direct HTTP concerns.
- **repository.py**: Data access layer. Owns all SQLAlchemy session interactions. Methods accept and return domain models or Pydantic schemas. No business logic or HTTP concerns.
- **schemas.py**: Pydantic models for request validation, response serialization, and internal data transfer. Separate from ORM models.
- **models.py**: SQLAlchemy ORM table definitions. Database schema only. No business logic.
- **query_service.py** (optional): Read-optimized queries when CQRS separation adds value. Uses raw SQL or SQLAlchemy core for complex reads.

## Cross-Cutting Modules

Located in `backend/app/common/`:

| Module | Purpose |
|--------|---------|
| `config.py` | Centralized settings via Pydantic Settings |
| `database.py` | Async SQLAlchemy engine, session factory, connectivity checks |
| `dependencies.py` | Shared FastAPI dependency injection |
| `exceptions.py` | Application exception hierarchy |
| `health.py` | Health, readiness, and dependency check endpoints |
| `lifespan.py` | FastAPI lifespan (startup/shutdown) |
| `logging.py` | Structured logging setup |
| `redis.py` | Redis client wrapper and connectivity |
| `minio.py` | MinIO object storage client wrapper |

## Anti-Patterns

- **No `dao.py` files**: Repository is the data access layer. Do not create Data Access Object files.
- **No direct DB in routers**: Routes must not import or use SQLAlchemy sessions directly.
- **No business logic in models**: ORM models define schema only.
- **No HTTP in repositories**: Repositories must not access request objects or return HTTP responses.
- **No raw SQL in services**: Complex queries belong in repositories or query services.
