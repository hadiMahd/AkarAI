from __future__ import annotations

from dataclasses import dataclass, field
from uuid import UUID

from app.rag.schemas import RagPolicyAnswer, RagRetrievalCitation, RagRetrievalDebug, RagRetrievalEvidence


@dataclass(slots=True)
class RetrievalCandidate:
    chunk_id: UUID
    document_id: UUID
    document_filename: str
    page_ids: list[UUID]
    page_numbers: list[int]
    text: str
    vector_rank: int
    vector_score: float
    rerank_rank: int | None = None
    rerank_score: float | None = None


@dataclass(slots=True)
class RetrievalResult:
    status: str
    answer: str
    citations: list[RagRetrievalCitation] = field(default_factory=list)
    evidence: list[RagRetrievalEvidence] = field(default_factory=list)
    debug: RagRetrievalDebug | None = None


def truncate_text(text: str, limit: int = 240) -> str:
    normalized = " ".join(text.split())
    if len(normalized) <= limit:
        return normalized
    return normalized[: max(0, limit - 1)] + "…"


def source_label(document_filename: str, page_numbers: list[int]) -> str:
    pages = ", ".join(str(page) for page in sorted(set(page_numbers)))
    if pages:
        return f"{document_filename} p.{pages}"
    return document_filename


def build_citations(candidates: list[RetrievalCandidate]) -> list[RagRetrievalCitation]:
    citations: list[RagRetrievalCitation] = []
    seen: set[tuple[UUID, int]] = set()
    for candidate in candidates:
        for page_number in candidate.page_numbers:
            key = (candidate.document_id, page_number)
            if key in seen:
                continue
            seen.add(key)
            citations.append(
                RagRetrievalCitation(
                    document_id=candidate.document_id,
                    document_filename=candidate.document_filename,
                    page_number=page_number,
                    source_label=source_label(candidate.document_filename, [page_number]),
                )
            )
    return citations


def build_evidence(candidates: list[RetrievalCandidate], parent_page_text: dict[UUID, str] | None = None) -> list[RagRetrievalEvidence]:
    parent_page_text = parent_page_text or {}
    evidence: list[RagRetrievalEvidence] = []
    for candidate in candidates:
        evidence.append(
            RagRetrievalEvidence(
                chunk_id=candidate.chunk_id,
                document_id=candidate.document_id,
                page_ids=candidate.page_ids,
                document_filename=candidate.document_filename,
                page_numbers=candidate.page_numbers,
                source_label=source_label(candidate.document_filename, candidate.page_numbers),
                vector_rank=candidate.vector_rank,
                vector_score=candidate.vector_score,
                rerank_rank=candidate.rerank_rank,
                rerank_score=candidate.rerank_score,
                text_preview=truncate_text(candidate.text),
                parent_page_text=truncate_text(parent_page_text.get(candidate.page_ids[0], ""), 800) if candidate.page_ids else None,
            )
        )
    return evidence


def assemble_result(
    query: str,
    candidates: list[RetrievalCandidate],
    *,
    answer_text: str | None = None,
    reranker_used: bool,
    reranker_provider: str | None,
    fallback_reason: str | None,
    confidence_status: str,
    retrieval_log_id: UUID,
    parent_page_text: dict[UUID, str] | None = None,
    guardrail_status: str | None = None,
    guardrail_blocked_reason: str | None = None,
    generation_provider: str | None = None,
) -> RetrievalResult:
    evidence = build_evidence(candidates, parent_page_text)
    citations = build_citations(candidates)
    if not evidence:
        status = "insufficient_evidence"
        answer = answer_text or "I could not find enough policy evidence to answer that."
    elif confidence_status == "fallback":
        status = "fallback"
        answer = answer_text or f"I found partial evidence for: {query}"
    else:
        status = "answered"
        answer = answer_text or f"Grounded answer for: {query}"
    debug = RagRetrievalDebug(
        reranker_used=reranker_used,
        reranker_provider=reranker_provider,
        fallback_reason=fallback_reason,
        confidence_status=confidence_status,
        retrieval_log_id=retrieval_log_id,
        guardrail_status=guardrail_status,
        guardrail_blocked_reason=guardrail_blocked_reason,
        generation_provider=generation_provider,
        vector_candidate_count=len(candidates),
        rerank_candidate_count=len([candidate for candidate in candidates if candidate.rerank_rank is not None]),
    )
    return RetrievalResult(
        status=status,
        answer=answer,
        citations=citations,
        evidence=evidence,
        debug=debug,
    )


def to_policy_answer(result: RetrievalResult) -> RagPolicyAnswer:
    return RagPolicyAnswer(
        status=result.status,
        answer=result.answer,
        citations=result.citations,
        evidence=result.evidence,
        debug=result.debug,
    )
