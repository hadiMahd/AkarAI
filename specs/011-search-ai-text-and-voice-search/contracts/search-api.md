# Contract: Search, AI Text Search, and Voice Search

## Existing Endpoint Reused

### `GET /listings`

Runs the final public listing search using confirmed filters.

#### Query Parameters

- `location?: string`
- `city?: string`
- `min_price?: number`
- `max_price?: number`
- `bedrooms?: number`
- `bathrooms?: number`
- `parking?: number`
- `floor?: number`
- `property_type?: string`
- `listing_purpose?: string`
- `furnishing?: string`
- `min_area_size?: number`
- `max_area_size?: number`
- `sort?: string`
- `page?: integer`
- `page_size?: integer`
- `cursor?: string`

#### Response

Uses existing `PaginatedPublicListingsResponse`.

## New Endpoint

### `POST /search/intent`

Extracts an editable `SearchIntent` from natural-language text. Does not run listing search.

#### Request

```json
{
  "query": "3 bedroom apartment for rent in Beirut under 1200 with parking on floor 4",
  "source_mode": "ai_text",
  "locale": "en",
  "include_debug": false
}
```

#### Response

```json
{
  "intent": {
    "source_mode": "ai_text",
    "raw_query": "3 bedroom apartment for rent in Beirut under 1200 with parking on floor 4",
    "filters": {
      "listing_purpose": "rent",
      "property_type": "apartment",
      "city": "Beirut",
      "max_price": 1200,
      "bedrooms": 3,
      "parking": 1,
      "floor": 4
    },
    "unsupported_criteria": [],
    "needs_confirmation": [],
    "unclear_location_intent": null,
    "confidence": "high",
    "provider": "azure_openai",
    "fallback_reason": null
  },
  "log_id": "b6e7f4fa-42e6-4b4e-9364-a6c2e63525d4"
}
```

#### Failure/Fallback Response

```json
{
  "intent": {
    "source_mode": "ai_text",
    "raw_query": "something vague",
    "filters": {},
    "unsupported_criteria": [],
    "needs_confirmation": [],
    "unclear_location_intent": {
      "phrase": "near Beirut",
      "reason": "unsupported_area_expansion",
      "suggested_action": "remove_location_filter",
      "resolved_city": null
    },
    "confidence": "fallback",
    "provider": "azure_openai",
    "fallback_reason": "low_confidence_or_unresolved_location"
  },
  "log_id": "b6e7f4fa-42e6-4b4e-9364-a6c2e63525d4"
}
```

## New Endpoint

### `POST /search/voice`

Transcribes a voice recording with Azure Whisper and extracts an editable `SearchIntent` from the transcript. Does not run listing search.

#### Request

`multipart/form-data`

- `audio`: audio file blob
- `locale?: string`
- `include_debug?: boolean`

#### Response

```json
{
  "transcript": {
    "transcript": "show me apartments for rent in Beirut under twelve hundred dollars",
    "provider": "azure_whisper",
    "duration_ms": 4200,
    "language": "en",
    "confidence": "usable",
    "fallback_reason": null
  },
  "intent": {
    "source_mode": "voice",
    "raw_query": "show me apartments for rent in Beirut under twelve hundred dollars",
    "transcript": "show me apartments for rent in Beirut under twelve hundred dollars",
    "filters": {
      "listing_purpose": "rent",
      "property_type": "apartment",
      "city": "Beirut",
      "max_price": 1200,
      "parking": 1
    },
    "unsupported_criteria": [],
    "needs_confirmation": [],
    "unclear_location_intent": null,
    "confidence": "medium",
    "provider": "azure_openai",
    "fallback_reason": null
  },
  "log_id": "ee2cae34-c1ce-4640-a5c7-53d0cb027333"
}
```

#### Failure/Fallback Response

```json
{
  "transcript": {
    "transcript": "",
    "provider": "azure_whisper",
    "duration_ms": null,
    "language": null,
    "confidence": "failed",
    "fallback_reason": "transcription_unavailable"
  },
  "intent": {
    "source_mode": "voice",
    "raw_query": null,
    "transcript": "",
    "filters": {},
    "unsupported_criteria": [],
    "needs_confirmation": [],
    "unclear_location_intent": null,
    "confidence": "fallback",
    "provider": null,
    "fallback_reason": "transcription_unavailable"
  },
  "log_id": "ee2cae34-c1ce-4640-a5c7-53d0cb027333"
}
```

## New Endpoint

### `POST /search/logs/confirmation`

Records confirmation edits before the frontend runs `GET /listings` with the confirmed filters.

#### Request

```json
{
  "source_log_id": "b6e7f4fa-42e6-4b4e-9364-a6c2e63525d4",
  "source_mode": "ai_text",
  "original_intent": {
    "filters": {
      "city": "Beirut",
      "max_price": 1200,
      "parking": 1
    }
  },
  "confirmed_filters": {
    "city": "Jounieh",
    "max_price": 1100,
    "listing_purpose": "rent",
    "parking": 1
  },
  "edited_fields": ["city", "max_price"]
}
```

#### Response

```json
{
  "log_id": "20aca1a0-9a5d-4a11-84ac-52e1ce8ca789",
  "status": "recorded"
}
```

## Error Semantics

- `400`: invalid filters, invalid audio payload, malformed intent object
- `401`: authenticated-only action attempted without required session, where applicable
- `413`: voice payload exceeds allowed size
- `422`: schema validation failed
- `429`: manual, AI text, or voice rate limit exceeded
- `503`: provider unavailable and no fallback response can be produced

Provider raw errors must not be returned directly to clients.
