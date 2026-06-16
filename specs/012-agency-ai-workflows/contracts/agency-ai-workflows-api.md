# Contract: Agency AI Workflows

## New Endpoint

### `POST /agency/listings/spec-sheet-extractions`

Uploads a temporary property spec sheet from the agency listing form, queues OCR extraction, and returns a job handle for reviewable extracted fields. The uploaded file is not retained after extraction in this phase.

#### Request

`multipart/form-data`

- `file`: document or image upload

#### Response

```json
{
  "job_id": "job-uuid",
  "status": "queued",
  "provider": "azure_computer_vision_read"
}
```

#### Result Response

```json
{
  "job_id": "job-uuid",
  "status": "review_ready",
  "provider": "azure_computer_vision_read",
  "warnings": [],
  "extracted_specs": {
    "property_type": "apartment",
    "bedrooms": 3,
    "bathrooms": 2,
    "parking": 1,
    "floor": 4,
    "area_size": 180,
    "area_unit": "sqm",
    "city": "Beirut",
    "raw_text_excerpt": "Apartment 4B, 3 bedrooms, 2 bathrooms..."
  }
}
```

#### Failure Response

```json
{
  "status": "failed",
  "provider": "azure_computer_vision_read",
  "warnings": ["The uploaded sheet was partially unreadable."],
  "fallback_reason": "ocr_unavailable_or_unreadable"
}
```

## New Endpoint

### `POST /agency/listings/draft`

Queues listing copy generation from the current listing form state and optional OCR-derived fields. Does not save or publish the listing.

#### Request

```json
{
  "listing_id": null,
  "listing_context": {
    "property_type": "apartment",
    "listing_purpose": "rent",
    "price": 1200,
    "currency": "USD",
    "bedrooms": 3,
    "bathrooms": 2,
    "area_size": 180,
    "area_unit": "sqm",
    "city": "Beirut",
    "address": "Hamra",
    "furnishing": "furnished"
  },
  "extracted_specs": {
    "parking": 1,
    "floor": 4
  }
}
```

#### Request

```json
{
  "job_id": "job-uuid",
  "status": "queued"
}
```

#### Result Response

```json
{
  "job_id": "job-uuid",
  "status": "generated",
  "title": "Furnished 3-Bedroom Apartment in Hamra",
  "description": "Spacious 3-bedroom apartment for rent in Hamra with ...",
  "highlights": ["Furnished", "1 parking space", "4th floor"],
  "guardrail_status": "passed",
  "generation_provider": "azure_openai"
}
```

## Existing Endpoint Extended

### `POST /api/v1/agencies/rag/chat/threads/{thread_id}/messages`

The existing agency assistant chat endpoint keeps the same request/response shape, but its behavior expands from policy-only retrieval to policy grounding plus approved read-only tenant tools. Small answers remain synchronous.

#### Request

```json
{
  "content": "Show me the last 5 leads and remind me what the agency refund policy says.",
  "top_k": 8,
  "include_debug": true
}
```

#### Response

```json
{
  "thread": {
    "id": "thread-uuid",
    "tenant_id": "tenant-uuid",
    "owner_user_id": "user-uuid",
    "title": "Conversation",
    "message_count": 4,
    "created_at": "2026-06-15T10:00:00Z",
    "updated_at": "2026-06-15T10:01:00Z",
    "last_message_at": "2026-06-15T10:01:00Z"
  },
  "user_message": {
    "id": "user-message-uuid",
    "thread_id": "thread-uuid",
    "tenant_id": "tenant-uuid",
    "owner_user_id": "user-uuid",
    "role": "user",
    "content": "Show me the last 5 leads and remind me what the agency refund policy says.",
    "sequence_number": 3,
    "retrieval_log_id": null,
    "answer": null,
    "created_at": "2026-06-15T10:01:00Z"
  },
  "assistant_message": {
    "id": "assistant-message-uuid",
    "thread_id": "thread-uuid",
    "tenant_id": "tenant-uuid",
    "owner_user_id": "user-uuid",
    "role": "assistant",
    "content": "Here are the last 5 leads ...",
    "sequence_number": 4,
    "retrieval_log_id": "retrieval-log-uuid",
    "answer": {
      "status": "answered",
      "answer": "Here are the last 5 leads ...",
      "citations": [
        {
          "document_id": "doc-uuid",
          "document_filename": "refund-policy.pdf",
          "page_number": 2,
          "source_label": "refund-policy.pdf p.2"
        }
      ],
      "evidence": [],
      "debug": {
        "reranker_used": true,
        "reranker_provider": "openrouter",
        "confidence_status": "sufficient",
        "guardrail_status": "passed",
        "generation_provider": "azure_openai",
        "retrieval_log_id": "retrieval-log-uuid"
      }
    },
    "created_at": "2026-06-15T10:01:00Z"
  }
}
```

Operational tool usage remains implicit in the answer contract; raw tool payloads are not returned to the client.

## New Endpoint

### `POST /agency/leads/{lead_id}/reply-draft`

Queues one suggested external reply draft for a lead detail view.

#### Request

```json
{
  "channel": "email"
}
```

#### Request

```json
{
  "job_id": "job-uuid",
  "status": "queued"
}
```

#### Result Response

```json
{
  "job_id": "job-uuid",
  "status": "generated",
  "channel": "email",
  "subject": "Regarding your property inquiry",
  "draft_text": "Thanks for reaching out about the apartment in Beirut...",
  "guardrail_status": "passed",
  "generation_provider": "azure_openai"
}
```

## New Endpoint

### `POST /me/comparison-summary`

Queues a summary for listings currently selected on the protected user compare page.

#### Request

```json
{
  "listing_ids": [
    "listing-uuid-1",
    "listing-uuid-2",
    "listing-uuid-3"
  ]
}
```

#### Request

```json
{
  "job_id": "job-uuid",
  "status": "queued"
}
```

#### Result Response

```json
{
  "job_id": "job-uuid",
  "status": "generated",
  "summary": "### Key differences\n\n- Listing A offers ...",
  "key_differences": [
    "Listing A has the largest area.",
    "Listing B is the lowest monthly rent."
  ],
  "best_fit_notes": [
    "Listing C may suit a furnished rental preference."
  ],
  "guardrail_status": "passed",
  "generation_provider": "azure_openai"
}
```

## New Endpoint

### `GET /agency/ai/jobs/{job_id}`

Returns the current status/result for OCR and generation jobs.

#### Response

```json
{
  "job_id": "job-uuid",
  "job_type": "listing_draft",
  "status": "generated",
  "result": {
    "title": "Furnished 3-Bedroom Apartment in Hamra",
    "description": "Spacious 3-bedroom apartment for rent in Hamra with ...",
    "highlights": ["Furnished", "1 parking space", "4th floor"]
  }
}
```

## Error Semantics

- `400`: invalid file type, malformed request shape, or invalid job lookup
- `401`: unauthenticated user/employee request
- `403`: role is not allowed for the requested agency-side action
- `404`: listing, lead, thread, or tenant-scoped resource not found
- `413`: uploaded spec sheet exceeds allowed size
- `422`: schema validation failed
- `429`: rate limit exceeded for assistant/generation/OCR route
- `503`: provider unavailable and no safe fallback response can be produced

Provider raw errors and raw OCR output must not be returned directly to clients.
