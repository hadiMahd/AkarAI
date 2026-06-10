import { useState, useEffect } from "react";
import { useSearchParams } from "react-router-dom";
import { useQuery } from "@tanstack/react-query";
import { apiClient } from "@/lib/api/client";
import { queryKeys } from "@/lib/query/query-client";
import { SearchForm } from "@/features/search/SearchForm";
import { ListingCard } from "@/features/listings/ListingCard";
import { ListingsToolbar } from "@/features/listings/ListingsToolbar";
import { useSavedListings, useSavedListingsFull } from "@/features/saved-listings/useSavedListings";
import { ListSkeleton } from "@/components/LoadingSkeleton";
import { EmptyState } from "@/components/EmptyState";
import { ErrorState } from "@/components/ErrorState";
import { Card, CardContent, CardHeader, CardTitle } from "@/components/ui/card";

interface ListingListItem {
  id: string;
  title: string;
  description: string;
  property_type: string;
  listing_purpose: "sale" | "rent";
  price: number;
  currency: string;
  bedrooms: number | null;
  bathrooms: number | null;
  area_size: number | null;
  area_unit: string;
  city: string;
  address: string;
  status: string;
}

interface ListingsResponse {
  items: ListingListItem[];
  total: number;
  page: number;
  page_size: number;
  has_next: boolean;
  has_previous: boolean;
}

interface SearchFilters {
  q?: string;
  purpose?: string;
  property_type?: string;
  city?: string;
  min_price?: number;
  max_price?: number;
  min_bedrooms?: number;
  min_bathrooms?: number;
  sort_by?: string;
  sort_order?: string;
  page?: number;
  page_size?: number;
}

export function ListingsPage() {
  const [searchParams, setSearchParams] = useSearchParams();
  const [filters, setFilters] = useState<SearchFilters>({});
  const showSaved = searchParams.get("saved") === "true";
  const { savedListings } = useSavedListings();
  const { savedListings: savedListingsFull } = useSavedListingsFull();

  useEffect(() => {
    const newFilters: SearchFilters = {
      q: searchParams.get("q") || undefined,
      purpose: searchParams.get("purpose") || undefined,
      property_type: searchParams.get("property_type") || undefined,
      city: searchParams.get("city") || undefined,
      min_price: searchParams.get("min_price") ? Number(searchParams.get("min_price")) : undefined,
      max_price: searchParams.get("max_price") ? Number(searchParams.get("max_price")) : undefined,
      min_bedrooms: searchParams.get("min_bedrooms") ? Number(searchParams.get("min_bedrooms")) : undefined,
      min_bathrooms: searchParams.get("min_bathrooms") ? Number(searchParams.get("min_bathrooms")) : undefined,
      sort_by: searchParams.get("sort_by") || "created_at",
      sort_order: searchParams.get("sort_order") || "desc",
      page: searchParams.get("page") ? Number(searchParams.get("page")) : 1,
      page_size: 12,
    };
    setFilters(newFilters);
  }, [searchParams]);

  const { data, isLoading, error, refetch } = useQuery<ListingsResponse, Error>({
    queryKey: [...queryKeys.listings.lists(filters as Record<string, unknown>), showSaved, savedListings.length],
    queryFn: async () => {
      if (showSaved) {
        const page = filters.page || 1;
        const pageSize = filters.page_size || 12;
        const start = (page - 1) * pageSize;
        const items: ListingListItem[] = savedListingsFull
          .slice(start, start + pageSize)
          .map((item) => ({
            id: item.listing.id,
            title: item.listing.title,
            description: item.listing.description || "",
            property_type: item.listing.property_type || "",
            listing_purpose: item.listing.listing_purpose || "sale",
            price: item.listing.price || 0,
            currency: item.listing.currency || "USD",
            bedrooms: item.listing.bedrooms,
            bathrooms: item.listing.bathrooms,
            area_size: item.listing.area_size,
            area_unit: item.listing.area_unit || "sqm",
            city: item.listing.city || "",
            address: item.listing.location_text || "",
            status: item.listing.status,
          }));
        return {
          items,
          total: savedListingsFull.length,
          page,
          page_size: pageSize,
          has_next: start + pageSize < savedListingsFull.length,
          has_previous: page > 1,
        };
      }
      const sort =
        filters.sort_by === "price" && filters.sort_order === "asc"
          ? "price_asc"
          : filters.sort_by === "price" && filters.sort_order === "desc"
            ? "price_desc"
            : filters.sort_by === "area_size" && filters.sort_order === "asc"
              ? "area_size_asc"
              : filters.sort_by === "area_size" && filters.sort_order === "desc"
                ? "area_size_desc"
                : "newest";

      return apiClient<ListingsResponse>("/listings", {
        params: {
          location: [filters.q, filters.city].filter(Boolean).join(" ") || undefined,
          listing_purpose: filters.purpose,
          property_type: filters.property_type,
          min_price: filters.min_price,
          max_price: filters.max_price,
          bedrooms: filters.min_bedrooms,
          bathrooms: filters.min_bathrooms,
          sort,
          page: filters.page || 1,
          page_size: filters.page_size || 12,
        },
      });
    },
  });

  const totalPages = data ? Math.max(1, Math.ceil(data.total / data.page_size)) : 1;

  const handleFilterChange = (newFilters: SearchFilters) => {
    const params = new URLSearchParams();
    Object.entries(newFilters).forEach(([key, value]) => {
      if (value !== undefined && value !== null && value !== "") {
        params.set(key, String(value));
      }
    });
    setSearchParams(params);
  };

  return (
    <div className="space-y-6">
      <div>
        <h1 className="text-3xl font-bold mb-2">
          {showSaved ? "Saved Listings" : "Browse Listings"}
        </h1>
        <p className="text-muted-foreground">
          {showSaved
            ? "View your saved properties"
            : "Search and filter available properties"}
        </p>
      </div>

      {!showSaved && (
        <Card>
          <CardHeader>
            <CardTitle>Search & Filter</CardTitle>
          </CardHeader>
          <CardContent>
            <SearchForm filters={filters} onFilterChange={handleFilterChange} />
          </CardContent>
        </Card>
      )}

      {data && data.items.length > 0 && (
        <ListingsToolbar
          total={data.total}
          sortBy={filters.sort_by || "created_at"}
          sortOrder={filters.sort_order || "desc"}
          onSortChange={(sortBy, sortOrder) =>
            handleFilterChange({ ...filters, sort_by: sortBy, sort_order: sortOrder })
          }
        />
      )}

      {isLoading && <ListSkeleton count={6} />}

      {error && (
        <ErrorState
          message="Failed to load listings. Please try again."
          onRetry={() => refetch()}
        />
      )}

      {data && data.items.length === 0 && (
        <EmptyState
          icon="search"
          title={showSaved ? "No saved listings" : "No listings found"}
          description={
            showSaved
              ? "You haven't saved any listings yet."
              : "Try adjusting your search filters."
          }
        />
      )}

      {data && data.items.length > 0 && (
        <>
          <div className="grid md:grid-cols-2 lg:grid-cols-3 gap-6">
            {data.items.map((listing) => (
              <ListingCard key={listing.id} listing={listing} />
            ))}
          </div>

          {totalPages > 1 && (
            <div className="flex items-center justify-center gap-2">
              <button
                onClick={() =>
                  handleFilterChange({ ...filters, page: (filters.page || 1) - 1 })
                }
                disabled={!filters.page || filters.page <= 1}
                className="px-4 py-2 text-sm border rounded-md disabled:opacity-50"
              >
                Previous
              </button>
              <span className="text-sm text-muted-foreground">
                Page {filters.page || 1} of {totalPages}
              </span>
              <button
                onClick={() =>
                  handleFilterChange({ ...filters, page: (filters.page || 1) + 1 })
                }
                disabled={(filters.page || 1) >= totalPages}
                className="px-4 py-2 text-sm border rounded-md disabled:opacity-50"
              >
                Next
              </button>
            </div>
          )}
        </>
      )}
    </div>
  );
}
