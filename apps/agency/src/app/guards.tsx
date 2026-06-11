import { type ReactNode } from "react";
import { Navigate, Outlet, useLocation } from "react-router-dom";
import { useAgencyAuth } from "@/features/auth/useAgencyAuth";
import { LoadingSkeleton } from "@/components/LoadingSkeleton";
import { isAgencyAdmin } from "@/lib/session/tenant-session";
import { getTenantSession } from "@/lib/session/auth-session";

export function ProtectedRoute() {
  const { user, isLoading } = useAgencyAuth();
  const location = useLocation();

  if (isLoading) {
    return <LoadingSkeleton />;
  }

  if (!user) {
    return <Navigate to="/sign-in" state={{ from: location }} replace />;
  }

  return <Outlet />;
}

export function PublicOnlyRoute() {
  const { user, isLoading } = useAgencyAuth();

  if (isLoading) {
    return <LoadingSkeleton />;
  }

  if (user) {
    return <Navigate to="/dashboard" replace />;
  }

  return <Outlet />;
}

export function AdminOnlyRoute({ children }: { children?: ReactNode }) {
  const { user } = useAgencyAuth();
  const location = useLocation();

  if (!user) {
    return <Navigate to="/sign-in" state={{ from: location }} replace />;
  }
  const session = getTenantSession();

  if (!isAgencyAdmin(session)) {
    return <Navigate to="/dashboard" replace />;
  }

  return children ? <>{children}</> : <Outlet />;
}
