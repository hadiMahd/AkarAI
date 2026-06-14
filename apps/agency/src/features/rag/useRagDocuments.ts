import { useQuery, useMutation, useQueryClient } from "@tanstack/react-query";
import { apiClient } from "@/lib/api/client";
import { queryKeys } from "@/lib/query/query-client";
import { getAccessToken, getTenantSession } from "@/lib/session/auth-session";

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

interface RagRetrievalQueryRequest {
  query: string;
  top_k?: number;
  include_debug?: boolean;
  conversation_messages?: RagConversationMessage[];
}

interface RagConversationMessage {
  role: "user" | "assistant";
  content: string;
}

interface RagChatThread {
  id: string;
  tenant_id: string;
  owner_user_id: string;
  title: string;
  message_count: number;
  created_at: string;
  updated_at: string;
  last_message_at: string;
}

interface RagChatMessage {
  id: string;
  thread_id: string;
  tenant_id: string;
  owner_user_id: string;
  role: "user" | "assistant";
  content: string;
  sequence_number: number;
  retrieval_log_id?: string | null;
  answer?: RagPolicyAnswer | null;
  created_at: string;
}

interface RagChatThreadDetailResponse {
  thread: RagChatThread;
  messages: RagChatMessage[];
}

interface RagChatSendMessageRequest {
  content: string;
  top_k?: number;
  include_debug?: boolean;
}

interface RagChatSendMessageResponse {
  thread: RagChatThread;
  user_message: RagChatMessage;
  assistant_message: RagChatMessage;
}

interface PaginatedRagChatThreadsResponse {
  items: RagChatThread[];
  total: number;
  page: number;
  size: number;
}

interface RagRetrievalCitation {
  document_id: string;
  document_filename: string;
  page_number: number;
  source_label: string;
}

interface RagRetrievalEvidence {
  chunk_id: string;
  document_id: string;
  page_ids: string[];
  document_filename: string;
  page_numbers: number[];
  source_label: string;
  vector_rank: number;
  vector_score: number;
  rerank_rank?: number | null;
  rerank_score?: number | null;
  text_preview: string;
  parent_page_text?: string | null;
}

interface RagRetrievalDebug {
  reranker_used: boolean;
  reranker_provider?: string | null;
  fallback_reason?: string | null;
  confidence_status: string;
  retrieval_log_id: string;
  guardrail_status?: string | null;
  guardrail_blocked_reason?: string | null;
  generation_provider?: string | null;
  vector_candidate_count?: number | null;
  rerank_candidate_count?: number | null;
}

interface RagPolicyAnswer {
  status: string;
  answer: string;
  citations: RagRetrievalCitation[];
  evidence: RagRetrievalEvidence[];
  debug?: RagRetrievalDebug | null;
}

interface RagRetrievalLog {
  id: string;
  tenant_id: string;
  document_id?: string | null;
  actor_user_id?: string | null;
  actor_role: string;
  query: string;
  retrieval_scope: string;
  selected_document_ids: string[];
  selected_chunk_ids: string[];
  selected_page_ids: string[];
  reranker_used: boolean;
  reranker_provider?: string | null;
  fallback_reason?: string | null;
  confidence_status: string;
  retrieved_at: string;
  created_at: string;
}

interface PaginatedRagRetrievalLogsResponse {
  items: RagRetrievalLog[];
  total: number;
  page: number;
  size: number;
}

interface RagRetrievalLogFilter {
  actor_role?: string;
  confidence_status?: string;
  date_from?: string;
  date_to?: string;
}

interface RagEvaluationRun {
  id: string;
  run_label: string;
  started_at: string;
  completed_at?: string | null;
  total_examples: number;
  passed_examples: number;
  failed_examples: number;
  summary: Record<string, unknown>;
  created_at: string;
}

interface PaginatedRagEvaluationRunsResponse {
  items: RagEvaluationRun[];
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

async function replaceRagDocument(documentId: string, file: File): Promise<RagDocument> {
  const formData = new FormData();
  formData.append("file", file);

  return apiClient<RagDocument>(`/api/v1/agencies/rag/documents/${documentId}/replace`, {
    method: "POST",
    body: formData,
    headers: {},
  });
}

async function submitRagPolicyQuery(payload: RagRetrievalQueryRequest): Promise<RagPolicyAnswer> {
  return apiClient<RagPolicyAnswer>("/api/v1/agencies/rag/query", {
    method: "POST",
    body: JSON.stringify(payload),
  });
}

async function fetchRagRetrievalLogs(
  page = 1,
  pageSize = 20,
  filters?: RagRetrievalLogFilter,
): Promise<PaginatedRagRetrievalLogsResponse> {
  const params: Record<string, string | number> = { page, page_size: pageSize };
  if (filters?.actor_role) params.actor_role = filters.actor_role;
  if (filters?.confidence_status) params.confidence_status = filters.confidence_status;
  if (filters?.date_from) params.date_from = filters.date_from;
  if (filters?.date_to) params.date_to = filters.date_to;
  return apiClient<PaginatedRagRetrievalLogsResponse>("/api/v1/agencies/rag/retrieval-logs", { params });
}

async function fetchRagChatThreads(page = 1, pageSize = 20): Promise<PaginatedRagChatThreadsResponse> {
  return apiClient<PaginatedRagChatThreadsResponse>("/api/v1/agencies/rag/chat/threads", {
    params: { page, page_size: pageSize },
  });
}

async function createRagChatThread(title?: string): Promise<RagChatThreadDetailResponse> {
  return apiClient<RagChatThreadDetailResponse>("/api/v1/agencies/rag/chat/threads", {
    method: "POST",
    body: JSON.stringify(title ? { title } : {}),
  });
}

async function fetchRagChatThread(threadId: string): Promise<RagChatThreadDetailResponse> {
  return apiClient<RagChatThreadDetailResponse>(`/api/v1/agencies/rag/chat/threads/${threadId}`);
}

async function sendRagChatMessage(
  threadId: string,
  payload: RagChatSendMessageRequest,
): Promise<RagChatSendMessageResponse> {
  return apiClient<RagChatSendMessageResponse>(`/api/v1/agencies/rag/chat/threads/${threadId}/messages`, {
    method: "POST",
    body: JSON.stringify(payload),
  });
}

async function fetchRagEvaluationRuns(page = 1, pageSize = 20): Promise<PaginatedRagEvaluationRunsResponse> {
  return apiClient<PaginatedRagEvaluationRunsResponse>("/api/v1/agencies/rag/evaluation-runs", {
    params: { page, page_size: pageSize },
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

export function useReplaceRagDocument() {
  const queryClient = useQueryClient();

  return useMutation({
    mutationFn: ({ documentId, file }: { documentId: string; file: File }) =>
      replaceRagDocument(documentId, file),
    onSuccess: (document) => {
      queryClient.invalidateQueries({ queryKey: queryKeys.rag.list({}) });
      queryClient.invalidateQueries({ queryKey: queryKeys.rag.detail(document.id) });
    },
  });
}

export function useRagPolicyQuery() {
  return useMutation({
    mutationFn: (payload: RagRetrievalQueryRequest) => submitRagPolicyQuery(payload),
  });
}

export function useRagChatThreads(page = 1, pageSize = 20) {
  return useQuery({
    queryKey: queryKeys.rag.chatThreads({ page, page_size: pageSize }),
    queryFn: () => fetchRagChatThreads(page, pageSize),
  });
}

export function useRagChatThread(threadId: string | null) {
  return useQuery({
    queryKey: queryKeys.rag.chatThread(threadId || "empty"),
    queryFn: () => fetchRagChatThread(threadId as string),
    enabled: !!threadId,
  });
}

export function useCreateRagChatThread() {
  const queryClient = useQueryClient();

  return useMutation({
    mutationFn: (title?: string) => createRagChatThread(title),
    onSuccess: (result) => {
      queryClient.invalidateQueries({ queryKey: queryKeys.rag.chatThreads({}) });
      queryClient.setQueryData(queryKeys.rag.chatThread(result.thread.id), result);
    },
  });
}

export function useSendRagChatMessage() {
  const queryClient = useQueryClient();

  return useMutation({
    mutationFn: ({ threadId, payload }: { threadId: string; payload: RagChatSendMessageRequest }) =>
      sendRagChatMessage(threadId, payload),
    onSuccess: (result) => {
      queryClient.invalidateQueries({ queryKey: queryKeys.rag.chatThreads({}) });
      queryClient.setQueryData<RagChatThreadDetailResponse>(
        queryKeys.rag.chatThread(result.thread.id),
        (existing) => ({
          thread: result.thread,
          messages: [
            ...(existing?.messages || []),
            result.user_message,
            result.assistant_message,
          ],
        }),
      );
    },
  });
}

export function useRagRetrievalLogs(
  page = 1,
  pageSize = 20,
  filters?: RagRetrievalLogFilter,
) {
  const tenantSession = getTenantSession();
  const isAdmin = tenantSession?.role === "agency_admin";

  return useQuery({
    queryKey: queryKeys.rag.retrievalLogs({ page, page_size: pageSize, ...filters }),
    queryFn: () => fetchRagRetrievalLogs(page, pageSize, filters),
    enabled: isAdmin,
  });
}

export {
  createRagChatThread,
  fetchRagEvaluationRuns,
  fetchRagChatThread,
  fetchRagChatThreads,
  fetchRagRetrievalLogs,
  sendRagChatMessage,
  submitRagPolicyQuery,
};

export type {
  PaginatedRagChatThreadsResponse,
  PaginatedRagEvaluationRunsResponse,
  PaginatedRagRetrievalLogsResponse,
  RagChatMessage,
  RagChatSendMessageRequest,
  RagChatSendMessageResponse,
  RagChatThread,
  RagChatThreadDetailResponse,
  RagEvaluationRun,
  RagPolicyAnswer,
  RagConversationMessage,
  RagRetrievalCitation,
  RagRetrievalDebug,
  RagRetrievalEvidence,
  RagRetrievalLog,
  RagRetrievalLogFilter,
  RagRetrievalQueryRequest,
};

export type { RagDocument };
