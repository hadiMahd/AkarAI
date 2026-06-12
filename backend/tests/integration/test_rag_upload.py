"""Integration tests for RAG document upload, RBAC, validation, and status."""
from datetime import datetime, timezone
from unittest.mock import patch
from uuid import uuid4

import pytest
from httpx import AsyncClient

FAKE_PDF_BYTES = b"%PDF-1.4\n1 0 obj\n<</Type/Catalog>>\nendobj\n%%EOF"


async def _login(async_client: AsyncClient, email: str, password: str) -> str:
    resp = await async_client.post("/auth/login", json={"email": email, "password": password})
    assert resp.status_code == 200
    return resp.json()["access_token"]


async def _create_tenant_admin(db_session, slug_prefix: str = "rag-tenant"):
    from sqlalchemy import text

    from app.agencies.models import AgencyEmployeeMembership, AgencyTenant
    from app.common.security import hash_password
    from app.users.models import User

    now = datetime.now(timezone.utc)
    tenant_id = uuid4()
    user_id = uuid4()
    password = "TestPass123!"

    role_result = await db_session.execute(
        text("SELECT id FROM roles WHERE slug = 'agency_admin' LIMIT 1")
    )
    role_id = role_result.scalar_one()

    tenant = AgencyTenant(
        id=tenant_id,
        name=f"{slug_prefix}-{tenant_id.hex[:4]}",
        slug=f"{slug_prefix}-{tenant_id.hex[:8]}",
        status="active",
        created_at=now,
        updated_at=now,
    )
    user = User(
        id=user_id,
        email=f"{slug_prefix}-admin-{user_id.hex[:8]}@example.com",
        password_hash=hash_password(password),
        name="RAG Tenant Admin",
        role_id=role_id,
        is_active=True,
        status="active",
        created_at=now,
        updated_at=now,
    )
    membership = AgencyEmployeeMembership(
        id=uuid4(),
        agency_tenant_id=tenant_id,
        user_id=user_id,
        role_id=role_id,
        status="active",
        display_name="RAG Tenant Admin",
        work_email=user.email,
        created_at=now,
        updated_at=now,
    )
    db_session.add_all([tenant, user])
    await db_session.commit()

    db_session.add(membership)
    await db_session.commit()
    return tenant, user, membership, password


@pytest.mark.anyio
class TestRagUpload:
    async def test_upload_pdf_returns_202_and_outbox_event(self, async_client: AsyncClient, agency_admin_user, db_session):
        """T007: Authorized agency_admin uploads PDF, gets 202, outbox event created."""
        from sqlalchemy import select
        from app.common.events import OutboxEvent

        user, password = agency_admin_user
        token = await _login(async_client, user.email, password)

        with patch("app.rag.service._extract_text_from_pdf", return_value="test policy text"):
            resp = await async_client.post(
                "/api/v1/agencies/rag/documents",
                headers={"Authorization": f"Bearer {token}"},
                files={"file": ("policy.pdf", FAKE_PDF_BYTES, "application/pdf")},
            )

        assert resp.status_code == 202
        doc = resp.json()
        assert doc["status"] == "pending"
        assert doc["filename"] == "policy.pdf"
        assert doc["id"] is not None

        result = await db_session.execute(
            select(OutboxEvent).where(
                OutboxEvent.event_name == "rag.document_uploaded",
                OutboxEvent.idempotency_key == f"rag-document-upload-{doc['id']}",
            )
        )
        event = result.scalar_one_or_none()
        assert event is not None, "Outbox event rag.document_uploaded should have been created"
        assert event.status == "pending"
        assert event.idempotency_key == f"rag-document-upload-{doc['id']}"

    async def test_upload_pdf_returns_202_with_fixture_user(self, async_client: AsyncClient):
        """Happy path upload with seeded agency admin user."""
        token = await _login(async_client, "agency.admin@akarai.test", "Test1234!")

        with patch("app.rag.service._extract_text_from_pdf", return_value="dummy policy text"):
            resp = await async_client.post(
                "/api/v1/agencies/rag/documents",
                headers={"Authorization": f"Bearer {token}"},
                files={"file": ("policy.pdf", FAKE_PDF_BYTES, "application/pdf")},
            )

        assert resp.status_code == 202
        doc = resp.json()
        assert doc["status"] == "pending"
        assert doc["filename"] == "policy.pdf"

    async def test_upload_requires_authentication(self, async_client: AsyncClient):
        """Upload without auth token returns 401."""
        resp = await async_client.post(
            "/api/v1/agencies/rag/documents",
            files={"file": ("policy.pdf", FAKE_PDF_BYTES, "application/pdf")},
        )
        assert resp.status_code == 401

    async def test_upload_non_pdf_rejected(self, async_client: AsyncClient):
        """T009: Non-PDF files rejected with 400."""
        token = await _login(async_client, "agency.admin@akarai.test", "Test1234!")
        resp = await async_client.post(
            "/api/v1/agencies/rag/documents",
            headers={"Authorization": f"Bearer {token}"},
            files={"file": ("notes.txt", b"hello world", "text/plain")},
        )
        assert resp.status_code == 400

        resp = await async_client.post(
            "/api/v1/agencies/rag/documents",
            headers={"Authorization": f"Bearer {token}"},
            files={"file": ("image.png", b"\x89PNG\r\n\x1a\n", "image/png")},
        )
        assert resp.status_code == 400

    async def test_upload_empty_file_rejected(self, async_client: AsyncClient):
        """Empty PDF file rejected with 400."""
        token = await _login(async_client, "agency.admin@akarai.test", "Test1234!")
        resp = await async_client.post(
            "/api/v1/agencies/rag/documents",
            headers={"Authorization": f"Bearer {token}"},
            files={"file": ("empty.pdf", b"%PDF-1.4\n", "application/pdf")},
        )

        assert resp.status_code == 400
        assert "empty" in resp.json().get("detail", "").lower()

    async def test_upload_scanned_pdf_no_text_rejected(self, async_client: AsyncClient):
        """T009: Scanned PDF with no extractable text is rejected with 400
        before any document record is created."""
        token = await _login(async_client, "agency.admin@akarai.test", "Test1234!")

        with patch("app.rag.service._extract_text_from_pdf") as mock_extract:
            mock_extract.side_effect = Exception("No extractable text")
            resp = await async_client.post(
                "/api/v1/agencies/rag/documents",
                headers={"Authorization": f"Bearer {token}"},
                files={"file": ("scanned.pdf", FAKE_PDF_BYTES, "application/pdf")},
            )

        assert resp.status_code == 400

    async def test_cross_tenant_isolation(self, async_client: AsyncClient, db_session):
        """T008: A user from tenant B cannot see documents from tenant A."""
        tenant_a, user_a, membership_a, password_a = await _create_tenant_admin(db_session, "tenant-a")
        tenant_b, user_b, membership_b, password_b = await _create_tenant_admin(db_session, "tenant-b")

        token_a = await _login(async_client, user_a.email, password_a)
        token_b = await _login(async_client, user_b.email, password_b)

        with patch("app.rag.service._extract_text_from_pdf", return_value="tenant A policy"):
            resp = await async_client.post(
                "/api/v1/agencies/rag/documents",
                headers={"Authorization": f"Bearer {token_a}"},
                files={"file": ("policy.pdf", FAKE_PDF_BYTES, "application/pdf")},
            )
            assert resp.status_code == 202
            doc_a_id = resp.json()["id"]

        list_resp = await async_client.get(
            "/api/v1/agencies/rag/documents",
            headers={"Authorization": f"Bearer {token_b}"},
        )
        assert list_resp.status_code == 200
        data = list_resp.json()
        ids = [item["id"] for item in data.get("items", [])]
        assert doc_a_id not in ids

        get_resp = await async_client.get(
            f"/api/v1/agencies/rag/documents/{doc_a_id}",
            headers={"Authorization": f"Bearer {token_b}"},
        )
        assert get_resp.status_code == 404

        await db_session.delete(membership_a)
        await db_session.delete(user_a)
        await db_session.delete(membership_b)
        await db_session.delete(user_b)
        await db_session.delete(tenant_a)
        await db_session.delete(tenant_b)
        await db_session.commit()

    async def test_support_employee_cannot_upload(self, async_client: AsyncClient, support_user):
        """Support employee role gets 403 on upload."""
        user, password = support_user
        token = await _login(async_client, user.email, password)
        with patch("app.rag.service._extract_text_from_pdf", return_value="text"):
            resp = await async_client.post(
                "/api/v1/agencies/rag/documents",
                headers={"Authorization": f"Bearer {token}"},
                files={"file": ("policy.pdf", FAKE_PDF_BYTES, "application/pdf")},
            )
            assert resp.status_code == 403


@pytest.mark.anyio
class TestRagListAndDetail:
    """T021, T022, T023: GET endpoints for listing and detail."""

    async def _create_test_document(self, async_client: AsyncClient, token: str) -> dict:
        with patch("app.rag.service._extract_text_from_pdf", return_value="test"):
            resp = await async_client.post(
                "/api/v1/agencies/rag/documents",
                headers={"Authorization": f"Bearer {token}"},
                files={"file": ("policy.pdf", FAKE_PDF_BYTES, "application/pdf")},
            )
            assert resp.status_code == 202
            return resp.json()

    async def test_list_documents(self, async_client: AsyncClient):
        """T022: List RAG documents returns paginated response."""
        token = await _login(async_client, "agency.admin@akarai.test", "Test1234!")
        await self._create_test_document(async_client, token)

        resp = await async_client.get(
            "/api/v1/agencies/rag/documents",
            headers={"Authorization": f"Bearer {token}"},
        )
        assert resp.status_code == 200
        data = resp.json()
        assert "items" in data
        assert "total" in data
        assert "page" in data
        assert "size" in data

    async def test_list_documents_pagination(self, async_client: AsyncClient):
        """T022: Pagination params are respected."""
        token = await _login(async_client, "agency.admin@akarai.test", "Test1234!")

        resp = await async_client.get(
            "/api/v1/agencies/rag/documents?page=1&page_size=5",
            headers={"Authorization": f"Bearer {token}"},
        )
        assert resp.status_code == 200
        data = resp.json()
        assert data["page"] == 1
        assert data["size"] == 5
        assert isinstance(data["items"], list)

    async def test_get_document_by_id(self, async_client: AsyncClient):
        """T023: Get single RAG document by ID and verify status."""
        token = await _login(async_client, "agency.admin@akarai.test", "Test1234!")
        doc = await self._create_test_document(async_client, token)

        resp = await async_client.get(
            f"/api/v1/agencies/rag/documents/{doc['id']}",
            headers={"Authorization": f"Bearer {token}"},
        )
        assert resp.status_code == 200
        data = resp.json()
        assert data["id"] == doc["id"]
        assert data["status"] == "pending"
        assert data["filename"] == "policy.pdf"

    async def test_get_document_not_found(self, async_client: AsyncClient):
        """Non-existent document returns 404."""
        token = await _login(async_client, "agency.admin@akarai.test", "Test1234!")
        fake_id = str(uuid4())
        resp = await async_client.get(
            f"/api/v1/agencies/rag/documents/{fake_id}",
            headers={"Authorization": f"Bearer {token}"},
        )
        assert resp.status_code == 404

    async def test_list_requires_auth(self, async_client: AsyncClient):
        """List without auth returns 401."""
        resp = await async_client.get("/api/v1/agencies/rag/documents")
        assert resp.status_code == 401

    async def test_get_document_requires_auth(self, async_client: AsyncClient):
        """Get document without auth returns 401."""
        resp = await async_client.get(f"/api/v1/agencies/rag/documents/{uuid4()}")
        assert resp.status_code == 401
