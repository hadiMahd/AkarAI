import { createBrowserRouter } from "react-router-dom";
import { AdminOnlyRoute, ProtectedRoute, PublicOnlyRoute } from "./guards";
import { SignInPage } from "@/pages/auth/SignInPage";
import { DashboardPage } from "@/pages/dashboard/DashboardPage";
import { AgencyProfilePage } from "@/pages/profile/AgencyProfilePage";
import { EmployeesPage } from "@/pages/employees/EmployeesPage";
import { ListingsPage } from "@/pages/listings/ListingsPage";
import { ListingEditorPage } from "@/pages/listings/ListingEditorPage";
import { ViewingSlotsPage } from "@/pages/listings/ViewingSlotsPage";
import { LeadsPage } from "@/pages/leads/LeadsPage";
import { LeadDetailPage } from "@/pages/leads/LeadDetailPage";
import { ReviewedLeadsPage } from "@/pages/leads/ReviewedLeadsPage";
import { ViewingsPage } from "@/pages/viewings/ViewingsPage";
import { SpamLeadsPage } from "@/pages/placeholders/SpamLeadsPage";
import { RagDocumentsPage } from "@/pages/rag/RagDocumentsPage";
import { ProtectedLayout } from "@/components/ProtectedLayout";
import { RouteErrorFallback } from "@/components/ErrorBoundary";

export const router = createBrowserRouter([
  {
    element: <PublicOnlyRoute />,
    errorElement: <RouteErrorFallback />,
    children: [
      { path: "/sign-in", element: <SignInPage />, errorElement: <RouteErrorFallback /> },
    ],
  },
  {
    element: <ProtectedRoute />,
    errorElement: <RouteErrorFallback />,
    children: [
      {
        element: <ProtectedLayout />,
        errorElement: <RouteErrorFallback />,
        children: [
          { path: "/dashboard", element: <DashboardPage />, errorElement: <RouteErrorFallback /> },
          { path: "/leads", element: <LeadsPage />, errorElement: <RouteErrorFallback /> },
          { path: "/leads/reviewed", element: <ReviewedLeadsPage />, errorElement: <RouteErrorFallback /> },
          { path: "/leads/:leadId", element: <LeadDetailPage />, errorElement: <RouteErrorFallback /> },
          { path: "/viewings", element: <ViewingsPage />, errorElement: <RouteErrorFallback /> },
          { path: "/spam-leads", element: <SpamLeadsPage />, errorElement: <RouteErrorFallback /> },
          { path: "/profile", element: <AdminOnlyRoute><AgencyProfilePage /></AdminOnlyRoute>, errorElement: <RouteErrorFallback /> },
          { path: "/employees", element: <AdminOnlyRoute><EmployeesPage /></AdminOnlyRoute>, errorElement: <RouteErrorFallback /> },
          { path: "/listings", element: <AdminOnlyRoute><ListingsPage /></AdminOnlyRoute>, errorElement: <RouteErrorFallback /> },
          { path: "/listings/new", element: <AdminOnlyRoute><ListingEditorPage /></AdminOnlyRoute>, errorElement: <RouteErrorFallback /> },
          { path: "/listings/:listingId", element: <AdminOnlyRoute><ListingEditorPage /></AdminOnlyRoute>, errorElement: <RouteErrorFallback /> },
          { path: "/listings/:listingId/slots", element: <AdminOnlyRoute><ViewingSlotsPage /></AdminOnlyRoute>, errorElement: <RouteErrorFallback /> },
          { path: "/policy-documents", element: <AdminOnlyRoute><RagDocumentsPage /></AdminOnlyRoute>, errorElement: <RouteErrorFallback /> },
        ],
      },
    ],
  },
  {
    path: "/",
    element: <SignInPage />,
    errorElement: <RouteErrorFallback />,
  },
]);
