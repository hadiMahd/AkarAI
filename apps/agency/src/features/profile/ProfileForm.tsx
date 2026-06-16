import { useState, useEffect, type FormEvent } from "react";
import { useAgencyProfile, type AgencyProfile } from "./useAgencyProfile";
import { Button } from "@/components/ui/button";
import { Input } from "@/components/ui/input";
import { Label } from "@/components/ui/label";
import { Textarea } from "@/components/ui/textarea";
import { Card, CardContent, CardHeader, CardTitle } from "@/components/ui/card";
import { AlertCircle, CheckCircle2 } from "lucide-react";
import { getApiErrorMessage } from "@/lib/api/errors";

export function ProfileForm() {
  const { profile, isLoading, updateProfile, isUpdating, updateError } = useAgencyProfile();
  const [formData, setFormData] = useState<Partial<AgencyProfile>>({});
  const [successMessage, setSuccessMessage] = useState("");

  useEffect(() => {
    if (profile) {
      setFormData({
        display_name: profile.display_name,
        legal_name: profile.legal_name,
        description: profile.description,
        phone: profile.phone,
        email: profile.email,
        website_url: profile.website_url,
        address: profile.address,
        city: profile.city,
        country: profile.country,
      });
    }
  }, [profile]);

  const handleSubmit = async (e: FormEvent) => {
    e.preventDefault();
    setSuccessMessage("");
    try {
      const updateData: Record<string, string | undefined> = {};
      if (formData.display_name !== undefined) updateData.display_name = formData.display_name ?? undefined;
      if (formData.legal_name !== undefined) updateData.legal_name = formData.legal_name ?? undefined;
      if (formData.description !== undefined) updateData.description = formData.description ?? undefined;
      if (formData.phone !== undefined) updateData.phone = formData.phone ?? undefined;
      if (formData.email !== undefined) updateData.email = formData.email ?? undefined;
      if (formData.website_url !== undefined) updateData.website_url = formData.website_url ?? undefined;
      if (formData.address !== undefined) updateData.address = formData.address ?? undefined;
      if (formData.city !== undefined) updateData.city = formData.city ?? undefined;
      if (formData.country !== undefined) updateData.country = formData.country ?? undefined;
      await updateProfile(updateData);
      setSuccessMessage("Profile updated successfully");
      setTimeout(() => setSuccessMessage(""), 3000);
    } catch {
      // Error is handled by the mutation
    }
  };

  if (isLoading) {
    return (
      <Card>
        <CardHeader>
          <CardTitle>Loading profile...</CardTitle>
        </CardHeader>
        <CardContent>
          <div className="space-y-4">
            {Array.from({ length: 5 }).map((_, i) => (
              <div key={i} className="h-10 bg-muted animate-pulse rounded" />
            ))}
          </div>
        </CardContent>
      </Card>
    );
  }

  return (
    <Card>
      <CardHeader>
        <CardTitle>Agency Profile</CardTitle>
      </CardHeader>
      <CardContent>
        <form onSubmit={handleSubmit} className="space-y-4">
          {successMessage && (
            <div className="flex items-center gap-2 p-3 rounded-md bg-green-50 text-green-700 text-sm">
              <CheckCircle2 className="h-4 w-4" />
              <span>{successMessage}</span>
            </div>
          )}
          {updateError && (
            <div role="alert" className="flex items-center gap-2 p-3 rounded-md bg-destructive/10 text-destructive text-sm">
              <AlertCircle className="h-4 w-4" />
              <span>{getApiErrorMessage(updateError, "agency.profile.update", { fallback: "We couldn't save your changes. Try again in a moment." })}</span>
            </div>
          )}
          <div className="grid gap-4 md:grid-cols-2">
            <div className="space-y-2">
              <Label htmlFor="display_name">Display Name</Label>
              <Input
                id="display_name"
                value={formData.display_name || ""}
                onChange={(e) => setFormData({ ...formData, display_name: e.target.value })}
              />
            </div>
            <div className="space-y-2">
              <Label htmlFor="legal_name">Legal Name</Label>
              <Input
                id="legal_name"
                value={formData.legal_name || ""}
                onChange={(e) => setFormData({ ...formData, legal_name: e.target.value })}
              />
            </div>
            <div className="space-y-2">
              <Label htmlFor="email">Email</Label>
              <Input
                id="email"
                type="email"
                value={formData.email || ""}
                onChange={(e) => setFormData({ ...formData, email: e.target.value })}
              />
            </div>
            <div className="space-y-2">
              <Label htmlFor="phone">Phone</Label>
              <Input
                id="phone"
                value={formData.phone || ""}
                onChange={(e) => setFormData({ ...formData, phone: e.target.value })}
              />
            </div>
            <div className="space-y-2">
              <Label htmlFor="website_url">Website</Label>
              <Input
                id="website_url"
                value={formData.website_url || ""}
                onChange={(e) => setFormData({ ...formData, website_url: e.target.value })}
              />
            </div>
            <div className="space-y-2">
              <Label htmlFor="city">City</Label>
              <Input
                id="city"
                value={formData.city || ""}
                onChange={(e) => setFormData({ ...formData, city: e.target.value })}
              />
            </div>
            <div className="space-y-2">
              <Label htmlFor="country">Country</Label>
              <Input
                id="country"
                value={formData.country || ""}
                onChange={(e) => setFormData({ ...formData, country: e.target.value })}
              />
            </div>
          </div>
          <div className="space-y-2">
            <Label htmlFor="description">Description</Label>
            <Textarea
              id="description"
              value={formData.description || ""}
              onChange={(e) => setFormData({ ...formData, description: e.target.value })}
              rows={3}
            />
          </div>
          <div className="space-y-2">
            <Label htmlFor="address">Address</Label>
            <Input
              id="address"
              value={formData.address || ""}
              onChange={(e) => setFormData({ ...formData, address: e.target.value })}
            />
          </div>
          <Button type="submit" disabled={isUpdating}>
            {isUpdating ? "Saving..." : "Save Changes"}
          </Button>
        </form>
      </CardContent>
    </Card>
  );
}
