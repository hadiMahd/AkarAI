"""RBAC / tenant-isolation tests for RAG retrieval."""
from datetime import datetime, timezone
from unittest.mock import patch
from uuid import uuid4

import pytest
from httpx import AsyncClient

from app.auth.models import Role
from app.rag.models import RagChunk, RagDocument, RagPage


async def _login(client: AsyncClient, email: str, password: str) -> str:
    resp = await client.post("/auth/login", json={"email": email, "password": password})
    assert resp.status_code == 200
    return resp.json()["access_token"]


async def _create_tenant_and_membership(db_session, role_slug: str, suffix: str):
    from sqlalchemy import text
    from app.agencies.models import AgencyEmployeeMembership, AgencyTenant
    from app.common.security import hash_password
    from app.users.models import User

    now = datetime.now(timezone.utc)
    tenant_id = uuid4()
    user_id = uuid4()

    role_result = await db_session.execute(
        text("SELECT id FROM roles WHERE slug = :slug"),
        {"slug": role_slug},
    )
    role_id = role_result.scalar_one()

    tenant = AgencyTenant(
        id=tenant_id,
        name=f"rbac-tenant-{suffix}-{tenant_id.hex[:4]}",
        slug=f"rbac-tenant-{suffix}-{tenant_id.hex[:8]}",
        status="active",
        created_at=now,
        updated_at=now,
    )
    user = User(
        id=user_id,
        email=f"rbac-user-{suffix}-{user_id.hex[:8]}@example.com",
        password_hash=hash_password("TestPass123!"),
        name=f"RBAC User {suffix}",
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
        display_name=user.name,
        work_email=user.email,
        created_at=now,
        updated_at=now,
    )
    db_session.add(tenant)
    await db_session.flush()
    db_session.add(user)
    await db_session.flush()
    db_session.add(membership)
    await db_session.flush()
    await db_session.commit()
    return tenant, user, "TestPass123!"


async def _insert_doc_for_tenant(db_session, tenant_id, suffix=""):
    from app.rag.models import RagChunk, RagDocument, RagPage

    doc_id = uuid4()
    page_id = uuid4()
    now = datetime.now(timezone.utc)

    doc = RagDocument(
        id=doc_id,
        tenant_id=tenant_id,
        filename=f"policy-{suffix}.pdf",
        status="processed",
        blob_path=f"rag-vault/{tenant_id}/{doc_id}/original/policy-{suffix}.pdf",
        created_at=now,
        updated_at=now,
    )
    page = RagPage(
        id=page_id,
        document_id=doc_id,
        tenant_id=tenant_id,
        page_number=1,
        blob_path=f"rag-vault/{tenant_id}/{doc_id}/page-1.png",
        content=f"Policy {suffix} content.",
        created_at=now,
    )
    chunk = RagChunk(
        id=uuid4(),
        document_id=doc_id,
        tenant_id=tenant_id,
        page_ids=[page_id],
        content_hash=f"chunk-hash-{suffix}",
        text=f"Policy {suffix} content.",
        embedding=[0.1] * 1536,
        status="active",
        created_at=now,
    )
    db_session.add(doc)
    await db_session.commit()
    db_session.add(page)
    await db_session.commit()
    db_session.add(chunk)
    await db_session.commit()
    return doc


@pytest.mark.anyio
class TestRagRetrievalTenantIsolation:
    async def test_cross_tenant_query_denied(self, async_client: AsyncClient, db_session):
        """Tenant A user should not see Tenant B documents in query results."""
        tenant_a, user_a, pw_a = await _create_tenant_and_membership(db_session, "agency_admin", "qry-a")
        tenant_b, user_b, pw_b = await _create_tenant_and_membership(db_session, "agency_admin", "qry-b")

        await _insert_doc_for_tenant(db_session, tenant_a.id, suffix="A")

        token_b = await _login(async_client, user_b.email, pw_b)

        with patch("app.rag.service.get_embedding_provider") as mock_embed:
            mock_embed.return_value.embed.return_value = [[0.1] * 1536]
            resp = await async_client.post(
                "/api/v1/agencies/rag/query",
                headers={"Authorization": f"Bearer {token_b}"},
                json={"query": "policy A content"},
            )

        assert resp.status_code == 200
        data = resp.json()
        assert data["status"] == "insufficient_evidence"

    async def test_support_employee_accessing_logs_denied(self, async_client: AsyncClient, db_session):
        """Support employees cannot access retrieval logs regardless of tenant."""
        tenant, user, pw = await _create_tenant_and_membership(db_session, "support_employee", "se")

        token = await _login(async_client, user.email, pw)
        resp = await async_client.get(
            "/api/v1/agencies/rag/retrieval-logs",
            headers={"Authorization": f"Bearer {token}"},
        )
        assert resp.status_code == 403

    async def test_platform_admin_accessing_logs_denied(self, async_client: AsyncClient, db_session):
        """Retrieval logs are agency-admin only at the router boundary."""
        tenant, user, pw = await _create_tenant_and_membership(db_session, "platform_admin", "pa")

        token = await _login(async_client, user.email, pw)
        resp = await async_client.get(
            "/api/v1/agencies/rag/retrieval-logs",
            headers={"Authorization": f"Bearer {token}"},
        )
        assert resp.status_code == 403
