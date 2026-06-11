import { useQuery } from "@tanstack/react-query";
import { getTenantContext } from "@/lib/api/auth";
import { queryKeys } from "@/lib/query/query-client";
import { getAccessToken } from "@/lib/session/auth-session";
import type { AgencyTenantSession } from "@/lib/session/tenant-session";

export function useTenantSession() {
  const query = useQuery({
    queryKey: queryKeys.tenant.context,
    queryFn: getTenantContext,
    enabled: !!getAccessToken(),
    retry: false,
  });

  const session: AgencyTenantSession | null = query.data
    ? {
        userId: query.data.actor_id,
        tenantId: query.data.tenant_id ?? "",
        role: query.data.role,
        permissions: query.data.permissions,
        isActive: true,
      }
    : null;

  return {
    session,
    isLoading: query.isLoading,
    error: query.error,
  };
}
