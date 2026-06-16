import { useQuery, useMutation, useQueryClient } from "@tanstack/react-query";
import { apiClient } from "@/lib/api/client";
import { queryKeys } from "@/lib/query/query-client";

interface Listing {
  id: string;
  agency_tenant_id: string;
  title: string;
  description: string | null;
  property_type: string | null;
  listing_purpose: string | null;
  price: number | null;
  currency: string | null;
  bedrooms: number | null;
  bathrooms: number | null;
  parking: number | null;
  floor: number | null;
  area_size: number | null;
  area_unit: string | null;
  furnishing: string | null;
  location_text: string | null;
  address: string | null;
  city: string | null;
  country: string | null;
  status: string;
  created_at: string;
  updated_at: string;
}

interface ListingCreateRequest {
  title: string;
  description?: string;
  property_type?: string;
  listing_purpose?: string;
  price?: number;
  currency?: string;
  bedrooms?: number;
  bathrooms?: number;
  parking?: number;
  floor?: number;
  area_size?: number;
  area_unit?: string;
  furnishing?: string;
  location_text?: string;
  address?: string;
  city?: string;
  country?: string;
  status: string;
}

interface ListingPhotoMetadata {
  id: string;
  listing_id: string;
  agency_tenant_id: string;
  object_key: string;
  caption: string | null;
  alt_text: string | null;
  display_order: number;
  status: string;
  content_type: string | null;
  file_size_bytes: number | null;
  width: number | null;
  height: number | null;
  moderation_label: string | null;
  moderation_score: number | null;
  quality_score: number | null;
  preview_url: string | null;
  created_at: string;
  updated_at: string;
}

interface ListingPhotoPreflightResponse {
  safe: boolean;
  rejection_reason: string | null;
  message: string;
  content_type: string | null;
  file_size_bytes: number | null;
  width: number | null;
  height: number | null;
  moderation_label: string | null;
  moderation_score: number | null;
}

interface PaginatedListingsResponse {
  items: Listing[];
  page: number;
  page_size: number;
  total: number;
  has_next: boolean;
  has_previous: boolean;
}

async function fetchListings(page = 1, pageSize = 20): Promise<PaginatedListingsResponse> {
  return apiClient<PaginatedListingsResponse>("/agency/listings", {
    params: { page, page_size: pageSize },
  });
}

async function fetchListing(id: string): Promise<Listing> {
  return apiClient<Listing>(`/agency/listings/${id}`);
}

async function createListing(data: ListingCreateRequest): Promise<Listing> {
  return apiClient<Listing>("/agency/listings", {
    method: "POST",
    body: JSON.stringify(data),
  });
}

async function updateListing(id: string, data: Partial<ListingCreateRequest>): Promise<Listing> {
  return apiClient<Listing>(`/agency/listings/${id}`, {
    method: "PATCH",
    body: JSON.stringify(data),
  });
}

async function fetchListingPhotos(listingId: string): Promise<ListingPhotoMetadata[]> {
  return apiClient<ListingPhotoMetadata[]>(`/agency/listings/${listingId}/photos`);
}

export async function uploadListingPhoto(
  listingId: string,
  formData: FormData
): Promise<ListingPhotoMetadata> {
  return apiClient<ListingPhotoMetadata>(`/agency/listings/${listingId}/photos/upload`, {
    method: "POST",
    body: formData,
  });
}

export async function validateListingPhotoBeforeUpload(
  file: File
): Promise<ListingPhotoPreflightResponse> {
  const formData = new FormData();
  formData.append("file", file);

  return apiClient<ListingPhotoPreflightResponse>("/agency/listings/photos/validate", {
    method: "POST",
    body: formData,
  });
}

async function archiveListing(id: string): Promise<void> {
  return apiClient<void>(`/agency/listings/${id}`, {
    method: "DELETE",
  });
}

export function useAgencyListings() {
  const queryClient = useQueryClient();

  const query = useQuery({
    queryKey: queryKeys.listings.all,
    queryFn: () => fetchListings(),
  });

  const createMutation = useMutation({
    mutationFn: createListing,
    onSuccess: () => {
      queryClient.invalidateQueries({ queryKey: queryKeys.listings.all });
    },
  });

  const archiveMutation = useMutation({
    mutationFn: archiveListing,
    onSuccess: () => {
      queryClient.invalidateQueries({ queryKey: queryKeys.listings.all });
    },
  });

  const publishMutation = useMutation({
    mutationFn: (id: string) => updateListing(id, { status: "active" }),
    onSuccess: (_data, id) => {
      queryClient.invalidateQueries({ queryKey: queryKeys.listings.all });
      queryClient.invalidateQueries({ queryKey: queryKeys.listings.detail(id) });
    },
  });

  return {
    listings: query.data?.items ?? [],
    total: query.data?.total ?? 0,
    isLoading: query.isLoading,
    error: query.error,
    createListing: createMutation.mutateAsync,
    isCreating: createMutation.isPending,
    createError: createMutation.error,
    archiveListing: archiveMutation.mutateAsync,
    isArchiving: archiveMutation.isPending,
    publishListing: publishMutation.mutateAsync,
    isPublishing: publishMutation.isPending,
  };
}

export function useListingDetail(id: string) {
  const queryClient = useQueryClient();

  const query = useQuery({
    queryKey: queryKeys.listings.detail(id),
    queryFn: () => fetchListing(id),
    enabled: !!id,
  });

  const updateMutation = useMutation({
    mutationFn: (data: Partial<ListingCreateRequest>) => updateListing(id, data),
    onSuccess: () => {
      queryClient.invalidateQueries({ queryKey: queryKeys.listings.detail(id) });
      queryClient.invalidateQueries({ queryKey: queryKeys.listings.all });
    },
  });

  return {
    listing: query.data,
    isLoading: query.isLoading,
    error: query.error,
    updateListing: updateMutation.mutateAsync,
    isUpdating: updateMutation.isPending,
    updateError: updateMutation.error,
  };
}

export function useListingPhotos(listingId: string) {
  const queryClient = useQueryClient();

  const query = useQuery({
    queryKey: queryKeys.listings.photos(listingId),
    queryFn: () => fetchListingPhotos(listingId),
    enabled: !!listingId,
  });

  const uploadMutation = useMutation({
    mutationFn: (formData: FormData) => uploadListingPhoto(listingId, formData),
    onSuccess: () => {
      queryClient.invalidateQueries({ queryKey: queryKeys.listings.photos(listingId) });
      queryClient.invalidateQueries({ queryKey: queryKeys.listings.detail(listingId) });
      queryClient.invalidateQueries({ queryKey: queryKeys.listings.all });
    },
  });

  return {
    photos: query.data ?? [],
    isLoading: query.isLoading,
    error: query.error,
    uploadPhoto: uploadMutation.mutateAsync,
    isUploading: uploadMutation.isPending,
  };
}

export type {
  Listing,
  ListingCreateRequest,
  ListingPhotoMetadata,
  ListingPhotoPreflightResponse,
};
