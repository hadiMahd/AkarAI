import uuid

import pytest

from app.common.tenant import TenantContext, require_tenant, ensure_tenant_match


class TestTenantContext:
    def test_default_tenant_context_is_empty(self):
        ctx = TenantContext()
        assert ctx.actor_id is None
        assert ctx.role is None
        assert ctx.permissions == []
        assert ctx.tenant_id is None
        assert ctx.is_platform_actor is False

    def test_tenant_context_with_agency_data(self):
        actor_id = uuid.uuid4()
        tenant_id = uuid.uuid4()
        ctx = TenantContext(
            actor_id=actor_id,
            role="agency_admin",
            permissions=["listing:read", "agency:read"],
            tenant_id=tenant_id,
            membership_id=uuid.uuid4(),
            source="api",
        )
        assert ctx.actor_id == actor_id
        assert ctx.role == "agency_admin"
        assert ctx.tenant_id == tenant_id
        assert ctx.is_platform_actor is False

    def test_tenant_context_with_platform_admin(self):
        ctx = TenantContext(
            actor_id=uuid.uuid4(),
            role="platform_admin",
            permissions=["system:admin"],
            is_platform_actor=True,
        )
        assert ctx.role == "platform_admin"
        assert ctx.is_platform_actor is True

    def test_require_tenant_with_valid_context(self):
        ctx = TenantContext(
            actor_id=uuid.uuid4(),
            role="agency_admin",
            tenant_id=uuid.uuid4(),
        )
        result = require_tenant(ctx)
        assert result is ctx

    def test_require_tenant_with_platform_actor_no_tenant(self):
        ctx = TenantContext(
            actor_id=uuid.uuid4(),
            role="platform_admin",
            is_platform_actor=True,
        )
        result = require_tenant(ctx)
        assert result is ctx

    def test_require_tenant_without_context_raises(self):
        with pytest.raises(PermissionError, match="Tenant context is required"):
            require_tenant(None)

    def test_require_tenant_without_tenant_or_platform_raises(self):
        ctx = TenantContext(actor_id=uuid.uuid4(), role="agency_admin")
        with pytest.raises(PermissionError, match="active tenant membership"):
            require_tenant(ctx)

    def test_ensure_tenant_match_allows_matching(self):
        tid = uuid.uuid4()
        ctx = TenantContext(actor_id=uuid.uuid4(), tenant_id=tid)
        ensure_tenant_match(ctx, tid)

    def test_ensure_tenant_match_allows_platform(self):
        tid = uuid.uuid4()
        ctx = TenantContext(actor_id=uuid.uuid4(), is_platform_actor=True)
        ensure_tenant_match(ctx, tid)

    def test_ensure_tenant_match_denies_cross_tenant(self):
        ctx = TenantContext(actor_id=uuid.uuid4(), tenant_id=uuid.uuid4())
        with pytest.raises(PermissionError, match="Cross-tenant"):
            ensure_tenant_match(ctx, uuid.uuid4())



