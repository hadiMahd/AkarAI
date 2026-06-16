import { useState, useEffect, useCallback, useRef } from "react";
import { useSearchParams } from "react-router-dom";
import { useQuery } from "@tanstack/react-query";
import { apiClient } from "@/lib/api/client";
import { getApiErrorMessage } from "@/lib/api/errors";
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
  price: number | null;
  currency: string | null;
  bedrooms: number | null;
  bathrooms: number | null;
  area_size: number | null;
  area_unit: string;
  city: string;
  address: string;
  status: string;
  thumbnail_url?: string | null;
}

interface ListingsResponse {
  items: ListingListItem[];
  total: number;
  page: number;
  page_size: number;
  has_next: boolean;
  has_previous: boolean;
  next_cursor: string | null;
}

interface SearchFilters {
  q?: string;
  purpose?: string;
  property_type?: string;
  city?: string[];
  min_price?: number;
  max_price?: number;
  min_bedrooms?: number;
  min_bathrooms?: number;
  parking?: number;
  floor?: number;
  furnishing?: string;
  min_area_size?: number;
  max_area_size?: number;
  sort_by?: string;
  sort_order?: string;
  page_size?: number;
}

function sortToApi(sortBy: string, sortOrder: string): string {
  if (sortBy === "created_at" && sortOrder === "asc") return "oldest";
  if (sortBy === "created_at" && sortOrder === "desc") return "newest";
  if (sortBy === "price" && sortOrder === "asc") return "price_asc";
  if (sortBy === "price" && sortOrder === "desc") return "price_desc";
  if (sortBy === "area_size" && sortOrder === "asc") return "area_size_asc";
  if (sortBy === "area_size" && sortOrder === "desc") return "area_size_desc";
  return "newest";
}

export function ListingsPage() {
  const [searchParams, setSearchParams] = useSearchParams();
  const [filters, setFilters] = useState<SearchFilters>({});
  const [cursor, setCursor] = useState<string | undefined>(undefined);
  const [prevCursors, setPrevCursors] = useState<string[]>([]);
  const filtersRef = useRef(filters);

  const showSaved = searchParams.get("saved") === "true";
  const { savedListings } = useSavedListings();
  const { savedListings: savedListingsFull } = useSavedListingsFull();

  useEffect(() => {
    const cities = searchParams.getAll("city").filter(Boolean);
    const newFilters: SearchFilters = {
      q: searchParams.get("q") || undefined,
      purpose: searchParams.get("purpose") || undefined,
      property_type: searchParams.get("property_type") || undefined,
      city: cities.length > 0 ? cities : undefined,
      min_price: searchParams.get("min_price") ? Number(searchParams.get("min_price")) : undefined,
      max_price: searchParams.get("max_price") ? Number(searchParams.get("max_price")) : undefined,
      min_bedrooms: searchParams.get("min_bedrooms") ? Number(searchParams.get("min_bedrooms")) : undefined,
      min_bathrooms: searchParams.get("min_bathrooms") ? Number(searchParams.get("min_bathrooms")) : undefined,
      parking: searchParams.get("parking") ? Number(searchParams.get("parking")) : undefined,
      floor: searchParams.get("floor") ? Number(searchParams.get("floor")) : undefined,
      furnishing: searchParams.get("furnishing") || undefined,
      min_area_size: searchParams.get("min_area_size") ? Number(searchParams.get("min_area_size")) : undefined,
      max_area_size: searchParams.get("max_area_size") ? Number(searchParams.get("max_area_size")) : undefined,
      sort_by: searchParams.get("sort_by") || "created_at",
      sort_order: searchParams.get("sort_order") || "desc",
      page_size: 12,
    };
    filtersRef.current = newFilters;
    setFilters(newFilters);
    setCursor(undefined);
    setPrevCursors([]);
  }, [searchParams]);

  const buildApiParams = useCallback(() => {
    const sort = sortToApi(filters.sort_by || "created_at", filters.sort_order || "desc");
    return {
      location: filters.q,
      city: filters.city,
      listing_purpose: filters.purpose,
      property_type: filters.property_type,
      min_price: filters.min_price,
      max_price: filters.max_price,
      bedrooms: filters.min_bedrooms,
      bathrooms: filters.min_bathrooms,
      parking: filters.parking,
      floor: filters.floor,
      furnishing: filters.furnishing,
      min_area_size: filters.min_area_size,
      max_area_size: filters.max_area_size,
      sort,
      page_size: filters.page_size || 12,
    };
  }, [filters]);

  const { data, isLoading, error, refetch } = useQuery<ListingsResponse, Error>({
    queryKey: [
      ...queryKeys.listings.lists(filters as Record<string, unknown>),
      showSaved,
      savedListings.length,
      cursor,
    ],
    staleTime: 0,
    refetchOnMount: "always",
    queryFn: async () => {
      if (showSaved) {
        const pageSize = filters.page_size || 12;
        const start = (prevCursors.length) * pageSize;
        const items: ListingListItem[] = savedListingsFull
          .slice(start, start + pageSize)
          .map((item) => ({
            id: item.listing.id,
            title: item.listing.title,
            description: item.listing.description || "",
            property_type: item.listing.property_type || "",
            listing_purpose: item.listing.listing_purpose || "sale",
            price: item.listing.price ?? null,
            currency: item.listing.currency ?? null,
            bedrooms: item.listing.bedrooms,
            bathrooms: item.listing.bathrooms,
            area_size: item.listing.area_size,
            area_unit: item.listing.area_unit || "sqm",
            city: item.listing.city || "",
            address: item.listing.location_text || "",
            status: item.listing.status,
            thumbnail_url: item.listing.thumbnail_url,
          }));
        return {
          items,
          total: savedListingsFull.length,
          page: prevCursors.length + 1,
          page_size: pageSize,
          has_next: start + pageSize < savedListingsFull.length,
          has_previous: prevCursors.length > 0,
          next_cursor: null,
        };
      }

      const params: Record<
        string,
        string | number | boolean | Array<string | number | boolean> | undefined
      > = { ...buildApiParams() };
      if (cursor) {
        params.cursor = cursor;
      }

      return apiClient<ListingsResponse>("/listings", { params });
    },
  });

  const handleFilterChange = (newFilters: SearchFilters) => {
    const params = new URLSearchParams();
    Object.entries(newFilters).forEach(([key, value]) => {
      if (value !== undefined && value !== null && value !== "") {
        if (Array.isArray(value)) {
          value
            .filter((item) => item !== "")
            .forEach((item) => params.append(key, String(item)));
        } else {
          params.set(key, String(value));
        }
      }
    });
    setSearchParams(params);
  };

  const handleNextPage = useCallback(() => {
    if (data?.next_cursor) {
      setPrevCursors((prev) => [...prev, cursor ?? ""]);
      setCursor(data.next_cursor);
    }
  }, [data, cursor]);

  const handlePrevPage = useCallback(() => {
    const prev = prevCursors[prevCursors.length - 1];
    if (prev !== undefined) {
      setPrevCursors((p) => p.slice(0, -1));
      setCursor(prev || undefined);
    }
  }, [prevCursors]);

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
            <SearchForm
              filters={filters}
              onFilterChange={handleFilterChange}
              onFiltersChange={(partialFilters) =>
                handleFilterChange({ ...filters, ...partialFilters } as SearchFilters)
              }
            />
          </CardContent>
        </Card>
      )}

      {data && data.items.length > 0 && (
        <ListingsToolbar
          total={showSaved ? data.total : undefined}
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
          message={getApiErrorMessage(error, "listing.load", {
            fallback: "We couldn't load listings. Try refreshing the page.",
          })}
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

          <div className="flex items-center justify-center gap-2">
            <button
              onClick={handlePrevPage}
              disabled={prevCursors.length === 0}
              className="px-4 py-2 text-sm border rounded-md disabled:opacity-50"
            >
              Previous
            </button>
            <button
              onClick={handleNextPage}
              disabled={!data.has_next || !data.next_cursor}
              className="px-4 py-2 text-sm border rounded-md disabled:opacity-50"
            >
              Next
            </button>
          </div>
        </>
      )}
    </div>
  );
}
