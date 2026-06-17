import { apiClient } from "./client";

export interface User {
  id: string;
  email: string;
  name: string;
  phone?: string | null;
  avatar_url?: string;
  is_active: boolean;
  created_at: string;
  updated_at: string;
}

export interface ActorSummary {
  id: string;
  email: string;
  name?: string | null;
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
    name: response.actor.name || response.actor.email,
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

export interface SavedListingItem {
  id: string;
  user_id: string;
  listing_id: string;
  created_at: string;
  deleted_at: string | null;
}

export interface SavedListingWithDetails extends SavedListingItem {
  listing: {
    id: string;
    title: string;
    description: string | null;
    property_type: string | null;
    listing_purpose: "sale" | "rent" | null;
    price: number | null;
    currency: string | null;
    bedrooms: number | null;
    bathrooms: number | null;
    area_size: number | null;
    area_unit: string | null;
    furnishing: string | null;
    location_text: string | null;
    city: string | null;
    country: string | null;
    status: string;
    thumbnail_url?: string | null;
    created_at: string;
    updated_at: string;
  };
}

export interface PaginatedSavedListingsResponse {
  items: SavedListingItem[];
  page: number;
  page_size: number;
  total: number;
  has_next: boolean;
  has_previous: boolean;
}

export interface PaginatedSavedListingsWithDetailsResponse {
  items: SavedListingWithDetails[];
  page: number;
  page_size: number;
  total: number;
  has_next: boolean;
  has_previous: boolean;
}

export async function listSavedListings(page = 1, pageSize = 20): Promise<PaginatedSavedListingsResponse> {
  return apiClient<PaginatedSavedListingsResponse>("/me/saved-listings", {
    params: { page, page_size: pageSize },
  });
}

export async function listSavedListingsWithDetails(page = 1, pageSize = 20): Promise<PaginatedSavedListingsWithDetailsResponse> {
  return apiClient<PaginatedSavedListingsWithDetailsResponse>("/me/saved-listings/with-details", {
    params: { page, page_size: pageSize },
  });
}

export async function saveListing(listingId: string): Promise<SavedListingItem> {
  return apiClient<SavedListingItem>(`/me/saved-listings/${listingId}`, {
    method: "PUT",
  });
}

export async function unsaveListing(listingId: string): Promise<void> {
  return apiClient<void>(`/me/saved-listings/${listingId}`, {
    method: "DELETE",
  });
}
