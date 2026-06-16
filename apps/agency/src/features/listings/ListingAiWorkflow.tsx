import { useEffect, useState } from "react";
import { Sparkles, FileScan, AlertTriangle, Loader2 } from "lucide-react";
import {
  useListingDraft,
  useSpecExtraction,
  useUploadSpecSheet,
  type ExtractedListingSpecs,
} from "@/features/agencyAi/useAgencyAi";
import { getApiErrorMessage } from "@/lib/api/errors";
import { Button } from "@/components/ui/button";
import { Card, CardContent, CardHeader, CardTitle } from "@/components/ui/card";

const EXTRACTION_PHRASES = [
  "Reading the sheet",
  "Extracting fields",
  "Normalizing details",
  "Matching form fields",
  "Preparing review",
];

interface ListingAiWorkflowProps {
  listingContext: Record<string, unknown>;
  onApplyDraft: (draft: { title: string; description: string; highlights: string[] }) => void;
  onApplyExtractedSpecs: (specs: ExtractedListingSpecs) => void;
  hasFormContext: boolean;
}

type ExtractionState =
  | { kind: "idle" }
  | { kind: "uploading"; file: string }
  | { kind: "polling"; jobId: string; file: string }
  | { kind: "review_ready"; jobId: string; specs: ExtractedListingSpecs | null; warnings: string[] }
  | { kind: "failed"; jobId: string; reason: string | null; warnings: string[] };

function describeExtractionFailure(reason: string | null | undefined): string {
  if (!reason) {
    return "We couldn't read that spec sheet.";
  }
  if (reason.includes("ocr_unavailable_or_unreadable")) {
    return "We couldn't read enough text from that file. Try a clearer scan or enter the details manually.";
  }
  if (reason.includes("ocr_failed")) {
    return "The OCR service could not process that file right now. Try again in a moment.";
  }
  return reason;
}

export function ListingAiWorkflow({
  listingContext,
  onApplyDraft,
  onApplyExtractedSpecs,
  hasFormContext,
}: ListingAiWorkflowProps) {
  const [extraction, setExtraction] = useState<ExtractionState>({ kind: "idle" });
  const [phraseIndex, setPhraseIndex] = useState(0);
  const uploadMutation = useUploadSpecSheet();
  const draftMutation = useListingDraft();
  const { data: extractionData, error: extractionError } = useSpecExtraction(
    extraction.kind === "polling" ? extraction.jobId : null,
  );

  useEffect(() => {
    if (extraction.kind !== "polling" || !extractionData) {
      return;
    }

    if (extractionData.status === "review_ready" || extractionData.status === "completed") {
      setExtraction({
        kind: "review_ready",
        jobId: extractionData.job_id,
        specs: extractionData.extracted_specs ?? null,
        warnings: extractionData.warnings ?? [],
      });
      return;
    }

    if (extractionData.status === "failed" || extractionData.status === "blocked") {
      setExtraction({
        kind: "failed",
        jobId: extractionData.job_id,
        reason: describeExtractionFailure(extractionData.fallback_reason),
        warnings: extractionData.warnings ?? [],
      });
    }
  }, [extraction.kind, extractionData]);

  useEffect(() => {
    if (extraction.kind !== "polling" || !extractionError) {
      return;
    }
    setExtraction({
      kind: "failed",
      jobId: extraction.jobId,
      reason: describeExtractionFailure(getApiErrorMessage(extractionError, "agencyAi.job.status")),
      warnings: [],
    });
  }, [extraction.kind, extraction.jobId, extractionError]);

  useEffect(() => {
    if (extraction.kind !== "polling") {
      setPhraseIndex(0);
      return;
    }
    const timer = window.setInterval(() => {
      setPhraseIndex((current) => (current + 1) % EXTRACTION_PHRASES.length);
    }, 1400);
    return () => window.clearInterval(timer);
  }, [extraction.kind]);

  const onUpload = async (file: File) => {
    setExtraction({ kind: "uploading", file: file.name });
    try {
      const accepted = await uploadMutation.mutateAsync(file);
      setExtraction({ kind: "polling", jobId: accepted.job_id, file: file.name });
    } catch (error) {
      setExtraction({
        kind: "failed",
        jobId: "",
        reason: getApiErrorMessage(error, "agencyAi.spec.upload"),
        warnings: [],
      });
    }
  };

  const onGenerateDraft = async () => {
    if (!hasFormContext) return;
    try {
      const result = await draftMutation.mutateAsync({
        listing_context: listingContext,
        extracted_specs: extraction.kind === "review_ready" ? extraction.specs ?? null : null,
      });
      if (result.title && result.description) {
        onApplyDraft({
          title: result.title,
          description: result.description,
          highlights: result.highlights ?? [],
        });
      }
    } catch (error) {
      // surfaced through draftMutation.error
    }
  };

  const resetExtraction = () => setExtraction({ kind: "idle" });

  const isUploading = uploadMutation.isPending || extraction.kind === "uploading";
  const isGenerating = draftMutation.isPending;
  const draftError = draftMutation.error
    ? getApiErrorMessage(draftMutation.error, "agencyAi.listing.draft")
    : null;

  return (
    <Card>
      <CardHeader>
        <CardTitle className="flex items-center gap-2 text-base">
          <Sparkles className="h-4 w-4" />
          AI listing assist
        </CardTitle>
      </CardHeader>
      <CardContent className="space-y-4">
        <div className="space-y-2">
          <label className="flex items-center gap-2 text-sm font-medium">
            <FileScan className="h-4 w-4" />
            Temporary spec sheet
          </label>
          <input
            type="file"
            accept="application/pdf,image/jpeg,image/png,image/webp"
            disabled={isUploading}
            onChange={(event) => {
              const file = event.target.files?.[0];
              if (file) {
                void onUpload(file);
              }
              event.target.value = "";
            }}
            className="block w-full text-sm file:mr-3 file:rounded file:border-0 file:bg-muted file:px-3 file:py-1 file:text-sm file:font-medium hover:file:bg-muted/80"
          />
          <p className="text-xs text-muted-foreground">
            The file is read for extraction only and is not stored as a listing attachment.
          </p>
        </div>

        {extraction.kind === "uploading" && (
          <div className="flex items-center gap-2 text-sm text-muted-foreground">
            <Loader2 className="h-4 w-4 animate-spin" />
            Reading {extraction.file}…
          </div>
        )}

        {extraction.kind === "polling" && (
          <div className="flex items-center gap-2 text-sm text-muted-foreground">
            <Loader2 className="h-4 w-4 animate-spin" />
            {EXTRACTION_PHRASES[phraseIndex]} from {extraction.file}…
          </div>
        )}

        {extraction.kind === "review_ready" && (
          <div className="space-y-2 rounded border border-dashed p-3 text-sm">
            <p className="font-medium">Review extracted fields</p>
            {extraction.warnings.length > 0 && (
              <p className="flex items-center gap-2 text-amber-600">
                <AlertTriangle className="h-4 w-4" />
                {extraction.warnings[0]}
              </p>
            )}
            {extraction.specs ? (
              <pre className="max-h-40 overflow-auto rounded bg-muted p-2 text-xs">
                {JSON.stringify(extraction.specs, null, 2)}
              </pre>
            ) : (
              <p className="text-muted-foreground">No fields could be extracted.</p>
            )}
            <div className="flex gap-2">
              <Button
                type="button"
                size="sm"
                variant="secondary"
                onClick={() => {
                  if (extraction.kind === "review_ready" && extraction.specs) {
                    onApplyExtractedSpecs(extraction.specs);
                  }
                  resetExtraction();
                }}
                disabled={!extraction.specs}
              >
                Apply to form
              </Button>
              <Button type="button" size="sm" variant="ghost" onClick={resetExtraction}>
                Discard
              </Button>
            </div>
          </div>
        )}

        {extraction.kind === "failed" && (
          <div className="space-y-2 rounded border border-destructive/40 bg-destructive/5 p-3 text-sm">
            <p className="flex items-center gap-2 text-destructive">
              <AlertTriangle className="h-4 w-4" />
              {extraction.reason ?? "We couldn't read that spec sheet."}
            </p>
            {extraction.warnings.length > 0 && (
              <p className="text-muted-foreground">{extraction.warnings[0]}</p>
            )}
            <Button type="button" size="sm" variant="ghost" onClick={resetExtraction}>
              Try another file
            </Button>
          </div>
        )}

        <div className="border-t pt-3">
          <Button
            type="button"
            onClick={() => void onGenerateDraft()}
            disabled={isGenerating || !hasFormContext}
            className="w-full"
          >
            {isGenerating ? (
              <>
                <Loader2 className="mr-2 h-4 w-4 animate-spin" />
                Generating draft…
              </>
            ) : (
              <>
                <Sparkles className="mr-2 h-4 w-4" />
                Generate AI listing draft
              </>
            )}
          </Button>
          {!hasFormContext && (
            <p className="mt-2 text-xs text-muted-foreground">
              Add a title, city, and price before requesting a draft.
            </p>
          )}
          {draftError && (
            <p className="mt-2 text-sm text-destructive">{draftError}</p>
          )}
        </div>
      </CardContent>
    </Card>
  );
}
