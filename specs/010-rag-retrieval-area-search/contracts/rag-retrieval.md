# Contract: RAG Retrieval and Reranking

## Ask Agency Policy Question

`POST /api/v1/agencies/rag/query`

**Auth**: Agency Admin or Support Employee

**Request**

```json
{
  "query": "What is our cancellation policy?",
  "top_k": 8,
  "include_debug": true
}
```

**Response: 200 OK**

```json
{
  "status": "answered",
  "answer": "Grounded answer text.",
  "citations": [
    {
      "document_id": "uuid",
      "document_filename": "policy.pdf",
      "page_number": 3,
      "source_label": "policy.pdf p.3"
    }
  ],
  "evidence": [
    {
      "chunk_id": "uuid",
      "document_id": "uuid",
      "page_ids": ["uuid"],
      "document_filename": "policy.pdf",
      "page_numbers": [3],
      "source_label": "policy.pdf p.3",
      "vector_rank": 1,
      "vector_score": 0.82,
      "rerank_rank": 1,
      "rerank_score": 0.94,
      "text_preview": "Relevant bounded evidence preview..."
    }
  ],
  "debug": {
    "reranker_used": true,
    "reranker_provider": "openrouter",
    "fallback_reason": null,
    "confidence_status": "sufficient",
    "retrieval_log_id": "uuid"
  }
}
```

**Response: 200 OK, insufficient evidence**

```json
{
  "status": "insufficient_evidence",
  "answer": "I could not find enough policy evidence to answer that.",
  "citations": [],
  "evidence": [],
  "debug": {
    "reranker_used": false,
    "reranker_provider": null,
    "fallback_reason": "low_confidence",
    "confidence_status": "insufficient",
    "retrieval_log_id": "uuid"
  }
}
```

**Errors**

- `400 Bad Request`: Empty query or invalid top_k.
- `401 Unauthorized`: Missing or invalid session.
- `403 Forbidden`: Actor lacks agency retrieval permission or tenant context.

## List Retrieval Logs

`GET /api/v1/agencies/rag/retrieval-logs?page=1&page_size=20`

**Auth**: Agency Admin

**Response: 200 OK**

```json
{
  "items": [
    {
      "id": "uuid",
      "query": "What is our cancellation policy?",
      "actor_user_id": "uuid",
      "actor_role": "agency_admin",
      "confidence_status": "sufficient",
      "reranker_used": true,
      "fallback_reason": null,
      "created_at": "2026-06-12T19:00:00Z"
    }
  ],
  "total": 1,
  "page": 1,
  "page_size": 20
}
```

## Agency Policy Q&A UI Contract

The agency UI must provide:
- A policy question input.
- A submit action.
- Loading and error states.
- Answer display.
- Citation display with document filename and page number.
- Optional debug/evidence panel for validation.
- Empty state when no processed policy documents are available.
