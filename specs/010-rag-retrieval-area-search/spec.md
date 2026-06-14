# Feature Specification: RAG Retrieval and Reranking

**Feature Branch**: `010-rag-retrieval-openrouter-reranking-and-area-search-rag`

**Created**: 2026-06-12

**Status**: Draft

**Input**: User description: "current phase ask me for details dont assume anything"

## User Scenarios & Testing *(mandatory)*

### User Story 1 - Retrieve Agency Policy Answers (Priority: P1)

Agency admins and support employees need to ask questions about their agency policy documents and receive answers grounded only in documents available to their agency.

**Why this priority**: Agency policy retrieval is the direct continuation of policy document upload and ingestion. It proves that uploaded documents can be used safely and accurately.

**Independent Test**: Upload policy documents for two agencies, ask a policy question as an employee from one agency, and verify the answer uses only that employee's agency documents with cited source references.

**Acceptance Scenarios**:

1. **Given** an agency employee has access to processed policy documents, **When** they ask a policy question, **Then** the response uses only documents from that employee's agency and includes source references.
2. **Given** another agency has a document with relevant but tenant-private content, **When** the first agency employee asks a matching question, **Then** the response does not use or expose the other agency's content.
3. **Given** no relevant agency policy content exists, **When** the employee asks a policy question, **Then** the system clearly says it could not find enough policy evidence and does not invent an answer.

---

### User Story 2 - Support Assistant Retrieval (Priority: P2)

Support employees need retrieval-assisted answers for agency operations without gaining permissions beyond their role.

**Why this priority**: Support employees are daily operators. Retrieval must respect role boundaries and give useful answers without expanding their authority.

**Independent Test**: Sign in as a support employee, ask questions covered by agency policy documents, and verify answers include allowed policy sources while excluding listing-management or employee-management actions.

**Acceptance Scenarios**:

1. **Given** a support employee asks about an allowed agency policy, **When** matching policy evidence exists, **Then** the response cites policy sources from the employee's agency.
2. **Given** a support employee asks for an admin-only action or confidential platform-wide data, **When** retrieval is performed, **Then** the response refuses or limits the answer according to the support role.

---

### User Story 3 - Evaluate Retrieval Quality (Priority: P3)

The project owner needs repeatable evaluation runs that show whether retrieval and answers are improving or regressing as documents, prompts, and ranking behavior change.

**Why this priority**: RAG behavior can regress silently. A baseline and repeatable evaluation process are required before layering user-facing AI flows on top.

**Independent Test**: Run the retrieval evaluation set twice against the same documents and verify that the run records comparable quality metrics, failed cases, and source evidence.

**Acceptance Scenarios**:

1. **Given** a fixed evaluation dataset, **When** the evaluation runs, **Then** it records retrieval quality, answer grounding quality, and examples that failed acceptance thresholds.
2. **Given** a retrieval change is made, **When** the evaluation runs again, **Then** the project owner can compare the new run against the baseline.

### Edge Cases

- A user asks a question before any matching document has completed processing.
- A document is replaced while retrieval is in progress.
- A retrieved child chunk matches but the parent page text is unavailable.
- Multiple agencies upload near-identical policy documents.
- The reranker is unavailable, rate-limited, or returns no useful ordering.
- Retrieval returns low-confidence evidence below the allowed answer threshold.
- Evaluation examples contain outdated or deleted documents.

## Requirements *(mandatory)*

### Functional Requirements

- **FR-001**: The system MUST let authorized agency staff ask policy questions against their agency's processed policy documents.
- **FR-002**: The system MUST restrict policy retrieval to documents, pages, and chunks belonging to the requesting staff member's agency tenant.
- **FR-003**: The system MUST include source references for retrieval-backed policy answers, including document identity and page-level evidence where available.
- **FR-004**: The system MUST avoid answering when retrieved evidence is insufficient, contradictory, or outside the user's allowed scope.
- **FR-005**: The system MUST support support-employee retrieval without granting support employees admin-only capabilities or platform-wide visibility.
- **FR-006**: The system MUST provide a basic agency policy Q&A screen for authorized agency staff.
- **FR-007**: The system MUST also expose retrieval behavior in a backend contract so later assistant flows can reuse the same grounded retrieval result.
- **FR-008**: The system MUST return answer text, source citations, ranked evidence, and debug fields needed for retrieval testing and evaluation.
- **FR-009**: The system MUST log retrieval activity with tenant, actor, query, selected sources, confidence outcome, and whether a fallback was used.
- **FR-010**: The system MUST support reranking retrieved evidence before final answer or search filter selection.
- **FR-011**: The system MUST degrade cleanly when reranking is unavailable by using the best available retrieval order and recording the fallback.
- **FR-012**: The system MUST fetch parent page evidence for selected child chunks so citations and answer grounding are based on complete page context.
- **FR-013**: The system MUST provide repeatable retrieval evaluation runs that compare current behavior against a baseline.
- **FR-014**: Evaluation results MUST identify weak examples, missing evidence, and answer grounding failures.
- **FR-015**: The system MUST reject retrieval requests that lack required tenant context or user authorization.
- **FR-016**: Retrieval logs and evaluation artifacts MUST avoid exposing secrets or unnecessary personal data.
- **FR-017**: The system MUST NOT implement area knowledge source management, area document ingestion, or area search RAG in this phase.

### Key Entities *(include if feature involves data)*

- **Retrieval Query**: A user's or employee's question, tenant context, actor context, request type, and requested retrieval scope.
- **Retrieved Evidence**: Ranked chunks, parent page text references, source documents, confidence outcome, and reranking outcome.
- **Policy Answer**: A grounded response for agency staff, including cited evidence and refusal or fallback state when evidence is insufficient.
- **Retrieval Evaluation Example**: A test question, expected evidence or behavior, expected answer qualities, and evaluation result.
- **Retrieval Log**: An audit record of retrieval inputs, selected evidence, actor context, tenant scope, and quality/fallback metadata.

### Constitution Alignment *(mandatory)*

- **Product Boundary**: This feature affects agency policy RAG retrieval only. It must not create buyer-to-agency real-time chat. User inquiries remain structured leads and viewing bookings remain scheduled viewing records.
- **Tenant/RBAC Impact**: Agency Admin and Support Employee can retrieve only their agency policy sources. Platform Admin area knowledge management is out of scope for this phase.
- **AI/RAG Scope**: This feature covers agency policy RAG retrieval, support assistant retrieval foundations, reranking, retrieval logs, and retrieval evaluation baselines. It does not implement area search RAG, listing page AI chat, generated lead replies, OCR, STT, TTS, or voice search.
- **Reliability/Security/Performance**: Retrieval must enforce tenant scope, use paginated logs where shown, preserve source traceability, record reranking fallback, avoid unnecessary PII in logs, and use Vault-managed provider secrets.
- **Unknowns to Clarify**: None.

## Success Criteria *(mandatory)*

### Measurable Outcomes

- **SC-001**: In tenant isolation tests, 100% of agency policy retrieval attempts return only sources from the requesting agency.
- **SC-002**: At least 90% of accepted policy answers include a cited source document and page reference.
- **SC-003**: At least 85% of policy retrieval evaluation examples return acceptable grounded answers or explicitly fall back without unsupported claims.
- **SC-004**: Retrieval evaluation can be run repeatedly and produces comparable baseline results for at least 25 policy retrieval examples.
- **SC-005**: 95% of retrieval requests either return a grounded response, ranked evidence, or a clear fallback within 5 seconds under normal local development data volume.
- **SC-006**: 100% of low-confidence retrieval cases in the evaluation set avoid unsupported final answers.

## Assumptions

- Phase 8 document upload, replacement, page extraction, chunking, embeddings, and tenant-scoped document storage are available.
- Retrieval must remain auditable before later user-facing AI flows depend on it.
- Reranking is part of this phase, but retrieval must still work with a recorded fallback if reranking is unavailable.
- Existing authentication, tenant context, role permissions, Vault-backed secrets, and ingestion logs remain the source of truth for access and audit decisions.
- Area search RAG and area knowledge management are intentionally deferred from this phase.
