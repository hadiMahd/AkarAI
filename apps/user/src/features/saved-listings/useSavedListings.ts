import { useState, useEffect } from "react";

interface Listing {
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

const STORAGE_KEY = "akarai_saved_listings";

export function useSavedListings() {
  const [savedListings, setSavedListings] = useState<Listing[]>([]);

  useEffect(() => {
    const stored = localStorage.getItem(STORAGE_KEY);
    if (stored) {
      try {
        setSavedListings(JSON.parse(stored));
      } catch {
        setSavedListings([]);
      }
    }
  }, []);

  const toggleSaved = (listing: Listing) => {
    setSavedListings((prev) => {
      const isSaved = prev.some((l) => l.id === listing.id);
      const newListings = isSaved
        ? prev.filter((l) => l.id !== listing.id)
        : [...prev, listing];
      localStorage.setItem(STORAGE_KEY, JSON.stringify(newListings));
      return newListings;
    });
  };

  const isSaved = (listingId: string) => {
    return savedListings.some((l) => l.id === listingId);
  };

  const clearAll = () => {
    setSavedListings([]);
    localStorage.removeItem(STORAGE_KEY);
  };

  return {
    savedListings,
    toggleSaved,
    isSaved,
    clearAll,
  };
}