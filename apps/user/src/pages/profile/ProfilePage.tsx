import { useSearchParams } from "react-router-dom";
import { useQuery } from "@tanstack/react-query";
import { ProfileTabs } from "@/features/profile/ProfileTabs";
import { SavedListingsTab } from "@/features/profile/SavedListingsTab";
import { SubmittedInquiriesTab } from "@/features/profile/SubmittedInquiriesTab";
import { ScheduledViewingsTab } from "@/features/profile/ScheduledViewingsTab";
import { useSavedListings } from "@/features/saved-listings/useSavedListings";
import { useAuth } from "@/features/auth/useAuth";
import { apiClient } from "@/lib/api/client";
import { Card, CardContent } from "@/components/ui/card";
import { Bookmark, CalendarDays, Mail, MessageSquare, UserRound } from "lucide-react";

export type ProfileTab = "saved" | "inquiries" | "viewings";

interface PaginatedItemsResponse {
  total: number;
}

export function ProfilePage() {
  const [searchParams, setSearchParams] = useSearchParams();
  const rawTab = searchParams.get("tab");
  const activeTab: ProfileTab =
    rawTab === "inquiries" || rawTab === "viewings" ? rawTab : "saved";
  const { user } = useAuth();
  const { savedListings } = useSavedListings();

  const { data: inquiriesData } = useQuery<PaginatedItemsResponse>({
    queryKey: ["profile-inquiries-summary"],
    queryFn: () => apiClient<PaginatedItemsResponse>("/me/inquiries"),
  });

  const { data: viewingsData } = useQuery<PaginatedItemsResponse>({
    queryKey: ["profile-viewings-summary"],
    queryFn: () => apiClient<PaginatedItemsResponse>("/me/viewings"),
  });

  const handleTabChange = (tab: ProfileTab) => {
    const next = new URLSearchParams(searchParams);
    if (tab === "saved") {
      next.delete("tab");
    } else {
      next.set("tab", tab);
    }
    setSearchParams(next, { replace: true });
  };

  return (
    <div className="space-y-6">
      <Card>
        <CardContent className="p-6">
          <div className="flex flex-col gap-6 lg:flex-row lg:items-start lg:justify-between">
            <div className="space-y-3">
              <div className="flex items-center gap-3">
                <div className="flex h-12 w-12 items-center justify-center rounded-full bg-primary/10 text-primary">
                  <UserRound className="h-6 w-6" />
                </div>
                <div>
                  <h1 className="text-2xl font-semibold">{user?.name || "My Profile"}</h1>
                  <div className="mt-1 flex items-center gap-2 text-sm text-muted-foreground">
                    <Mail className="h-4 w-4" />
                    <span>{user?.email}</span>
                  </div>
                </div>
              </div>
              <p className="max-w-2xl text-sm text-muted-foreground">
                Review your saved properties, contact history, and booked tours.
              </p>
            </div>

            <div className="grid grid-cols-1 gap-3 sm:grid-cols-3">
              <div className="rounded-md border px-4 py-3">
                <div className="flex items-center gap-2 text-sm text-muted-foreground">
                  <Bookmark className="h-4 w-4" />
                  Saved
                </div>
                <div className="mt-2 text-2xl font-semibold">{savedListings.length}</div>
              </div>
              <div className="rounded-md border px-4 py-3">
                <div className="flex items-center gap-2 text-sm text-muted-foreground">
                  <MessageSquare className="h-4 w-4" />
                  Inquiries
                </div>
                <div className="mt-2 text-2xl font-semibold">{inquiriesData?.total ?? 0}</div>
              </div>
              <div className="rounded-md border px-4 py-3">
                <div className="flex items-center gap-2 text-sm text-muted-foreground">
                  <CalendarDays className="h-4 w-4" />
                  Viewings
                </div>
                <div className="mt-2 text-2xl font-semibold">{viewingsData?.total ?? 0}</div>
              </div>
            </div>
          </div>
        </CardContent>
      </Card>

      <ProfileTabs activeTab={activeTab} onTabChange={handleTabChange} />

      <div className="mt-6">
        {activeTab === "saved" && <SavedListingsTab />}
        {activeTab === "inquiries" && <SubmittedInquiriesTab />}
        {activeTab === "viewings" && <ScheduledViewingsTab />}
      </div>
    </div>
  );
}
