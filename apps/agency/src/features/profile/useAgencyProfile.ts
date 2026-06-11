import { useQuery, useMutation, useQueryClient } from "@tanstack/react-query";
import { apiClient } from "@/lib/api/client";
import { queryKeys } from "@/lib/query/query-client";

interface AgencyProfile {
  id: string;
  agency_tenant_id: string;
  display_name: string;
  legal_name: string | null;
  description: string | null;
  phone: string | null;
  email: string | null;
  website_url: string | null;
  address: string | null;
  city: string | null;
  country: string | null;
  status: string;
  created_at: string;
  updated_at: string;
}

interface AgencyProfileUpdate {
  display_name?: string;
  legal_name?: string;
  description?: string;
  phone?: string;
  email?: string;
  website_url?: string;
  address?: string;
  city?: string;
  country?: string;
  status?: string;
}

async function fetchAgencyProfile(): Promise<AgencyProfile> {
  return apiClient<AgencyProfile>("/agencies/me/profile");
}

async function updateAgencyProfile(data: AgencyProfileUpdate): Promise<AgencyProfile> {
  return apiClient<AgencyProfile>("/agencies/me/profile", {
    method: "PUT",
    body: JSON.stringify(data),
  });
}

export function useAgencyProfile() {
  const queryClient = useQueryClient();

  const query = useQuery({
    queryKey: queryKeys.profile.agency,
    queryFn: fetchAgencyProfile,
  });

  const mutation = useMutation({
    mutationFn: updateAgencyProfile,
    onSuccess: () => {
      queryClient.invalidateQueries({ queryKey: queryKeys.profile.agency });
    },
  });

  return {
    profile: query.data,
    isLoading: query.isLoading,
    error: query.error,
    updateProfile: mutation.mutateAsync,
    isUpdating: mutation.isPending,
    updateError: mutation.error,
  };
}

export type { AgencyProfile, AgencyProfileUpdate };
