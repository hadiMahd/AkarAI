# AI Provider Interfaces

This module defines provider interfaces and their concrete implementations via Azure OpenAI.

## Provider Interfaces

- `ChatProvider` — chat/completion
- `EmbeddingProvider` — text embeddings
- `RerankingProvider` — result reranking
- `OCRProvider` — optical character recognition
- `STTProvider` — speech-to-text (Azure Whisper)
- `TTSProvider` — text-to-speech
- `ImageModerationProvider` — image content moderation
- `ImageQualityProvider` — image quality assessment
- `SpamClassifierProvider` — spam detection
- `LeadClassifierProvider` — lead scoring/classification

## Registry

`registry.py` provides `register_provider`, `get_provider`, `get_chat_provider`, `get_stt_provider`, and related helpers. The primary chat provider is configured via the `AI_PRIMARY_PROVIDER` environment variable (default: `azure_openai`).

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

## Configuring Azure Whisper Deployment

Set the following environment variables (or Vault secrets):

- `AZURE_OPENAI_ENDPOINT` — your Azure OpenAI resource endpoint (e.g. `https://my-resource.openai.azure.com/`)
- `AZURE_OPENAI_API_KEY` — your Azure OpenAI API key
- `AZURE_WHISPER_DEPLOYMENT` — the deployment name for the Whisper model (e.g. `whisper`)
- `AI_PRIMARY_PROVIDER` — set to `azure_openai` (default)

The STT provider is registered lazily under the key `azure_stt` in the registry and is cached after first access.
