# Feature Specification: Agency AI Workflows

**Feature Branch**: `012-agency-ai-workflows`

**Created**: 2026-06-15

**Status**: Draft

**Input**: User description: "Current phase from PLAN.md: Phase 12 - Agency AI Workflows"

## User Scenarios & Testing *(mandatory)*

### User Story 1 - Generate Listing Drafts (Priority: P1)

An agency admin starts a new listing or updates an existing one, uploads an optional spec sheet for OCR extraction, and uses AI assistance to generate listing copy from the structured listing fields and any extracted property specs once processing completes, then reviews the draft before saving it.

**Why this priority**: This is the clearest direct productivity gain for agency admins and is explicitly required by the phase acceptance criteria.

**Independent Test**: Can be fully tested by opening a listing form, uploading a spec sheet, waiting for review-ready extracted fields, triggering draft generation, reviewing the generated title/description/spec text, editing it, and saving without relying on other AI workflows.

**Acceptance Scenarios**:

1. **Given** an agency admin has entered minimum required listing details, **When** the admin asks for a generated draft, **Then** the system queues the request and later returns editable listing copy without publishing or saving automatically.
2. **Given** a generated draft is shown, **When** the admin edits or rejects it, **Then** the system preserves human review as the final step before save.

---

### User Story 2 - Answer Agency Questions with Tools (Priority: P1)

An agency admin or support employee asks the agency assistant a workflow or operational question and receives a grounded answer that can combine agency policy knowledge with approved read-only access to tenant listings and leads.

**Why this priority**: Agency assistance is the central tenant-safe AI workflow for daily operations and builds directly on the existing RAG foundation.

**Independent Test**: Can be fully tested by uploading processed policy documents, asking policy and operational questions from the agency workspace, and verifying the answer is tenant-scoped, tool-limited, and cites supporting evidence where policy knowledge is used.

**Acceptance Scenarios**:

1. **Given** processed agency policy documents exist, **When** an authorized employee asks a supported policy question, **Then** the assistant returns a grounded answer tied to that agency's knowledge only.
2. **Given** an authorized employee asks an operational question such as recent leads or listing lookup, **When** the request fits approved read-only tools, **Then** the assistant answers using only that tenant's allowed data.
3. **Given** the available evidence and allowed tools do not support the question, **When** the employee asks anyway, **Then** the assistant declines or falls back without inventing unsupported details.

---

### User Story 3 - Draft Replies and Compare Listings (Priority: P2)

An agency admin or support employee opens a lead workflow to draft a customer-facing reply, while a signed-in user opens the comparison page to request an AI summary of the listings currently in the comparison set after the job completes.

**Why this priority**: Suggested replies and user-facing comparison summaries reduce manual writing time and help decision-making, but they depend on the core assistant and listing workflows being stable first.

**Independent Test**: Can be fully tested by opening a lead detail surface and the user comparison page separately, requesting a draft or summary, waiting for completion, and confirming each result is reviewable before any further action.

**Acceptance Scenarios**:

1. **Given** a lead record contains enough context, **When** an authorized employee requests a suggested reply, **Then** the system queues the draft, produces a reviewable result, and opens the selected external channel with that draft.
2. **Given** a signed-in user has added multiple listings to the comparison page, **When** the user requests an AI comparison, **Then** the system queues the comparison summary and later summarizes differences using listing title, description, and specs without using images.

### Edge Cases

- What happens when OCR input is low quality, partially unreadable, or yields conflicting property specs?
- How does the system behave when the assistant is asked for tenant data outside its approved read-only tools or outside the agency's approved policy scope?
- What happens when a lead reply draft is requested for a lead with missing contact method or sparse context?
- What happens when a user requests a comparison summary with only one listing or with stale comparison-session data?
- How are AI actions limited for support employees versus agency admins when the feature appears in shared agency surfaces?

## Requirements *(mandatory)*

### Functional Requirements

- **FR-001**: The system MUST let an agency admin request generated listing copy from listing context and review the generated result before saving any listing changes.
- **FR-002**: The system MUST keep generated listing copy editable and MUST NOT auto-publish, auto-save, or auto-send any AI-generated content.
- **FR-003**: The system MUST extract property specifications from scanned or image-based property documents and present extracted values for human review before they affect listing data.
- **FR-004**: The system MUST provide an agency support assistant that answers from tenant-scoped agency policy knowledge with citations and explicit fallback behavior when evidence is insufficient.
- **FR-005**: The agency support assistant MUST support approved read-only tools over tenant operational data, including listing lookup and lead lookup, in addition to tenant policy knowledge.
- **FR-006**: The agency support assistant MUST restrict operational access to approved read-only queries such as listing retrieval, recent leads, and date-based lead lookups, and MUST refuse unsupported or write-oriented actions.
- **FR-007**: The system MUST provide one suggested reply per lead detail view and require human review before that reply is copied or opened in an external communication channel.
- **FR-008**: The system MUST open WhatsApp and email externally with a prepared draft instead of sending messages directly from inside the product.
- **FR-009**: The system MUST provide an AI comparison summary on the user compare page for the listings currently selected there.
- **FR-010**: The AI comparison summary MUST use listing title, description, and specs only, and MUST NOT rely on listing images.
- **FR-011**: All agency AI actions MUST enforce tenant isolation, role permissions, and auditability for the acting employee.
- **FR-012**: The system MUST apply PII redaction and safety controls to prompts, outputs, logs, and cached artifacts used by agency AI workflows.
- **FR-013**: OCR-based extraction MUST use Azure Computer Vision Read OCR as the provider for this phase.
- **FR-014**: The system MUST track OCR extraction, listing draft generation, lead reply drafting, and comparison summaries as auditable jobs with queued, processing, completed, blocked, and failed states.
- **FR-015**: The system MUST let small policy-and-tool assistant answers complete synchronously while preserving the same tenant, redaction, and audit rules.

### Key Entities *(include if feature involves data)*

- **Agency AI Job**: A trackable job that moves through queued, processing, completed, blocked, and failed states for OCR extraction or longer generation flows.
- **Listing Draft Request**: A tenant-scoped request to generate or regenerate listing copy from structured listing context and optional extracted specs.
- **Extracted Property Specs**: Reviewable property attributes recovered from scanned or image-based source material before a human accepts them.
- **Agency Assistant Conversation**: A tenant-scoped question/answer exchange grounded in approved agency knowledge and constrained by employee role and allowed read-only operational tools.
- **Lead Reply Draft**: A reviewable reply suggestion linked to one lead and one external communication channel.
- **Comparison Summary Request**: A tenant-scoped request to summarize differences across listings selected on the comparison page.
- **Agency AI Audit Event**: A persistent audit record for AI request, completion, blocking, or failure outcomes using the existing audit log store.

### Constitution Alignment *(mandatory)*

- **Product Boundary**: This feature adds agency-side AI workflows plus a user-side listing comparison summary. It does not introduce buyer-to-agency real-time chat, and any customer communication remains draft-only with external sending.
- **Tenant/RBAC Impact**: Affected roles are Agency Admin, Support Employee, and signed-in User for the comparison summary only. Listing generation, OCR extraction, support assistant responses, reply drafts, summaries, logs, and cached artifacts must remain correctly scoped. Support-employee permissions must stay narrower than agency-admin permissions where editing or publishing risk exists, and assistant tool access must remain read-only.
- **AI/RAG Scope**: This feature extends agency AI workflows, agency policy RAG usage, approved read-only tool usage over tenant listings and leads, user comparison summarization, and provider-interface usage. It must not alter homepage search-only AI boundaries.
- **Reliability/Security/Performance**: OCR and longer generation jobs run asynchronously through auditable jobs. Rate limits, audit logs, PII redaction, tenant-safe caching, and Vault-managed provider secrets remain required. Any saved drafts or summaries must preserve review-before-action behavior.
- **Unknowns to Clarify**: None.

## Success Criteria *(mandatory)*

### Measurable Outcomes

- **SC-001**: Agency admins can generate and review a first listing draft in under 30 seconds for the common listing-entry path.
- **SC-002**: At least 90% of assistant answers shown to agency users include grounded citations or an explicit insufficient-evidence fallback.
- **SC-003**: Authorized employees can produce a reply draft and signed-in users can produce a comparison summary in a single interaction without the product sending any outbound message automatically.
- **SC-005**: Job state transitions for OCR and generation flows are visible to users or employees without exposing raw provider payloads.
- **SC-004**: Tenant-isolation checks prevent cross-agency AI context leakage in 100% of validation scenarios for this feature set.

## Assumptions

- Existing authentication, tenant context, RAG ingestion, reranking, guardrail foundations, and read-only role-safe data access patterns will be reused.
- Agency dashboard summarization remains out of scope for this spec unless one of the clarified flows requires it directly.
- Conversation persistence, draft persistence, and analytics depth can reuse existing product patterns unless the later plan identifies a stronger need.
- The current agency UI surfaces for listings, leads, and policy assistance will host these workflows rather than adding a separate standalone application.
