"""Shared read-only query helpers for the platform admin dashboard.

These helpers aggregate data that already exists in the platform
(search logs, audit logs, listing inventory) for the read-only
dashboard. They MUST stay aggregate-only in this phase; the
Streamlit admin app does not get direct DB access.
"""
from __future__ import annotations

import json
from collections import defaultdict
from datetime import date, datetime, timedelta, timezone
from typing import Any, Iterable, Optional, Sequence
from uuid import UUID

from sqlalchemy import and_, func, select
from sqlalchemy.ext.asyncio import AsyncSession

from app.admin.schemas import (
    DashboardFilterScope,
    DemandGapEntry,
    DemandInsightSnapshot,
    PaginatedAuditLogResponse,
    PlatformAuditLogView,
    RankedSegment,
    RoleAccessSummary,
    RoleOverviewResponse,
    SearchVolumeTrendPoint,
)
from app.audit.feature_mapping import FEATURE_AREAS, build_audit_view_metadata, normalize_feature_area
from app.audit.models import AuditLog
from app.common.config import settings
from app.cities.models import City
from app.listings.models import Listing
from app.search.models import SearchLog


# ---------------------------------------------------------------------------
# Helpers
# ---------------------------------------------------------------------------


def _to_date(value: date | str | datetime) -> date:
    if isinstance(value, date) and not isinstance(value, datetime):
        return value
    if isinstance(value, datetime):
        return value.date()
    return datetime.fromisoformat(str(value)).date()


def _normalize_scope(
    *,
    date_from: date | str,
    date_to: date | str,
    range_preset: Optional[str],
    city: Optional[str],
    property_type: Optional[str],
    listing_purpose: Optional[str],
) -> DashboardFilterScope:
    df = _to_date(date_from)
    dt = _to_date(date_to)
    if df > dt:
        raise ValueError("date_from must be on or before date_to")
    window = (dt - df).days
    if window > settings.platform_dashboard_max_window_days:
        raise ValueError(
            f"Requested window of {window} days exceeds the platform maximum of "
            f"{settings.platform_dashboard_max_window_days} days."
        )
    preset = range_preset or "custom"
    if preset not in ("last_7_days", "last_30_days", "last_90_days", "custom"):
        raise ValueError(f"Unsupported range_preset: {preset}")
    return DashboardFilterScope(
        date_from=df,
        date_to=dt,
        range_preset=preset,
        city=city,
        property_type=property_type,
        listing_purpose=listing_purpose,
    )


def _scope_filters_to_search_log_columns(
    scope: DashboardFilterScope,
) -> list:
    """Best-effort: map dashboard filters onto ``search_logs.filters`` JSONB.

    ``search_logs.filters`` is a JSON blob; we cannot fully push these
    filters into the query, so we apply them in Python after fetch.
    """
    return []


def _scope_filters_to_listing_columns(
    scope: DashboardFilterScope,
) -> list:
    clauses = [Listing.status != "archived"]
    if scope.city:
        clauses.append(func.lower(Listing.city) == scope.city.lower())
    if scope.property_type:
        clauses.append(Listing.property_type == scope.property_type)
    if scope.listing_purpose:
        clauses.append(Listing.listing_purpose == scope.listing_purpose)
    return clauses


def _budget_band(price: float | int | None) -> str:
    if price is None:
        return "unknown"
    if price < 50_000:
        return "<50k"
    if price < 100_000:
        return "50k-100k"
    if price < 250_000:
        return "100k-250k"
    if price < 500_000:
        return "250k-500k"
    if price < 1_000_000:
        return "500k-1M"
    return "1M+"


def _normalize_filter_values(value: Any) -> list[str]:
    if value is None:
        return []
    if isinstance(value, str):
        normalized = value.strip()
        return [normalized] if normalized else []
    if isinstance(value, (list, tuple, set)):
        out: list[str] = []
        for item in value:
            out.extend(_normalize_filter_values(item))
        return out
    normalized = str(value).strip()
    return [normalized] if normalized else []


def _normalize_known_cities(
    value: Any,
    *,
    city_lookup: dict[str, str],
) -> list[str]:
    seen: set[str] = set()
    out: list[str] = []
    for candidate in _normalize_filter_values(value):
        normalized = city_lookup.get(candidate.lower())
        if normalized is None or normalized in seen:
            continue
        seen.add(normalized)
        out.append(normalized)
    return out


def _filter_contains_value(value: Any, expected: str) -> bool:
    expected_lower = expected.strip().lower()
    if not expected_lower:
        return False
    return any(candidate.lower() == expected_lower for candidate in _normalize_filter_values(value))


def _rank_segments(
    counts: dict[str, int],
    total: int,
    *,
    limit: int,
) -> list[RankedSegment]:
    items = sorted(counts.items(), key=lambda kv: (-kv[1], kv[0]))
    out: list[RankedSegment] = []
    for rank, (label, count) in enumerate(items[:limit], start=1):
        share = float(count) / total if total > 0 else 0.0
        out.append(
            RankedSegment(
                label=label,
                search_count=count,
                share=round(share, 4),
                rank=rank,
            )
        )
    return out


def _bucket_dates(
    df: date, dt: date, *, buckets: int
) -> list[tuple[datetime, datetime]]:
    if buckets <= 0:
        return []
    if df == dt:
        start = datetime.combine(df, datetime.min.time(), tzinfo=timezone.utc)
        return [(start, start + timedelta(days=1))]
    span_seconds = (
        datetime.combine(dt + timedelta(days=1), datetime.min.time(), tzinfo=timezone.utc)
        - datetime.combine(df, datetime.min.time(), tzinfo=timezone.utc)
    ).total_seconds()
    if span_seconds <= 0:
        return []
    bucket_seconds = span_seconds / buckets
    out: list[tuple[datetime, datetime]] = []
    cursor = datetime.combine(df, datetime.min.time(), tzinfo=timezone.utc)
    for i in range(buckets):
        b_start = cursor + timedelta(seconds=bucket_seconds * i)
        b_end = cursor + timedelta(seconds=bucket_seconds * (i + 1))
        out.append((b_start, b_end))
    return out


# ---------------------------------------------------------------------------
# Insights query
# ---------------------------------------------------------------------------


def _matches_filter_scope(record_filters: dict | None, scope: DashboardFilterScope) -> bool:
    if not record_filters or not isinstance(record_filters, dict):
        return True
    if scope.city and not _filter_contains_value(record_filters.get("city"), scope.city):
        return False
    if scope.property_type and record_filters.get("property_type") != scope.property_type:
        return False
    if scope.listing_purpose and record_filters.get("listing_purpose") != scope.listing_purpose:
        return False
    return True


async def _fetch_search_logs_for_scope(
    session: AsyncSession,
    scope: DashboardFilterScope,
) -> list[SearchLog]:
    start_dt = datetime.combine(scope.date_from, datetime.min.time(), tzinfo=timezone.utc)
    end_dt = datetime.combine(scope.date_to + timedelta(days=1), datetime.min.time(), tzinfo=timezone.utc)
    stmt = (
        select(SearchLog)
        .where(
            and_(
                SearchLog.created_at >= start_dt,
                SearchLog.created_at < end_dt,
            )
        )
        .order_by(SearchLog.created_at.asc())
    )
    result = await session.execute(stmt)
    items = list(result.scalars().all())
    return [log for log in items if _matches_filter_scope(log.filters, scope)]


async def _fetch_listing_inventory_for_scope(
    session: AsyncSession,
    scope: DashboardFilterScope,
) -> list[Listing]:
    clauses = _scope_filters_to_listing_columns(scope)
    stmt = select(Listing).where(and_(*clauses))
    result = await session.execute(stmt)
    return list(result.scalars().all())


async def _fetch_active_city_lookup(session: AsyncSession) -> dict[str, str]:
    result = await session.execute(
        select(City.name)
        .where(City.is_active.is_(True))
        .order_by(City.name.asc())
    )
    lookup: dict[str, str] = {}
    for (name,) in result.all():
        normalized = (name or "").strip()
        if normalized:
            lookup[normalized.lower()] = normalized.lower()
    return lookup


def _derive_demand_gaps(
    search_logs: Sequence[SearchLog],
    listings: Sequence[Listing],
    *,
    city_lookup: dict[str, str],
) -> list[DemandGapEntry]:
    """Build a small set of cross-dimension gap signals.

    The gaps are aggregate-only: they compare search demand counts
    (per city) to active supply counts (per city) and return a
    deterministic gap_score for each.
    """
    demand_by_city: dict[str, int] = defaultdict(int)
    for log in search_logs:
        f = log.filters or {}
        if not isinstance(f, dict):
            continue
        cities = _normalize_known_cities(f.get("city"), city_lookup=city_lookup)
        for city in cities:
            demand_by_city[city.lower()] += 1
    supply_by_city: dict[str, int] = defaultdict(int)
    for listing in listings:
        city = city_lookup.get((listing.city or "").strip().lower())
        if city is None:
            continue
        if listing.status == "active":
            supply_by_city[city.lower()] += 1

    cities = set(demand_by_city.keys()) | set(supply_by_city.keys())
    out: list[DemandGapEntry] = []
    for city in sorted(cities):
        demand = demand_by_city.get(city, 0)
        supply = supply_by_city.get(city, 0)
        if demand == 0 and supply == 0:
            continue
        # gap_score: ratio of demand to supply, bounded.
        if supply == 0:
            gap_score = 1.0
            direction = "undersupplied"
        else:
            ratio = demand / supply
            gap_score = round(min(ratio, 5.0), 4)
            if ratio >= 1.5:
                direction = "undersupplied"
            elif ratio <= 0.5:
                direction = "oversupplied"
            else:
                direction = "balanced"
        out.append(
            DemandGapEntry(
                dimension_type="city",
                dimension_label=city,
                demand_count=demand,
                supply_count=supply,
                gap_score=gap_score,
                gap_direction=direction,
            )
        )
    out.sort(key=lambda e: (-e.gap_score, e.dimension_label))
    return out[: settings.platform_dashboard_top_segment_limit]


def _build_trend(
    search_logs: Sequence[SearchLog],
    scope: DashboardFilterScope,
) -> list[SearchVolumeTrendPoint]:
    buckets = _bucket_dates(
        scope.date_from,
        scope.date_to,
        buckets=settings.platform_dashboard_trend_bucket_count,
    )
    if not buckets:
        return []
    out: list[SearchVolumeTrendPoint] = []
    for b_start, b_end in buckets:
        count = 0
        for log in search_logs:
            ts = log.created_at
            if ts.tzinfo is None:
                ts = ts.replace(tzinfo=timezone.utc)
            if b_start <= ts < b_end:
                count += 1
        out.append(
            SearchVolumeTrendPoint(
                bucket_start=b_start,
                bucket_end=b_end,
                search_count=count,
            )
        )
    return out


async def build_demand_insight_snapshot(
    session: AsyncSession,
    *,
    date_from: date | str,
    date_to: date | str,
    range_preset: Optional[str] = None,
    city: Optional[str] = None,
    property_type: Optional[str] = None,
    listing_purpose: Optional[str] = None,
) -> DemandInsightSnapshot:
    scope = _normalize_scope(
        date_from=date_from,
        date_to=date_to,
        range_preset=range_preset,
        city=city,
        property_type=property_type,
        listing_purpose=listing_purpose,
    )

    search_logs = await _fetch_search_logs_for_scope(session, scope)
    listings = await _fetch_listing_inventory_for_scope(session, scope)
    city_lookup = await _fetch_active_city_lookup(session)

    total = len(search_logs)

    area_counts: dict[str, int] = defaultdict(int)
    property_counts: dict[str, int] = defaultdict(int)
    budget_counts: dict[str, int] = defaultdict(int)
    for log in search_logs:
        f = log.filters or {}
        if not isinstance(f, dict):
            continue
        for city in _normalize_known_cities(f.get("city"), city_lookup=city_lookup):
            area_counts[city.lower()] += 1
        if f.get("property_type"):
            property_counts[str(f["property_type"])] += 1
        # Budget band derived from min_price/max_price midpoint, fallback
        # to result_count for non-priced searches.
        price_for_band = f.get("max_price")
        if price_for_band is None:
            price_for_band = f.get("min_price")
        band = _budget_band(price_for_band)
        if band != "unknown":
            budget_counts[band] += 1

    trend = _build_trend(search_logs, scope)
    demand_gaps = _derive_demand_gaps(search_logs, listings, city_lookup=city_lookup)
    area_total = sum(area_counts.values())
    budget_total = sum(budget_counts.values())
    property_total = sum(property_counts.values())

    return DemandInsightSnapshot(
        generated_at=datetime.now(timezone.utc),
        scope=scope,
        search_volume_total=total,
        search_volume_trend=trend,
        top_areas=_rank_segments(
            area_counts, area_total, limit=settings.platform_dashboard_top_segment_limit
        ),
        top_budget_bands=_rank_segments(
            budget_counts, budget_total, limit=settings.platform_dashboard_top_segment_limit
        ),
        top_property_types=_rank_segments(
            property_counts, property_total, limit=settings.platform_dashboard_top_segment_limit
        ),
        demand_gaps=demand_gaps,
    )


# ---------------------------------------------------------------------------
# Audit log query
# ---------------------------------------------------------------------------


def _coerce_actor_role(value: Any) -> str:
    if value is None or value == "":
        return "unknown"
    return str(value)


async def list_audit_logs(
    session: AsyncSession,
    *,
    page: int,
    page_size: int,
    date_from: datetime | None = None,
    date_to: datetime | None = None,
    feature_area: Optional[str] = None,
    actor_role: Optional[str] = None,
    result: Optional[str] = None,
) -> PaginatedAuditLogResponse:
    page = max(1, page)
    page_size = max(1, min(page_size, settings.platform_dashboard_audit_max_page_size))

    clauses = []
    if date_from is not None:
        clauses.append(AuditLog.created_at >= date_from)
    if date_to is not None:
        clauses.append(AuditLog.created_at <= date_to)
    if result is not None:
        clauses.append(AuditLog.result == result)

    base = select(AuditLog)
    if clauses:
        base = base.where(and_(*clauses))

    stmt = base.order_by(AuditLog.created_at.desc())
    rows = list((await session.execute(stmt)).scalars().all())

    filtered_items: list[PlatformAuditLogView] = []
    for row in rows:
        normalized_feature = normalize_feature_area(row.action, row.resource_type)
        if feature_area is not None and normalized_feature != feature_area:
            continue
        metadata = row.event_metadata if isinstance(row.event_metadata, dict) else {}
        resolved_actor_role = _coerce_actor_role(
            metadata.get("actor_role") or ("agency" if row.tenant_id else "platform")
        )
        if actor_role is not None and resolved_actor_role != actor_role:
            continue
        filtered_items.append(
            PlatformAuditLogView(
                id=str(row.id),
                created_at=row.created_at,
                actor_role=resolved_actor_role,
                feature_area=normalized_feature,
                action=row.action,
                result=row.result or "unknown",
                redacted_metadata=build_audit_view_metadata(
                    metadata,
                    actor_role=resolved_actor_role,
                ),
                actor_user_id=str(row.actor_user_id) if row.actor_user_id else None,
                tenant_scope_label="platform" if row.tenant_id is None else "agency",
            )
        )

    total = len(filtered_items)
    start = (page - 1) * page_size
    end = start + page_size
    items = filtered_items[start:end]

    return PaginatedAuditLogResponse(
        items=items,
        page=page,
        page_size=page_size,
        total=total,
        has_next=(page * page_size) < total,
        has_previous=page > 1,
    )


# ---------------------------------------------------------------------------
# Role overview query
# ---------------------------------------------------------------------------


ROLE_DISPLAY_NAMES = {
    "user": "User",
    "agency_admin": "Agency Admin",
    "support_employee": "Support Employee",
    "platform_admin": "Platform Admin",
}


# Each entry: (role_slug, surface_access, restricted_surfaces)
ROLE_SURFACE_ACCESS = {
    "user": (
        "Public marketplace search",
        "Saved listings",
        "Comparison sessions",
        "Lead inquiries",
        "Viewing bookings",
    ),
    "agency_admin": (
        "Agency dashboard",
        "Agency listings (read/write)",
        "Agency leads (read/write)",
        "Agency viewings (read/write)",
        "Agency AI workflows",
    ),
    "support_employee": (
        "Read-only agency context",
        "Tenant support actions (read)",
    ),
    "platform_admin": (
        "Platform admin dashboard",
        "Aggregate marketplace insights",
        "Redacted AI audit log viewer",
        "Role / access overview",
    ),
}


ROLE_RESTRICTED_SURFACES = {
    "user": (
        "Agency dashboard",
        "Platform admin dashboard",
        "Aggregate marketplace insights",
        "AI audit log viewer",
    ),
    "agency_admin": (
        "Platform admin dashboard",
        "Aggregate marketplace insights",
        "AI audit log viewer",
        "Other agency tenants",
    ),
    "support_employee": (
        "Agency listings (write)",
        "Agency leads (write)",
        "Platform admin dashboard",
        "Aggregate marketplace insights",
        "AI audit log viewer",
    ),
    "platform_admin": (
        "Agency-scoped mutations (without explicit authorization)",
    ),
}


async def build_role_overview(session: AsyncSession) -> RoleOverviewResponse:
    from app.auth.models import Permission, Role, RolePermission

    role_rows = (await session.execute(select(Role))).scalars().all()
    perm_rows = (
        await session.execute(
            select(Role.slug, Permission.key)
            .select_from(RolePermission)
            .join(Role, Role.id == RolePermission.role_id)
            .join(Permission, Permission.id == RolePermission.permission_id)
        )
    ).all()

    by_role: dict[str, set[str]] = defaultdict(set)
    for slug, key in perm_rows:
        if slug is None or key is None:
            continue
        by_role[str(slug)].add(str(key))

    items: list[RoleAccessSummary] = []
    for role in role_rows:
        slug = role.slug
        items.append(
            RoleAccessSummary(
                role_slug=slug,
                display_name=ROLE_DISPLAY_NAMES.get(slug, role.name or slug),
                granted_permissions=sorted(by_role.get(slug, set())),
                surface_access=list(ROLE_SURFACE_ACCESS.get(slug, ())),
                restricted_surfaces=list(ROLE_RESTRICTED_SURFACES.get(slug, ())),
            )
        )
    items.sort(key=lambda r: r.role_slug)
    return RoleOverviewResponse(items=items)


__all__ = [
    "FEATURE_AREAS",
    "build_demand_insight_snapshot",
    "build_role_overview",
    "list_audit_logs",
]
