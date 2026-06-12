# Quickstart & Validation: RAG Storage & Ingestion

## Validation Scenarios

### 1. Happy Path: Valid PDF Upload & Processing
1. Login as an Agency Admin to get a token.
2. Upload a valid policy PDF (e.g., `policy.pdf`) via `POST /api/v1/agencies/rag/documents`.
3. Receive a `202 Accepted` response with status `pending`.
4. Run `GET /api/v1/agencies/rag/documents/{id}` a few seconds later.
5. Verify the status transitions to `processing` and then `processed`.
6. Verify in the database (`rag_chunks` table) that vectors and chunk data have been stored.

### 2. Failure Path: Invalid File Type
1. Upload a `.docx` or image file to `POST /api/v1/agencies/rag/documents`.
2. Verify you receive a `400 Bad Request` explicitly rejecting non-PDF.

### 3. Edge Case: Empty or Unparseable PDF
1. Upload a `.pdf` that contains only images and no extractable text.
2. Verify the document is created as `pending`.
3. Check `GET /api/v1/agencies/rag/documents/{id}` shortly after.
4. Verify the status updates to `failed` and no chunks are stored.
