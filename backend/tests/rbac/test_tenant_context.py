import uuid

from app.common.tenant import TenantContext


class TestTenantContext:
    def test_default_tenant_context(self):
        ctx = TenantContext()
        assert ctx.actor_id is None
        assert ctx.role is None
        assert ctx.permissions == []
        assert ctx.tenant_id is None
        assert ctx.source == "internal"

    def test_tenant_context_with_values(self):
        actor = uuid.uuid4()
        tenant = uuid.uuid4()
        ctx = TenantContext(
            actor_id=actor,
            role="agency_admin",
            permissions=["listing:read"],
            tenant_id=tenant,
            request_id="req-1",
            source="api",
        )
        assert ctx.actor_id == actor
        assert ctx.role == "agency_admin"
        assert "listing:read" in ctx.permissions
        assert ctx.tenant_id == tenant
        assert ctx.request_id == "req-1"
        assert ctx.source == "api"
