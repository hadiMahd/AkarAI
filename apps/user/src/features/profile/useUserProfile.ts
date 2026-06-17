import { useMutation, useQuery, useQueryClient } from "@tanstack/react-query";

import { queryKeys } from "@/lib/query/query-client";
import { getSession, setSession } from "@/lib/session/auth-session";
import { getMyProfile, updateMyProfile, type UpdateUserProfileRequest } from "@/lib/api/profile";

export function useUserProfile() {
  return useQuery({
    queryKey: queryKeys.user.profile,
    queryFn: getMyProfile,
  });
}

export function useUpdateUserProfile() {
  const queryClient = useQueryClient();

  return useMutation({
    mutationFn: (data: UpdateUserProfileRequest) => updateMyProfile(data),
    onSuccess: (profile) => {
      queryClient.setQueryData(queryKeys.user.profile, profile);

      const session = getSession();
      if (session.accessToken && session.user) {
        setSession(session.accessToken, {
          ...session.user,
          name: profile.name || session.user.email,
          phone: profile.phone,
        });
        queryClient.setQueryData(queryKeys.user.me, {
          ...session.user,
          name: profile.name || session.user.email,
          phone: profile.phone,
        });
      }
    },
  });
}
