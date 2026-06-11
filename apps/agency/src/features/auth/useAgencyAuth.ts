import { useMutation, useQueryClient } from "@tanstack/react-query";
import { useNavigate } from "react-router-dom";
import { signIn as apiSignIn, signOut as apiSignOut, type SignInRequest, type SignInResponse, type ActorSummary } from "@/lib/api/auth";
import { setSession, setTenantSession, setUser, clearSession, getSession } from "@/lib/session/auth-session";
import { queryKeys } from "@/lib/query/query-client";
import type { AgencyUser } from "@/lib/api/auth";
import type { AgencyTenantSession } from "@/lib/session/tenant-session";

function actorToUser(actor: ActorSummary): AgencyUser {
  return {
    id: actor.id,
    email: actor.email,
    name: actor.email,
    is_active: actor.is_active,
    created_at: "",
    updated_at: "",
    role: actor.role,
    permissions: actor.permissions,
    tenant_id: actor.tenant_id,
  };
}

function actorToTenantSession(actor: ActorSummary): AgencyTenantSession {
  return {
    userId: actor.id,
    tenantId: actor.tenant_id ?? "",
    role: actor.role,
    permissions: actor.permissions,
    isActive: actor.is_active,
  };
}

export function useAgencyAuth() {
  const queryClient = useQueryClient();
  const navigate = useNavigate();
  const { user: sessionUser } = getSession();

  const user = sessionUser || null;

  const signInMutation = useMutation({
    mutationFn: apiSignIn,
    onSuccess: (data: SignInResponse) => {
      const user = actorToUser(data.actor);
      const tenantSession = actorToTenantSession(data.actor);
      setSession(data.access_token, user, tenantSession);
      setUser(user);
      setTenantSession(tenantSession);
      queryClient.setQueryData(queryKeys.user.me, user);
      navigate("/dashboard");
    },
  });

  const signOutMutation = useMutation({
    mutationFn: apiSignOut,
    onSuccess: () => {
      clearSession();
      queryClient.clear();
      navigate("/sign-in");
    },
  });

  return {
    user,
    isAuthenticated: !!user,
    signIn: (data: SignInRequest) => signInMutation.mutateAsync(data),
    logout: () => signOutMutation.mutateAsync(),
    isSigningIn: signInMutation.isPending,
    signInError: signInMutation.error,
    isLoading: false,
  };
}
