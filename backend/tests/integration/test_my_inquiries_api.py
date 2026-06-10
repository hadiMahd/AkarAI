import pytest
from httpx import AsyncClient
from sqlalchemy.ext.asyncio import AsyncSession
from datetime import datetime, timedelta, timezone
import uuid

pytestmark = pytest.mark.asyncio


async def test_list_my_inquiries(
    async_client: AsyncClient,
    db_session: AsyncSession,
    test_user,
    test_tenant,
    test_listing,
):
    from app.leads.models import Lead

    user, password = test_user
    inquiry_id = uuid.uuid4()
    inquiry = Lead(
        id=inquiry_id,
        listing_id=test_listing.id,
        user_id=user.id,
        agency_tenant_id=test_tenant.id,
        message="I'm interested in this property",
        status="new",
        created_at=datetime.now(timezone.utc),
        updated_at=datetime.now(timezone.utc),
    )
    db_session.add(inquiry)
    await db_session.commit()

    login_resp = await async_client.post(
        "/auth/login",
        json={"email": user.email, "password": password},
    )
    access_token = login_resp.json()["access_token"]
    headers = {"Authorization": f"Bearer {access_token}"}

    response = await async_client.get("/me/inquiries", headers=headers)

    assert response.status_code == 200
    data = response.json()
    assert "items" in data
    assert "page" in data
    assert "total" in data

    inquiry_data = next((i for i in data["items"] if i["id"] == str(inquiry_id)), None)
    assert inquiry_data is not None
    assert inquiry_data["listing_id"] == str(test_listing.id)
    assert inquiry_data["status"] == "new"

    from sqlalchemy import text
    await db_session.execute(text(f"DELETE FROM leads WHERE id = '{inquiry_id}'"))
    await db_session.commit()


async def test_list_my_inquiries_unauthenticated(
    async_client: AsyncClient,
):
    response = await async_client.get("/me/inquiries")

    assert response.status_code == 401


async def test_my_inquiries_only_shows_own_data(
    async_client: AsyncClient,
    db_session: AsyncSession,
    test_user,
    test_tenant,
    test_listing,
):
    from app.leads.models import Lead
    from app.users.models import User
    from app.common.security import hash_password

    user1, password1 = test_user

    user2_id = uuid.uuid4()
    user2 = User(
        id=user2_id,
        email=f"test2-{uuid.uuid4().hex[:8]}@example.com",
        password_hash=hash_password("TestPass123!"),
        name="Test User 2",
        is_active=True,
        status="active",
        created_at=datetime.now(timezone.utc),
        updated_at=datetime.now(timezone.utc),
    )
    db_session.add(user2)
    await db_session.commit()

    inquiry1_id = uuid.uuid4()
    inquiry1 = Lead(
        id=inquiry1_id,
        listing_id=test_listing.id,
        user_id=user1.id,
        agency_tenant_id=test_tenant.id,
        message="User 1 inquiry",
        status="new",
        created_at=datetime.now(timezone.utc),
        updated_at=datetime.now(timezone.utc),
    )

    inquiry2_id = uuid.uuid4()
    inquiry2 = Lead(
        id=inquiry2_id,
        listing_id=test_listing.id,
        user_id=user2.id,
        agency_tenant_id=test_tenant.id,
        message="User 2 inquiry",
        status="new",
        created_at=datetime.now(timezone.utc),
        updated_at=datetime.now(timezone.utc),
    )

    db_session.add_all([inquiry1, inquiry2])
    await db_session.commit()

    login_resp = await async_client.post(
        "/auth/login",
        json={"email": user1.email, "password": password1},
    )
    access_token = login_resp.json()["access_token"]
    headers = {"Authorization": f"Bearer {access_token}"}

    response = await async_client.get("/me/inquiries", headers=headers)

    assert response.status_code == 200
    data = response.json()

    inquiry_ids = [i["id"] for i in data["items"]]
    assert str(inquiry1_id) in inquiry_ids
    assert str(inquiry2_id) not in inquiry_ids

    from sqlalchemy import text
    await db_session.execute(text(f"DELETE FROM leads WHERE id IN ('{inquiry1_id}', '{inquiry2_id}')"))
    await db_session.execute(text(f"DELETE FROM users WHERE id = '{user2_id}'"))
    await db_session.commit()


async def test_my_inquiries_pagination(
    async_client: AsyncClient,
    db_session: AsyncSession,
    test_user,
    test_tenant,
    test_listing,
):
    from app.leads.models import Lead

    user, password = test_user
    inquiry_ids = []

    for i in range(3):
        inquiry_id = uuid.uuid4()
        inquiry_ids.append(inquiry_id)
        inquiry = Lead(
            id=inquiry_id,
            listing_id=test_listing.id,
            user_id=user.id,
            agency_tenant_id=test_tenant.id,
            message=f"Inquiry {i}",
            status="new",
            created_at=datetime.now(timezone.utc),
            updated_at=datetime.now(timezone.utc),
        )
        db_session.add(inquiry)

    await db_session.commit()

    login_resp = await async_client.post(
        "/auth/login",
        json={"email": user.email, "password": password},
    )
    access_token = login_resp.json()["access_token"]
    headers = {"Authorization": f"Bearer {access_token}"}

    response = await async_client.get("/me/inquiries?page=1&page_size=2", headers=headers)

    assert response.status_code == 200
    data = response.json()
    assert len(data["items"]) == 2
    assert data["total"] >= 3
    assert data["has_next"] is True

    from sqlalchemy import text
    ids_str = "', '".join(str(i) for i in inquiry_ids)
    await db_session.execute(text(f"DELETE FROM leads WHERE id IN ('{ids_str}')"))
    await db_session.commit()
