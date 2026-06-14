import { useEffect, useRef, useState } from "react";
import ReactMarkdown from "react-markdown";
import remarkGfm from "remark-gfm";
import rehypeSanitize from "rehype-sanitize";
import {
  useCreateRagChatThread,
  useRagDocuments,
  useUploadRagDocument,
  useRagDocument,
  useRagChatThread,
  useRagChatThreads,
  useReplaceRagDocument,
  useSendRagChatMessage,
  useRagRetrievalLogs,
  downloadRagDocument,
} from "@/features/rag/useRagDocuments";
import type { RagChatMessage, RagPolicyAnswer, RagRetrievalDebug, RagRetrievalLog } from "@/features/rag/useRagDocuments";
import { getTenantSession } from "@/lib/session/auth-session";
import { Card, CardContent, CardHeader, CardTitle } from "@/components/ui/card";
import { Bot, FileText, MessageSquarePlus, Upload, RefreshCw, History } from "lucide-react";
import { Button } from "@/components/ui/button";
import { Input } from "@/components/ui/input";
import { Textarea } from "@/components/ui/textarea";

export function RagDocumentsPage() {
  const [page, setPage] = useState(1);
  const { data, isLoading, refetch } = useRagDocuments(page, 20);
  const uploadMutation = useUploadRagDocument();
  const replaceMutation = useReplaceRagDocument();
  const [selectedFile, setSelectedFile] = useState<File | null>(null);

  const tenantSession = getTenantSession();
  const isAdmin = tenantSession?.role === "agency_admin";

  const handleFileChange = (e: React.ChangeEvent<HTMLInputElement>) => {
    const file = e.target.files?.[0] || null;
    setSelectedFile(file);
  };

  const handleUpload = async () => {
    if (!selectedFile) return;
    
    try {
      await uploadMutation.mutateAsync(selectedFile);
      setSelectedFile(null);
      refetch();
    } catch (error) {
      console.error("Upload failed:", error);
    }
  };

  return (
    <div className="space-y-6">
      <div className="flex items-center justify-between">
        <div>
          <h2 className="text-2xl font-bold">Policy Documents</h2>
          <p className="text-muted-foreground">Upload and manage policy documents for RAG ingestion</p>
        </div>
        <Button variant="outline" onClick={() => refetch()}>
          <RefreshCw className="h-4 w-4 mr-2" />
          Refresh
        </Button>
      </div>
      <Card>
        <CardHeader>
          <CardTitle className="flex items-center gap-2">
            <Upload className="h-5 w-5" />
            Upload New Document
          </CardTitle>
        </CardHeader>
        <CardContent>
          <div className="flex items-center gap-4">
            <Input
              type="file"
              accept=".pdf"
              onChange={handleFileChange}
              className="flex-1"
            />
            <Button
              onClick={handleUpload}
              disabled={!selectedFile || uploadMutation.isPending}
            >
              {uploadMutation.isPending ? "Uploading..." : "Upload"}
            </Button>
          </div>
          {uploadMutation.error && (
            <p className="mt-2 text-sm text-destructive">
              Upload failed: {(uploadMutation.error as Error).message}
            </p>
          )}
        </CardContent>
      </Card>

      <Card>
        <CardHeader>
          <CardTitle className="flex items-center gap-2">
            <FileText className="h-5 w-5" />
            Documents
          </CardTitle>
        </CardHeader>
        <CardContent>
          {isLoading ? (
            <div className="space-y-4">
              {Array.from({ length: 3 }).map((_, i) => (
                <div key={i} className="h-16 rounded bg-muted animate-pulse" />
              ))}
            </div>
          ) : !data || data.items.length === 0 ? (
            <p className="text-muted-foreground">No documents uploaded yet.</p>
          ) : (
            <div className="space-y-4">
              <div className="overflow-x-auto">
                <table className="w-full text-sm">
                  <thead>
                    <tr className="border-b">
                      <th className="px-2 py-3 text-left font-medium">Filename</th>
                      <th className="px-2 py-3 text-left font-medium">Status</th>
                      <th className="px-2 py-3 text-left font-medium">Uploaded</th>
                      <th className="px-2 py-3 text-left font-medium">Actions</th>
                    </tr>
                  </thead>
                  <tbody>
                    {data.items.map((doc) => (
                      <RagDocumentRow
                        key={doc.id}
                        documentId={doc.id}
                        filename={doc.filename}
                        status={doc.status}
                        createdAt={doc.created_at}
                        onReplace={async (documentId, file) => {
                          await replaceMutation.mutateAsync({ documentId, file });
                          refetch();
                        }}
                        isReplacing={replaceMutation.isPending}
                      />
                    ))}
                  </tbody>
                </table>
              </div>
              <div className="flex items-center justify-between">
                <p className="text-sm text-muted-foreground">
                  Page {data.page} of {Math.ceil(data.total / data.size)} ({data.total} total)
                </p>
                <div className="flex gap-2">
                  <Button variant="outline" size="sm" onClick={() => setPage((p) => Math.max(1, p - 1))} disabled={page === 1}>
                    Previous
                  </Button>
                  <Button
                    variant="outline"
                    size="sm"
                    onClick={() => setPage((p) => p + 1)}
                    disabled={page >= Math.ceil(data.total / data.size)}
                  >
                    Next
                  </Button>
                </div>
              </div>
            </div>
          )}
        </CardContent>
      </Card>

      {isAdmin && <RetrievalLogSection />}
    </div>
  );
}

export function RagAssistantPage() {
  const { data } = useRagDocuments(1, 20);
  const hasProcessedDocuments = data?.items?.some((doc) => doc.status === "processed") ?? false;

  return (
    <div className="flex h-[calc(100vh-7rem)] min-h-[760px] flex-col gap-3">
      <div>
        <h2 className="text-xl font-bold">Policy Assistant</h2>
        <p className="text-sm text-muted-foreground">Chat against processed policy evidence in a dedicated workspace.</p>
      </div>
      <div className="min-h-0 flex-1">
        <PolicyAssistantTab hasProcessedDocuments={hasProcessedDocuments} />
      </div>
    </div>
  );
}

function PolicyAssistantTab({ hasProcessedDocuments }: { hasProcessedDocuments: boolean }) {
  const [query, setQuery] = useState("");
  const [selectedThreadId, setSelectedThreadId] = useState<string | null>(null);
  const [expandedMessages, setExpandedMessages] = useState<Record<string, boolean>>({});
  const transcriptContainerRef = useRef<HTMLDivElement | null>(null);
  const { data: threadsData, isLoading: isLoadingThreads } = useRagChatThreads(1, 50);
  const { data: threadDetail, isLoading: isLoadingThread } = useRagChatThread(selectedThreadId);
  const createThreadMutation = useCreateRagChatThread();
  const sendMessageMutation = useSendRagChatMessage();
  const isPending = createThreadMutation.isPending || sendMessageMutation.isPending;
  const messages = threadDetail?.messages ?? [];

  useEffect(() => {
    const container = transcriptContainerRef.current;
    if (container) {
      if (typeof container.scrollTo === "function") {
        container.scrollTo({
          top: container.scrollHeight,
          behavior: "smooth",
        });
      } else {
        container.scrollTop = container.scrollHeight;
      }
    }
  }, [selectedThreadId, messages.length, isPending]);

  const handleSubmit = async (e: React.FormEvent) => {
    e.preventDefault();
    if (!query.trim() || !selectedThreadId) return;
    const nextQuestion = query.trim();
    setQuery("");
    try {
      const result = await sendMessageMutation.mutateAsync({
        threadId: selectedThreadId,
        payload: {
          content: nextQuestion,
          top_k: 8,
          include_debug: true,
        },
      });
      setExpandedMessages((previous) => ({
        ...previous,
        [result.assistant_message.id]: false,
      }));
    } catch (error) {
      setQuery(nextQuestion);
    }
  };

  const handleCreateThread = async () => {
    const result = await createThreadMutation.mutateAsync(undefined);
    setSelectedThreadId(result.thread.id);
  };

  const selectedThreadTitle = threadDetail?.thread.title ?? "Conversation";

  return (
    <Card className="h-full border-border/70">
      <CardContent className="flex h-full flex-col p-0">
        {!hasProcessedDocuments ? (
          <div className="p-5">
            <p className="text-sm text-muted-foreground">
              No processed policy documents available. Upload and wait for a document to finish processing before asking questions.
            </p>
          </div>
        ) : (
          <div className="grid h-full min-h-0 overflow-hidden rounded-lg bg-muted/20 md:grid-cols-[220px_minmax(0,1fr)] lg:grid-cols-[240px_minmax(0,1fr)]">
            <aside className="flex min-h-0 flex-col border-r border-border/70 bg-background/90">
              <div className="border-b border-border/70 p-3">
                <Button size="sm" className="w-full" onClick={handleCreateThread} disabled={createThreadMutation.isPending}>
                  <MessageSquarePlus className="mr-2 h-4 w-4" />
                  {createThreadMutation.isPending ? "Creating..." : "New conversation"}
                </Button>
              </div>
              <div className="min-h-0 flex-1 overflow-y-auto p-2">
                {isLoadingThreads ? (
                  <div className="space-y-2 p-1">
                    {Array.from({ length: 4 }).map((_, index) => (
                      <div key={index} className="h-14 animate-pulse rounded-md bg-muted" />
                    ))}
                  </div>
                ) : !threadsData || threadsData.items.length === 0 ? (
                  <div className="flex h-full items-center justify-center px-3 text-center text-xs text-muted-foreground">
                    No conversations yet. Create one to start asking policy questions.
                  </div>
                ) : (
                  <div className="space-y-1">
                    {threadsData.items.map((thread) => (
                      <button
                        key={thread.id}
                        type="button"
                        onClick={() => setSelectedThreadId(thread.id)}
                        className={`w-full rounded-md border px-2.5 py-2 text-left transition ${
                          selectedThreadId === thread.id
                            ? "border-sky-300 bg-sky-50"
                            : "border-transparent hover:border-border hover:bg-muted/40"
                        }`}
                      >
                        <div className="truncate text-sm font-medium leading-5">{thread.title}</div>
                        <div className="mt-0.5 flex items-center justify-between text-[11px] text-muted-foreground">
                          <span>{thread.message_count} messages</span>
                          <span>{new Date(thread.last_message_at).toLocaleDateString()}</span>
                        </div>
                      </button>
                    ))}
                  </div>
                )}
              </div>
            </aside>

            <section className="flex min-h-0 min-w-0 flex-col bg-background/95">
              {!selectedThreadId ? (
                <div className="flex h-full items-center justify-center px-5">
                  <div className="max-w-sm text-center">
                    <div className="mx-auto mb-3 flex h-10 w-10 items-center justify-center rounded-full border border-sky-200 bg-sky-50 text-sky-700">
                      <Bot className="h-5 w-5" />
                    </div>
                    <p className="text-sm font-medium">Choose a conversation or create a new one.</p>
                    <p className="mt-1.5 text-sm text-muted-foreground">
                      The assistant keeps the latest policy context while the full thread remains durable.
                    </p>
                  </div>
                </div>
              ) : (
                <>
                  <div className="border-b border-border/70 px-4 py-3">
                    <div className="text-sm font-medium">{selectedThreadTitle}</div>
                    <div className="text-[11px] text-muted-foreground">Context sent to the model is limited to the latest 4 turns.</div>
                  </div>

                  <div ref={transcriptContainerRef} className="min-h-0 flex-1 overflow-y-auto px-3 py-3 sm:px-4">
                    {isLoadingThread ? (
                      <div className="space-y-3">
                        {Array.from({ length: 3 }).map((_, index) => (
                          <div key={index} className="h-20 animate-pulse rounded-lg bg-muted" />
                        ))}
                      </div>
                    ) : messages.length === 0 ? (
                      <div className="flex h-full items-center justify-center">
                        <div className="max-w-sm rounded-2xl border border-dashed border-border/80 bg-background/90 px-5 py-6 text-center shadow-sm">
                          <div className="mx-auto mb-3 flex h-10 w-10 items-center justify-center rounded-full border border-sky-200 bg-sky-50 text-sky-700">
                            <Bot className="h-5 w-5" />
                          </div>
                          <p className="text-sm font-medium">Ask about policy documents, procedures, and internal rules.</p>
                          <p className="mt-1.5 text-sm text-muted-foreground">Answers stay grounded in uploaded evidence and this conversation thread.</p>
                        </div>
                      </div>
                    ) : (
                      <div className="space-y-4 pb-2">
                        {messages.map((message) => (
                          <ChatMessageRow
                            key={message.id}
                            message={message}
                            showDebug={!!expandedMessages[message.id]}
                            onToggleDebug={() =>
                              setExpandedMessages((previous) => ({
                                ...previous,
                                [message.id]: !previous[message.id],
                              }))
                            }
                          />
                        ))}
                        {sendMessageMutation.isPending && (
                          <div className="flex justify-start">
                            <div className="w-full max-w-[96%] rounded-2xl rounded-bl-md border border-border/70 bg-background px-3 py-3 shadow-sm">
                              <div className="mb-2 flex items-center gap-2 text-[11px] font-medium uppercase tracking-[0.12em] text-muted-foreground">
                                <Bot className="h-3.5 w-3.5" />
                                Policy Assistant
                              </div>
                              <div className="flex items-center gap-2">
                                <span className="h-2 w-2 animate-pulse rounded-full bg-sky-500" />
                                <span className="text-sm text-muted-foreground">Thinking through the policy evidence...</span>
                              </div>
                            </div>
                          </div>
                        )}
                      </div>
                    )}
                  </div>

                  <div className="border-t border-border/70 bg-background p-3 sm:p-4">
                    <form onSubmit={handleSubmit} className="space-y-2">
                      <Textarea
                        placeholder="Message the policy assistant..."
                        value={query}
                        onChange={(e) => setQuery(e.target.value)}
                        disabled={isPending}
                        rows={2}
                        className="resize-none border-border/80 bg-background"
                      />
                      {sendMessageMutation.error && (
                        <p className="text-sm text-destructive">
                          {(sendMessageMutation.error as Error).message}
                        </p>
                      )}
                      <div className="flex items-center justify-between gap-3">
                        <p className="text-[11px] text-muted-foreground">
                          The latest 4 turns are sent for followups; the full chat stays stored.
                        </p>
                        <Button size="sm" type="submit" disabled={isPending || !query.trim()} className="min-w-24">
                          {isPending ? "Sending..." : "Send"}
                        </Button>
                      </div>
                    </form>
                  </div>
                </>
              )}
            </section>
          </div>
        )}
      </CardContent>
    </Card>
  );
}

function ChatMessageRow({
  message,
  showDebug,
  onToggleDebug,
}: {
  message: RagChatMessage;
  showDebug: boolean;
  onToggleDebug: () => void;
}) {
  if (message.role === "user") {
    return (
      <div className="flex justify-end">
        <div className="max-w-[92%] rounded-2xl rounded-br-md bg-slate-900 px-3.5 py-2.5 text-sm text-slate-50 shadow-sm lg:max-w-[88%]">
          {message.content}
        </div>
      </div>
    );
  }

  return (
    <div className="flex justify-start">
      <div className="w-full max-w-[97%] rounded-2xl rounded-bl-md border border-border/70 bg-background px-3.5 py-3 shadow-sm lg:max-w-[94%]">
        <div className="mb-2 flex items-center gap-2 text-[11px] font-medium uppercase tracking-[0.12em] text-muted-foreground">
          <Bot className="h-3.5 w-3.5" />
          Policy Assistant
        </div>
        {message.answer ? (
          <AssistantAnswerCard answer={message.answer} showDebug={showDebug} onToggleDebug={onToggleDebug} />
        ) : (
          <div className="rounded-xl border border-destructive/20 bg-destructive/5 px-4 py-3 text-sm text-destructive">
            {message.content}
          </div>
        )}
      </div>
    </div>
  );
}

function AssistantAnswerCard({ answer, showDebug, onToggleDebug }: { answer: RagPolicyAnswer; showDebug: boolean; onToggleDebug: () => void }) {
  const isAnswered = answer.status === "answered";
  const isInsufficient = answer.status === "insufficient_evidence";

  return (
    <div className="space-y-4">
      <div className={`rounded-md border p-4 ${isAnswered ? "bg-muted/50" : isInsufficient ? "bg-yellow-50 border-yellow-200" : "bg-orange-50 border-orange-200"}`}>
        <p className="text-sm font-medium mb-1">
          {isAnswered ? "Answer" : isInsufficient ? "Insufficient Evidence" : "Partial Answer"}
        </p>
        <div className="prose prose-sm max-w-none dark:prose-invert">
          <ReactMarkdown remarkPlugins={[remarkGfm]} rehypePlugins={[rehypeSanitize]}>
            {answer.answer}
          </ReactMarkdown>
        </div>
      </div>

      {answer.citations.length > 0 && (
        <div>
          <p className="text-sm font-medium mb-2">Citations</p>
          <div className="flex flex-wrap gap-2">
            {answer.citations.map((citation, i) => (
              <span key={i} className="inline-flex items-center rounded-full bg-blue-100 px-2.5 py-0.5 text-xs font-medium text-blue-800">
                {citation.source_label}
              </span>
            ))}
          </div>
        </div>
      )}

      <div>
        <button onClick={onToggleDebug} className="text-xs text-muted-foreground hover:text-foreground">
          {showDebug ? "Hide" : "Show"} evidence &amp; debug
        </button>
      </div>

      {showDebug && (
        <div className="space-y-3">
          {answer.debug && <DebugPanel debug={answer.debug} />}

          {answer.evidence.length > 0 && (
            <div>
              <p className="text-sm font-medium mb-2">Ranked Evidence</p>
              <div className="space-y-2">
                {answer.evidence.map((ev, i) => (
                  <div key={i} className="rounded border p-3 text-xs">
                    <div className="flex justify-between mb-1">
                      <span className="font-medium">{ev.source_label}</span>
                      <span className="text-muted-foreground">
                        v{ev.vector_rank}
                        {ev.rerank_rank != null && ` | r${ev.rerank_rank}`}
                      </span>
                    </div>
                    <p className="text-muted-foreground line-clamp-2">{ev.text_preview}</p>
                    {ev.parent_page_text && (
                      <details className="mt-1">
                        <summary className="cursor-pointer text-muted-foreground">Page context</summary>
                        <p className="mt-1 text-muted-foreground">{ev.parent_page_text}</p>
                      </details>
                    )}
                  </div>
                ))}
              </div>
            </div>
          )}
        </div>
      )}
    </div>
  );
}

function DebugPanel({ debug }: { debug: RagRetrievalDebug }) {
  return (
    <div className="rounded border bg-gray-50 p-3 text-xs space-y-1">
      <p className="font-medium">Debug</p>
      <div className="grid grid-cols-2 gap-x-4 gap-y-1 text-muted-foreground">
        <span>Reranker used</span><span>{debug.reranker_used ? "Yes" : "No"}</span>
        {debug.reranker_provider && <><span>Provider</span><span>{debug.reranker_provider}</span></>}
        {debug.fallback_reason && <><span>Fallback reason</span><span>{debug.fallback_reason}</span></>}
        <span>Confidence</span><span>{debug.confidence_status}</span>
        {debug.guardrail_status && <><span>Guardrails</span><span>{debug.guardrail_status}</span></>}
        {debug.guardrail_blocked_reason && <><span>Blocked reason</span><span>{debug.guardrail_blocked_reason}</span></>}
        {debug.generation_provider && <><span>Generation provider</span><span>{debug.generation_provider}</span></>}
        {debug.vector_candidate_count != null && <><span>Vector candidates</span><span>{debug.vector_candidate_count}</span></>}
        {debug.rerank_candidate_count != null && <><span>Rerank candidates</span><span>{debug.rerank_candidate_count}</span></>}
        <span>Log ID</span><span className="font-mono truncate">{debug.retrieval_log_id}</span>
      </div>
    </div>
  );
}

function RetrievalLogSection() {
  const [logPage, setLogPage] = useState(1);
  const [expandedLog, setExpandedLog] = useState<string | null>(null);
  const { data, isLoading, error } = useRagRetrievalLogs(logPage, 20);

  const toggleExpand = (id: string) => {
    setExpandedLog(expandedLog === id ? null : id);
  };

    return (
    <Card>
      <CardHeader>
        <CardTitle className="flex items-center gap-2">
          <History className="h-5 w-5" />
          Retrieval History
        </CardTitle>
      </CardHeader>
      <CardContent>
        {isLoading ? (
          <div className="space-y-4">
            {Array.from({ length: 3 }).map((_, i) => (
              <div key={i} className="h-16 bg-muted animate-pulse rounded" />
            ))}
          </div>
        ) : error ? (
          <p className="text-sm text-destructive">
            Failed to load retrieval logs: {(error as Error).message}
          </p>
        ) : !data || data.items.length === 0 ? (
          <p className="text-sm text-muted-foreground">No retrieval queries yet.</p>
        ) : (
          <div className="space-y-4">
            <div className="overflow-x-auto">
              <table className="w-full text-sm">
                <thead>
                  <tr className="border-b">
                    <th className="text-left py-3 px-2 font-medium">Query</th>
                    <th className="text-left py-3 px-2 font-medium">Role</th>
                    <th className="text-left py-3 px-2 font-medium">Confidence</th>
                    <th className="text-left py-3 px-2 font-medium">Reranker</th>
                    <th className="text-left py-3 px-2 font-medium">Date</th>
                  </tr>
                </thead>
                <tbody>
                  {data.items.map((log) => (
                    <RetrievalLogRow
                      key={log.id}
                      log={log}
                      isExpanded={expandedLog === log.id}
                      onToggle={() => toggleExpand(log.id)}
                    />
                  ))}
                </tbody>
              </table>
            </div>
            <div className="flex items-center justify-between">
              <p className="text-sm text-muted-foreground">
                Page {data.page} of {Math.ceil(data.total / data.size)} ({data.total} total)
              </p>
              <div className="flex gap-2">
                <Button
                  variant="outline"
                  size="sm"
                  onClick={() => setLogPage(p => Math.max(1, p - 1))}
                  disabled={logPage === 1}
                >
                  Previous
                </Button>
                <Button
                  variant="outline"
                  size="sm"
                  onClick={() => setLogPage(p => p + 1)}
                  disabled={logPage >= Math.ceil(data.total / data.size)}
                >
                  Next
                </Button>
              </div>
            </div>
          </div>
        )}
      </CardContent>
    </Card>
  );
}

function RetrievalLogRow({ log, isExpanded, onToggle }: { log: RagRetrievalLog; isExpanded: boolean; onToggle: () => void }) {
  const confidenceColors: Record<string, string> = {
    sufficient: "bg-green-100 text-green-700",
    insufficient: "bg-yellow-100 text-yellow-700",
    fallback: "bg-orange-100 text-orange-700",
  };

  return (
    <>
      <tr className="border-b cursor-pointer hover:bg-muted/50" onClick={onToggle}>
        <td className="py-3 px-2 max-w-[200px] truncate">{log.query}</td>
        <td className="py-3 px-2">
          <span className="text-xs">{log.actor_role}</span>
        </td>
        <td className="py-3 px-2">
          <span className={`inline-flex items-center rounded-full px-2 py-0.5 text-xs ${confidenceColors[log.confidence_status] || "bg-gray-100 text-gray-700"}`}>
            {log.confidence_status}
          </span>
        </td>
        <td className="py-3 px-2 text-xs">{log.reranker_used ? (log.reranker_provider || "Yes") : "No"}</td>
        <td className="py-3 px-2 text-xs text-muted-foreground">
          {new Date(log.created_at).toLocaleString()}
        </td>
      </tr>
      {isExpanded && (
        <tr className="bg-muted/30">
          <td colSpan={5} className="px-4 py-3">
            <div className="text-xs space-y-2">
              <div className="grid grid-cols-2 gap-x-4 gap-y-1">
                <span className="font-medium">Log ID:</span>
                <span className="font-mono">{log.id}</span>
                <span className="font-medium">Scope:</span>
                <span>{log.retrieval_scope}</span>
                {log.fallback_reason && (
                  <><span className="font-medium">Fallback:</span><span>{log.fallback_reason}</span></>
                )}
                <span className="font-medium">Documents referenced:</span>
                <span>{log.selected_document_ids.length}</span>
                <span className="font-medium">Chunks referenced:</span>
                <span>{log.selected_chunk_ids.length}</span>
                {log.actor_user_id && (
                  <><span className="font-medium">Actor ID:</span><span className="font-mono">{log.actor_user_id}</span></>
                )}
              </div>
            </div>
          </td>
        </tr>
      )}
    </>
  );
}

function RagDocumentRow({
  documentId,
  filename,
  status,
  createdAt,
  onReplace,
  isReplacing,
}: {
  documentId: string;
  filename: string;
  status: string;
  createdAt: string;
  onReplace: (documentId: string, file: File) => Promise<void>;
  isReplacing: boolean;
}) {
  const { document } = useRagDocument(documentId);
  const currentStatus = document?.status || status;
  const replaceInputRef = useRef<HTMLInputElement | null>(null);

  const statusColors: Record<string, string> = {
    pending: "bg-yellow-100 text-yellow-700",
    processing: "bg-blue-100 text-blue-700",
    processed: "bg-green-100 text-green-700",
    failed: "bg-red-100 text-red-700",
  };

  return (
    <tr className="border-b">
      <td className="py-3 px-2">{filename}</td>
      <td className="py-3 px-2">
        <span className={`inline-flex items-center rounded-full px-2 py-1 text-xs ${statusColors[currentStatus] || "bg-gray-100 text-gray-700"}`}>
          {currentStatus}
        </span>
      </td>
      <td className="py-3 px-2">{new Date(createdAt).toLocaleDateString()}</td>
      <td className="py-3 px-2">
        <div className="flex items-center gap-2">
          <Button
            variant="ghost"
            size="sm"
            disabled={currentStatus !== "processed" || !document}
            onClick={async () => {
              if (!document) return;
              const previewWindow = window.open("about:blank", "_blank");
              if (!previewWindow) return;
              previewWindow.opener = null;

              try {
                const blob = await downloadRagDocument(document);
                const url = URL.createObjectURL(blob);
                previewWindow.location.href = url;
                window.setTimeout(() => URL.revokeObjectURL(url), 60000);
              } catch (error) {
                previewWindow.close();
                throw error;
              }
            }}
          >
            View
          </Button>
          <input
            ref={replaceInputRef}
            type="file"
            accept=".pdf"
            className="hidden"
            onChange={async (event) => {
              const input = event.currentTarget;
              const file = input.files?.[0];
              if (!file) return;
              await onReplace(documentId, file);
              input.value = "";
            }}
          />
          <Button
            variant="outline"
            size="sm"
            disabled={currentStatus === "processing" || isReplacing}
            onClick={() => replaceInputRef.current?.click()}
          >
            {isReplacing ? "Replacing..." : "Replace PDF"}
          </Button>
        </div>
      </td>
    </tr>
  );
}
