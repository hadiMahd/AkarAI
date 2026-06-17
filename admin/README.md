# AkarAI Platform Admin (Streamlit)

> Read-only platform admin dashboard. Lives in this `admin/` service
> and talks to the backend over the `platform:*` read APIs.

## Views

The root app (`app.py`) owns the only login gate and renders four tabs
after authentication:

1. `Home`
2. `Marketplace Insights` via `insights_view.py`
3. `AI Audit Logs` via `audit_logs_view.py`
4. `Role & Access Overview` via `role_access_view.py`

## Auth model

- Login uses the existing backend `POST /auth/login`.
- The access gate (`admin/components.py:require_dashboard_access`) requires
  the actor to be `platform_admin` AND hold the dedicated
  `platform:dashboard_read` permission. The check mirrors the backend
  dependency and never lets a non-platform-admin reach any of the
  read-only views.

## Environment

| Var | Default | Purpose |
|-----|---------|---------|
| `BACKEND_URL` | `http://backend:8000` | Backend read API base URL |
| `APP_ENV` | `development` | Logged on the home page |

## Local dev

```bash
pip install -r requirements.txt
BACKEND_URL=http://localhost:8000 streamlit run app.py --server.port=8501
```

## Tests

```bash
docker compose exec admin python -m pytest admin/tests
```

Tests do not require a running backend. They cover the
`AdminAPIClient` HTTP layer plus the single-shell tab wiring.
