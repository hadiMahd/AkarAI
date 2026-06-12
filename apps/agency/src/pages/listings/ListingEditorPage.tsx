import { useCallback, useState } from "react";
import { useParams } from "react-router-dom";
import { ListingForm } from "@/features/listings/ListingForm";
import { ListingMediaManager } from "@/features/listings/ListingMediaManager";
import type { StagedListingPhoto } from "@/features/listings/listing-media";

export function ListingEditorPage() {
  const { listingId: routeListingId } = useParams();
  const [createdListingId, setCreatedListingId] = useState<string | null>(null);
  const [stagedPhotos, setStagedPhotos] = useState<StagedListingPhoto[]>([]);
  const effectiveListingId = routeListingId ?? createdListingId;
  const isCreateMode = !effectiveListingId;

  const handleListingCreated = useCallback((id: string) => {
    setCreatedListingId(id);
  }, []);

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
      />
    </div>
  );
}
