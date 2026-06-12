# API Contracts: RAG Storage & Ingestion

## Upload Document
`POST /api/v1/agencies/rag/documents`
- **Headers**: `Authorization: Bearer <token>`
- **Content-Type**: `multipart/form-data`
- **Body**: 
  - `file`: `(PDF File)`
- **Response**: `202 Accepted`
  ```json
  {
    "id": "uuid",
    "filename": "policy.pdf",
    "status": "pending",
    "created_at": "2026-06-12T..."
  }
  ```

## Get Document Status
`GET /api/v1/agencies/rag/documents/{id}`
- **Headers**: `Authorization: Bearer <token>`
- **Response**: `200 OK`
  ```json
  {
    "id": "uuid",
    "filename": "policy.pdf",
    "status": "processed",
    "created_at": "2026-06-12T...",
    "updated_at": "2026-06-12T..."
  }
  ```

## List RAG Documents
`GET /api/v1/agencies/rag/documents`
- **Headers**: `Authorization: Bearer <token>`
- **Response**: `200 OK`
  ```json
  {
    "items": [
      {
        "id": "uuid",
        "filename": "policy.pdf",
        "status": "processed",
        "created_at": "2026-06-12T..."
      }
    ],
    "total": 1,
    "page": 1,
    "size": 50
  }
  ```
