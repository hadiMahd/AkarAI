# Quickstart: Search, AI Text Search, and Voice Search

## Prerequisites

- Docker Compose stack running with backend, user app, PostgreSQL, Redis, Vault, and MinIO.
- Vault contains the existing Azure OpenAI chat deployment and Azure Whisper deployment values.
- At least several active listings exist with city, purpose, type, price, bedroom, bathroom, furnishing, and area fields.

## Setup

```bash
docker compose up -d backend user-app postgres redis vault
docker compose exec backend alembic upgrade head
```

## Validation Scenarios

### 1. Manual Search

1. Open the user app listing search page.
2. Apply filters for purpose, property type, city, price range, bedrooms, bathrooms, furnishing, and area size.
3. Submit search.
4. Change sort order and paginate.

Expected:
- Only active public listings matching the confirmed filters are returned.
- URL/search state remains stable across pagination and sorting.
- Manual search is logged with sanitized filter payload.

### 2. AI Text Search Confirmation

1. Enter: `3 bedroom apartment for rent in Beirut under 1200 with parking`.
2. Review the confirmation panel.
3. Change `city` or `max_price`.
4. Confirm and run search.

Expected:
- The interpreted intent is editable before results are applied.
- Unsupported criteria such as parking are shown separately if the listing schema cannot apply them.
- Final results use the edited confirmed filters, not the raw interpretation.

### 3. Vague Location Handling

1. Enter: `calm apartment near Beirut under 1000`.
2. Review the confirmation panel.

Expected:
- The vague location appears as unresolved location intent.
- The system does not automatically expand "near Beirut" into hidden city filters.
- The user can choose a concrete city or proceed without a location filter.

### 4. Voice Search

1. Use the microphone control and say: `show me apartments for rent in Beirut under twelve hundred`.
2. Stop recording and wait for transcription.
3. Review transcript and extracted filters.
4. Edit transcript or filters if needed.
5. Confirm search.

Expected:
- Azure Whisper returns a visible transcript.
- The transcript feeds the same filter extraction and confirmation flow as AI text search.
- Final results use confirmed filters only.

### 5. Provider Failure and Rate Limit Recovery

1. Temporarily misconfigure the AI extraction provider or STT provider in local test settings.
2. Submit AI text and voice searches.
3. Repeat AI or voice requests until rate-limited.

Expected:
- Provider failures produce a clear fallback state and keep manual search usable.
- Rate-limited requests return a clear recovery message.
- Search state is not lost.
- Logs record fallback/rate-limit events without raw secrets or unnecessary personal data.

## Focused Test Commands

```bash
docker compose exec backend pytest backend/tests/unit/test_search_intent.py backend/tests/unit/test_ai_search_extraction.py backend/tests/unit/test_voice_search.py backend/tests/integration/test_search_api.py
docker compose exec user-app npm run test -- search
```

No e2e browser automation is part of this phase.
