# Research: RAG Retrieval and Reranking

## Decision: Build both a backend retrieval contract and a basic agency policy Q&A screen

**Rationale**: The backend contract makes retrieval reusable by later assistant phases, while the agency Q&A screen gives a direct way to manually validate answers, citations, fallback behavior, and tenant isolation.

**Alternatives considered**:
- Backend-only retrieval endpoint: faster, but weak manual validation.
- UI-only retrieval flow: not reusable enough for later assistants.

## Decision: Defer area search RAG and area knowledge management

**Rationale**: The user explicitly removed area knowledge source work from this phase. Keeping Phase 9 limited to agency policy retrieval avoids mixing platform-owned area knowledge with agency-private policy retrieval.

**Alternatives considered**:
- Seed curated area files: rejected by user for this phase.
- Platform-admin area upload workflow: rejected by user for this phase.

## Decision: Return answer, citations, ranked evidence, and debug fields

**Rationale**: This supports both production-facing grounded answers and the validation/evaluation workflow needed before later AI features depend on retrieval quality.

**Alternatives considered**:
- Answer plus citations only: better UX, but insufficient for debugging and evals.
- Ranked evidence only: useful foundation, but does not validate answer generation behavior.

## Decision: Keep retrieval tenant-scoped at every lookup step

**Rationale**: Agency policy documents are tenant-private. Retrieval must filter documents, chunks, parent pages, logs, and answer context by the requesting agency tenant before any AI provider call.

**Alternatives considered**:
- Filter after vector retrieval: rejected because provider prompts and debug outputs could receive cross-tenant evidence.

## Decision: Use existing Azure OpenAI embeddings and add OpenRouter SDK behind the reranking provider interface

**Rationale**: Embeddings are already configured in the Phase 8 ingestion foundation. Reranking belongs behind the existing provider interface so feature code does not hardcode provider details. OpenRouter is the user-approved reranking provider for this phase.

**Alternatives considered**:
- Direct provider call from RAG service: rejected because it violates provider-interface boundaries.
- Other reranking providers: left available for later fallback or replacement, but not selected for this phase.

## Decision: Fetch parent page text after child chunk retrieval

**Rationale**: Child chunks are useful for matching, but final answers and citations need complete parent-page context to reduce fragmented or misleading answers.

**Alternatives considered**:
- Answer from child chunks only: simpler, but lower grounding quality and weaker citations.

## Decision: Evaluation baseline is required in this phase

**Rationale**: Retrieval and answer quality can regress silently. A repeatable dataset and command allow future phases to compare quality changes before shipping AI flows.

**Alternatives considered**:
- Manual-only validation: rejected because it is not repeatable and does not protect against regressions.
