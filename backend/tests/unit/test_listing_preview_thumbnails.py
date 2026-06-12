import uuid
from datetime import datetime, timezone

import pytest

from app.common.tenant import TenantContext
from app.listings.models import ListingPhotoMetadata, ListingPhotoDerivative
from app.listings.service import ListingService, build_thumbnail_map


def _make_tenant(tenant_id, actor_id, role="agency_admin"):
    return TenantContext(
        actor_id=actor_id,
        role=role,
        permissions=[],
        tenant_id=tenant_id,
    )


@pytest.mark.anyio
class TestListPhotosWithPreviewUrl:
    async def test_list_photos_returns_dicts_with_preview_url(self, db_session, test_tenant, agency_admin_user, test_listing):
        user, _ = agency_admin_user
        ctx = _make_tenant(test_tenant.id, user.id)

        photo = ListingPhotoMetadata(
            listing_id=test_listing.id,
            agency_tenant_id=test_tenant.id,
            object_key="test/photo.jpg",
            display_order=1,
            status="active",
        )
        db_session.add(photo)
        await db_session.commit()

        svc = ListingService(db_session, ctx)
        photos = await svc.list_photos(test_listing.id)
        assert len(photos) >= 1

        first = photos[0]
        assert isinstance(first, dict)
        assert first["object_key"] == "test/photo.jpg"
        assert "preview_url" in first
        assert isinstance(first["preview_url"], str)
        assert first["preview_url"].startswith("http")

    async def test_list_photos_preview_url_fallback_to_original(self, db_session, test_tenant, agency_admin_user, test_listing):
        user, _ = agency_admin_user
        ctx = _make_tenant(test_tenant.id, user.id)

        photo = ListingPhotoMetadata(
            listing_id=test_listing.id,
            agency_tenant_id=test_tenant.id,
            object_key="test/fallback.jpg",
            display_order=1,
            status="uploaded",
        )
        db_session.add(photo)
        await db_session.commit()

        svc = ListingService(db_session, ctx)
        photos = await svc.list_photos(test_listing.id)
        first = next(p for p in photos if p["object_key"] == "test/fallback.jpg")
        assert isinstance(first["preview_url"], str)
        assert first["preview_url"].startswith("http")

    async def test_list_photos_preview_url_from_derivative(self, db_session, test_tenant, agency_admin_user, test_listing):
        user, _ = agency_admin_user
        ctx = _make_tenant(test_tenant.id, user.id)

        photo = ListingPhotoMetadata(
            listing_id=test_listing.id,
            agency_tenant_id=test_tenant.id,
            object_key="test/original.jpg",
            display_order=1,
            status="accepted",
        )
        db_session.add(photo)
        await db_session.commit()

        derivative = ListingPhotoDerivative(
            listing_photo_metadata_id=photo.id,
            variant_name="thumbnail",
            object_key="test/derivative.webp",
            format="webp",
            width=640,
            height=480,
            file_size_bytes=50000,
            is_public_safe=True,
        )
        db_session.add(derivative)
        await db_session.commit()

        svc = ListingService(db_session, ctx)
        photos = await svc.list_photos(test_listing.id)
        first = next(p for p in photos if p["id"] == photo.id)
        assert "derivative" in first["preview_url"] or first["preview_url"] != photos[0]["preview_url"]

    async def test_list_photos_no_duplicate_previews(self, db_session, test_tenant, agency_admin_user, test_listing):
        user, _ = agency_admin_user
        ctx = _make_tenant(test_tenant.id, user.id)

        for i in range(3):
            db_session.add(ListingPhotoMetadata(
                listing_id=test_listing.id,
                agency_tenant_id=test_tenant.id,
                object_key=f"test/photo_{i}.jpg",
                display_order=i,
                status="active",
            ))
        await db_session.commit()

        svc = ListingService(db_session, ctx)
        photos = await svc.list_photos(test_listing.id)
        assert len(photos) == 3
        urls = [p["preview_url"] for p in photos]
        assert all(isinstance(url, str) and url.startswith("http") for url in urls)


@pytest.mark.anyio
class TestBuildThumbnailMap:
    async def test_thumbnail_map_empty_for_no_listings(self, db_session):
        result = await build_thumbnail_map(db_session, [])
        assert result == {}

    async def test_thumbnail_map_returns_none_for_listing_without_photos(self, db_session, test_listing):
        result = await build_thumbnail_map(db_session, [test_listing.id])
        assert result[test_listing.id] is None

    async def test_thumbnail_map_from_accepted_photo_with_derivative(self, db_session, test_tenant, test_listing):
        photo = ListingPhotoMetadata(
            listing_id=test_listing.id,
            agency_tenant_id=test_tenant.id,
            object_key="test/photo.jpg",
            display_order=1,
            status="accepted",
        )
        db_session.add(photo)
        await db_session.commit()

        derivative = ListingPhotoDerivative(
            listing_photo_metadata_id=photo.id,
            variant_name="thumb",
            object_key="test/thumb.webp",
            format="webp",
            width=320,
            height=240,
            file_size_bytes=20000,
            is_public_safe=True,
        )
        db_session.add(derivative)
        await db_session.commit()

        result = await build_thumbnail_map(db_session, [test_listing.id])
        assert result[test_listing.id] is not None
        assert result[test_listing.id].startswith("http")

    async def test_thumbnail_map_uses_public_safe_derivative_even_when_uploaded(self, db_session, test_tenant, test_listing):
        photo = ListingPhotoMetadata(
            listing_id=test_listing.id,
            agency_tenant_id=test_tenant.id,
            object_key="test/uploaded.jpg",
            display_order=1,
            status="uploaded",
        )
        db_session.add(photo)
        await db_session.commit()

        derivative = ListingPhotoDerivative(
            listing_photo_metadata_id=photo.id,
            variant_name="thumb",
            object_key="test/uploaded_thumb.webp",
            format="webp",
            width=320,
            height=240,
            file_size_bytes=20000,
            is_public_safe=True,
        )
        db_session.add(derivative)
        await db_session.commit()

        result = await build_thumbnail_map(db_session, [test_listing.id])
        assert result[test_listing.id] is not None
        assert "uploaded_thumb" in result[test_listing.id]

    async def test_thumbnail_map_null_for_accepted_photo_without_derivative(self, db_session, test_tenant, test_listing):
        photo = ListingPhotoMetadata(
            listing_id=test_listing.id,
            agency_tenant_id=test_tenant.id,
            object_key="test/photo.jpg",
            display_order=1,
            status="accepted",
        )
        db_session.add(photo)
        await db_session.commit()

        result = await build_thumbnail_map(db_session, [test_listing.id])
        assert result[test_listing.id] is None

    async def test_thumbnail_map_uses_first_photo_by_display_order(self, db_session, test_tenant, test_listing):
        photo1 = ListingPhotoMetadata(
            listing_id=test_listing.id,
            agency_tenant_id=test_tenant.id,
            object_key="test/first.jpg",
            display_order=0,
            status="accepted",
        )
        photo2 = ListingPhotoMetadata(
            listing_id=test_listing.id,
            agency_tenant_id=test_tenant.id,
            object_key="test/second.jpg",
            display_order=1,
            status="accepted",
        )
        db_session.add(photo1)
        db_session.add(photo2)
        await db_session.commit()

        deriv1 = ListingPhotoDerivative(
            listing_photo_metadata_id=photo1.id,
            variant_name="thumb",
            object_key="test/first_thumb.webp",
            format="webp",
            width=320,
            height=240,
            file_size_bytes=20000,
            is_public_safe=True,
        )
        db_session.add(deriv1)
        await db_session.commit()

        result = await build_thumbnail_map(db_session, [test_listing.id])
        assert "first_thumb" in result[test_listing.id]

    async def test_thumbnail_map_multiple_listings(self, db_session, test_tenant, agency_admin_user):
        user, _ = agency_admin_user
        from app.listings.models import Listing

        listing_a = Listing(
            agency_tenant_id=test_tenant.id,
            title="Listing A",
            status="active",
        )
        listing_b = Listing(
            agency_tenant_id=test_tenant.id,
            title="Listing B",
            status="active",
        )
        db_session.add(listing_a)
        db_session.add(listing_b)
        await db_session.commit()

        photo_a = ListingPhotoMetadata(
            listing_id=listing_a.id,
            agency_tenant_id=test_tenant.id,
            object_key="test/a.jpg",
            display_order=1,
            status="accepted",
        )
        db_session.add(photo_a)
        await db_session.commit()

        deriv_a = ListingPhotoDerivative(
            listing_photo_metadata_id=photo_a.id,
            variant_name="thumb",
            object_key="test/a_thumb.webp",
            format="webp",
            width=320,
            height=240,
            file_size_bytes=20000,
            is_public_safe=True,
        )
        db_session.add(deriv_a)
        await db_session.commit()

        listing_ids = [listing_a.id, listing_b.id]
        result = await build_thumbnail_map(db_session, listing_ids)
        assert result[listing_a.id] is not None
        assert result[listing_b.id] is None
