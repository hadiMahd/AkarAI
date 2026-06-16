# Research: Agency AI Workflows

## Decision: Reuse the existing shared guardrailed generation path for all new text outputs

**Rationale**: Listing drafts, lead reply drafts, and user comparison summaries all need the same redaction, safety, and provider-indirection guarantees already established for policy answers. Reusing the shared generation path avoids policy drift and keeps future AI features on one protection layer.

**Alternatives considered**:
- Call Azure OpenAI directly from each feature service: rejected because it duplicates provider logic and bypasses shared guardrails/redaction.
- Build a separate agency-only generation wrapper: rejected because the current wrapper is already the project-wide AI boundary.

## Decision: Extend the current RAG chat assistant instead of creating a second assistant stack

**Rationale**: The agency app already has `RagAssistantPage`, chat threads, cached thread detail, and guarded generation. Extending this assistant with approved read-only operational tools is lower risk than standing up a parallel assistant model, UI, and persistence path.

**Alternatives considered**:
- New `agency_assistant` module with separate routes and storage: rejected because it duplicates existing thread/message handling and increases migration/UI churn.
- Keep the assistant policy-only and add separate listing/lead mini-tools: rejected because the user explicitly wants one assistant that can answer both policy and operational questions.

## Decision: Open the assistant route to support employees while keeping admin-only management surfaces restricted

**Rationale**: The user explicitly wants support employees to use the assistant. The existing policy-documents and retrieval-log surfaces remain admin-only because they manage sensitive source material and diagnostic history, while answering read-only operational/policy questions fits the support role.

**Alternatives considered**:
- Keep assistant admin-only: rejected by user decision.
- Open document management and retrieval logs to support employees too: rejected because it widens source-control and diagnostics access unnecessarily.

## Decision: Keep assistant operational tools narrow, read-only, and backend-owned

**Rationale**: The user wants examples such as “get listing by …”, “get leads of tomorrow”, and “last 5 leads”. These are read/query tasks. Restricting tools to a small read-only catalog preserves tenant safety and makes prompt/tool auditing tractable.

**Alternatives considered**:
- Let the model answer directly from arbitrary SQL-like access: rejected for safety and maintainability.
- Add write tools for listings/leads in the assistant: rejected because the user asked for lookup-style tools and the constitution requires narrower permissions.

## Decision: Use synchronous temporary OCR extraction inside the listing form flow

**Rationale**: The spec-sheet upload is a dedicated extraction surface inside the create/edit listing form, and the user chose temporary handling only. A synchronous request keeps the review loop simple: upload, extract, review, apply selected fields, discard the file.

**Alternatives considered**:
- Persist the spec sheet as a long-lived attachment and run worker extraction: rejected because the user explicitly chose temporary-only handling.
- Separate OCR into a standalone pre-listing workflow: rejected because the user wants it inside the listing form.

## Decision: Use Azure Computer Vision Read OCR through the `OCRProvider` interface

**Rationale**: The provided Azure sample shows the Read API pattern and matches the project rule that exact providers must be user-approved. Wrapping it in `OCRProvider` keeps feature code provider-agnostic.

**Alternatives considered**:
- Hardcode Azure OCR calls in listing services: rejected because provider logic belongs behind interfaces.
- Azure Document Intelligence: rejected because the user asked to choose from the provided OCR guidance, which matches Computer Vision Read.

## Decision: Generate user comparison summaries from listing IDs, not client-sent listing text blobs

**Rationale**: The current compare page stores listing snapshots in `sessionStorage`. The backend should accept only selected listing IDs, then load fresh public-safe listing fields before summarization. This avoids stale or manipulated client payloads and keeps summaries aligned with current data.

**Alternatives considered**:
- Send full listing title/description/spec text from the client: rejected because it trusts stale client state and duplicates server-owned data.
- Persist comparison sessions server-side first: rejected as unnecessary scope expansion for this phase.

## Decision: Keep lead reply output as a reviewed draft that the frontend launches externally

**Rationale**: The phase acceptance criteria already say WhatsApp/email should open externally with a draft. The backend should return structured draft content; the frontend should build the external launch URL.

**Alternatives considered**:
- Send outbound email/WhatsApp directly from the backend: rejected by phase scope and product boundary.
- Limit replies to plain copied text with no channel hint: rejected because the existing acceptance criteria require opening the external channel with the draft.
