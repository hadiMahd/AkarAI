import { useMutation, useQuery } from "@tanstack/react-query";
import { apiClient } from "@/lib/api/client";
import { queryKeys } from "@/lib/query/query-client";

export interface ExtractedListingSpecs {
  property_type?: string | null;
  listing_purpose?: string | null;
  bedrooms?: number | null;
  bathrooms?: number | null;
  parking?: number | null;
  floor?: number | null;
  area_size?: string | number | null;
  area_unit?: string | null;
  furnishing?: string | null;
  address?: string | null;
  city?: string | null;
  location_text?: string | null;
  raw_text_excerpt?: string | null;
  field_confidence?: Record<string, string>;
  source_snippets?: Record<string, string>;
}

export interface SpecExtractionAccepted {
  job_id: string;
  status: string;
  provider: string;
}

export interface SpecExtractionResult {
  job_id: string;
  status: string;
  provider: string;
  warnings: string[];
  fallback_reason?: string | null;
  extracted_specs?: ExtractedListingSpecs | null;
}

export interface ListingDraftRequest {
  listing_id?: string | null;
  listing_context: Record<string, unknown>;
  extracted_specs?: ExtractedListingSpecs | null;
}

export interface ListingDraftResponse {
  job_id: string;
  status: string;
  title?: string | null;
  description?: string | null;
  highlights: string[];
  guardrail_status?: string | null;
  generation_provider?: string | null;
  blocked_reason?: string | null;
  warnings: string[];
}

export interface LeadReplyDraftResponse {
  job_id: string;
  status: string;
  channel: "email" | "whatsapp";
  subject?: string | null;
  body?: string | null;
  guardrail_status?: string | null;
  generation_provider?: string | null;
  blocked_reason?: string | null;
}

export interface AgencyAIJob {
  id: string;
  job_type: string;
  status: string;
  result_payload?: Record<string, unknown> | null;
  error_message?: string | null;
  created_at: string;
  started_at?: string | null;
  completed_at?: string | null;
}

async function uploadSpecSheet(
  file: File,
): Promise<SpecExtractionAccepted> {
  const form = new FormData();
  form.append("file", file);
  return apiClient<SpecExtractionAccepted>(
    "/api/v1/agencies/listings/spec-sheet-extractions",
    {
      method: "POST",
      body: form,
    },
  );
}

export function useUploadSpecSheet() {
  return useMutation({
    mutationFn: uploadSpecSheet,
  });
}

async function fetchSpecExtraction(jobId: string): Promise<SpecExtractionResult> {
  return apiClient<SpecExtractionResult>(
    `/api/v1/agencies/listings/spec-sheet-extractions/${jobId}`,
  );
}

export function useSpecExtraction(jobId: string | null) {
  return useQuery({
    queryKey: jobId ? queryKeys.agencyAi.specExtraction(jobId) : ["agency", "ai", "spec-extraction", "idle"],
    queryFn: () => fetchSpecExtraction(jobId as string),
    enabled: Boolean(jobId),
    refetchInterval: (query) => {
      const data = query.state.data as SpecExtractionResult | undefined;
      if (!data) return 1500;
      if (data.status === "queued" || data.status === "processing") return 1500;
      return false;
    },
  });
}

async function generateListingDraft(
  payload: ListingDraftRequest,
): Promise<ListingDraftResponse> {
  return apiClient<ListingDraftResponse>(
    "/api/v1/agencies/listings/draft",
    {
      method: "POST",
      body: JSON.stringify(payload),
    },
  );
}

export function useListingDraft() {
  return useMutation({
    mutationFn: generateListingDraft,
  });
}

async function generateLeadReplyDraft(
  leadId: string,
  channel: "email" | "whatsapp",
): Promise<LeadReplyDraftResponse> {
  return apiClient<LeadReplyDraftResponse>(
    `/api/v1/agencies/leads/${leadId}/reply-draft`,
    {
      method: "POST",
      body: JSON.stringify({ channel }),
    },
  );
}

export function useLeadReplyDraft() {
  return useMutation({
    mutationFn: ({ leadId, channel }: { leadId: string; channel: "email" | "whatsapp" }) =>
      generateLeadReplyDraft(leadId, channel),
  });
}

async function fetchJobStatus(jobId: string): Promise<AgencyAIJob> {
  return apiClient<AgencyAIJob>(
    `/api/v1/agencies/ai/jobs/${jobId}`,
  );
}

export function useAgencyAiJob(jobId: string | null) {
  return useQuery({
    queryKey: jobId ? queryKeys.agencyAi.jobStatus(jobId) : ["agency", "ai", "job", "idle"],
    queryFn: () => fetchJobStatus(jobId as string),
    enabled: Boolean(jobId),
    refetchInterval: (query) => {
      const data = query.state.data as AgencyAIJob | undefined;
      if (!data) return 1500;
      if (data.status === "queued" || data.status === "processing") return 1500;
      return false;
    },
  });
}
