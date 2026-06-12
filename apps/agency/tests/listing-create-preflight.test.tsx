import { fireEvent, screen, waitFor } from "@testing-library/react";
import { useState } from "react";
import { vi } from "vitest";
import { renderWithProviders } from "./test-utils";
import { ListingMediaManager } from "@/features/listings/ListingMediaManager";
import type { StagedListingPhoto } from "@/features/listings/listing-media";

vi.mock("@/features/listings/useAgencyListings", () => ({
  useListingPhotos: () => ({
    photos: [],
    isLoading: false,
    uploadPhoto: vi.fn(),
    isUploading: false,
    error: null,
  }),
  validateListingPhotoBeforeUpload: vi.fn(async () => ({
    safe: true,
    rejection_reason: null,
    message: "Image is safe to upload.",
    content_type: "image/png",
    file_size_bytes: 128,
    width: 1,
    height: 1,
    moderation_label: "safe",
    moderation_score: 0.04,
  })),
}));

function CreateListingMediaHarness() {
  const [stagedPhotos, setStagedPhotos] = useState<StagedListingPhoto[]>([]);
  return (
    <ListingMediaManager
      listingId={null}
      stagedPhotos={stagedPhotos}
      onStagedPhotosChange={setStagedPhotos}
    />
  );
}

describe("listing create media preflight", () => {
  it("shows a safe-to-upload state after preflight passes", async () => {
    renderWithProviders(<CreateListingMediaHarness />);

    const input = screen.getByLabelText(/select photos/i);
    const file = new File([new Uint8Array([137, 80, 78, 71])], "living-room.png", {
      type: "image/png",
    });

    fireEvent.change(input, { target: { files: [file] } });

    await waitFor(() => {
      expect(screen.getByText(/photos are safe to upload/i)).toBeInTheDocument();
      expect(screen.getByText(/living-room\.png/i)).toBeInTheDocument();
    });
  });
});
