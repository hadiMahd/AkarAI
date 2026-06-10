import { useQuery, useMutation, useQueryClient } from "@tanstack/react-query";
import { useNavigate } from "react-router-dom";
import { signIn as apiSignIn, signUp as apiSignUp, signOut as apiSignOut, getCurrentUser, type SignInRequest, type SignUpRequest, type ActorSummary } from "@/lib/api/auth";
import { setSession, clearSession, getSession } from "@/lib/session/auth-session";
import { queryKeys } from "@/lib/query/query-client";

function actorToUser(actor: ActorSummary) {
  return {
    id: actor.id,
    email: actor.email,
    name: actor.email,
    is_active: actor.is_active,
    created_at: "",
    updated_at: "",
  };
}

export function useAuth() {
  const queryClient = useQueryClient();
  const navigate = useNavigate();
  const { accessToken, user: sessionUser } = getSession();

  const { data: user, isLoading, error } = useQuery({
    queryKey: queryKeys.user.me,
    queryFn: getCurrentUser,
    enabled: !!accessToken,
    initialData: sessionUser || undefined,
    retry: false,
  });

  const signInMutation = useMutation({
    mutationFn: apiSignIn,
    onSuccess: (data) => {
      const user = actorToUser(data.actor);
      setSession(data.access_token, user);
      queryClient.setQueryData(queryKeys.user.me, user);
      navigate("/home");
    },
  });

  const signUpMutation = useMutation({
    mutationFn: apiSignUp,
    onSuccess: (data) => {
      const user = actorToUser(data.actor);
      setSession(data.access_token, user);
      queryClient.setQueryData(queryKeys.user.me, user);
      navigate("/home");
    },
  });

  const signOutMutation = useMutation({
    mutationFn: apiSignOut,
    onSuccess: () => {
      clearSession();
      queryClient.clear();
      navigate("/");
    },
  });

  return {
    user: user || null,
    isLoading,
    error,
    isAuthenticated: !!user,
    signIn: (data: SignInRequest) => signInMutation.mutateAsync(data),
    signUp: (data: SignUpRequest) => signUpMutation.mutateAsync(data),
    logout: () => signOutMutation.mutateAsync(),
    isSigningIn: signInMutation.isPending,
    isSigningUp: signUpMutation.isPending,
    signInError: signInMutation.error,
    signUpError: signUpMutation.error,
  };
}
