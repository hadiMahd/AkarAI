export const AGENCY_ROUTES = {
  signIn: "/sign-in",
  dashboard: "/dashboard",
  profile: "/profile",
  employees: "/employees",
  listings: "/listings",
  listingNew: "/listings/new",
  listingDetail: (id: string) => `/listings/${id}`,
  listingSlots: (id: string) => `/listings/${id}/slots`,
  leads: "/leads",
  leadsReviewed: "/leads/reviewed",
  leadDetail: (id: string) => `/leads/${id}`,
  viewings: "/viewings",
  spamLeads: "/spam-leads",
  policyDocuments: "/policy-documents",
} as const;

export type AgencyRouteKey = keyof typeof AGENCY_ROUTES;

export const ADMIN_ONLY_ROUTES = [
  "profile",
  "employees",
  "listings",
  "listingNew",
  "policyDocuments",
] as const;

export const SHARED_ROUTES = [
  "dashboard",
  "leads",
  "leadsReviewed",
  "viewings",
  "spamLeads",
] as const;

export function isRouteAdminOnly(routeKey: string): boolean {
  return (ADMIN_ONLY_ROUTES as readonly string[]).includes(routeKey);
}

export function isRouteShared(routeKey: string): boolean {
  return (SHARED_ROUTES as readonly string[]).includes(routeKey);
}
