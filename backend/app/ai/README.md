# AI Provider Interfaces

This module defines provider interfaces and their concrete implementations via Azure OpenAI.

## Provider Interfaces

- `ChatProvider` — chat/completion
- `EmbeddingProvider` — text embeddings
- `RerankingProvider` — result reranking
- `OCRProvider` — optical character recognition (Azure Computer Vision Read)
- `STTProvider` — speech-to-text (Azure Whisper)
- `TTSProvider` — text-to-speech
- `ImageModerationProvider` — image content moderation
- `ImageQualityProvider` — image quality assessment
- `SpamClassifierProvider` — spam detection
- `LeadClassifierProvider` — lead scoring/classification

## Registry

`registry.py` provides `register_provider`, `get_provider`, `get_chat_provider`, `get_stt_provider`, `get_ocr_provider`, and related helpers. The primary chat provider is configured via the `AI_PRIMARY_PROVIDER` environment variable (default: `azure_openai`). The OCR provider is selected via `OCR_PROVIDER` (default: `azure_computer_vision_read`).

## Chat Provider Usage (extract_search_intent)

The `SearchService.extract_search_intent(q)` method uses `get_chat_provider()` to extract structured filters from a natural-language query:

```python
from app.ai.registry import get_chat_provider

provider = get_chat_provider()
response = await provider.chat([
    {"role": "system", "content": EXTRACTION_PROMPT},
    {"role": "user", "content": user_query},
])
text = response.get("text", "")
```

The provider must implement `ChatProvider.chat(messages) -> dict` returning at minimum `{"text": "..."}`.

## STT Provider Usage (transcribe_and_extract)

The `SearchService.transcribe_and_extract(audio_bytes, content_type)` method uses `get_stt_provider()` to transcribe voice input:

```python
from app.ai.registry import get_stt_provider

provider = get_stt_provider()
transcript_text = await provider.transcribe(audio_bytes, content_type=content_type)
```

The provider must implement `STTProvider.transcribe(audio_bytes, content_type) -> str`.

## OCR Provider Usage (Phase 12: Agency AI Workflows)

The `AgencyAIService.run_spec_extraction` flow uses `get_ocr_provider()` to extract
text from a temporary property spec sheet inside the agency listing form. The OCR
provider is registered under `azure_computer_vision_read` and uses the v3.2 Read
API: submit the file, poll the returned operation URL, and return the recognized
text lines.

```python
from app.ai.registry import get_ocr_provider

provider = get_ocr_provider()
text = await provider.extract_text(file_bytes, content_type="application/pdf")
```

The provider must implement `OCRProvider.extract_text(file_bytes, content_type) -> str`.

## Shared Guardrailed Generation (Phase 12)

`app.ai.guardrails.generate_guardrailed_agency_text` provides a single guarded
generation path that:

- Detects prompt injection / out-of-scope queries.
- Routes input through the OpenRouter content safety judge (when configured).
- Calls the configured chat provider.
- Routes output through the content safety judge again.
- Returns a structured `GuardrailedGenerationResult` with status, blocked reason,
  and the chosen generation provider.

Use it for all listing drafts, lead reply drafts, and comparison summaries to keep
policy, redaction, and provider-indirection guarantees consistent.

## Agency AI Job Lifecycle (Phase 12)

`app.ai.jobs` provides a small state machine for the four job types introduced in
this phase:

- `JOB_TYPE_OCR_EXTRACTION`
- `JOB_TYPE_LISTING_DRAFT`
- `JOB_TYPE_LEAD_REPLY_DRAFT`
- `JOB_TYPE_COMPARISON_SUMMARY`

`new_job` creates a queued job. `mark_processing` / `mark_completed` / `mark_failed`
move it through the lifecycle. Each transition stamps the corresponding timestamp
column and (for completed/failed) writes the result payload or error message.

## Configuring Azure Whisper Deployment

Set the following environment variables (or Vault secrets):

- `AZURE_OPENAI_ENDPOINT` — your Azure OpenAI resource endpoint (e.g. `https://my-resource.openai.azure.com/`)
- `AZURE_OPENAI_API_KEY` — your Azure OpenAI API key
- `AZURE_WHISPER_DEPLOYMENT` — the deployment name for the Whisper model (e.g. `whisper`)
- `AI_PRIMARY_PROVIDER` — set to `azure_openai` (default)

The STT provider is registered lazily under the key `azure_stt` in the registry and is cached after first access.

## Configuring Azure Computer Vision Read OCR

Set the following environment variables (or Vault secrets):

- `OCR_PROVIDER` — `azure_computer_vision_read` (default)
- `AZURE_CV_ENDPOINT` — your Azure Computer Vision endpoint (e.g. `https://my-cv.cognitiveservices.azure.com/`)
- `AZURE_CV_API_KEY` — your Azure Computer Vision key

The OCR provider is registered lazily under `azure_computer_vision_read` and cached
after first access. Calls fail-closed if the endpoint or key is missing.

## Lead Processing Pipeline

Lead classification uses a dedicated model service for two-stage inference.

### Architecture

```
User → Lead Creation → outbox(lead.created) → Worker → Model Service → Callback → Backend
```

1. **Lead Creation**: Save lead + create pending `LeadSpamResult` (and `LeadLevelResult` for non-empty).
2. **Outbox Event**: Emit `lead.created` with idempotency key `lead.created.{lead_id}`.
3. **Worker**: Claims the event, forwards to model service via `POST /classify`.
4. **Model Service**: Runs spam classifier → calls back with spam result → runs Hot/Normal ranker → calls back with level result.
5. **Callback**: Backend persists `LeadClassificationCallbackRequest` via idempotent upsert. Late callbacks update classification without touching review state.

### Fail-Open
- Empty messages → immediate spam (no model service call).
- Model unavailable → `not_spam` / `normal` defaults.
- Worker failures → best-effort, lead is already saved.

### Configuration
- `LEAD_MODEL_SERVICE_URL` (default: `http://lead-model-service:8100`)
- `LEAD_MODEL_SERVICE_CALLBACK_TOKEN` (Vault secret: `akarai/lead_model_service`)
- `LEAD_PROCESSING_RETRY_MAX_ATTEMPTS` (default: 3)
- `LEAD_PROCESSING_EMPTY_MESSAGE_IS_SPAM` (default: true)
