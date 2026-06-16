# Quickstart: Agency AI Workflows

## Prerequisites

- Docker Compose stack running with backend, agency app, user app, workers, PostgreSQL, Redis, Vault, and MinIO.
- Vault contains the existing Azure OpenAI chat/embedding credentials and the OCR credentials needed for Azure Computer Vision Read.
- At least one agency tenant exists with:
  - one agency admin
  - one support employee
  - several listings
  - several leads
  - processed policy documents for the assistant
- The protected user app has at least 2 active public listings available for comparison.

## Setup

```bash
docker compose up -d backend agency-app user-app workers postgres redis vault
docker compose exec backend alembic upgrade head
```

## Validation Scenarios

### 1. Temporary Spec Extraction in Listing Form

1. Sign in to the agency app as an agency admin.
2. Open the create-listing page.
3. In the dedicated spec-sheet upload area, upload a property spec sheet.
4. Wait for the extracted fields to become review-ready.
5. Apply only selected extracted values to the listing form.

Expected:
- The file is used for extraction only and is not shown later as a durable listing attachment.
- Extracted values are reviewable before they touch the form.
- Low-confidence or unreadable fields are surfaced as warnings instead of silently applied.

### 2. Listing Draft Generation

1. Stay on the create-listing or edit-listing form as an agency admin.
2. Fill enough structured listing details to describe the property.
3. Request an AI draft.
4. Wait for the queued job to finish.
5. Edit the returned title/description before saving.

Expected:
- The draft appears after processing without saving or publishing anything automatically.
- The generated text reflects the current form state plus any applied extracted specs.
- Guardrail/provider failures degrade to a clear error state without corrupting the form.

### 3. Assistant Access for Support Employees

1. Sign in as a support employee.
2. Open the assistant route.
3. Ask a policy question backed by agency RAG.
4. Ask an operational question such as “show me the last 5 leads”.

Expected:
- Support employees can access the assistant route.
- Policy answers cite tenant policy evidence.
- Operational answers use only approved read-only listing/lead data.
- Unsupported write-style requests are refused.
- Support employees still cannot access policy-document management or retrieval-log admin pages.

### 4. Lead Reply Draft

1. Sign in as an agency admin or support employee.
2. Open a lead detail page.
3. Request a reply draft for email or WhatsApp.
4. Wait for the queued job to finish.
5. Launch the external channel.

Expected:
- One reviewable draft is returned for the selected lead after processing completes.
- The app opens the external channel with the prepared draft.
- No message is sent directly by the backend.

### 5. User Compare Summary

1. Sign in to the user app.
2. Add 2 to 4 listings to the compare tray.
3. Open the compare page.
4. Request an AI comparison summary.
5. Wait for the summary job to complete.

Expected:
- The summary is generated from the selected listings only after the job completes.
- The output focuses on listing title, description, and specs rather than images.
- Removing a listing and re-running the summary changes the result accordingly.

## Focused Test Commands

```bash
docker compose exec backend pytest backend/tests/unit/test_agency_listing_ai.py backend/tests/integration/test_agency_listing_ai_api.py backend/tests/rbac/test_agency_listing_ai_rbac.py backend/tests/unit/test_rag_assistant_tools.py backend/tests/integration/test_rag_chat_tools_api.py backend/tests/rbac/test_rag_assistant_support_access.py backend/tests/unit/test_lead_reply_and_comparison_summary.py backend/tests/integration/test_lead_reply_api.py backend/tests/integration/test_comparison_summary_api.py backend/tests/rbac/test_lead_reply_and_comparison_summary_access.py
docker compose exec agency-app npm run test -- listing-ai-workflow rag-policy-qa lead-reply-draft
docker compose exec user-app npm run test -- comparison-ai-summary
```

No broad e2e browser automation is part of this phase unless explicitly requested later.
