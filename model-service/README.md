# Lead Model Service

Dedicated inference service for lead classification (two-stage: spam → Hot/Normal).

## Architecture

- **`/classify`**: Receives a lead, runs spam detection first, then Hot/Normal for non-spam leads.
- **Callback**: Posts results back to the backend callback endpoint with bearer token auth.

## Artifacts

Place classifier model files in `artifacts/`:
- `spam_model.joblib` — scikit-learn spam classifier
- `spam_vectorizer.joblib` — text vectorizer for spam model
- `level_model.joblib` — scikit-learn Hot/Normal ranker
- `level_vectorizer.joblib` — text vectorizer for level model

If models are missing, the service fails open: spam → not_spam, level → normal.

## Configuration

Environment variables:
- `BACKEND_URL` — backend API URL for callbacks (default: http://backend:8000)
- `CALLBACK_TOKEN` — bearer token for callback auth
- `REDIS_URL` — Redis connection string
