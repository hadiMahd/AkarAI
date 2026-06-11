import type { ActorSummary } from "../api/auth";

export interface AgencyTenantSession {
  userId: string;
  tenantId: string;
  role: string;
  permissions: string[];
  isActive: boolean;
}

export function actorToTenantSession(actor: ActorSummary): AgencyTenantSession | null {
  if (!actor.role) {
    return null;
  }
  return {
    userId: actor.id,
    tenantId: actor.tenant_id ?? "",
    role: actor.role,
    permissions: actor.permissions || [],
    isActive: actor.is_active,
  };
}

export function isAgencyAdmin(session: AgencyTenantSession | null): boolean {
  return session?.role === "agency_admin";
}

export function isSupportEmployee(session: AgencyTenantSession | null): boolean {
  return session?.role === "support_employee";
}

export function hasPermission(session: AgencyTenantSession | null, permission: string): boolean {
  if (!session) return false;
  return session.permissions.includes(permission);
}
