# Research: Search, AI Text Search, and Voice Search

## Decision: Use one canonical `SearchIntent` contract across manual, AI text, and voice flows

**Rationale**: Manual search is already the source of truth. AI text and voice should not run separate listing queries; they should produce the same confirmed filter object that manual search uses. This keeps cache keys, logs, pagination, and UI state consistent.

**Alternatives considered**:
- Separate AI search endpoint returning listings directly: rejected because it bypasses user confirmation and duplicates listing query logic.
- Frontend-only extraction state: rejected because logs, rate limits, and provider fallbacks need server-owned validation.

## Decision: Use the existing primary `ChatProvider` for AI filter extraction

**Rationale**: The constitution requires provider interfaces and the backend already has a chat provider boundary. Search extraction should call the provider interface with a strict JSON schema prompt, validate the returned object, and fallback to manual editing when confidence is low or parsing fails.

**Alternatives considered**:
- Hardcode Azure OpenAI in `search/service.py`: rejected because provider-specific logic does not belong in feature services.
- Regex-only extraction: rejected because it is brittle for mixed natural-language property requests.

## Decision: Use Azure Whisper through `STTProvider` for voice search

**Rationale**: The user confirmed Azure Whisper is the intended STT provider. The provider boundary already exists, and settings already include `azure_whisper_deployment`. Voice search should transcribe audio first, then feed the transcript into the same AI text extraction path.

**Alternatives considered**:
- Provider interface only with no real STT: rejected after user clarified that real mic-to-feature extraction is required now.
- Browser SpeechRecognition only: rejected because it is not a stable backend-owned provider path and would not support consistent logging/rate limiting.

## Decision: Exclude area expansion and represent vague location as unresolved intent

**Rationale**: The user chose to exclude area expansion from this phase. Vague phrases like "near Beirut" should become `unclear_location_intent` requiring manual confirmation, not hidden automatic filters.

**Alternatives considered**:
- Area RAG now: rejected by user scope.
- Silently search city text with vague phrases: rejected because it creates surprising and low-quality results.

## Decision: Search logs store sanitized structured events, not raw provider payloads

**Rationale**: Search logs are needed for quality, troubleshooting, rate-limit visibility, and validation, but user-provided search text may include PII or secrets. Logs should store source mode, redacted query/transcript, interpreted intent, confirmed filters, fallback/rate-limit outcome, and counts.

**Alternatives considered**:
- No logs: rejected because the phase requires search logs and quality validation.
- Store full raw prompts/responses: rejected because it violates privacy and increases cleanup risk.

## Decision: Keep rate limits per search mode in Redis

**Rationale**: Manual search, AI text extraction, and voice transcription have different cost profiles. Redis-backed rate-limit helpers already exist and can be extended with separate keys and limits.

**Alternatives considered**:
- One shared search limit: rejected because voice/AI calls are more expensive than manual DB search.
- DB-backed throttling: rejected because Redis is already the project rate-limit store.

## Decision: No TTS/spoken summaries

**Rationale**: The user chose not to include spoken result summaries. Voice is input-only in this phase.

**Alternatives considered**:
- TTS provider boundary now: rejected as unnecessary scope because no user-facing spoken summaries are planned.
