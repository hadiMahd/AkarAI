import { vi } from "vitest";
import { screen, waitFor, render } from "@testing-library/react";
import { QueryClient, QueryClientProvider } from "@tanstack/react-query";
import { MemoryRouter } from "react-router-dom";

vi.mock("@/lib/api/client", () => ({
  apiClient: vi.fn(async (endpoint: string) => {
    if (endpoint === "/agency/listings/test-listing/photos") {
      return [
        {
          id: "photo-1",
          listing_id: "test-listing",
          agency_tenant_id: "tenant-1",
          object_key: "listing-photos/originals/tenant-1/test-listing/photo.jpg",
          caption: "Front view",
          alt_text: null,
          display_order: 1,
          status: "accepted",
          content_type: "image/jpeg",
          file_size_bytes: 50000,
          width: 1920,
          height: 1080,
          moderation_label: null,
          moderation_score: null,
          quality_score: null,
          preview_url: "http://localhost:9000/property-media/listing-photos/derivatives/photo-1/thumb.webp?X-Amz-Signature=test",
          created_at: "2024-01-01T00:00:00Z",
          updated_at: "2024-01-01T00:00:00Z",
        },
        {
          id: "photo-2",
          listing_id: "test-listing",
          agency_tenant_id: "tenant-1",
          object_key: "listing-photos/originals/tenant-1/test-listing/photo2.jpg",
          caption: "Kitchen",
          alt_text: null,
          display_order: 2,
          status: "uploaded",
          content_type: "image/jpeg",
          file_size_bytes: 45000,
          width: null,
          height: null,
          moderation_label: null,
          moderation_score: null,
          quality_score: null,
          preview_url: null,
          created_at: "2024-01-01T00:00:00Z",
          updated_at: "2024-01-01T00:00:00Z",
        },
      ];
    }
    if (endpoint === "/agency/listings/test-listing/photos/upload") {
      return { id: "photo-3" };
    }
    if (endpoint === "/agency/listings/test-listing") {
      return { id: "test-listing", title: "Test Listing" };
    }
    return {};
  }),
  restoreSession: vi.fn().mockResolvedValue(false),
  configureAuthInterceptors: vi.fn(),
}));

vi.mock("@/lib/session/auth-session", () => ({
  getSession: () => ({
    accessToken: "token",
    user: { id: "user-1", email: "a@b.com", name: "A", is_active: true, created_at: "", updated_at: "", role: "agency_admin", permissions: [], tenant_id: "tenant-1" },
  }),
  getTenantSession: () => ({ userId: "user-1", tenantId: "tenant-1", role: "agency_admin", permissions: [], isActive: true }),
}));

vi.mock("@/features/auth/useTenantSession", () => ({
  useTenantSession: () => ({
    session: { userId: "user-1", tenantId: "tenant-1", role: "agency_admin", permissions: [], isActive: true },
    isLoading: false,
    error: null,
  }),
}));

import { useState } from "react";
import { ListingMediaManager } from "@/features/listings/ListingMediaManager";
import type { StagedListingPhoto } from "@/features/listings/listing-media";

function TestWrapper() {
  const [staged, setStaged] = useState<StagedListingPhoto[]>([]);
  return (
    <MemoryRouter>
      <QueryClientProvider client={new QueryClient({ defaultOptions: { queries: { retry: false, gcTime: 0 } } })}>
        <ListingMediaManager listingId="test-listing" stagedPhotos={staged} onStagedPhotosChange={setStaged} />
      </QueryClientProvider>
    </MemoryRouter>
  );
}

describe("ListingMediaManager photo preview", () => {
  it("renders image when preview_url is present", async () => {
    render(<TestWrapper />);
    await waitFor(() => {
      const img = screen.getByAltText("Front view") as HTMLImageElement;
      expect(img).toBeInTheDocument();
      expect(img.src).toContain("localhost:9000");
      expect(img.src).toContain("X-Amz-Signature=test");
    });
  });

  it("shows processing placeholder when preview_url is null", async () => {
    render(<TestWrapper />);
    await waitFor(() => {
      expect(screen.getByText("Kitchen")).toBeInTheDocument();
    });
    expect(screen.getByText("Processing preview...")).toBeInTheDocument();
  });

  it("shows failed fallback when image errors", async () => {
    render(<TestWrapper />);
    await waitFor(() => {
      const img = screen.getByAltText("Front view") as HTMLImageElement;
      img.dispatchEvent(new Event("error"));
    });
    await waitFor(() => {
      expect(screen.getByText("Failed to load image")).toBeInTheDocument();
    });
  });
});
