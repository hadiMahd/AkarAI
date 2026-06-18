import { useEffect, useRef, useState, type FormEvent } from "react";
import { AlertCircle, Calendar, CheckCircle2, ShieldCheck, Trash2 } from "lucide-react";
import { useAgencyListings, useListingDetail, uploadListingPhoto } from "./useAgencyListings";
import { useListingCities } from "./useListingCities";
import type { StagedListingPhoto } from "./listing-media";
import type { DraftViewingSlot } from "./viewing-slot-draft";
import { clearListingDraft, saveListingDraft } from "./listing-draft-storage";
import { ListingAiWorkflow } from "./ListingAiWorkflow";
import { createViewingSlot } from "./useViewingSlots";
import { Button } from "@/components/ui/button";
import { Input } from "@/components/ui/input";
import { Label } from "@/components/ui/label";
import { Textarea } from "@/components/ui/textarea";
import { getApiErrorMessage } from "@/lib/api/errors";

import { Card, CardContent, CardHeader, CardTitle } from "@/components/ui/card";

export type ListingFormData = {
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

function minViewingDateTimeLocal() {
  const minimum = new Date(Date.now() + 5 * 60 * 1000);
  minimum.setSeconds(0, 0);
  return minimum.toISOString().slice(0, 16);
}

interface ListingFormProps {
  listingId?: string | null;
  onListingCreated?: (id: string) => void;
  stagedPhotos?: StagedListingPhoto[];
  onClearStagedPhotos?: () => void;
  stagedViewingSlots?: DraftViewingSlot[];
  onStagedViewingSlotsChange?: (slots: DraftViewingSlot[]) => void;
  initialFormData?: Partial<ListingFormData> | null;
  draftHydrated?: boolean;
}

export function ListingForm({
  listingId = null,
  onListingCreated,
  stagedPhotos = [],
  onClearStagedPhotos,
  stagedViewingSlots = [],
  onStagedViewingSlotsChange,
  initialFormData = null,
  draftHydrated = true,
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
  const [slotDraft, setSlotDraft] = useState<DraftViewingSlot>({
    id: "",
    starts_at: "",
    ends_at: "",
    capacity: "1",
  });
  const seededListingId = useRef<string | null>(null);
  const restoredDraftApplied = useRef(false);

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

  useEffect(() => {
    if (listingId || restoredDraftApplied.current || !initialFormData) {
      return;
    }

    setFormData((current) => ({
      ...current,
      ...initialFormData,
    }));
    restoredDraftApplied.current = true;
  }, [initialFormData, listingId]);

  useEffect(() => {
    if (listingId || !draftHydrated) {
      return;
    }

    const timeout = window.setTimeout(() => {
      void saveListingDraft(formData, stagedPhotos, stagedViewingSlots);
    }, 300);

    return () => window.clearTimeout(timeout);
  }, [draftHydrated, formData, listingId, stagedPhotos, stagedViewingSlots]);

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

      if (stagedViewingSlots.length > 0) {
        await Promise.all(
          stagedViewingSlots.map((slot) =>
            createViewingSlot(created.id, {
              starts_at: new Date(slot.starts_at).toISOString(),
              ends_at: new Date(slot.ends_at).toISOString(),
              capacity: parseInt(slot.capacity, 10),
            }),
          ),
        );
      }

      await publishListing(created.id);
      await clearListingDraft();
      onClearStagedPhotos?.();
      onStagedViewingSlotsChange?.([]);
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
  const minimumSlotStart = minViewingDateTimeLocal();
  const showSeparatePublishButton = isEditing && listing && listing.status !== "active";
  const submitLabel = isEditing ? "Save Changes" : "Submit Listing";
  const isSaving = isCreating || isUpdating;
  const availableCities = Array.from(
    new Set([...(cityOptions ?? []), ...(formData.city ? [formData.city] : [])]),
  ).sort((left, right) => left.localeCompare(right));

  const handleDiscardDraft = async () => {
    setFormData(EMPTY_FORM);
    setSuccessMessage("");
    setLocalError("");
    setSlotDraft({ id: "", starts_at: "", ends_at: "", capacity: "1" });
    onClearStagedPhotos?.();
    onStagedViewingSlotsChange?.([]);
    await clearListingDraft();
  };

  const handleAddViewingSlot = () => {
    if (!slotDraft.starts_at || !slotDraft.ends_at) {
      setLocalError("Add both a start and end time for the viewing slot.");
      return;
    }

    if (new Date(slotDraft.starts_at) >= new Date(slotDraft.ends_at)) {
      setLocalError("Viewing slot end time must be after the start time.");
      return;
    }

    if (new Date(slotDraft.starts_at).getTime() < Date.now() + 5 * 60 * 1000) {
      setLocalError("Viewing slot start time must be at least 5 minutes in the future.");
      return;
    }

    if (parseInt(slotDraft.capacity, 10) < 1) {
      setLocalError("Viewing slot capacity must be at least 1.");
      return;
    }

    onStagedViewingSlotsChange?.([
      ...stagedViewingSlots,
      {
        ...slotDraft,
        id:
          typeof crypto !== "undefined" && typeof crypto.randomUUID === "function"
            ? crypto.randomUUID()
            : `${Date.now()}-${Math.random().toString(16).slice(2)}`,
      },
    ]);
    setLocalError("");
    setSlotDraft({ id: "", starts_at: "", ends_at: "", capacity: "1" });
  };

  const handleRemoveViewingSlot = (slotId: string) => {
    onStagedViewingSlotsChange?.(stagedViewingSlots.filter((slot) => slot.id !== slotId));
  };

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

          {!isEditing ? (
            <div className="space-y-4 rounded-lg border p-4">
              <div className="flex items-start justify-between gap-4">
                <div>
                  <h3 className="flex items-center gap-2 text-base font-semibold">
                    <Calendar className="h-4 w-4" />
                    Viewing Availability
                  </h3>
                  <p className="text-sm text-muted-foreground">
                    Add the dates and times buyers can book. They will be saved when you submit the listing.
                  </p>
                </div>
              </div>

              <div className="grid gap-4 md:grid-cols-3">
                <div className="space-y-2">
                  <Label htmlFor="slot_starts_at">Start Time</Label>
                  <Input
                    id="slot_starts_at"
                    type="datetime-local"
                    value={slotDraft.starts_at}
                    onChange={(e) => setSlotDraft({ ...slotDraft, starts_at: e.target.value })}
                    min={minimumSlotStart}
                  />
                </div>
                <div className="space-y-2">
                  <Label htmlFor="slot_ends_at">End Time</Label>
                  <Input
                    id="slot_ends_at"
                    type="datetime-local"
                    value={slotDraft.ends_at}
                    onChange={(e) => setSlotDraft({ ...slotDraft, ends_at: e.target.value })}
                    min={slotDraft.starts_at || minimumSlotStart}
                  />
                </div>
                <div className="space-y-2">
                  <Label htmlFor="slot_capacity">Capacity</Label>
                  <Input
                    id="slot_capacity"
                    type="number"
                    min="1"
                    value={slotDraft.capacity}
                    onChange={(e) => setSlotDraft({ ...slotDraft, capacity: e.target.value })}
                  />
                </div>
              </div>

              <Button type="button" variant="outline" onClick={handleAddViewingSlot}>
                Add Viewing Date
              </Button>

              {stagedViewingSlots.length === 0 ? (
                <p className="text-sm text-muted-foreground">
                  No viewing dates added yet.
                </p>
              ) : (
                <div className="space-y-2">
                  {stagedViewingSlots.map((slot) => (
                    <div
                      key={slot.id}
                      className="flex items-center justify-between gap-3 rounded-md border px-3 py-2 text-sm"
                    >
                      <div className="space-y-1">
                        <p>
                          {new Date(slot.starts_at).toLocaleString()} to{" "}
                          {new Date(slot.ends_at).toLocaleString()}
                        </p>
                        <p className="text-muted-foreground">Capacity: {slot.capacity}</p>
                      </div>
                      <Button
                        type="button"
                        variant="ghost"
                        size="sm"
                        onClick={() => handleRemoveViewingSlot(slot.id)}
                        className="text-destructive hover:text-destructive"
                      >
                        <Trash2 className="h-4 w-4" />
                      </Button>
                    </div>
                  ))}
                </div>
              )}
            </div>
          ) : null}

          <div className="flex flex-wrap items-center gap-3 pt-2">
            <Button type="submit" disabled={isSaving || isListingLoading}>
              {isSaving ? "Saving..." : submitLabel}
            </Button>
            {!isEditing ? (
              <Button type="button" variant="outline" onClick={() => void handleDiscardDraft()}>
                Discard Draft
              </Button>
            ) : null}
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
