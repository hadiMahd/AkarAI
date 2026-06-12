import { describe, expect, it } from "vitest";
import {
  ALLOWED_LISTING_PHOTO_MIME_TYPES,
  MAX_LISTING_PHOTO_UPLOAD_BYTES,
  validateListingPhotoFile,
} from "@/features/listings/listing-media";

describe("listing media validation", () => {
  it("allows jpeg png and webp uploads", () => {
    for (const type of ALLOWED_LISTING_PHOTO_MIME_TYPES) {
      const file = new File([new Uint8Array([1, 2, 3])], `photo.${type.split("/")[1]}`, { type });
      expect(validateListingPhotoFile(file)).toEqual({ ok: true });
    }
  });

  it("rejects unsupported file types", () => {
    const file = new File([new Uint8Array([1, 2, 3])], "doc.pdf", { type: "application/pdf" });
    expect(validateListingPhotoFile(file)).toEqual({
      ok: false,
      error: "Use a JPEG, PNG, or WebP image.",
    });
  });

  it("rejects oversized uploads", () => {
    const file = new File([new Uint8Array(MAX_LISTING_PHOTO_UPLOAD_BYTES + 1)], "photo.png", {
      type: "image/png",
    });
    expect(validateListingPhotoFile(file)).toEqual({
      ok: false,
      error: `Images must be ${(MAX_LISTING_PHOTO_UPLOAD_BYTES / (1024 * 1024)).toFixed(1)} MB or smaller.`,
    });
  });
});
