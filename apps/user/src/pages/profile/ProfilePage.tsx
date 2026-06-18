import { useEffect, useState } from "react";
import { useSearchParams } from "react-router-dom";
import { useQuery } from "@tanstack/react-query";
import { ProfileTabs } from "@/features/profile/ProfileTabs";
import { SavedListingsTab } from "@/features/profile/SavedListingsTab";
import { SubmittedInquiriesTab } from "@/features/profile/SubmittedInquiriesTab";
import { ScheduledViewingsTab } from "@/features/profile/ScheduledViewingsTab";
import { useUpdateUserProfile, useUserProfile } from "@/features/profile/useUserProfile";
import { useSavedListings } from "@/features/saved-listings/useSavedListings";
import { useAuth } from "@/features/auth/useAuth";
import { apiClient } from "@/lib/api/client";
import { getApiErrorMessage } from "@/lib/api/errors";
import { Card, CardContent } from "@/components/ui/card";
import { Alert, AlertDescription } from "@/components/ui/alert";
import { Bookmark, CalendarDays, Mail, MessageSquare, Phone, UserRound } from "lucide-react";
import { Button } from "@/components/ui/button";
import { Input } from "@/components/ui/input";

export type ProfileTab = "profile" | "saved" | "inquiries" | "viewings";

interface PaginatedItemsResponse {
  total: number;
}

export function ProfilePage() {
  const [searchParams, setSearchParams] = useSearchParams();
  const rawTab = searchParams.get("tab");
  const activeTab: ProfileTab =
    rawTab === "saved" || rawTab === "inquiries" || rawTab === "viewings" ? rawTab : "profile";
  const { user } = useAuth();
  const { savedListings } = useSavedListings();
  const { data: profile } = useUserProfile();
  const updateProfile = useUpdateUserProfile();
  const [name, setName] = useState("");
  const [phone, setPhone] = useState("");

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
    next.set("tab", tab);
    setSearchParams(next, { replace: true });
  };

  const displayName = profile?.name || user?.name || "My Profile";
  const completionRequested = searchParams.get("complete") === "lead";

  useEffect(() => {
    if (profile) {
      setName(profile.name || "");
      setPhone(profile.phone || "");
    }
  }, [profile]);

  const handleSaveProfile = (e: React.FormEvent) => {
    e.preventDefault();
    updateProfile.mutate({
      name,
      phone,
    });
  };

  return (
    <div className="space-y-6">
      <ProfileTabs activeTab={activeTab} onTabChange={handleTabChange} />

      <div className="mt-6">
        {activeTab === "profile" && (
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
                        <h1 className="text-2xl font-semibold">{displayName}</h1>
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

            <Card>
              <CardContent className="p-6">
                <div className="space-y-4">
                  {(completionRequested || profile && !profile.is_complete_for_leads) && (
                    <Alert>
                      <AlertDescription>
                        Complete your profile before sending leads. Your name and at least one contact method must be available to agencies.
                      </AlertDescription>
                    </Alert>
                  )}

                  <div className="space-y-1">
                    <h2 className="text-lg font-semibold">Contact details</h2>
                    <p className="text-sm text-muted-foreground">
                      Agencies receive these details when you submit a property inquiry.
                    </p>
                  </div>

                  <form onSubmit={handleSaveProfile} className="grid gap-4 md:grid-cols-2">
                    <div className="space-y-2">
                      <label htmlFor="profile_name" className="text-sm font-medium">
                        Name
                      </label>
                      <Input
                        id="profile_name"
                        value={name}
                        onChange={(e) => setName(e.target.value)}
                        placeholder="Your full name"
                      />
                    </div>

                    <div className="space-y-2">
                      <label htmlFor="profile_phone" className="text-sm font-medium">
                        Phone
                      </label>
                      <Input
                        id="profile_phone"
                        value={phone}
                        onChange={(e) => setPhone(e.target.value)}
                        placeholder="+961..."
                      />
                    </div>

                    <div className="space-y-2 md:col-span-2">
                      <label htmlFor="profile_email" className="text-sm font-medium">
                        Email
                      </label>
                      <div className="flex items-center gap-2 rounded-md border px-3 py-2 text-sm text-muted-foreground">
                        <Mail className="h-4 w-4" />
                        <span>{user?.email}</span>
                      </div>
                    </div>

                    {profile && !profile.is_complete_for_leads && (
                      <div className="md:col-span-2 rounded-md border border-amber-200 bg-amber-50 px-3 py-2 text-sm text-amber-900">
                        Missing for lead submission: {profile.missing_fields.join(", ")}
                      </div>
                    )}

                    {updateProfile.isError && (
                      <div className="md:col-span-2 rounded-md border border-destructive/20 bg-destructive/5 px-3 py-2 text-sm text-destructive">
                        {getApiErrorMessage(updateProfile.error, "generic", {
                          fallback: "We couldn't save your profile. Try again in a moment.",
                        })}
                      </div>
                    )}

                    {updateProfile.isSuccess && (
                      <div className="md:col-span-2 rounded-md border border-green-200 bg-green-50 px-3 py-2 text-sm text-green-800">
                        Profile updated.
                      </div>
                    )}

                    <div className="md:col-span-2 flex items-center justify-between gap-3">
                      <div className="flex items-center gap-2 text-sm text-muted-foreground">
                        <Phone className="h-4 w-4" />
                        <span>Name and one contact method are required for lead submission.</span>
                      </div>
                      <Button type="submit" disabled={updateProfile.isPending}>
                        {updateProfile.isPending ? "Saving..." : "Save profile"}
                      </Button>
                    </div>
                  </form>
                </div>
              </CardContent>
            </Card>
          </div>
        )}
        {activeTab === "saved" && <SavedListingsTab />}
        {activeTab === "inquiries" && <SubmittedInquiriesTab />}
        {activeTab === "viewings" && <ScheduledViewingsTab />}
      </div>
    </div>
  );
}
