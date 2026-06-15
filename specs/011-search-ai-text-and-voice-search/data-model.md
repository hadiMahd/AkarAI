# Data Model: Search, AI Text Search, and Voice Search

## Entities

### `SearchIntent`

Normalized representation of a user's search request before final confirmation.

- `id` (UUID or request-local ID)
- `source_mode` (Enum: `manual`, `ai_text`, `voice`)
- `raw_query` (Text, optional, redacted before logging)
- `transcript` (Text, optional, redacted before logging)
- `filters` (`ConfirmedSearchFilters`, partial)
- `unsupported_criteria` (List of strings)
- `needs_confirmation` (List of field keys)
- `unclear_location_intent` (`UnclearLocationIntent`, optional)
- `confidence` (Enum: `high`, `medium`, `low`, `fallback`)
- `provider` (String, optional)
- `fallback_reason` (String, optional)

### `ConfirmedSearchFilters`

The only structure allowed to drive final listing result queries.

- `q` (String, optional)
- `listing_purpose` (Enum/string, optional: sale/rent values currently supported by listings)
- `property_type` (String, optional)
- `city` (String, optional)
- `location` (String, optional)
- `min_price` (Number, optional)
- `max_price` (Number, optional)
- `bedrooms` (Integer, optional)
- `bathrooms` (Integer, optional)
- `parking` (Integer, optional)
- `floor` (Integer, optional)
- `furnishing` (String, optional)
- `min_area_size` (Number, optional)
- `max_area_size` (Number, optional)
- `sort` (String, optional)
- `page` (Integer, default 1)
- `page_size` (Integer, default 20, max 100)

### `UnclearLocationIntent`

Represents vague location language that is not automatically expanded in this phase.

- `phrase` (Text, redacted before logging)
- `reason` (Enum/string: `vague_area`, `unsupported_area_expansion`, `ambiguous_city`)
- `suggested_action` (Enum/string: `select_city`, `remove_location_filter`, `manual_filter`)
- `resolved_city` (String, optional, only after user confirmation)

### `VoiceSearchTranscript`

User-visible transcription result used before filter extraction and confirmation.

- `transcript` (Text)
- `provider` (String: `azure_whisper`)
- `duration_ms` (Integer, optional)
- `language` (String, optional)
- `confidence` (Enum: `usable`, `unclear`, `empty`, `failed`)
- `fallback_reason` (String, optional)

### `SearchLog`

Privacy-safe audit record for manual, AI text, and voice search events.

Existing fields are extended conceptually:
- `id` (UUID)
- `user_id` (UUID, nullable)
- `agency_tenant_id` (UUID, nullable; public search normally null)
- `source_mode` (Enum: `manual`, `ai_text`, `voice`)
- `event_type` (Enum: `manual_search`, `intent_extracted`, `voice_transcribed`, `confirmation_edited`, `search_applied`, `fallback`, `rate_limited`)
- `raw_query_redacted` (Text, optional)
- `transcript_redacted` (Text, optional)
- `intent` (JSON, sanitized and bounded)
- `filters` (JSON, sanitized confirmed filters)
- `sort` (String, optional)
- `result_count` (Integer)
- `provider` (String, optional)
- `fallback_reason` (String, optional)
- `created_at` (DateTime)

## Existing Entities Reused

### `Listing`

Source of public search results. Queries must only return `status = active` listings and public-safe fields.

### `PublicListingResponse`

Returned listing card/detail-safe representation. AI and voice flows must end in the same listing response shape as manual search.

## Validation Rules

- Final listing queries may only use `ConfirmedSearchFilters`.
- `page_size` must be between 1 and 100.
- Price and area ranges must reject invalid negative values and normalize inverted ranges through validation or user correction.
- Parking and floor filters must validate non-negative integer values.
- AI and voice search must not apply filters until the user confirms or edits the interpreted object.
- Vague location terms must be represented as `unclear_location_intent`, must not become concrete city filters automatically, and may resolve to no location filter when the user chooses to continue.
- Search logs must redact secrets and personal data in raw query, transcript, unsupported criteria, and debug/fallback text.
- Voice upload must enforce allowed content types, bounded file size, and request timeout behavior.
- Provider failures must produce fallback intent responses, not raw provider errors.

## State Transitions

- **AI text search**: `submitted` → `intent_extracted` → `confirmation_pending` → `confirmed` → `results_loaded`
- **Voice search**: `recording` → `transcribing` → `transcribed` → `intent_extracted` → `confirmation_pending` → `confirmed` → `results_loaded`
- **Fallback path**: `submitted/transcribing` → `fallback` → `manual_editing`
- **Rate limit path**: `submitted` → `rate_limited` with current search state preserved
