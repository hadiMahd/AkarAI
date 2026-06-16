import { useEffect, useRef, useState, type FormEvent } from "react";
import { AlertCircle, CheckCircle2, ShieldCheck } from "lucide-react";
import { useAgencyListings, useListingDetail, uploadListingPhoto } from "./useAgencyListings";
import { useListingCities } from "./useListingCities";
import type { StagedListingPhoto } from "./listing-media";
import { ListingAiWorkflow } from "./ListingAiWorkflow";
import { Button } from "@/components/ui/button";
import { Input } from "@/components/ui/input";
import { Label } from "@/components/ui/label";
import { Textarea } from "@/components/ui/textarea";
import { getApiErrorMessage } from "@/lib/api/errors";

import { Card, CardContent, CardHeader, CardTitle } from "@/components/ui/card";

type ListingFormData = {
  title: string;
  description: string;
  property_type: string;
  listing_purpose: string;
  price: string;
  currency: string;
  bedrooms: string;
  bathrooms: string;
  parking: string;
  floor: string;
  area_size: string;
  area_unit: string;
  furnishing: string;
  location_text: string;
  address: string;
  city: string;
  country: string;
};

const EMPTY_FORM: ListingFormData = {
  title: "",
  description: "",
  property_type: "",
  listing_purpose: "rent",
  price: "",
  currency: "USD",
  bedrooms: "",
  bathrooms: "",
  parking: "",
  floor: "",
  area_size: "",
  area_unit: "sqft",
  furnishing: "",
  location_text: "",
  address: "",
  city: "",
  country: "",
};

interface ListingFormProps {
  listingId?: string | null;
  onListingCreated?: (id: string) => void;
  stagedPhotos?: StagedListingPhoto[];
  onClearStagedPhotos?: () => void;
}

export function ListingForm({
  listingId = null,
  onListingCreated,
  stagedPhotos = [],
  onClearStagedPhotos,
}: ListingFormProps) {
  const { createListing, isCreating, createError, publishListing, isPublishing } = useAgencyListings();
  const {
    listing,
    isLoading: isListingLoading,
    error: listingError,
    updateListing,
    isUpdating,
    updateError,
  } = useListingDetail(listingId || "");
  const { data: cityOptions = [], isLoading: isCitiesLoading } = useListingCities();

  const [formData, setFormData] = useState<ListingFormData>(EMPTY_FORM);
  const [successMessage, setSuccessMessage] = useState("");
  const [localError, setLocalError] = useState("");
  const seededListingId = useRef<string | null>(null);

  useEffect(() => {
    if (!listing || listing.id === seededListingId.current) {
      return;
    }

    setFormData({
      title: listing.title ?? "",
      description: listing.description ?? "",
      property_type: listing.property_type ?? "",
      listing_purpose: listing.listing_purpose ?? "rent",
      price: listing.price ? String(listing.price) : "",
      currency: listing.currency ?? "USD",
      bedrooms: listing.bedrooms ? String(listing.bedrooms) : "",
      bathrooms: listing.bathrooms ? String(listing.bathrooms) : "",
      parking: listing.parking ? String(listing.parking) : "",
      floor: listing.floor ? String(listing.floor) : "",
      area_size: listing.area_size ? String(listing.area_size) : "",
      area_unit: listing.area_unit ?? "sqft",
      furnishing: listing.furnishing ?? "",
      location_text: listing.location_text ?? "",
      address: listing.address ?? "",
      city: listing.city ?? "",
      country: listing.country ?? "",
    });
    seededListingId.current = listing.id;
  }, [listing]);

  const buildPayload = () => ({
    ...formData,
    price: formData.price ? parseFloat(formData.price) : undefined,
    bedrooms: formData.bedrooms ? parseInt(formData.bedrooms) : undefined,
    bathrooms: formData.bathrooms ? parseInt(formData.bathrooms) : undefined,
    parking: formData.parking ? parseInt(formData.parking) : undefined,
    floor: formData.floor ? parseInt(formData.floor) : undefined,
    area_size: formData.area_size ? parseFloat(formData.area_size) : undefined,
  });

  const handleSubmit = async (e: FormEvent) => {
    e.preventDefault();
    setSuccessMessage("");
    setLocalError("");

    try {
      const payload = buildPayload();

      if (listingId) {
        await updateListing(payload);
        setSuccessMessage("Listing updated.");
        return;
      }

      const pendingPhotos = stagedPhotos.filter((photo) => photo.status === "checking");
      const rejectedPhotos = stagedPhotos.filter((photo) => photo.status === "rejected");
      if (pendingPhotos.length > 0) {
        setLocalError("Wait for all selected photos to finish the safety check.");
        return;
      }
      if (rejectedPhotos.length > 0) {
        setLocalError("Remove rejected photos before submitting the listing.");
        return;
      }

      const safePhotos = stagedPhotos.filter((photo) => photo.status === "safe");
      const created = await createListing({ ...payload, status: "inactive" });
      onListingCreated?.(created.id);

      if (safePhotos.length > 0) {
        await Promise.all(
          safePhotos.map((photo, i) => {
            const formData = new FormData();
            formData.append("file", photo.file);
            formData.append("display_order", String(i));
            return uploadListingPhoto(created.id, formData);
          })
        );
      }

      await publishListing(created.id);
      onClearStagedPhotos?.();
      setSuccessMessage(`Listing submitted with ${safePhotos.length} photo(s).`);
    } catch {
      // handled by mutation state
    }
  };

  const handlePublish = async () => {
    if (!listingId) return;
    try {
      await publishListing(listingId);
      setSuccessMessage("Listing published and is now live.");
    } catch {
      // handled by mutation state
    }
  };

  const isEditing = Boolean(listingId);
  const showSeparatePublishButton = isEditing && listing && listing.status !== "active";
  const submitLabel = isEditing ? "Save Changes" : "Submit Listing";
  const isSaving = isCreating || isUpdating;
  const availableCities = Array.from(
    new Set([...(cityOptions ?? []), ...(formData.city ? [formData.city] : [])]),
  ).sort((left, right) => left.localeCompare(right));

  return (
    <Card>
      <CardHeader>
        <CardTitle>{isEditing ? "Edit Listing Details" : "Listing Details"}</CardTitle>
      </CardHeader>
      <CardContent>
        {listingError ? (
          <div role="alert" className="mb-4 flex items-center gap-2 rounded-md bg-destructive/10 p-3 text-sm text-destructive">
            <AlertCircle className="h-4 w-4" />
            <span>{getApiErrorMessage(listingError, "listing.load", { fallback: "We couldn't load this listing." })}</span>
          </div>
        ) : null}

        <form onSubmit={handleSubmit} className="space-y-4">
          {successMessage && (
            <div className="flex items-center gap-2 rounded-md bg-green-50 p-3 text-sm text-green-700">
              <CheckCircle2 className="h-4 w-4" />
              <span>{successMessage}</span>
            </div>
          )}
          {localError && (
            <div role="alert" className="flex items-center gap-2 rounded-md bg-destructive/10 p-3 text-sm text-destructive">
              <AlertCircle className="h-4 w-4" />
              <span>{localError}</span>
            </div>
          )}
          {createError && !isEditing && (
            <div role="alert" className="flex items-center gap-2 rounded-md bg-destructive/10 p-3 text-sm text-destructive">
              <AlertCircle className="h-4 w-4" />
              <span>{getApiErrorMessage(createError, "listing.create", { fallback: "We couldn't create this listing. Try again in a moment." })}</span>
            </div>
          )}
          {updateError && (
            <div role="alert" className="flex items-center gap-2 rounded-md bg-destructive/10 p-3 text-sm text-destructive">
              <AlertCircle className="h-4 w-4" />
              <span>{getApiErrorMessage(updateError, "listing.update", { fallback: "We couldn't save your changes. Try again in a moment." })}</span>
            </div>
          )}

          <ListingAiWorkflow
            listingContext={buildPayload()}
            hasFormContext={Boolean(formData.title.trim() && formData.city.trim() && formData.price.trim())}
            onApplyDraft={(draft) => {
              setFormData((current) => ({
                ...current,
                title: draft.title,
                description: draft.description,
              }));
            }}
            onApplyExtractedSpecs={(specs) => {
              setFormData((current) => ({
                ...current,
                property_type: specs.property_type ?? current.property_type,
                listing_purpose: specs.listing_purpose ?? current.listing_purpose,
                bedrooms: specs.bedrooms != null ? String(specs.bedrooms) : current.bedrooms,
                bathrooms: specs.bathrooms != null ? String(specs.bathrooms) : current.bathrooms,
                parking: specs.parking != null ? String(specs.parking) : current.parking,
                floor: specs.floor != null ? String(specs.floor) : current.floor,
                area_size: specs.area_size != null ? String(specs.area_size) : current.area_size,
                area_unit: specs.area_unit ?? current.area_unit,
                furnishing: specs.furnishing ?? current.furnishing,
                location_text: specs.location_text ?? current.location_text,
                address: specs.address ?? current.address,
                city: specs.city ?? current.city,
              }));
            }}
          />

          <div className="grid gap-4 md:grid-cols-2">
            <div className="space-y-2 md:col-span-2">
              <Label htmlFor="title">Title</Label>
              <Input
                id="title"
                value={formData.title}
                onChange={(e) => setFormData({ ...formData, title: e.target.value })}
                required
                disabled={isListingLoading}
              />
            </div>
            <div className="space-y-2 md:col-span-2">
              <Label htmlFor="description">Description</Label>
              <Textarea
                id="description"
                value={formData.description}
                onChange={(e) => setFormData({ ...formData, description: e.target.value })}
                rows={3}
                disabled={isListingLoading}
              />
            </div>
            <div className="space-y-2">
              <Label htmlFor="property_type">Property Type</Label>
              <Input
                id="property_type"
                value={formData.property_type}
                onChange={(e) => setFormData({ ...formData, property_type: e.target.value })}
                placeholder="Apartment, House, etc."
                disabled={isListingLoading}
              />
            </div>
            <div className="space-y-2">
              <Label htmlFor="listing_purpose">Purpose</Label>
              <select
                id="listing_purpose"
                value={formData.listing_purpose}
                onChange={(e) => setFormData({ ...formData, listing_purpose: e.target.value })}
                className="flex h-10 w-full rounded-md border border-input bg-background px-3 py-2 text-sm"
                disabled={isListingLoading}
              >
                <option value="rent">Rent</option>
                <option value="sale">Sale</option>
              </select>
            </div>
            <div className="space-y-2">
              <Label htmlFor="price">Price</Label>
              <Input
                id="price"
                type="number"
                value={formData.price}
                onChange={(e) => setFormData({ ...formData, price: e.target.value })}
                disabled={isListingLoading}
              />
            </div>
            <div className="space-y-2">
              <Label htmlFor="currency">Currency</Label>
              <Input
                id="currency"
                value={formData.currency}
                onChange={(e) => setFormData({ ...formData, currency: e.target.value })}
                disabled={isListingLoading}
              />
            </div>
            <div className="space-y-2">
              <Label htmlFor="bedrooms">Bedrooms</Label>
              <Input
                id="bedrooms"
                type="number"
                value={formData.bedrooms}
                onChange={(e) => setFormData({ ...formData, bedrooms: e.target.value })}
                disabled={isListingLoading}
              />
            </div>
            <div className="space-y-2">
              <Label htmlFor="bathrooms">Bathrooms</Label>
              <Input
                id="bathrooms"
                type="number"
                value={formData.bathrooms}
                onChange={(e) => setFormData({ ...formData, bathrooms: e.target.value })}
                disabled={isListingLoading}
              />
            </div>
            <div className="space-y-2">
              <Label htmlFor="parking">Parking</Label>
              <Input
                id="parking"
                type="number"
                value={formData.parking}
                onChange={(e) => setFormData({ ...formData, parking: e.target.value })}
                disabled={isListingLoading}
              />
            </div>
            <div className="space-y-2">
              <Label htmlFor="floor">Floor</Label>
              <Input
                id="floor"
                type="number"
                value={formData.floor}
                onChange={(e) => setFormData({ ...formData, floor: e.target.value })}
                disabled={isListingLoading}
              />
            </div>
            <div className="space-y-2">
              <Label htmlFor="area_size">Area Size</Label>
              <Input
                id="area_size"
                type="number"
                value={formData.area_size}
                onChange={(e) => setFormData({ ...formData, area_size: e.target.value })}
                disabled={isListingLoading}
              />
            </div>
            <div className="space-y-2">
              <Label htmlFor="area_unit">Area Unit</Label>
              <Input
                id="area_unit"
                value={formData.area_unit}
                onChange={(e) => setFormData({ ...formData, area_unit: e.target.value })}
                disabled={isListingLoading}
              />
            </div>
            <div className="space-y-2 md:col-span-2">
              <Label htmlFor="furnishing">Furnishing</Label>
              <Input
                id="furnishing"
                value={formData.furnishing}
                onChange={(e) => setFormData({ ...formData, furnishing: e.target.value })}
                disabled={isListingLoading}
              />
            </div>
            <div className="space-y-2 md:col-span-2">
              <Label htmlFor="location_text">Location</Label>
              <Input
                id="location_text"
                value={formData.location_text}
                onChange={(e) => setFormData({ ...formData, location_text: e.target.value })}
                disabled={isListingLoading}
              />
            </div>
            <div className="space-y-2">
              <Label htmlFor="address">Address</Label>
              <Input
                id="address"
                value={formData.address}
                onChange={(e) => setFormData({ ...formData, address: e.target.value })}
                disabled={isListingLoading}
              />
            </div>
            <div className="space-y-2">
              <Label htmlFor="city">City</Label>
              <select
                id="city"
                value={formData.city}
                onChange={(e) => setFormData({ ...formData, city: e.target.value })}
                className="flex h-10 w-full rounded-md border border-input bg-background px-3 py-2 text-sm"
                disabled={isListingLoading || (isCitiesLoading && availableCities.length === 0)}
              >
                <option value="">
                  {isCitiesLoading && availableCities.length === 0 ? "Loading cities..." : "Select a city"}
                </option>
                {availableCities.map((city) => (
                  <option key={city} value={city}>
                    {city}
                  </option>
                ))}
              </select>
            </div>
            <div className="space-y-2">
              <Label htmlFor="country">Country</Label>
              <Input
                id="country"
                value={formData.country}
                onChange={(e) => setFormData({ ...formData, country: e.target.value })}
                disabled={isListingLoading}
              />
            </div>
          </div>

          <div className="flex flex-wrap items-center gap-3 pt-2">
            <Button type="submit" disabled={isSaving || isListingLoading}>
              {isSaving ? "Saving..." : submitLabel}
            </Button>
            {showSeparatePublishButton && (
              <Button type="button" variant="outline" onClick={handlePublish} disabled={isPublishing}>
                <ShieldCheck className="mr-2 h-4 w-4" />
                {isPublishing ? "Publishing..." : "Publish Listing"}
              </Button>
            )}
          </div>
        </form>
      </CardContent>
    </Card>
  );
}
