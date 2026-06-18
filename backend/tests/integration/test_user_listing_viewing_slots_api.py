import pytest
from httpx import AsyncClient
from sqlalchemy.ext.asyncio import AsyncSession
from datetime import datetime, timedelta, timezone
import uuid

pytestmark = pytest.mark.anyio


async def test_list_viewing_slots_for_listing(
    async_client: AsyncClient,
    db_session: AsyncSession,
    test_user,
    test_tenant,
    test_listing,
):
    from app.viewings.models import ListingViewingSlot

    user, _password = test_user
    slot_id = uuid.uuid4()
    slot = ListingViewingSlot(
        id=slot_id,
        listing_id=test_listing.id,
        agency_tenant_id=test_tenant.id,
        starts_at=datetime.now(timezone.utc) + timedelta(days=1),
        ends_at=datetime.now(timezone.utc) + timedelta(days=1, hours=1),
        capacity=5,
        reserved_count=0,
        status="active",
        created_by_user_id=user.id,
        created_at=datetime.now(timezone.utc),
        updated_at=datetime.now(timezone.utc),
    )
    db_session.add(slot)
    await db_session.commit()

    response = await async_client.get(
        f"/listings/{test_listing.id}/viewing-slots",
    )

    assert response.status_code == 200
    data = response.json()
    assert isinstance(data, list)
    assert len(data) >= 1

    slot_data = next((s for s in data if s["id"] == str(slot_id)), None)
    assert slot_data is not None
    assert slot_data["capacity"] == 5
    assert slot_data["reserved_count"] == 0
    assert slot_data["status"] == "active"

    from sqlalchemy import text
    await db_session.execute(text(f"DELETE FROM listing_viewing_slots WHERE id = '{slot_id}'"))
    await db_session.commit()


async def test_list_viewing_slots_excludes_inactive(
    async_client: AsyncClient,
    db_session: AsyncSession,
    test_user,
    test_tenant,
    test_listing,
):
    from app.viewings.models import ListingViewingSlot

    user, _password = test_user
    inactive_slot_id = uuid.uuid4()
    inactive_slot = ListingViewingSlot(
        id=inactive_slot_id,
        listing_id=test_listing.id,
        agency_tenant_id=test_tenant.id,
        starts_at=datetime.now(timezone.utc) + timedelta(days=2),
        ends_at=datetime.now(timezone.utc) + timedelta(days=2, hours=1),
        capacity=3,
        reserved_count=0,
        status="inactive",
        created_by_user_id=user.id,
        created_at=datetime.now(timezone.utc),
        updated_at=datetime.now(timezone.utc),
    )
    db_session.add(inactive_slot)
    await db_session.commit()

    response = await async_client.get(
        f"/listings/{test_listing.id}/viewing-slots",
    )

    assert response.status_code == 200
    data = response.json()
    slot_ids = [s["id"] for s in data]
    assert str(inactive_slot_id) not in slot_ids

    from sqlalchemy import text
    await db_session.execute(text(f"DELETE FROM listing_viewing_slots WHERE id = '{inactive_slot_id}'"))
    await db_session.commit()


async def test_list_viewing_slots_unauthenticated(
    async_client: AsyncClient,
    test_listing,
):
    response = await async_client.get(f"/listings/{test_listing.id}/viewing-slots")

    assert response.status_code == 200


async def test_list_viewing_slots_nonexistent_listing(
    async_client: AsyncClient,
):
    fake_listing_id = uuid.uuid4()
    response = await async_client.get(
        f"/listings/{fake_listing_id}/viewing-slots",
    )

    assert response.status_code == 200
    data = response.json()
    assert data == []


async def test_viewing_slot_response_fields(
    async_client: AsyncClient,
    db_session: AsyncSession,
    test_user,
    test_tenant,
    test_listing,
):
    from app.viewings.models import ListingViewingSlot

    user, _password = test_user
    slot_id = uuid.uuid4()
    slot = ListingViewingSlot(
        id=slot_id,
        listing_id=test_listing.id,
        agency_tenant_id=test_tenant.id,
        starts_at=datetime.now(timezone.utc) + timedelta(days=3),
        ends_at=datetime.now(timezone.utc) + timedelta(days=3, hours=2),
        capacity=10,
        reserved_count=3,
        status="active",
        created_by_user_id=user.id,
        created_at=datetime.now(timezone.utc),
        updated_at=datetime.now(timezone.utc),
    )
    db_session.add(slot)
    await db_session.commit()

    response = await async_client.get(
        f"/listings/{test_listing.id}/viewing-slots",
    )

    assert response.status_code == 200
    data = response.json()
    slot_data = next((s for s in data if s["id"] == str(slot_id)), None)
    assert slot_data is not None

    assert "id" in slot_data
    assert "starts_at" in slot_data
    assert "ends_at" in slot_data
    assert "capacity" in slot_data
    assert "reserved_count" in slot_data
    assert "status" in slot_data

    assert "agency_tenant_id" not in slot_data
    assert "created_by_user_id" not in slot_data

    from sqlalchemy import text
    await db_session.execute(text(f"DELETE FROM listing_viewing_slots WHERE id = '{slot_id}'"))
    await db_session.commit()


async def test_list_viewing_slots_excludes_past_and_full_slots(
    async_client: AsyncClient,
    db_session: AsyncSession,
    test_user,
    test_tenant,
    test_listing,
):
    from app.viewings.models import ListingViewingSlot

    user, _password = test_user
    now = datetime.now(timezone.utc)
    visible_slot_id = uuid.uuid4()
    past_slot_id = uuid.uuid4()
    full_slot_id = uuid.uuid4()

    db_session.add_all(
        [
            ListingViewingSlot(
                id=visible_slot_id,
                listing_id=test_listing.id,
                agency_tenant_id=test_tenant.id,
                starts_at=now + timedelta(days=1),
                ends_at=now + timedelta(days=1, hours=1),
                capacity=2,
                reserved_count=0,
                status="active",
                created_by_user_id=user.id,
                created_at=now,
                updated_at=now,
            ),
            ListingViewingSlot(
                id=past_slot_id,
                listing_id=test_listing.id,
                agency_tenant_id=test_tenant.id,
                starts_at=now - timedelta(hours=2),
                ends_at=now - timedelta(hours=1),
                capacity=2,
                reserved_count=0,
                status="active",
                created_by_user_id=user.id,
                created_at=now,
                updated_at=now,
            ),
            ListingViewingSlot(
                id=full_slot_id,
                listing_id=test_listing.id,
                agency_tenant_id=test_tenant.id,
                starts_at=now + timedelta(days=2),
                ends_at=now + timedelta(days=2, hours=1),
                capacity=1,
                reserved_count=1,
                status="active",
                created_by_user_id=user.id,
                created_at=now,
                updated_at=now,
            ),
        ]
    )
    await db_session.commit()

    response = await async_client.get(f"/listings/{test_listing.id}/viewing-slots")

    assert response.status_code == 200
    data = response.json()
    slot_ids = {item["id"] for item in data}
    assert str(visible_slot_id) in slot_ids
    assert str(past_slot_id) not in slot_ids
    assert str(full_slot_id) not in slot_ids

    from sqlalchemy import text
    await db_session.execute(
        text(
            "DELETE FROM listing_viewing_slots "
            f"WHERE id IN ('{visible_slot_id}', '{past_slot_id}', '{full_slot_id}')"
        )
    )
    await db_session.commit()
