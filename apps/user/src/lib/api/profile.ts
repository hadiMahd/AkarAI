import { apiClient } from "./client";

export interface UserProfile {
  id: string;
  email: string;
  name: string | null;
  phone: string | null;
  is_complete_for_leads: boolean;
  missing_fields: string[];
}

export interface UpdateUserProfileRequest {
  name?: string | null;
  phone?: string | null;
}

export async function getMyProfile(): Promise<UserProfile> {
  return apiClient<UserProfile>("/me/profile");
}

export async function updateMyProfile(data: UpdateUserProfileRequest): Promise<UserProfile> {
  return apiClient<UserProfile>("/me/profile", {
    method: "PUT",
    body: JSON.stringify(data),
  });
}
