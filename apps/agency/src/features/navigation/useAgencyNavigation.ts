import { useMemo } from "react";
import { useLocation } from "react-router-dom";
import { AGENCY_ROUTES } from "./RouteAccess";
import type { AgencyTenantSession } from "@/lib/session/tenant-session";
import { isAgencyAdmin } from "@/lib/session/tenant-session";

export interface NavItem {
  name: string;
  href: string;
  routeKey: string;
  adminOnly: boolean;
}

export function useAgencyNavigation(session: AgencyTenantSession | null) {
  const location = useLocation();
  const isAdmin = isAgencyAdmin(session);

  const allNavItems: NavItem[] = useMemo(() => [
    { name: "Dashboard", href: AGENCY_ROUTES.dashboard, routeKey: "dashboard", adminOnly: false },
    { name: "Profile", href: AGENCY_ROUTES.profile, routeKey: "profile", adminOnly: true },
    { name: "Employees", href: AGENCY_ROUTES.employees, routeKey: "employees", adminOnly: true },
    { name: "Listings", href: AGENCY_ROUTES.listings, routeKey: "listings", adminOnly: true },
    { name: "Active Leads", href: AGENCY_ROUTES.leads, routeKey: "leads", adminOnly: false },
    { name: "Reviewed Leads", href: AGENCY_ROUTES.leadsReviewed, routeKey: "leadsReviewed", adminOnly: false },
    { name: "Viewings", href: AGENCY_ROUTES.viewings, routeKey: "viewings", adminOnly: false },
    { name: "Spam Leads", href: AGENCY_ROUTES.spamLeads, routeKey: "spamLeads", adminOnly: false },
    { name: "Policy Documents", href: AGENCY_ROUTES.policyDocuments, routeKey: "policyDocuments", adminOnly: true },
  ], []);

  const visibleNavItems = useMemo(() => {
    if (isAdmin) {
      return allNavItems;
    }
    return allNavItems.filter((item) => !item.adminOnly);
  }, [allNavItems, isAdmin]);

  const isActiveRoute = (href: string) => {
    if (location.pathname === href) {
      return true;
    }

    if (href === AGENCY_ROUTES.leads || href === AGENCY_ROUTES.leadsReviewed) {
      return false;
    }

    return location.pathname.startsWith(href + "/");
  };

  return {
    navItems: visibleNavItems,
    isActiveRoute,
    isAdmin,
  };
}
