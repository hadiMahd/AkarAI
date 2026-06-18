"""Platform admin service layer.

The service is responsible for:
- Validating filter scopes and applying them consistently
- Composing read-only responses from the ``query_service`` helpers
- Producing explicit empty-state responses when the source data is
  too thin to compute a panel
- Reading the per-scope cache and emitting a ``stale`` hint to the UI
  when data is older than a short freshness window
"""

from __future__ import annotations

import hashlib
import json
import logging
from datetime import date, datetime
from typing import Any, Optional
from uuid import UUID

from sqlalchemy.ext.asyncio import AsyncSession

from app.admin.query_service import (
    build_demand_insight_snapshot,
    build_role_overview,
    list_audit_logs,
)
from app.admin.schemas import (
    DemandInsightSnapshot,
    PaginatedAuditLogResponse,
    PaginatedRagEvalRunsResponse,
    RagEvalExampleView,
    RagEvalRunDetail,
    RagEvalRunListItem,
    RoleOverviewResponse,
)
from app.audit.repository import AuditLogRepository
from app.audit.service import AuditService
from app.common.cache import cache_get, cache_invalidate_namespace, cache_set
from app.common.config import settings
from app.common.exceptions import NotFoundError, ValidationError
from app.common.pagination import PaginationRequest, PaginationResult
from app.rag.repository import RagRepository

logger = logging.getLogger(__name__)


PLATFORM_DASHBOARD_INSIGHTS_CACHE_NAMESPACE = "platform_dashboard:insights"
PLATFORM_DASHBOARD_AUDIT_CACHE_NAMESPACE = "platform_dashboard:audit"
PLATFORM_DASHBOARD_ROLES_CACHE_NAMESPACE = "platform_dashboard:roles"
PLATFORM_DASHBOARD_RAG_EVALS_CACHE_NAMESPACE = "platform_dashboard:rag_evals"


def _build_insights_cache_key(payload: dict[str, Any]) -> str:
    serialized = json.dumps(payload, sort_keys=True, default=str, separators=(",", ":"))
    digest = hashlib.sha256(serialized.encode("utf-8")).hexdigest()
    return f"insights:v1:{digest}"


def _build_audit_cache_key(payload: dict[str, Any]) -> str:
    serialized = json.dumps(payload, sort_keys=True, default=str, separators=(",", ":"))
    digest = hashlib.sha256(serialized.encode("utf-8")).hexdigest()
    return f"audit:v1:{digest}"


class PlatformAdminService:
    """Coordinates read-only platform admin reads, with bounded cache + audit."""

    def __init__(self, session: AsyncSession):
        self._session = session
        self._audit_repo = AuditLogRepository(session)
        self._audit = AuditService(self._audit_repo)
        self._rag_repo = RagRepository(session)

    async def get_demand_insights(
        self,
        *,
        date_from: date | str,
        date_to: date | str,
        range_preset: Optional[str] = None,
        city: Optional[str] = None,
        property_type: Optional[str] = None,
        listing_purpose: Optional[str] = None,
        actor_id: Optional[str] = None,
    ) -> DemandInsightSnapshot:
        try:
            payload: dict[str, Any] = {
                "date_from": str(date_from),
                "date_to": str(date_to),
                "range_preset": range_preset or "custom",
                "city": city,
                "property_type": property_type,
                "listing_purpose": listing_purpose,
            }
            cache_key = _build_insights_cache_key(payload)
            cached = await cache_get(PLATFORM_DASHBOARD_INSIGHTS_CACHE_NAMESPACE, cache_key)
            if cached is not None and "generated_at" in cached:
                snapshot = DemandInsightSnapshot.model_validate(cached)
                await self._audit_view(
                    action="platform_dashboard.insights.read",
                    result="cache_hit",
                    actor_user_id=actor_id,
                )
                return snapshot

            snapshot = await build_demand_insight_snapshot(
                self._session,
                date_from=date_from,
                date_to=date_to,
                range_preset=range_preset,
                city=city,
                property_type=property_type,
                listing_purpose=listing_purpose,
            )
            await cache_set(
                PLATFORM_DASHBOARD_INSIGHTS_CACHE_NAMESPACE,
                cache_key,
                snapshot.model_dump(mode="json"),
                ttl=settings.platform_dashboard_insights_cache_ttl_seconds,
            )
            await self._audit_view(
                action="platform_dashboard.insights.read",
                result="fresh",
                actor_user_id=actor_id,
            )
            return snapshot
        except ValueError as exc:
            raise ValidationError(detail=str(exc), error_code="INVALID_DASHBOARD_SCOPE") from exc

    async def list_audit_logs(
        self,
        *,
        page: int,
        page_size: int,
        date_from: Optional[datetime] = None,
        date_to: Optional[datetime] = None,
        feature_area: Optional[str] = None,
        actor_role: Optional[str] = None,
        result: Optional[str] = None,
        actor_id: Optional[str] = None,
    ) -> PaginatedAuditLogResponse:
        page = max(1, page)
        page_size = max(1, min(page_size, settings.platform_dashboard_audit_max_page_size))
        cache_key = _build_audit_cache_key(
            {
                "page": page,
                "page_size": page_size,
                "date_from": date_from.isoformat() if date_from else None,
                "date_to": date_to.isoformat() if date_to else None,
                "feature_area": feature_area,
                "actor_role": actor_role,
                "result": result,
            }
        )
        cached = await cache_get(PLATFORM_DASHBOARD_AUDIT_CACHE_NAMESPACE, cache_key)
        if cached is not None and "items" in cached:
            response = PaginatedAuditLogResponse.model_validate(cached)
            await self._audit_view(
                action="platform_dashboard.audit_logs.read",
                result="cache_hit",
                actor_user_id=actor_id,
            )
            return response

        response = await list_audit_logs(
            self._session,
            page=page,
            page_size=page_size,
            date_from=date_from,
            date_to=date_to,
            feature_area=feature_area,
            actor_role=actor_role,
            result=result,
        )
        await cache_set(
            PLATFORM_DASHBOARD_AUDIT_CACHE_NAMESPACE,
            cache_key,
            response.model_dump(mode="json"),
            ttl=settings.platform_dashboard_audit_cache_ttl_seconds,
        )
        await self._audit_view(
            action="platform_dashboard.audit_logs.read",
            result="fresh",
            actor_user_id=actor_id,
        )
        return response

    async def get_role_overview(
        self,
        *,
        actor_id: Optional[str] = None,
    ) -> RoleOverviewResponse:
        cached = await cache_get(PLATFORM_DASHBOARD_ROLES_CACHE_NAMESPACE, "overview:v1")
        if cached is not None and "items" in cached:
            response = RoleOverviewResponse.model_validate(cached)
            await self._audit_view(
                action="platform_dashboard.roles.read",
                result="cache_hit",
                actor_user_id=actor_id,
            )
            return response
        response = await build_role_overview(self._session)
        await cache_set(
            PLATFORM_DASHBOARD_ROLES_CACHE_NAMESPACE,
            "overview:v1",
            response.model_dump(mode="json"),
            ttl=settings.platform_dashboard_audit_cache_ttl_seconds,
        )
        await self._audit_view(
            action="platform_dashboard.roles.read",
            result="fresh",
            actor_user_id=actor_id,
        )
        return response

    async def list_rag_eval_runs(
        self,
        *,
        page: int,
        page_size: int,
        actor_id: Optional[str] = None,
    ) -> PaginatedRagEvalRunsResponse:
        pagination = PaginationRequest(page=page, page_size=page_size)
        cache_key = _build_audit_cache_key(
            {"page": pagination.page, "page_size": pagination.page_size}
        )
        cached = await cache_get(PLATFORM_DASHBOARD_RAG_EVALS_CACHE_NAMESPACE, f"runs:{cache_key}")
        if cached is not None and "items" in cached:
            response = PaginatedRagEvalRunsResponse.model_validate(cached)
            await self._audit_view(
                action="platform_dashboard.rag_evals.read",
                result="cache_hit",
                actor_user_id=actor_id,
            )
            return response

        runs, total = await self._rag_repo.list_evaluation_runs(
            tenant_id=None,
            pagination=pagination,
        )
        payload = PaginationResult(
            items=[self._serialize_eval_run(run) for run in runs],
            total=total,
            pagination=pagination,
        )
        response = PaginatedRagEvalRunsResponse(
            items=payload.items,
            page=payload.page,
            page_size=payload.page_size,
            total=payload.total,
            has_next=payload.has_next,
            has_previous=payload.has_previous,
        )
        await cache_set(
            PLATFORM_DASHBOARD_RAG_EVALS_CACHE_NAMESPACE,
            f"runs:{cache_key}",
            response.model_dump(mode="json"),
            ttl=settings.platform_dashboard_audit_cache_ttl_seconds,
        )
        await self._audit_view(
            action="platform_dashboard.rag_evals.read",
            result="fresh",
            actor_user_id=actor_id,
        )
        return response

    async def get_rag_eval_run_detail(
        self,
        *,
        run_id: UUID,
        actor_id: Optional[str] = None,
    ) -> RagEvalRunDetail:
        cached = await cache_get(
            PLATFORM_DASHBOARD_RAG_EVALS_CACHE_NAMESPACE,
            f"run:{run_id}",
        )
        if cached is not None and "run" in cached:
            response = RagEvalRunDetail.model_validate(cached)
            await self._audit_view(
                action="platform_dashboard.rag_eval_detail.read",
                result="cache_hit",
                actor_user_id=actor_id,
            )
            return response

        run = await self._rag_repo.get_evaluation_run(run_id)
        if run is None:
            raise NotFoundError(
                detail="RAG eval run not found", error_code="RAG_EVAL_RUN_NOT_FOUND"
            )
        examples = await self._rag_repo.list_evaluation_examples_by_run_id(run_id)
        response = RagEvalRunDetail(
            run=self._serialize_eval_run(run),
            examples=[self._serialize_eval_example(example) for example in examples],
        )
        await cache_set(
            PLATFORM_DASHBOARD_RAG_EVALS_CACHE_NAMESPACE,
            f"run:{run_id}",
            response.model_dump(mode="json"),
            ttl=settings.platform_dashboard_audit_cache_ttl_seconds,
        )
        await self._audit_view(
            action="platform_dashboard.rag_eval_detail.read",
            result="fresh",
            actor_user_id=actor_id,
        )
        return response

    # ------------------------------------------------------------------
    # Invalidation hooks — called by listing/search write paths to keep
    # the dashboard fresh as source data changes.
    # ------------------------------------------------------------------

    async def invalidate_insights(self) -> None:
        await cache_invalidate_namespace(PLATFORM_DASHBOARD_INSIGHTS_CACHE_NAMESPACE)

    async def invalidate_audit(self) -> None:
        await cache_invalidate_namespace(PLATFORM_DASHBOARD_AUDIT_CACHE_NAMESPACE)

    async def invalidate_roles(self) -> None:
        await cache_invalidate_namespace(PLATFORM_DASHBOARD_ROLES_CACHE_NAMESPACE)

    async def invalidate_rag_evals(self) -> None:
        await cache_invalidate_namespace(PLATFORM_DASHBOARD_RAG_EVALS_CACHE_NAMESPACE)

    async def _audit_view(
        self,
        *,
        action: str,
        result: str,
        actor_user_id: Optional[str] = None,
    ) -> None:
        try:
            await self._audit.log_auth_event(
                action=action,
                result=result,
                actor_user_id=actor_user_id,
                metadata={"feature_area": "platform_dashboard"},
            )
        except Exception:  # pragma: no cover — audit must not break reads
            logger.warning("Platform admin view audit log failed", exc_info=True)

    def _serialize_eval_run(self, run: Any) -> RagEvalRunListItem:
        summary = run.summary or {}
        metrics = summary.get("metrics", {}) or {}
        latency = summary.get("latency_ms", {}) or {}
        threshold_failures = summary.get("threshold_failures", []) or []
        return RagEvalRunListItem(
            run_id=str(run.id),
            run_label=run.run_label,
            created_at=run.created_at,
            completed_at=run.completed_at,
            mode=summary.get("mode") or _infer_eval_mode(run.run_label),
            run_classification=_classify_eval_run(
                mode=summary.get("mode") or _infer_eval_mode(run.run_label),
                total_examples=run.total_examples,
                run_label=run.run_label,
            ),
            total_examples=run.total_examples,
            passed_examples=run.passed_examples,
            failed_examples=run.failed_examples,
            faithfulness=_to_float(metrics.get("faithfulness")),
            context_precision=_to_float(metrics.get("context_precision")),
            context_recall=_to_float(metrics.get("context_recall")),
            answer_relevancy=_to_float(metrics.get("answer_relevancy")),
            hit_at_1=_to_float(metrics.get("hit_at_1")),
            hit_at_5=_to_float(metrics.get("hit_at_5")),
            tenant_leakage_count=int(metrics.get("tenant_leakage_count") or 0),
            p95_latency_ms=_to_float(latency.get("p95")),
            judge_failures=int(summary.get("judge_failures") or 0),
            threshold_failures=[str(item) for item in threshold_failures],
            passed=not bool(threshold_failures),
        )

    def _serialize_eval_example(self, example: Any) -> RagEvalExampleView:
        summary = example.summary or {}
        metrics = summary.get("metrics", {}) or {}
        answer = summary.get("answer", {}) or {}
        failure_reasons = summary.get("failure_reasons", []) or []
        return RagEvalExampleView(
            example_id=example.id,
            query=example.query,
            tenant_fixture=example.tenant_fixture,
            expected_behavior=example.expected_behavior,
            passed=bool(example.passed),
            answer_status=answer.get("status"),
            faithfulness=_to_float(metrics.get("faithfulness")),
            context_precision=_to_float(metrics.get("context_precision")),
            context_recall=_to_float(metrics.get("context_recall")),
            answer_relevancy=_to_float(metrics.get("answer_relevancy")),
            hit_at_1=_to_bool(metrics.get("hit_at_1")),
            hit_at_5=_to_bool(metrics.get("hit_at_5")),
            expected_source_match=_to_bool(metrics.get("expected_source_match")),
            leaked_sources=[str(item) for item in (summary.get("leaked_sources") or [])],
            latency_ms=_to_float(summary.get("latency_ms")),
            failure_reasons=[str(item) for item in failure_reasons],
        )


def _infer_eval_mode(run_label: str | None) -> str:
    label = (run_label or "").lower()
    if "manual" in label:
        return "manual"
    return "blocking"


def _classify_eval_run(*, mode: str, total_examples: int, run_label: str | None) -> str:
    label = (run_label or "").lower()
    if (mode == "blocking" and total_examples == 20) or (mode == "manual" and total_examples == 40):
        return "full_suite"
    if label.startswith("ragas-test-run-") or label.startswith("int-test-eval-") or label.startswith("int-fail-eval-"):
        return "test"
    return "ad_hoc"


def _to_float(value: Any) -> float | None:
    try:
        return None if value is None else float(value)
    except (TypeError, ValueError):
        return None


def _to_bool(value: Any) -> bool | None:
    if value is None:
        return None
    return bool(value)


__all__ = [
    "PLATFORM_DASHBOARD_INSIGHTS_CACHE_NAMESPACE",
    "PLATFORM_DASHBOARD_AUDIT_CACHE_NAMESPACE",
    "PLATFORM_DASHBOARD_ROLES_CACHE_NAMESPACE",
    "PLATFORM_DASHBOARD_RAG_EVALS_CACHE_NAMESPACE",
    "PlatformAdminService",
]
