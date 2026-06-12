const MAX_LISTING_PHOTO_UPLOAD_BYTES = 10 * 1024 * 1024;
const ALLOWED_LISTING_PHOTO_MIME_TYPES = ["image/jpeg", "image/png", "image/webp"] as const;

type StagedListingPhotoStatus = "checking" | "safe" | "rejected";

interface StagedListingPhoto {
  id: string;
  file: File;
  status: StagedListingPhotoStatus;
  message: string;
  moderationLabel: string | null;
  moderationScore: number | null;
}

function formatBytes(bytes: number): string {
  const mb = bytes / (1024 * 1024);
  return `${mb.toFixed(mb >= 1 ? 1 : 2)} MB`;
}

function validateListingPhotoFile(file: File): { ok: true } | { ok: false; error: string } {
  if (!ALLOWED_LISTING_PHOTO_MIME_TYPES.includes(file.type as (typeof ALLOWED_LISTING_PHOTO_MIME_TYPES)[number])) {
    return {
      ok: false,
      error: "Use a JPEG, PNG, or WebP image.",
    };
  }

  if (file.size === 0) {
    return {
      ok: false,
      error: "The selected image is empty.",
    };
  }

  if (file.size > MAX_LISTING_PHOTO_UPLOAD_BYTES) {
    return {
      ok: false,
      error: `Images must be ${formatBytes(MAX_LISTING_PHOTO_UPLOAD_BYTES)} or smaller.`,
    };
  }

  return { ok: true };
}

function createStagedListingPhotoId(file: File): string {
  if (typeof crypto !== "undefined" && typeof crypto.randomUUID === "function") {
    return crypto.randomUUID();
  }

  return `${file.name}-${file.size}-${file.lastModified}-${Math.random().toString(36).slice(2)}`;
}

export {
  ALLOWED_LISTING_PHOTO_MIME_TYPES,
  MAX_LISTING_PHOTO_UPLOAD_BYTES,
  createStagedListingPhotoId,
  formatBytes,
  type StagedListingPhoto,
  type StagedListingPhotoStatus,
  validateListingPhotoFile,
};
