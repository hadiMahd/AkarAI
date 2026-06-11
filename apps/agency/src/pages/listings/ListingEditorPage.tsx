import { useParams } from "react-router-dom";
import { ListingForm } from "@/features/listings/ListingForm";

export function ListingEditorPage() {
  const { listingId } = useParams();

  return (
    <div className="space-y-6">
      <div>
        <h2 className="text-2xl font-bold">
          {listingId ? "Edit Listing" : "Create New Listing"}
        </h2>
        <p className="text-muted-foreground">
          {listingId ? "Update listing details" : "Create and publish a new listing immediately"}
        </p>
      </div>
      <ListingForm />
    </div>
  );
}
