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

export const router = createBrowserRouter([
  {
    path: "/",
    element: <LandingPage />,
  },
  {
    element: <PublicOnlyRoute />,
    children: [
      { path: "sign-in", element: <SignInPage /> },
      { path: "sign-up", element: <SignUpPage /> },
    ],
  },
  {
    element: <ProtectedRoute />,
    children: [
      {
        element: <ProtectedLayout />,
        children: [
          { path: "home", element: <HomePage /> },
          { path: "listings", element: <ListingsPage /> },
          { path: "listings/:id", element: <ListingDetailPage /> },
          { path: "comparison", element: <ComparisonPage /> },
          { path: "profile", element: <ProfilePage /> },
        ],
      },
    ],
  },
]);