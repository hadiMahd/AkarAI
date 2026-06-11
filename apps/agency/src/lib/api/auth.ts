export interface AgencyUser {
  id: string;
  email: string;
  name: string;
  is_active: boolean;
  created_at: string;
  updated_at: string;
  role?: string;
  permissions?: string[];
  tenant_id?: string | null;
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

export interface TenantContextResponse {
  actor_id: string;
  role: string;
  permissions: string[];
  tenant_id?: string | null;
  membership_id?: string | null;
  is_platform_actor: boolean;
}

export interface SignInRequest {
  email: string;
  password: string;
}

export interface SignInResponse extends AuthTokens {}

import { apiClient } from "./client";

export async function signIn(data: SignInRequest): Promise<SignInResponse> {
  return apiClient<SignInResponse>("/auth/login", {
    method: "POST",
    body: JSON.stringify(data),
  });
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

export async function getCurrentUser(): Promise<AgencyUser> {
  const response = await apiClient<{ actor: ActorSummary }>("/auth/me");
  return {
    id: response.actor.id,
    email: response.actor.email,
    name: response.actor.email,
    is_active: response.actor.is_active,
    created_at: "",
    updated_at: "",
    role: response.actor.role,
    permissions: response.actor.permissions,
    tenant_id: response.actor.tenant_id,
  };
}

export async function getTenantContext(): Promise<TenantContextResponse> {
  return apiClient<TenantContextResponse>("/tenant/context");
}
