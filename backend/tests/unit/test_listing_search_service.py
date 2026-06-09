import pytest
from sqlalchemy import select

from app.listings.models import Listing
from app.listings.query_service import ListingQueryService


@pytest.mark.anyio
class TestListingQueryService:
    async def test_build_public_search_query_no_filters(self, db_session):
        q = ListingQueryService.build_public_search_query()
        query_str = str(q).lower()
        assert "where" in query_str
        assert "status" in query_str
        assert "created_at" in query_str

    async def test_build_public_search_query_location_filter(self, db_session):
        q = ListingQueryService.build_public_search_query(location="Downtown")
        query_str = str(q).lower()
        assert "location_text" in query_str or "city" in query_str or "address" in query_str

    async def test_build_public_search_query_price_filters(self, db_session):
        q = ListingQueryService.build_public_search_query(min_price=100000, max_price=500000)
        query_str = str(q).lower()
        assert "price" in query_str

    async def test_build_public_search_query_bedrooms_filter(self, db_session):
        q = ListingQueryService.build_public_search_query(bedrooms=3)
        query_str = str(q).lower()
        assert "bedrooms" in query_str

    async def test_build_public_search_query_bathrooms_filter(self, db_session):
        q = ListingQueryService.build_public_search_query(bathrooms=2)
        query_str = str(q).lower()
        assert "bathrooms" in query_str

    async def test_build_public_search_query_property_type_filter(self, db_session):
        q = ListingQueryService.build_public_search_query(property_type="apartment")
        query_str = str(q).lower()
        assert "property_type" in query_str

    async def test_build_public_search_query_listing_purpose_filter(self, db_session):
        q = ListingQueryService.build_public_search_query(listing_purpose="sale")
        query_str = str(q).lower()
        assert "listing_purpose" in query_str

    async def test_build_public_search_query_furnishing_filter(self, db_session):
        q = ListingQueryService.build_public_search_query(furnishing="furnished")
        query_str = str(q).lower()
        assert "furnishing" in query_str

    async def test_build_public_search_query_area_size_filters(self, db_session):
        q = ListingQueryService.build_public_search_query(min_area_size=80, max_area_size=150)
        query_str = str(q).lower()
        assert "area_size" in query_str

    async def test_build_public_search_query_sort_newest(self, db_session):
        q = ListingQueryService.build_public_search_query(sort="newest")
        query_str = str(q).lower()
        assert "created_at" in query_str
        assert "desc" in query_str

    async def test_build_public_search_query_sort_price_asc(self, db_session):
        q = ListingQueryService.build_public_search_query(sort="price_asc")
        query_str = str(q).lower()
        assert "price" in query_str
        assert "asc" in query_str

    async def test_build_public_search_query_sort_price_desc(self, db_session):
        q = ListingQueryService.build_public_search_query(sort="price_desc")
        query_str = str(q).lower()
        assert "price" in query_str
        assert "desc" in query_str

    async def test_build_public_search_query_sort_area_size_asc(self, db_session):
        q = ListingQueryService.build_public_search_query(sort="area_size_asc")
        query_str = str(q).lower()
        assert "area_size" in query_str
        assert "asc" in query_str

    async def test_build_public_search_query_sort_area_size_desc(self, db_session):
        q = ListingQueryService.build_public_search_query(sort="area_size_desc")
        query_str = str(q).lower()
        assert "area_size" in query_str
        assert "desc" in query_str

    async def test_build_public_search_query_default_sort(self, db_session):
        q = ListingQueryService.build_public_search_query(sort="invalid_sort")
        query_str = str(q).lower()
        assert "created_at" in query_str
        assert "desc" in query_str

    async def test_build_public_search_query_multiple_filters(self, db_session):
        q = ListingQueryService.build_public_search_query(
            location="Downtown",
            min_price=100000,
            max_price=500000,
            bedrooms=3,
            property_type="apartment",
            sort="price_asc",
        )
        query_str = str(q).lower()
        assert "location_text" in query_str or "city" in query_str or "address" in query_str
        assert "price" in query_str
        assert "bedrooms" in query_str
        assert "property_type" in query_str
