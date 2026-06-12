import { useState, useEffect } from "react";

interface Listing {
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
}

const STORAGE_KEY = "akarai_comparison_listings";
const MAX_COMPARISON_ITEMS = 4;

export function useSessionComparison() {
  const [comparisonListings, setComparisonListings] = useState<Listing[]>([]);

  useEffect(() => {
    const stored = sessionStorage.getItem(STORAGE_KEY);
    if (stored) {
      try {
        setComparisonListings(JSON.parse(stored));
      } catch {
        setComparisonListings([]);
      }
    }
  }, []);

  const addToComparison = (listing: Listing) => {
    setComparisonListings((prev) => {
      if (prev.some((l) => l.id === listing.id)) {
        return prev;
      }
      if (prev.length >= MAX_COMPARISON_ITEMS) {
        return prev;
      }
      const newListings = [...prev, listing];
      sessionStorage.setItem(STORAGE_KEY, JSON.stringify(newListings));
      return newListings;
    });
  };

  const removeFromComparison = (listingId: string) => {
    setComparisonListings((prev) => {
      const newListings = prev.filter((l) => l.id !== listingId);
      sessionStorage.setItem(STORAGE_KEY, JSON.stringify(newListings));
      return newListings;
    });
  };

  const clearComparison = () => {
    setComparisonListings([]);
    sessionStorage.removeItem(STORAGE_KEY);
  };

  const isInComparison = (listingId: string) => {
    return comparisonListings.some((l) => l.id === listingId);
  };

  const canAddMore = comparisonListings.length < MAX_COMPARISON_ITEMS;

  return {
    comparisonListings,
    addToComparison,
    removeFromComparison,
    clearComparison,
    isInComparison,
    canAddMore,
    count: comparisonListings.length,
    maxItems: MAX_COMPARISON_ITEMS,
  };
}
