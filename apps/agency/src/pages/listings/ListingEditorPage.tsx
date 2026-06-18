import { useCallback, useEffect, useState } from "react";
import { useParams } from "react-router-dom";
import { loadListingDraft } from "@/features/listings/listing-draft-storage";
import { ListingForm } from "@/features/listings/ListingForm";
import { ListingMediaManager } from "@/features/listings/ListingMediaManager";
import { ViewingSlotsManager } from "@/features/listings/ViewingSlotsManager";
import type { ListingFormData } from "@/features/listings/ListingForm";
import type { StagedListingPhoto } from "@/features/listings/listing-media";
import type { DraftViewingSlot } from "@/features/listings/viewing-slot-draft";

export function ListingEditorPage() {
  const { listingId: routeListingId } = useParams();
  const [createdListingId, setCreatedListingId] = useState<string | null>(null);
  const [stagedPhotos, setStagedPhotos] = useState<StagedListingPhoto[]>([]);
  const [stagedViewingSlots, setStagedViewingSlots] = useState<DraftViewingSlot[]>([]);
  const [initialFormData, setInitialFormData] = useState<Partial<ListingFormData> | null>(null);
  const effectiveListingId = routeListingId ?? createdListingId;
  const isCreateMode = !effectiveListingId;
  const [draftHydrated, setDraftHydrated] = useState(!isCreateMode);

  const handleListingCreated = useCallback((id: string) => {
    setCreatedListingId(id);
  }, []);

  useEffect(() => {
    if (!isCreateMode) {
      setDraftHydrated(true);
      return;
    }

    void loadListingDraft().then((draft) => {
      setInitialFormData(draft.formData as Partial<ListingFormData>);
      setStagedPhotos(draft.stagedPhotos);
      setStagedViewingSlots(draft.stagedViewingSlots);
      setDraftHydrated(true);
    });
  }, [isCreateMode]);

  return (
    <div className="space-y-6">
      <div>
        <h2 className="text-2xl font-bold">
          {isCreateMode ? "Create New Listing" : "Edit Listing"}
        </h2>
        <p className="text-muted-foreground">
          {isCreateMode
            ? "Select photos first. They are safety-checked now and uploaded only when you submit."
            : "Review and manage your listing."}
        </p>
      </div>
      <ListingMediaManager
        key={effectiveListingId || "create"}
        listingId={effectiveListingId}
        stagedPhotos={stagedPhotos}
        onStagedPhotosChange={setStagedPhotos}
      />
      <ListingForm
        listingId={effectiveListingId}
        onListingCreated={handleListingCreated}
        stagedPhotos={stagedPhotos}
        onClearStagedPhotos={() => setStagedPhotos([])}
        stagedViewingSlots={stagedViewingSlots}
        onStagedViewingSlotsChange={setStagedViewingSlots}
        initialFormData={draftHydrated ? initialFormData : null}
        draftHydrated={draftHydrated}
      />
      {effectiveListingId ? (
        <ViewingSlotsManager listingId={effectiveListingId} embedded />
      ) : null}
    </div>
  );
}
