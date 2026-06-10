import { createBrowserRouter } from "react-router-dom";
import { ProtectedRoute, PublicOnlyRoute } from "./guards";
import { LandingPage } from "@/pages/landing/LandingPage";
import { SignInPage } from "@/pages/auth/SignInPage";
import { SignUpPage } from "@/pages/auth/SignUpPage";
import { HomePage } from "@/pages/home/HomePage";
import { ListingsPage } from "@/pages/listings/ListingsPage";
import { ListingDetailPage } from "@/pages/listing-detail/ListingDetailPage";
import { ComparisonPage } from "@/pages/comparison/ComparisonPage";
import { ProfilePage } from "@/pages/profile/ProfilePage";
import { ProtectedLayout } from "@/components/ProtectedLayout";
import { RouteErrorFallback } from "@/components/ErrorBoundary";

export const router = createBrowserRouter([
  {
    path: "/",
    element: <LandingPage />,
    errorElement: <RouteErrorFallback />,
  },
  {
    element: <PublicOnlyRoute />,
    errorElement: <RouteErrorFallback />,
    children: [
      { path: "sign-in", element: <SignInPage />, errorElement: <RouteErrorFallback /> },
      { path: "sign-up", element: <SignUpPage />, errorElement: <RouteErrorFallback /> },
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
          { path: "home", element: <HomePage />, errorElement: <RouteErrorFallback /> },
          { path: "listings", element: <ListingsPage />, errorElement: <RouteErrorFallback /> },
          { path: "listings/:id", element: <ListingDetailPage />, errorElement: <RouteErrorFallback /> },
          { path: "comparison", element: <ComparisonPage />, errorElement: <RouteErrorFallback /> },
          { path: "profile", element: <ProfilePage />, errorElement: <RouteErrorFallback /> },
        ],
      },
    ],
  },
]);