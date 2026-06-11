import { ProfileForm } from "@/features/profile/ProfileForm";

export function AgencyProfilePage() {
  return (
    <div className="space-y-6">
      <div>
        <h2 className="text-2xl font-bold">Profile Settings</h2>
        <p className="text-muted-foreground">Manage your agency profile</p>
      </div>
      <ProfileForm />
    </div>
  );
}
