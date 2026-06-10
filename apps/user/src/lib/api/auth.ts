import { apiClient } from "./client";

export interface User {
  id: string;
  email: string;
  name: string;
  avatar_url?: string;
  is_active: boolean;
  created_at: string;
  updated_at: string;
}

export interface ActorSummary {
  id: string;
  email: string;
  role: string;
  permissions: string[];
  tenant_id?: string | null;
  is_active: boolean;
}

export interface AuthTokens {
  access_token: string;
  token_type: string;
  expires_in: number;
  actor: ActorSummary;
}

export interface SignInRequest {
  email: string;
  password: string;
}

export interface SignUpRequest {
  email: string;
  password: string;
  name: string;
}

export interface SignInResponse extends AuthTokens {}

export interface SignUpResponse extends AuthTokens {}

export async function signIn(data: SignInRequest): Promise<SignInResponse> {
  return apiClient<SignInResponse>("/auth/login", {
    method: "POST",
    body: JSON.stringify(data),
  });
}

export async function signUp(data: SignUpRequest): Promise<SignUpResponse> {
  return apiClient<SignUpResponse>("/auth/register", {
    method: "POST",
    body: JSON.stringify(data),
  });
}

export async function getCurrentUser(): Promise<User> {
  const response = await apiClient<{ actor: ActorSummary }>("/auth/me");
  return {
    id: response.actor.id,
    email: response.actor.email,
    name: response.actor.email,
    is_active: response.actor.is_active,
    created_at: "",
    updated_at: "",
  };
}

export async function signOut(): Promise<void> {
  try {
    await apiClient("/auth/logout", {
      method: "POST",
    });
  } catch {
    // ignore
  }
}
