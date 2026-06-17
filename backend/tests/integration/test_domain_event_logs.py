import uuid
from datetime import datetime, timezone

import pytest
from httpx import AsyncClient

from app.common.events import DomainEventLog, write_domain_event_log


@pytest.mark.anyio
class TestDomainEventLogs:
    async def _login(self, client: AsyncClient, email: str, password: str = "Test1234!") -> str:
        resp = await client.post("/auth/login", json={"email": email, "password": password})
        assert resp.status_code == 200
        return resp.json()["access_token"]

    async def _complete_profile(self, client: AsyncClient, token: str, *, name: str) -> None:
        resp = await client.put(
            "/me/profile",
            json={"name": name, "phone": "+1234567890"},
            headers={"Authorization": f"Bearer {token}"},
        )
        assert resp.status_code == 200

    async def test_domain_event_log_created_on_lead_creation(self, async_client: AsyncClient, db_session):
        admin_token = await self._login(async_client, "agency.admin@akarai.test")

        listing_resp = await async_client.post("/agency/listings", json={
            "title": "Event Log Test",
            "description": "For event log tests",
            "property_type": "apartment",
            "listing_purpose": "sale",
            "price": 100000,
            "currency": "USD",
            "bedrooms": 1,
            "bathrooms": 1,
            "area_size": 50.0,
            "area_unit": "sqm",
            "furnishing": "unfurnished",
            "location_text": "Event City",
            "address": "1 Event St",
            "city": "Event City",
            "country": "Test Country",
            "status": "active",
        }, headers={"Authorization": f"Bearer {admin_token}"})
        listing_id = listing_resp.json()["id"]

        user_token = await self._login(async_client, "user@akarai.test")
        await self._complete_profile(async_client, user_token, name="Event Test")
        await async_client.post(
            f"/listings/{listing_id}/inquiries",
            json={"name": "Event Test", "email": "event@test.com", "message": "Interested"},
            headers={"Authorization": f"Bearer {user_token}"},
        )

        from sqlalchemy import select
        result = await db_session.execute(
            select(DomainEventLog).where(DomainEventLog.event_name == "lead.created")
        )
        logs = result.scalars().all()
        assert len(logs) >= 1

    async def test_domain_event_log_created_on_viewing_booking(self, async_client: AsyncClient, db_session):
        admin_token = await self._login(async_client, "agency.admin@akarai.test")

        listing_resp = await async_client.post("/agency/listings", json={
            "title": "Viewing Event Test",
            "description": "For viewing event log tests",
            "property_type": "apartment",
            "listing_purpose": "sale",
            "price": 150000,
            "currency": "USD",
            "bedrooms": 2,
            "bathrooms": 1,
            "area_size": 60.0,
            "area_unit": "sqm",
            "furnishing": "furnished",
            "location_text": "Viewing Event City",
            "address": "2 Event St",
            "city": "Viewing Event City",
            "country": "Test Country",
            "status": "active",
        }, headers={"Authorization": f"Bearer {admin_token}"})
        listing_id = listing_resp.json()["id"]

        from datetime import timedelta
        starts = datetime.now(timezone.utc) + timedelta(days=3)
        ends = starts + timedelta(hours=1)
        slot_resp = await async_client.post(
            f"/agency/listings/{listing_id}/viewing-slots",
            json={
                "starts_at": starts.isoformat(),
                "ends_at": ends.isoformat(),
                "capacity": 5,
            },
            headers={"Authorization": f"Bearer {admin_token}"},
        )
        slot_id = slot_resp.json()["id"]

        user_token = await self._login(async_client, "user@akarai.test")
        await async_client.post(
            f"/listings/{listing_id}/viewings",
            json={"viewing_slot_id": slot_id},
            headers={"Authorization": f"Bearer {user_token}"},
        )

        from sqlalchemy import select
        result = await db_session.execute(
            select(DomainEventLog).where(DomainEventLog.event_name == "viewing.scheduled")
        )
        logs = result.scalars().all()
        assert len(logs) >= 1

    async def test_domain_event_log_created_on_notification_read(self, async_client: AsyncClient, db_session):
        from sqlalchemy import text
        from app.notifications.models import Notification

        result = await db_session.execute(text("SELECT id FROM users WHERE email = 'user@akarai.test'"))
        user_id = result.fetchone()[0]

        n = Notification(
            recipient_user_id=user_id,
            channel="platform",
            template_key="event_log_read",
            status="pending",
        )
        db_session.add(n)
        await db_session.commit()

        token = await self._login(async_client, "user@akarai.test")
        await async_client.post(
            f"/notifications/{n.id}/read",
            headers={"Authorization": f"Bearer {token}"},
        )

        from sqlalchemy import select
        result = await db_session.execute(
            select(DomainEventLog).where(DomainEventLog.event_name == "notification.read")
        )
        logs = result.scalars().all()
        assert len(logs) >= 1

    async def test_domain_event_log_created_on_notification_dismiss(self, async_client: AsyncClient, db_session):
        from sqlalchemy import text
        from app.notifications.models import Notification

        result = await db_session.execute(text("SELECT id FROM users WHERE email = 'user@akarai.test'"))
        user_id = result.fetchone()[0]

        n = Notification(
            recipient_user_id=user_id,
            channel="platform",
            template_key="event_log_dismiss",
            status="pending",
        )
        db_session.add(n)
        await db_session.commit()

        token = await self._login(async_client, "user@akarai.test")
        await async_client.post(
            f"/notifications/{n.id}/dismiss",
            headers={"Authorization": f"Bearer {token}"},
        )

        from sqlalchemy import select
        result = await db_session.execute(
            select(DomainEventLog).where(DomainEventLog.event_name == "notification.dismissed")
        )
        logs = result.scalars().all()
        assert len(logs) >= 1

    async def test_domain_event_log_has_correct_fields(self, async_client: AsyncClient, db_session):
        admin_token = await self._login(async_client, "agency.admin@akarai.test")

        listing_resp = await async_client.post("/agency/listings", json={
            "title": "Field Test",
            "description": "For field tests",
            "property_type": "apartment",
            "listing_purpose": "rent",
            "price": 1000,
            "currency": "USD",
            "bedrooms": 1,
            "bathrooms": 1,
            "area_size": 40.0,
            "area_unit": "sqm",
            "furnishing": "unfurnished",
            "location_text": "Field City",
            "address": "3 Field St",
            "city": "Field City",
            "country": "Test Country",
            "status": "active",
        }, headers={"Authorization": f"Bearer {admin_token}"})
        listing_id = listing_resp.json()["id"]

        user_token = await self._login(async_client, "user@akarai.test")
        await self._complete_profile(async_client, user_token, name="Field Test")
        inquiry_resp = await async_client.post(
            f"/listings/{listing_id}/inquiries",
            json={"name": "Field Test", "email": "field@test.com"},
            headers={"Authorization": f"Bearer {user_token}"},
        )
        lead_id = inquiry_resp.json()["id"]

        from sqlalchemy import select
        result = await db_session.execute(
            select(DomainEventLog).where(
                DomainEventLog.event_name == "lead.created",
                DomainEventLog.aggregate_id == lead_id,
            )
        )
        logs = result.scalars().all()
        assert len(logs) >= 1
        log = logs[0]
        assert log.aggregate_type == "lead"
        assert log.actor_user_id is not None
        assert log.created_at is not None

    async def test_list_domain_logs_via_api(self, async_client: AsyncClient):
        admin_token = await self._login(async_client, "agency.admin@akarai.test")
        resp = await async_client.get(
            "/agency/domain-logs",
            headers={"Authorization": f"Bearer {admin_token}"},
        )
        assert resp.status_code == 200
        data = resp.json()
        assert "items" in data
        assert "total" in data
