import { useQuery, useMutation, useQueryClient } from "@tanstack/react-query";
import { apiClient } from "@/lib/api/client";
import { queryKeys } from "@/lib/query/query-client";
import { getAccessToken } from "@/lib/session/auth-session";

interface RagDocument {
  id: string;
  tenant_id: string;
  filename: string;
  status: string;
  blob_path: string;
  document_url?: string | null;
  download_url?: string | null;
  created_at: string;
  updated_at: string;
}

interface PaginatedRagDocumentsResponse {
  items: RagDocument[];
  total: number;
  page: number;
  size: number;
}

async function fetchRagDocuments(page = 1, pageSize = 20): Promise<PaginatedRagDocumentsResponse> {
  return apiClient<PaginatedRagDocumentsResponse>("/api/v1/agencies/rag/documents", {
    params: { page, page_size: pageSize },
  });
}

async function fetchRagDocument(documentId: string): Promise<RagDocument> {
  return apiClient<RagDocument>(`/api/v1/agencies/rag/documents/${documentId}`);
}

async function uploadRagDocument(file: File): Promise<RagDocument> {
  const formData = new FormData();
  formData.append("file", file);
  
  return apiClient<RagDocument>("/api/v1/agencies/rag/documents", {
    method: "POST",
    body: formData,
    headers: {},
  });
}

export async function downloadRagDocument(document: RagDocument): Promise<Blob> {
  const accessToken = getAccessToken();
  if (!accessToken) {
    throw new Error("Not authenticated");
  }
  const downloadPath = document.download_url || document.document_url;
  if (!downloadPath) {
    throw new Error("Download unavailable");
  }
  return apiClient<Blob>(downloadPath, {
    responseType: "blob",
  });
}

export function useRagDocuments(page = 1, pageSize = 20) {
  return useQuery({
    queryKey: queryKeys.rag.list({ page, page_size: pageSize }),
    queryFn: () => fetchRagDocuments(page, pageSize),
  });
}

export function useRagDocument(documentId: string) {
  const query = useQuery({
    queryKey: queryKeys.rag.detail(documentId),
    queryFn: () => fetchRagDocument(documentId),
    enabled: !!documentId,
    refetchInterval: (query) => {
      const data = query.state.data;
      if (data && (data.status === "pending" || data.status === "processing")) {
        return 2000;
      }
      return false;
    },
  });

  return {
    document: query.data,
    isLoading: query.isLoading,
    error: query.error,
  };
}

export function useUploadRagDocument() {
  const queryClient = useQueryClient();

  return useMutation({
    mutationFn: (file: File) => uploadRagDocument(file),
    onSuccess: () => {
      queryClient.invalidateQueries({ queryKey: queryKeys.rag.list({}) });
    },
  });
}

export type { RagDocument };
