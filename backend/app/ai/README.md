# AI Provider Interfaces (Phase 2)

This module defines provider interfaces only. Concrete providers are **TBD_ASK_USER**.

## Provider Interfaces

- `ChatProvider` — chat/completion
- `EmbeddingProvider` — text embeddings
- `RerankingProvider` — result reranking
- `OCRProvider` — optical character recognition
- `STTProvider` — speech-to-text
- `TTSProvider` — text-to-speech
- `ImageModerationProvider` — image content moderation
- `ImageQualityProvider` — image quality assessment
- `SpamClassifierProvider` — spam detection
- `LeadClassifierProvider` — lead scoring/classification

## Registry

`registry.py` provides `register_provider` and `get_provider` helpers.
The primary provider is configured via `AI_PRIMARY_PROVIDER` (TBD_ASK_USER).

## Out of Scope (Phase 2)

- No real AI/ML model loading
- No embeddings generation
- No chat completion calls
- No OCR/image processing
- No spam or lead classification
- No RAG ingestion or retrieval
