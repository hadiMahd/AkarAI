import { useCallback, useMemo } from "react";
import { useSearchParams } from "react-router-dom";

export interface SearchFilters {
  q?: string;
  purpose?: string;
  property_type?: string;
  city?: string;
  min_price?: number;
  max_price?: number;
  bedrooms?: number;
  bathrooms?: number;
  furnishing?: string;
  min_area_size?: number;
  max_area_size?: number;
  sort?: string;
  page?: number;
  page_size?: number;
}

export function useSearchFilters() {
  const [searchParams, setSearchParams] = useSearchParams();

  const filters = useMemo<SearchFilters>(() => {
    const params = Object.fromEntries(searchParams.entries());
    return {
      q: params.q || undefined,
      purpose: params.purpose || undefined,
      property_type: params.property_type || undefined,
      city: params.city || undefined,
      min_price: params.min_price ? Number(params.min_price) : undefined,
      max_price: params.max_price ? Number(params.max_price) : undefined,
      bedrooms: params.bedrooms ? Number(params.bedrooms) : undefined,
      bathrooms: params.bathrooms ? Number(params.bathrooms) : undefined,
      furnishing: params.furnishing || undefined,
      min_area_size: params.min_area_size ? Number(params.min_area_size) : undefined,
      max_area_size: params.max_area_size ? Number(params.max_area_size) : undefined,
      sort: params.sort || "newest",
      page: params.page ? Number(params.page) : 1,
      page_size: params.page_size ? Number(params.page_size) : 20,
    };
  }, [searchParams]);

  const setFilters = useCallback(
    (newFilters: Partial<SearchFilters>) => {
      const params = new URLSearchParams();
      const merged = { ...filters, ...newFilters };

      Object.entries(merged).forEach(([key, value]) => {
        if (value !== undefined && value !== null && value !== "") {
          params.set(key, String(value));
        }
      });

      setSearchParams(params);
    },
    [filters, setSearchParams]
  );

  const resetFilters = useCallback(() => {
    setSearchParams(new URLSearchParams());
  }, [setSearchParams]);

  return { filters, setFilters, resetFilters };
}
