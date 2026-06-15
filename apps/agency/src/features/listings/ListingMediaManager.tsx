import {
  useEffect,
  useMemo,
  useState,
  type ChangeEvent,
  type Dispatch,
  type SetStateAction,
} from "react";
import { AlertCircle, CheckCircle2, ImagePlus, Loader2, X } from "lucide-react";
import { Card, CardContent, CardHeader, CardTitle } from "@/components/ui/card";
import { Button } from "@/components/ui/button";
import { Input } from "@/components/ui/input";
import { Label } from "@/components/ui/label";
import { Badge } from "@/components/ui/badge";
import { getApiErrorMessage } from "@/lib/api/errors";
import {
  useListingPhotos,
  uploadListingPhoto,
  validateListingPhotoBeforeUpload,
  type ListingPhotoMetadata,
} from "./useAgencyListings";
import {
  ALLOWED_LISTING_PHOTO_MIME_TYPES,
  MAX_LISTING_PHOTO_UPLOAD_BYTES,
  createStagedListingPhotoId,
  formatBytes,
  type StagedListingPhoto,
  validateListingPhotoFile,
} from "./listing-media";

interface ListingMediaManagerProps {
  listingId: string | null;
  stagedPhotos?: StagedListingPhoto[];
  onStagedPhotosChange?: Dispatch<SetStateAction<StagedListingPhoto[]>>;
}

export function ListingMediaManager({
  listingId,
  stagedPhotos = [],
  onStagedPhotosChange,
}: ListingMediaManagerProps) {
  const isCreateMode = !listingId;
  const canCreateObjectUrl =
    typeof URL !== "undefined" && typeof URL.createObjectURL === "function";
  const { photos, isLoading, isUploading, error } = useListingPhotos(listingId || "");

  const [formError, setFormError] = useState("");
  const [successMessage, setSuccessMessage] = useState("");

  const sortedPhotos = useMemo(
    () => [...photos].sort((a, b) => a.display_order - b.display_order),
    [photos]
  );

  // ── Create mode: staged photo logic ──────────────────────────────
  const stagedPreviews = useMemo(
    () =>
      canCreateObjectUrl
        ? stagedPhotos.map((photo) => ({ id: photo.id, url: URL.createObjectURL(photo.file) }))
        : [],
    [canCreateObjectUrl, stagedPhotos]
  );

  useEffect(() => {
    return () => stagedPreviews.forEach((preview) => URL.revokeObjectURL(preview.url));
  }, [stagedPreviews]);

  const allStagedPhotosSafe =
    stagedPhotos.length > 0 && stagedPhotos.every((photo) => photo.status === "safe");
  const stagedPhotosPending = stagedPhotos.some((photo) => photo.status === "checking");

  const updateStagedPhoto = (photoId: string, updater: (photo: StagedListingPhoto) => StagedListingPhoto) => {
    onStagedPhotosChange?.((current) =>
      current.map((photo) => (photo.id === photoId ? updater(photo) : photo))
    );
  };

  const runStagedPhotoPreflight = async (photo: StagedListingPhoto) => {
    try {
      const result = await validateListingPhotoBeforeUpload(photo.file);
      updateStagedPhoto(photo.id, (current) => ({
        ...current,
        status: result.safe ? "safe" : "rejected",
        message: result.message,
        moderationLabel: result.moderation_label,
        moderationScore: result.moderation_score,
      }));
    } catch {
      updateStagedPhoto(photo.id, (current) => ({
        ...current,
        status: "rejected",
        message: "Image safety could not be verified right now. Try again later.",
        moderationLabel: "moderation_failed",
        moderationScore: 1,
      }));
    }
  };

  const handleStagedFilesSelect = (event: ChangeEvent<HTMLInputElement>) => {
    setFormError("");
    setSuccessMessage("");

    const files = Array.from(event.target.files ?? []);
    if (files.length === 0) {
      return;
    }

    const nextItems: StagedListingPhoto[] = files.map((file) => {
      const validation = validateListingPhotoFile(file);
      if (!validation.ok) {
        return {
          id: createStagedListingPhotoId(file),
          file,
          status: "rejected",
          message: validation.error,
          moderationLabel: null,
          moderationScore: null,
        };
      }

      return {
        id: createStagedListingPhotoId(file),
        file,
        status: "checking",
        message: "Checking image safety...",
        moderationLabel: null,
        moderationScore: null,
      };
    });

    onStagedPhotosChange?.((current) => [...current, ...nextItems]);
    event.target.value = "";

    nextItems
      .filter((item) => item.status === "checking")
      .forEach((item) => {
        void runStagedPhotoPreflight(item);
      });
  };

  const handleRemoveStagedPhoto = (photoId: string) => {
    onStagedPhotosChange?.((current) => current.filter((photo) => photo.id !== photoId));
  };

  // ── Edit mode: local multi-upload state ──────────────────────────
  const [editStagedFiles, setEditStagedFiles] = useState<StagedListingPhoto[]>([]);

  const editStagedPreviews = useMemo(
    () =>
      canCreateObjectUrl
        ? editStagedFiles.map((photo) => ({ id: photo.id, url: URL.createObjectURL(photo.file) }))
        : [],
    [canCreateObjectUrl, editStagedFiles]
  );

  useEffect(() => {
    return () => editStagedPreviews.forEach((preview) => URL.revokeObjectURL(preview.url));
  }, [editStagedPreviews]);

  const allEditStagedSafe =
    editStagedFiles.length > 0 && editStagedFiles.every((photo) => photo.status === "safe");
  const editStagedPending = editStagedFiles.some((photo) => photo.status === "checking");

  const updateEditStagedPhoto = (photoId: string, updater: (photo: StagedListingPhoto) => StagedListingPhoto) => {
    setEditStagedFiles((current) =>
      current.map((photo) => (photo.id === photoId ? updater(photo) : photo))
    );
  };

  const runEditStagedPreflight = async (photo: StagedListingPhoto) => {
    try {
      const result = await validateListingPhotoBeforeUpload(photo.file);
      updateEditStagedPhoto(photo.id, (current) => ({
        ...current,
        status: result.safe ? "safe" : "rejected",
        message: result.message,
        moderationLabel: result.moderation_label,
        moderationScore: result.moderation_score,
      }));
    } catch {
      updateEditStagedPhoto(photo.id, (current) => ({
        ...current,
        status: "rejected",
        message: "Image safety could not be verified right now. Try again later.",
        moderationLabel: "moderation_failed",
        moderationScore: 1,
      }));
    }
  };

  const handleEditStagedFilesSelect = (event: ChangeEvent<HTMLInputElement>) => {
    setFormError("");
    setSuccessMessage("");

    const files = Array.from(event.target.files ?? []);
    if (files.length === 0) {
      return;
    }

    const nextItems: StagedListingPhoto[] = files.map((file) => {
      const validation = validateListingPhotoFile(file);
      if (!validation.ok) {
        return {
          id: createStagedListingPhotoId(file),
          file,
          status: "rejected",
          message: validation.error,
          moderationLabel: null,
          moderationScore: null,
        };
      }

      return {
        id: createStagedListingPhotoId(file),
        file,
        status: "checking",
        message: "Checking image safety...",
        moderationLabel: null,
        moderationScore: null,
      };
    });

    setEditStagedFiles((current) => [...current, ...nextItems]);
    event.target.value = "";

    nextItems
      .filter((item) => item.status === "checking")
      .forEach((item) => {
        void runEditStagedPreflight(item);
      });
  };

  const handleRemoveEditStagedPhoto = (photoId: string) => {
    setEditStagedFiles((current) => current.filter((photo) => photo.id !== photoId));
  };

  const handleBatchUpload = async () => {
    if (!listingId) return;
    setFormError("");
    setSuccessMessage("");

    const safeFiles = editStagedFiles.filter((photo) => photo.status === "safe");
    if (safeFiles.length === 0) {
      setFormError("No safe photos to upload.");
      return;
    }

    let uploaded = 0;
    for (let i = 0; i < safeFiles.length; i++) {
      const photo = safeFiles[i];
      const fd = new FormData();
      fd.append("file", photo.file);
      fd.append("display_order", String(sortedPhotos.length + i));
      try {
        await uploadListingPhoto(listingId, fd);
        uploaded++;
      } catch (uploadError) {
        setFormError(
          getApiErrorMessage(uploadError, "listing.media.upload", {
            fallback: `We couldn't upload "${photo.file.name}". Try again.`,
          }),
        );
      }
    }

    if (uploaded > 0) {
      setEditStagedFiles([]);
      setSuccessMessage(`${uploaded} photo(s) uploaded.`);
    }
  };

  // ── Staged photo card (shared between create and edit modes) ─────
  const renderStagedPhotoCard = (
    photo: StagedListingPhoto,
    previews: { id: string; url: string }[],
    onRemove: (id: string) => void,
    key: string,
  ) => {
    const preview = previews.find((item) => item.id === photo.id);
    return (
      <div key={key} className="relative rounded-md border bg-background p-2">
        {preview ? (
          <img
            src={preview.url}
            alt={photo.file.name}
            className="h-24 w-full rounded object-cover"
          />
        ) : null}
        <div className="mt-2 space-y-1">
          <p className="truncate text-xs font-medium">{photo.file.name}</p>
          <div className="flex items-center gap-2">
            <Badge variant={photo.status === "safe" ? "default" : "secondary"}>
              {photo.status}
            </Badge>
            {photo.moderationScore !== null ? (
              <span className="text-[11px] text-muted-foreground">
                score {photo.moderationScore.toFixed(2)}
              </span>
            ) : null}
          </div>
          <p className="text-xs text-muted-foreground">{photo.message}</p>
        </div>
        <button
          type="button"
          onClick={() => onRemove(photo.id)}
          className="absolute right-1 top-1 rounded-full bg-background p-0.5 shadow"
          aria-label={`Remove ${photo.file.name}`}
        >
          <X className="h-3 w-3" />
        </button>
      </div>
    );
  };

  function PhotoPreviewImage({ photo }: { photo: ListingPhotoMetadata }) {
    const [failed, setFailed] = useState(false);
    if (!photo.preview_url) {
      return (
        <div className="mt-3 flex h-36 items-center justify-center rounded-md bg-muted">
          <Loader2 className="mr-2 h-4 w-4 animate-spin" />
          <span className="text-xs text-muted-foreground">Processing preview...</span>
        </div>
      );
    }
    if (failed) {
      return (
        <div className="mt-3 flex h-36 items-center justify-center rounded-md bg-muted">
          <AlertCircle className="mr-2 h-4 w-4 text-destructive" />
          <span className="text-xs text-muted-foreground">Failed to load image</span>
        </div>
      );
    }
    return (
      <img
        src={photo.preview_url}
        alt={photo.alt_text || photo.caption || "Listing photo"}
        onError={() => { console.warn("Preview image failed to load:", photo.preview_url); setFailed(true); }}
        className="mt-3 h-36 w-full rounded-md object-cover"
      />
    );
  }

  return (
    <Card className="mt-6">
      <CardHeader className="space-y-2">
        <CardTitle className="flex items-center gap-2">
          <ImagePlus className="h-5 w-5" />
          Listing Photos
        </CardTitle>
        <p className="text-sm text-muted-foreground">
          {isCreateMode
            ? "Selected photos are scanned for NSFW before storage. Nothing is uploaded until you submit the listing."
            : "Accepted formats: JPEG, PNG, or WebP. Multiple files can be selected and uploaded in batch."}
        </p>
      </CardHeader>
      <CardContent className="space-y-6">
        {!isCreateMode && error ? (
          <div role="alert" className="flex items-center gap-2 rounded-md bg-destructive/10 p-3 text-sm text-destructive">
            <AlertCircle className="h-4 w-4" />
            <span>{getApiErrorMessage(error, "listing.media.load")}</span>
          </div>
        ) : null}

        {successMessage ? (
          <div className="flex items-center gap-2 rounded-md bg-green-50 p-3 text-sm text-green-700">
            <CheckCircle2 className="h-4 w-4" />
            <span>{successMessage}</span>
          </div>
        ) : null}

        {formError ? (
          <div className="flex items-center gap-2 rounded-md bg-destructive/10 p-3 text-sm text-destructive">
            <AlertCircle className="h-4 w-4" />
            <span>{formError}</span>
          </div>
        ) : null}

        {isCreateMode ? (
          <div className="space-y-4 rounded-lg border bg-muted/20 p-4">
            <div className="space-y-2">
              <Label htmlFor="staged-photo-files">Select photos</Label>
              <Input
                id="staged-photo-files"
                type="file"
                multiple
                accept={ALLOWED_LISTING_PHOTO_MIME_TYPES.join(",")}
                onChange={handleStagedFilesSelect}
              />
              <p className="text-xs text-muted-foreground">
                Max size {formatBytes(MAX_LISTING_PHOTO_UPLOAD_BYTES)} per file.
              </p>
            </div>

            {allStagedPhotosSafe ? (
              <div className="flex items-center gap-2 rounded-md bg-green-50 p-3 text-sm text-green-700">
                <CheckCircle2 className="h-4 w-4" />
                <span>Photos are safe to upload.</span>
              </div>
            ) : null}

            {stagedPhotosPending ? (
              <div className="flex items-center gap-2 rounded-md bg-muted p-3 text-sm text-muted-foreground">
                <Loader2 className="h-4 w-4 animate-spin" />
                <span>Checking selected photos...</span>
              </div>
            ) : null}

            {stagedPhotos.length > 0 ? (
              <div className="grid gap-3 sm:grid-cols-2 md:grid-cols-3">
                {stagedPhotos.map((photo) =>
                  renderStagedPhotoCard(photo, stagedPreviews, handleRemoveStagedPhoto, photo.id)
                )}
              </div>
            ) : null}
          </div>
        ) : (
          <div className="space-y-4 rounded-lg border bg-muted/20 p-4">
            <div className="space-y-2">
              <Label htmlFor="edit-photo-files">Add photos</Label>
              <Input
                id="edit-photo-files"
                type="file"
                multiple
                accept={ALLOWED_LISTING_PHOTO_MIME_TYPES.join(",")}
                onChange={handleEditStagedFilesSelect}
              />
              <p className="text-xs text-muted-foreground">
                Max size {formatBytes(MAX_LISTING_PHOTO_UPLOAD_BYTES)} per file. Multiple files supported.
              </p>
            </div>

            {allEditStagedSafe ? (
              <div className="flex items-center gap-2 rounded-md bg-green-50 p-3 text-sm text-green-700">
                <CheckCircle2 className="h-4 w-4" />
                <span>All photos passed safety check.</span>
              </div>
            ) : null}

            {editStagedPending ? (
              <div className="flex items-center gap-2 rounded-md bg-muted p-3 text-sm text-muted-foreground">
                <Loader2 className="h-4 w-4 animate-spin" />
                <span>Checking selected photos...</span>
              </div>
            ) : null}

            {editStagedFiles.length > 0 ? (
              <>
                <div className="grid gap-3 sm:grid-cols-2 md:grid-cols-3">
                  {editStagedFiles.map((photo) =>
                    renderStagedPhotoCard(photo, editStagedPreviews, handleRemoveEditStagedPhoto, `edit-${photo.id}`)
                  )}
                </div>
                <div className="flex flex-wrap items-center gap-2">
                  <Button
                    type="button"
                    onClick={handleBatchUpload}
                    disabled={isUploading || !allEditStagedSafe}
                  >
                    {isUploading ? "Uploading..." : `Upload ${editStagedFiles.filter((p) => p.status === "safe").length} Photo(s)`}
                  </Button>
                </div>
              </>
            ) : null}
          </div>
        )}

        {!isCreateMode ? (
          <div className="space-y-3">
            <div className="flex items-center justify-between">
              <h3 className="text-sm font-semibold">Current Photos</h3>
              <span className="text-xs text-muted-foreground">{sortedPhotos.length} total</span>
            </div>

            {isLoading ? (
              <div className="space-y-3">
                {Array.from({ length: 2 }).map((_, index) => (
                  <div key={index} className="h-16 rounded-md bg-muted animate-pulse" />
                ))}
              </div>
            ) : sortedPhotos.length === 0 ? (
              <p className="text-sm text-muted-foreground">No photos uploaded yet.</p>
            ) : (
              <div className="grid gap-3 md:grid-cols-2">
                {sortedPhotos.map((photo) => (
                  <div key={photo.id} className="rounded-lg border p-3">
                    <div className="flex items-start justify-between gap-3">
                      <div className="min-w-0 flex-1 space-y-1">
                        <p className="text-sm font-medium">{photo.caption || "Untitled photo"}</p>
                        <p className="text-xs text-muted-foreground truncate">{photo.alt_text || photo.object_key}</p>
                      </div>
                      <Badge variant={photo.status === "accepted" ? "default" : "secondary"}>
                        {photo.status}
                      </Badge>
                    </div>
                    <PhotoPreviewImage photo={photo} />
                    <div className="mt-3 flex flex-wrap gap-2 text-xs text-muted-foreground">
                      <span>Order {photo.display_order}</span>
                      <span>·</span>
                      <span>{photo.content_type || "unknown type"}</span>
                      {photo.width && photo.height ? (
                        <>
                          <span>·</span>
                          <span>
                            {photo.width} x {photo.height}
                          </span>
                        </>
                      ) : null}
                    </div>
                  </div>
                ))}
              </div>
            )}
          </div>
        ) : null}
      </CardContent>
    </Card>
  );
}
