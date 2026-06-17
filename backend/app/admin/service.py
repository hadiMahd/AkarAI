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
from datetime import date, datetime, timezone
from typing import Any, Optional

from sqlalchemy.ext.asyncio import AsyncSession

from app.admin.query_service import (
    build_demand_insight_snapshot,
    build_role_overview,
    list_audit_logs,
)
from app.admin.schemas import (
    DemandInsightSnapshot,
    PaginatedAuditLogResponse,
    RoleOverviewResponse,
)
from app.audit.service import AuditService
from app.audit.repository import AuditLogRepository
from app.common.cache import cache_get, cache_set, cache_invalidate_namespace
from app.common.config import settings
from app.common.exceptions import ValidationError


logger = logging.getLogger(__name__)


PLATFORM_DASHBOARD_INSIGHTS_CACHE_NAMESPACE = "platform_dashboard:insights"
PLATFORM_DASHBOARD_AUDIT_CACHE_NAMESPACE = "platform_dashboard:audit"
PLATFORM_DASHBOARD_ROLES_CACHE_NAMESPACE = "platform_dashboard:roles"


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
        cached = await cache_get(
            PLATFORM_DASHBOARD_ROLES_CACHE_NAMESPACE, "overview:v1"
        )
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


__all__ = [
    "PLATFORM_DASHBOARD_INSIGHTS_CACHE_NAMESPACE",
    "PLATFORM_DASHBOARD_AUDIT_CACHE_NAMESPACE",
    "PLATFORM_DASHBOARD_ROLES_CACHE_NAMESPACE",
    "PlatformAdminService",
]
