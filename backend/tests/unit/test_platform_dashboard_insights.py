"""Unit tests for the platform admin demand-insight query service.

These tests exercise the read-only query_service helpers that aggregate
``SearchLog`` + ``Listing`` data for the platform admin dashboard. They
do not require Docker — they construct in-memory session state via
direct inserts through the existing async session factory that the
backend's ``tests/conftest.py`` already wires up.
"""
from __future__ import annotations

import uuid
from datetime import date, datetime, timezone

import pytest

from app.admin.query_service import (
    _budget_band,
    _bucket_dates,
    _derive_demand_gaps,
    _filter_contains_value,
    _matches_filter_scope,
    _normalize_scope,
    _rank_segments,
    build_demand_insight_snapshot,
)
from app.admin.schemas import DemandInsightSnapshot
from app.common.config import settings


class _SearchLogStub:
    def __init__(self, *, filters=None, created_at=None, result_count=0):
        self.filters = filters or {}
        self.created_at = created_at or datetime.now(timezone.utc)
        self.result_count = result_count


class _ListingStub:
    def __init__(self, *, city=None, status="active", property_type="apartment", listing_purpose="rent"):
        self.city = city
        self.status = status
        self.property_type = property_type
        self.listing_purpose = listing_purpose


class TestBudgetBand:
    def test_under_50k(self):
        assert _budget_band(10_000) == "<50k"
        assert _budget_band(0) == "<50k"

    def test_thresholds(self):
        assert _budget_band(50_000) == "50k-100k"
        assert _budget_band(99_999) == "50k-100k"
        assert _budget_band(100_000) == "100k-250k"
        assert _budget_band(250_000) == "250k-500k"
        assert _budget_band(500_000) == "500k-1M"
        assert _budget_band(1_000_000) == "1M+"

    def test_unknown(self):
        assert _budget_band(None) == "unknown"


class TestBucketDates:
    def test_single_day_returns_one_bucket(self):
        d = date(2026, 1, 15)
        out = _bucket_dates(d, d, buckets=4)
        assert len(out) == 1

    def test_multiple_buckets_cover_range(self):
        out = _bucket_dates(date(2026, 1, 1), date(2026, 1, 10), buckets=5)
        assert len(out) == 5
        # Contiguous
        for i in range(len(out) - 1):
            assert out[i][1] == out[i + 1][0]


class TestNormalizeScope:
    def test_validates_window_size(self):
        with pytest.raises(ValueError):
            _normalize_scope(
                date_from=date(2025, 1, 1),
                date_to=date(2025, 12, 31),
                range_preset="custom",
                city=None,
                property_type=None,
                listing_purpose=None,
            )

    def test_validates_ordering(self):
        with pytest.raises(ValueError):
            _normalize_scope(
                date_from=date(2026, 1, 5),
                date_to=date(2026, 1, 1),
                range_preset="custom",
                city=None,
                property_type=None,
                listing_purpose=None,
            )

    def test_default_preset(self):
        scope = _normalize_scope(
            date_from=date(2026, 1, 1),
            date_to=date(2026, 1, 7),
            range_preset=None,
            city=None,
            property_type=None,
            listing_purpose=None,
        )
        assert scope.range_preset == "custom"

    def test_filters_passed_through(self):
        scope = _normalize_scope(
            date_from=date(2026, 1, 1),
            date_to=date(2026, 1, 7),
            range_preset="last_7_days",
            city="Beirut",
            property_type="apartment",
            listing_purpose="rent",
        )
        assert scope.city == "Beirut"
        assert scope.property_type == "apartment"
        assert scope.listing_purpose == "rent"


class TestMatchesFilterScope:
    def test_empty_filters_match(self):
        assert _matches_filter_scope({}, _scope_stub()) is True
        assert _matches_filter_scope(None, _scope_stub()) is True

    def test_city_filter(self):
        scope = _scope_stub(city="Beirut")
        assert _matches_filter_scope({"city": "Beirut"}, scope) is True
        assert _matches_filter_scope({"city": "beirut"}, scope) is True
        assert _matches_filter_scope({"city": "Tripoli"}, scope) is False

    def test_city_filter_accepts_multi_select_lists(self):
        scope = _scope_stub(city="Beirut")
        assert _matches_filter_scope({"city": ["Beirut", "Tripoli"]}, scope) is True
        assert _matches_filter_scope({"city": ["Tripoli", "Sidon"]}, scope) is False

    def test_property_type_filter(self):
        scope = _scope_stub(property_type="apartment")
        assert _matches_filter_scope({"property_type": "apartment"}, scope) is True
        assert _matches_filter_scope({"property_type": "villa"}, scope) is False


class TestRankSegments:
    def test_empty_counts_returns_empty(self):
        out = _rank_segments({}, 0, limit=5)
        assert out == []

    def test_orders_by_count_desc(self):
        counts = {"a": 5, "b": 10, "c": 1}
        out = _rank_segments(counts, 16, limit=3)
        assert [s.label for s in out] == ["b", "a", "c"]
        assert [s.rank for s in out] == [1, 2, 3]

    def test_share_is_bounded(self):
        out = _rank_segments({"a": 1}, 4, limit=1)
        assert out[0].share == 0.25

    def test_limit_truncates(self):
        out = _rank_segments({f"k{i}": i for i in range(20)}, 200, limit=5)
        assert len(out) == 5


class TestFilterHelpers:
    def test_filter_contains_value_handles_string_and_list(self):
        assert _filter_contains_value("Beirut", "beirut") is True
        assert _filter_contains_value(["Tripoli", "Beirut"], "beirut") is True
        assert _filter_contains_value(["Tripoli", "Sidon"], "beirut") is False

    def test_derive_demand_gaps_handles_multi_city_search_filters(self):
        class SearchLogStub:
            def __init__(self, filters):
                self.filters = filters

        class ListingStub:
            def __init__(self, city, status="active"):
                self.city = city
                self.status = status

        gaps = _derive_demand_gaps(
            search_logs=[SearchLogStub({"city": ["Beirut", "Tripoli"]})],
            listings=[ListingStub("Beirut"), ListingStub("Tripoli")],
            city_lookup={"beirut": "beirut", "tripoli": "tripoli"},
        )

        by_city = {entry.dimension_label: entry for entry in gaps}
        assert by_city["beirut"].demand_count == 1
        assert by_city["tripoli"].demand_count == 1

    def test_derive_demand_gaps_ignores_unknown_city_labels(self):
        class SearchLogStub:
            def __init__(self, filters):
                self.filters = filters

        class ListingStub:
            def __init__(self, city, status="active"):
                self.city = city
                self.status = status

        gaps = _derive_demand_gaps(
            search_logs=[
                SearchLogStub({"city": "Price Sort City"}),
                SearchLogStub({"city": "Beirut"}),
            ],
            listings=[ListingStub("Beirut"), ListingStub("Cursor Stable")],
            city_lookup={"beirut": "beirut"},
        )

        assert [entry.dimension_label for entry in gaps] == ["beirut"]


def _scope_stub(
    *,
    city: str | None = None,
    property_type: str | None = None,
    listing_purpose: str | None = None,
):
    from app.admin.schemas import DashboardFilterScope

    return DashboardFilterScope(
        date_from=date(2026, 1, 1),
        date_to=date(2026, 1, 7),
        range_preset="last_7_days",
        city=city,
        property_type=property_type,
        listing_purpose=listing_purpose,
    )


class TestBuildDemandInsightSnapshot:
    pytestmark = pytest.mark.asyncio

    @pytest.mark.integration
    async def test_empty_dataset_returns_zero_indicators(self, monkeypatch):
        async def _fake_fetch_search_logs(_session, _scope):
            return []

        async def _fake_fetch_listings(_session, _scope):
            return []

        async def _fake_city_lookup(_session):
            return {}

        monkeypatch.setattr(
            "app.admin.query_service._fetch_search_logs_for_scope",
            _fake_fetch_search_logs,
        )
        monkeypatch.setattr(
            "app.admin.query_service._fetch_listing_inventory_for_scope",
            _fake_fetch_listings,
        )
        monkeypatch.setattr(
            "app.admin.query_service._fetch_active_city_lookup",
            _fake_city_lookup,
        )

        snapshot = await build_demand_insight_snapshot(
            object(),
            date_from=date(2026, 1, 1),
            date_to=date(2026, 1, 7),
            range_preset="last_7_days",
        )
        assert isinstance(snapshot, DemandInsightSnapshot)
        assert snapshot.search_volume_total == 0
        assert snapshot.top_areas == []
        assert snapshot.top_budget_bands == []
        assert snapshot.top_property_types == []
        assert snapshot.demand_gaps == []
        assert len(snapshot.search_volume_trend) == settings.platform_dashboard_trend_bucket_count

    @pytest.mark.integration
    async def test_search_logs_produce_segments(self, monkeypatch):
        now = datetime.now(timezone.utc)
        rows = [
            _SearchLogStub(
                filters={"city": "Beirut", "property_type": "apartment", "max_price": 120_000},
                result_count=5,
                created_at=now,
            ),
            _SearchLogStub(
                filters={"city": "beirut", "property_type": "villa", "max_price": 800_000},
                result_count=2,
                created_at=now,
            ),
            _SearchLogStub(
                filters={"city": "Tripoli", "property_type": "apartment", "min_price": 200_000},
                result_count=0,
                created_at=now,
            ),
        ]

        async def _fake_fetch_search_logs(_session, _scope):
            return rows

        async def _fake_fetch_listings(_session, _scope):
            return []

        async def _fake_city_lookup(_session):
            return {"beirut": "beirut", "tripoli": "tripoli"}

        monkeypatch.setattr(
            "app.admin.query_service._fetch_search_logs_for_scope",
            _fake_fetch_search_logs,
        )
        monkeypatch.setattr(
            "app.admin.query_service._fetch_listing_inventory_for_scope",
            _fake_fetch_listings,
        )
        monkeypatch.setattr(
            "app.admin.query_service._fetch_active_city_lookup",
            _fake_city_lookup,
        )

        snapshot = await build_demand_insight_snapshot(
            object(),
            date_from=now.date(),
            date_to=now.date(),
            range_preset="custom",
        )
        assert snapshot.search_volume_total == 3
        assert snapshot.top_areas[0].label in {"beirut", "tripoli"}
        assert any(s.label == "apartment" for s in snapshot.top_property_types)
        assert any(s.label.startswith("100k") or s.label.startswith("50k") for s in snapshot.top_budget_bands)
        assert snapshot.top_property_types[0].share >= 0.66

    @pytest.mark.integration
    async def test_filters_restrict_segments(self, monkeypatch):
        now = datetime.now(timezone.utc)
        rows = [
            _SearchLogStub(
                filters={"city": "Beirut", "property_type": "apartment"},
                result_count=0,
                created_at=now,
            ),
            _SearchLogStub(
                filters={"city": "Tripoli", "property_type": "villa"},
                result_count=0,
                created_at=now,
            ),
        ]

        async def _fake_fetch_search_logs(_session, scope):
            return [row for row in rows if _matches_filter_scope(row.filters, scope)]

        async def _fake_fetch_listings(_session, _scope):
            return []

        async def _fake_city_lookup(_session):
            return {"beirut": "beirut", "tripoli": "tripoli"}

        monkeypatch.setattr(
            "app.admin.query_service._fetch_search_logs_for_scope",
            _fake_fetch_search_logs,
        )
        monkeypatch.setattr(
            "app.admin.query_service._fetch_listing_inventory_for_scope",
            _fake_fetch_listings,
        )
        monkeypatch.setattr(
            "app.admin.query_service._fetch_active_city_lookup",
            _fake_city_lookup,
        )

        snapshot = await build_demand_insight_snapshot(
            object(),
            date_from=now.date(),
            date_to=now.date(),
            range_preset="custom",
            city="Beirut",
            property_type="apartment",
        )
        # Only the Beirut + apartment row should match.
        assert snapshot.search_volume_total == 1
        assert snapshot.top_areas[0].label == "beirut"
        assert snapshot.top_property_types[0].label == "apartment"

    @pytest.mark.integration
    async def test_demand_gaps_compare_demand_and_supply(self, monkeypatch):
        now = datetime.now(timezone.utc)
        # 2 search hits for Beirut, none for Tripoli
        search_logs = [
            _SearchLogStub(filters={"city": "Beirut"}, result_count=0, created_at=now),
            _SearchLogStub(filters={"city": "Beirut"}, result_count=0, created_at=now),
        ]
        # 1 active listing in Beirut, 5 in Tripoli
        listings = [_ListingStub(city="Beirut")] + [_ListingStub(city="Tripoli") for _ in range(5)]

        async def _fake_fetch_search_logs(_session, _scope):
            return search_logs

        async def _fake_fetch_listings(_session, _scope):
            return listings

        async def _fake_city_lookup(_session):
            return {"beirut": "beirut", "tripoli": "tripoli"}

        monkeypatch.setattr(
            "app.admin.query_service._fetch_search_logs_for_scope",
            _fake_fetch_search_logs,
        )
        monkeypatch.setattr(
            "app.admin.query_service._fetch_listing_inventory_for_scope",
            _fake_fetch_listings,
        )
        monkeypatch.setattr(
            "app.admin.query_service._fetch_active_city_lookup",
            _fake_city_lookup,
        )

        snapshot = await build_demand_insight_snapshot(
            object(),
            date_from=now.date(),
            date_to=now.date(),
            range_preset="custom",
        )
        labels = {entry.dimension_label: entry for entry in snapshot.demand_gaps}
        assert "beirut" in labels
        assert "tripoli" in labels
        assert labels["beirut"].gap_direction in {"undersupplied", "balanced", "oversupplied"}
        # Tripoli is over-supplied relative to zero demand
        assert labels["tripoli"].gap_direction == "oversupplied"

    @pytest.mark.integration
    async def test_invalid_city_filters_are_removed_from_top_areas(self, monkeypatch):
        now = datetime.now(timezone.utc)
        rows = [
            _SearchLogStub(filters={"city": "Cursor Stable"}, created_at=now),
            _SearchLogStub(filters={"city": "Price Sort City"}, created_at=now),
            _SearchLogStub(filters={"city": "Beirut"}, created_at=now),
            _SearchLogStub(filters={"city": ["Tripoli", "Null Price Desc Sort City"]}, created_at=now),
        ]

        async def _fake_fetch_search_logs(_session, _scope):
            return rows

        async def _fake_fetch_listings(_session, _scope):
            return []

        async def _fake_city_lookup(_session):
            return {"beirut": "beirut", "tripoli": "tripoli"}

        monkeypatch.setattr(
            "app.admin.query_service._fetch_search_logs_for_scope",
            _fake_fetch_search_logs,
        )
        monkeypatch.setattr(
            "app.admin.query_service._fetch_listing_inventory_for_scope",
            _fake_fetch_listings,
        )
        monkeypatch.setattr(
            "app.admin.query_service._fetch_active_city_lookup",
            _fake_city_lookup,
        )

        snapshot = await build_demand_insight_snapshot(
            object(),
            date_from=now.date(),
            date_to=now.date(),
            range_preset="custom",
        )

        assert [segment.label for segment in snapshot.top_areas] == ["beirut", "tripoli"]
        assert all(segment.share == 0.5 for segment in snapshot.top_areas)
