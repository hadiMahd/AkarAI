<!-- SPECKIT START -->
For additional context about technologies to be used, project structure,
shell commands, and other important information, read the current plan
at specs/003-backend-core-foundation/plan.md
<!-- SPECKIT END -->

## Architecture Rules

- **No `dao.py` files**: `repository.py` is the data access layer. DAO files are forbidden.
- Module conventions: `router.py`, `service.py`, `repository.py`, `schemas.py`, `models.py`, optional `query_service.py`.
- See `backend/app/README.md` for full module conventions.
