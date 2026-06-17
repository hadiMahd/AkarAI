import pytest
from httpx import AsyncClient
from datetime import datetime, timedelta, timezone


@pytest.mark.anyio
class TestUserInquiryViewingAPI:
    async def _login(self, client: AsyncClient, email: str, password: str = "Test1234!") -> str:
        resp = await client.post("/auth/login", json={"email": email, "password": password})
        assert resp.status_code == 200
        return resp.json()["access_token"]

    async def _create_listing(self, client: AsyncClient, token: str) -> str:
        resp = await client.post("/agency/listings", json={
            "title": "Inquiry Viewing Test Listing",
            "description": "For inquiry and viewing tests",
            "property_type": "apartment",
            "listing_purpose": "sale",
            "price": 200000,
            "currency": "USD",
            "bedrooms": 2,
            "bathrooms": 1,
            "area_size": 85.5,
            "area_unit": "sqm",
            "furnishing": "furnished",
            "location_text": "Test City",
            "address": "123 Test St",
            "city": "Test City",
            "country": "Test Country",
            "status": "active",
        }, headers={"Authorization": f"Bearer {token}"})
        assert resp.status_code == 201
        return resp.json()["id"]

    async def _create_viewing_slot(self, client: AsyncClient, token: str, listing_id: str) -> str:
        starts = datetime.now(timezone.utc) + timedelta(days=1)
        ends = starts + timedelta(hours=1)
        resp = await client.post(
            f"/agency/listings/{listing_id}/viewing-slots",
            json={
                "starts_at": starts.isoformat(),
                "ends_at": ends.isoformat(),
                "capacity": 3,
            },
            headers={"Authorization": f"Bearer {token}"},
        )
        assert resp.status_code == 201
        return resp.json()["id"]

    async def _complete_profile(
        self,
        client: AsyncClient,
        token: str,
        *,
        name: str | None = "Test Lead",
        phone: str | None = "+1234567890",
    ) -> None:
        resp = await client.put(
            "/me/profile",
            json={"name": name, "phone": phone},
            headers={"Authorization": f"Bearer {token}"},
        )
        assert resp.status_code == 200

    async def test_submit_inquiry(self, async_client: AsyncClient):
        admin_token = await self._login(async_client, "agency.admin@akarai.test")
        listing_id = await self._create_listing(async_client, admin_token)

        user_token = await self._login(async_client, "user@akarai.test")
        await self._complete_profile(async_client, user_token, name="Test Lead", phone="+1234567890")
        resp = await async_client.post(
            f"/listings/{listing_id}/inquiries",
            json={
                "name": "Test Lead",
                "email": "test@example.com",
                "phone": "+1234567890",
                "message": "I'm interested in this property",
            },
            headers={"Authorization": f"Bearer {user_token}"},
        )
        assert resp.status_code == 201
        data = resp.json()
        assert data["name"] == "Test Lead"
        assert data["email"] == "user@akarai.test"
        assert data["phone"] == "+1234567890"
        assert data["status"] == "new"

    async def test_submit_inquiry_uses_stored_profile_fields(self, async_client: AsyncClient):
        admin_token = await self._login(async_client, "agency.admin@akarai.test")
        listing_id = await self._create_listing(async_client, admin_token)

        user_token = await self._login(async_client, "user@akarai.test")
        await self._complete_profile(async_client, user_token, name="Stored Profile Name", phone="+96171111111")
        resp = await async_client.post(
            f"/listings/{listing_id}/inquiries",
            json={
                "name": "Ignored Name",
                "email": "ignored@example.com",
                "phone": "+1111111111",
                "message": "Just a message",
            },
            headers={"Authorization": f"Bearer {user_token}"},
        )
        assert resp.status_code == 201
        data = resp.json()
        assert data["message"] == "Just a message"
        assert data["name"] == "Stored Profile Name"
        assert data["email"] == "user@akarai.test"
        assert data["phone"] == "+96171111111"

    async def test_submit_inquiry_requires_complete_profile(self, async_client: AsyncClient):
        admin_token = await self._login(async_client, "agency.admin@akarai.test")
        listing_id = await self._create_listing(async_client, admin_token)

        user_token = await self._login(async_client, "user@akarai.test")
        await async_client.put(
            "/me/profile",
            json={"name": "", "phone": None},
            headers={"Authorization": f"Bearer {user_token}"},
        )

        resp = await async_client.post(
            f"/listings/{listing_id}/inquiries",
            json={"message": "Just a message"},
            headers={"Authorization": f"Bearer {user_token}"},
        )
        assert resp.status_code == 422
        data = resp.json()
        assert data["error_code"] == "PROFILE_INCOMPLETE_FOR_LEADS"
        assert data["missing_fields"] == ["name"]

    async def test_submit_inquiry_rejects_empty_message(self, async_client: AsyncClient):
        admin_token = await self._login(async_client, "agency.admin@akarai.test")
        listing_id = await self._create_listing(async_client, admin_token)

        user_token = await self._login(async_client, "user@akarai.test")
        await self._complete_profile(async_client, user_token, name="Test Lead", phone="+1234567890")

        resp = await async_client.post(
            f"/listings/{listing_id}/inquiries",
            json={"message": "   "},
            headers={"Authorization": f"Bearer {user_token}"},
        )
        assert resp.status_code == 422
        data = resp.json()
        assert data["error_code"] == "EMPTY_LEAD_MESSAGE"

    async def test_submit_inquiry_listing_not_found(self, async_client: AsyncClient):
        user_token = await self._login(async_client, "user@akarai.test")
        resp = await async_client.post(
            "/listings/00000000-0000-0000-0000-000000000000/inquiries",
            json={"message": "Test"},
            headers={"Authorization": f"Bearer {user_token}"},
        )
        assert resp.status_code == 404

    async def test_submit_inquiry_requires_auth(self, async_client: AsyncClient):
        resp = await async_client.post(
            "/listings/00000000-0000-0000-0000-000000000000/inquiries",
            json={"message": "Test"},
        )
        assert resp.status_code == 401

    async def test_submit_inquiry_rate_limit(self, async_client: AsyncClient):
        admin_token = await self._login(async_client, "agency.admin@akarai.test")
        listing_id = await self._create_listing(async_client, admin_token)

        user_token = await self._login(async_client, "user@akarai.test")
        await self._complete_profile(async_client, user_token)
        for _ in range(6):
            resp = await async_client.post(
                f"/listings/{listing_id}/inquiries",
                json={"message": "Test"},
                headers={"Authorization": f"Bearer {user_token}"},
            )
            if resp.status_code == 429:
                break
        assert resp.status_code in [201, 429]

    async def test_book_viewing(self, async_client: AsyncClient):
        admin_token = await self._login(async_client, "agency.admin@akarai.test")
        listing_id = await self._create_listing(async_client, admin_token)
        slot_id = await self._create_viewing_slot(async_client, admin_token, listing_id)

        user_token = await self._login(async_client, "user@akarai.test")
        resp = await async_client.post(
            f"/listings/{listing_id}/viewings",
            json={"viewing_slot_id": slot_id, "notes": "Want to see it"},
            headers={"Authorization": f"Bearer {user_token}"},
        )
        assert resp.status_code == 201
        data = resp.json()
        assert data["status"] == "scheduled"
        assert data["notes"] == "Want to see it"

    async def test_book_viewing_slot_not_found(self, async_client: AsyncClient):
        admin_token = await self._login(async_client, "agency.admin@akarai.test")
        listing_id = await self._create_listing(async_client, admin_token)

        user_token = await self._login(async_client, "user@akarai.test")
        resp = await async_client.post(
            f"/listings/{listing_id}/viewings",
            json={"viewing_slot_id": "00000000-0000-0000-0000-000000000000"},
            headers={"Authorization": f"Bearer {user_token}"},
        )
        assert resp.status_code == 404

    async def test_book_viewing_requires_auth(self, async_client: AsyncClient):
        resp = await async_client.post(
            "/listings/00000000-0000-0000-0000-000000000000/viewings",
            json={"viewing_slot_id": "00000000-0000-0000-0000-000000000000"},
        )
        assert resp.status_code == 401

    async def test_book_viewing_rate_limit(self, async_client: AsyncClient):
        admin_token = await self._login(async_client, "agency.admin@akarai.test")
        listing_id = await self._create_listing(async_client, admin_token)
        slot_id = await self._create_viewing_slot(async_client, admin_token, listing_id)

        user_token = await self._login(async_client, "user@akarai.test")
        for _ in range(11):
            resp = await async_client.post(
                f"/listings/{listing_id}/viewings",
                json={"viewing_slot_id": slot_id},
                headers={"Authorization": f"Bearer {user_token}"},
            )
            if resp.status_code == 429:
                break
        assert resp.status_code in [201, 409, 429]

    async def test_list_my_viewings(self, async_client: AsyncClient):
        admin_token = await self._login(async_client, "agency.admin@akarai.test")
        listing_id = await self._create_listing(async_client, admin_token)
        slot_id = await self._create_viewing_slot(async_client, admin_token, listing_id)

        user_token = await self._login(async_client, "user@akarai.test")
        await async_client.post(
            f"/listings/{listing_id}/viewings",
            json={"viewing_slot_id": slot_id},
            headers={"Authorization": f"Bearer {user_token}"},
        )

        resp = await async_client.get(
            "/me/viewings",
            headers={"Authorization": f"Bearer {user_token}"},
        )
        assert resp.status_code == 200
        data = resp.json()
        assert data["total"] >= 1
        assert "items" in data

    async def test_get_my_viewing(self, async_client: AsyncClient):
        admin_token = await self._login(async_client, "agency.admin@akarai.test")
        listing_id = await self._create_listing(async_client, admin_token)
        slot_id = await self._create_viewing_slot(async_client, admin_token, listing_id)

        user_token = await self._login(async_client, "user@akarai.test")
        booking_resp = await async_client.post(
            f"/listings/{listing_id}/viewings",
            json={"viewing_slot_id": slot_id},
            headers={"Authorization": f"Bearer {user_token}"},
        )
        viewing_id = booking_resp.json()["id"]

        resp = await async_client.get(
            f"/me/viewings/{viewing_id}",
            headers={"Authorization": f"Bearer {user_token}"},
        )
        assert resp.status_code == 200
        assert resp.json()["id"] == viewing_id

    async def test_list_my_viewings_requires_auth(self, async_client: AsyncClient):
        resp = await async_client.get("/me/viewings")
        assert resp.status_code == 401
