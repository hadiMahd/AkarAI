import pytest
from datetime import datetime, timezone
from sqlalchemy import select

from app.listings.models import Listing
from app.listings.query_service import (
    ListingQueryService,
    encode_cursor,
    decode_cursor,
)


class TestCursorEncodeDecode:
    def test_roundtrip(self):
        vals = {"price": 100500.0, "id": "550e8400-e29b-41d4-a716-446655440000"}
        raw = encode_cursor(vals)
        assert isinstance(raw, str)
        assert decode_cursor(raw) == vals

    def test_decode_garbage_returns_none(self):
        assert decode_cursor("!!!not-base64!!!") is None

    def test_decode_invalid_json_returns_none(self):
        raw = "aW52YWxpZCBqc29u"
        assert decode_cursor(raw) is None


class TestMakeCursorFromItem:
    def make_item(self, **kwargs):
        defaults = dict(
            id="a1b2c3d4-e5f6-7890-abcd-ef1234567890",
            created_at=datetime(2025, 6, 1, 12, 0, 0, tzinfo=timezone.utc),
            price=None,
            area_size=None,
        )
        defaults.update(kwargs)
        return type("FakeListing", (), defaults)()

    def test_newest_sort_cursor(self):
        item = self.make_item()
        c = ListingQueryService.make_cursor_from_item(item, "newest")
        assert "created_at" in c
        assert c["id"] == item.id

    def test_price_cursor_with_value(self):
        item = self.make_item(price=250000.0)
        c = ListingQueryService.make_cursor_from_item(item, "price_desc")
        assert c["price"] == 250000.0
        assert c["id"] == item.id

    def test_price_cursor_null(self):
        item = self.make_item(price=None)
        c = ListingQueryService.make_cursor_from_item(item, "price_desc")
        assert c["price"] is None


class TestApplyPublicSearchCursor:
    def _first_where_str(self, q) -> str:
        s = str(q)
        idx = s.lower().find("where")
        return s[idx:] if idx != -1 else ""

    def test_newest_cursor_adds_where(self):
        q = select(Listing).order_by(Listing.created_at.desc(), Listing.id.desc())
        q2 = ListingQueryService.apply_public_search_cursor(
            q, "newest",
            {"created_at": "2025-01-01T00:00:00+00:00", "id": "abc"},
        )
        s = self._first_where_str(q2)
        assert "created_at" in s
        assert "id" in s

    def test_oldest_cursor_adds_where(self):
        q = select(Listing).order_by(Listing.created_at.asc(), Listing.id.asc())
        q2 = ListingQueryService.apply_public_search_cursor(
            q, "oldest",
            {"created_at": "2025-01-01T00:00:00+00:00", "id": "abc"},
        )
        s = self._first_where_str(q2)
        assert "created_at" in s
        assert ">" in s

    def test_price_desc_cursor_non_null(self):
        q = select(Listing).order_by(Listing.price.desc().nulls_last(), Listing.id.desc())
        q2 = ListingQueryService.apply_public_search_cursor(
            q, "price_desc",
            {"price": 150000.0, "id": "abc"},
        )
        s = self._first_where_str(q2)
        assert "price" in s
        assert "id" in s

    def test_price_desc_cursor_null(self):
        q = select(Listing).order_by(Listing.price.desc().nulls_last(), Listing.id.desc())
        q2 = ListingQueryService.apply_public_search_cursor(
            q, "price_desc",
            {"price": None, "id": "abc"},
        )
        s = self._first_where_str(q2)
        assert "price" in s
        assert "id" in s

    def test_price_asc_cursor_non_null(self):
        q = select(Listing).order_by(Listing.price.asc().nulls_last(), Listing.id.desc())
        q2 = ListingQueryService.apply_public_search_cursor(
            q, "price_asc",
            {"price": 150000.0, "id": "abc"},
        )
        s = self._first_where_str(q2)
        assert "price" in s

    def test_area_size_desc_cursor(self):
        q = select(Listing).order_by(Listing.area_size.desc().nulls_last(), Listing.id.desc())
        q2 = ListingQueryService.apply_public_search_cursor(
            q, "area_size_desc",
            {"area_size": 100.0, "id": "abc"},
        )
        s = self._first_where_str(q2)
        assert "area_size" in s
        assert "id" in s

    def test_area_size_asc_cursor(self):
        q = select(Listing).order_by(Listing.area_size.asc().nulls_last(), Listing.id.desc())
        q2 = ListingQueryService.apply_public_search_cursor(
            q, "area_size_asc",
            {"area_size": 100.0, "id": "abc"},
        )
        s = self._first_where_str(q2)
        assert "area_size" in s

    def test_default_sort_uses_newest_cursor(self):
        q = select(Listing).order_by(Listing.created_at.desc(), Listing.id.desc())
        q2 = ListingQueryService.apply_public_search_cursor(
            q, None,
            {"created_at": "2025-01-01T00:00:00+00:00", "id": "abc"},
        )
        s = self._first_where_str(q2)
        assert "created_at" in s
