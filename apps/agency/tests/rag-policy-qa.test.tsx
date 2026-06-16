import { vi } from "vitest";
import { screen, waitFor, fireEvent } from "@testing-library/react";
import userEvent from "@testing-library/user-event";
import { renderWithProviders } from "./test-utils";
import { RagAssistantPage, RagDocumentsPage, PENDING_PHRASES } from "@/pages/rag/RagDocumentsPage";
import { getTenantSession, getSession } from "@/lib/session/auth-session";
import { apiClient } from "@/lib/api/client";

vi.mock("@/lib/api/client", async (importOriginal) => {
  const actual = await importOriginal<typeof import("@/lib/api/client")>();
  return {
    ...actual,
    restoreSession: vi.fn().mockResolvedValue(false),
    apiClient: vi.fn(async (endpoint: string, _opts?: Record<string, unknown>) => {
      if (endpoint === "/api/v1/agencies/rag/documents" && (!_opts?.method || _opts.method === "GET")) {
        return {
          items: [
            {
              id: "doc-1", tenant_id: "tenant-1", filename: "policy.pdf",
              status: "processed", blob_path: "rag-vault/tenant-1/doc-1/original/policy.pdf",
              created_at: "2025-01-15T00:00:00Z", updated_at: "2025-01-15T00:00:00Z",
            },
          ],
          total: 1, page: 1, size: 20,
        };
      }
      if (endpoint === "/api/v1/agencies/rag/chat/threads" && (!_opts?.method || _opts.method === "GET")) {
        return {
          items: [
            {
              id: "thread-1",
              tenant_id: "tenant-1",
              owner_user_id: "user-1",
              title: "Parking policy followup",
              message_count: 2,
              created_at: "2025-01-15T00:00:00Z",
              updated_at: "2025-01-15T00:00:00Z",
              last_message_at: "2025-01-15T00:00:00Z",
            },
          ],
          total: 1,
          page: 1,
          size: 20,
        };
      }
      if (endpoint === "/api/v1/agencies/rag/chat/threads" && _opts?.method === "POST") {
        return {
          thread: {
            id: "thread-new",
            tenant_id: "tenant-1",
            owner_user_id: "user-1",
            title: "New conversation",
            message_count: 0,
            created_at: "2025-01-15T00:00:00Z",
            updated_at: "2025-01-15T00:00:00Z",
            last_message_at: "2025-01-15T00:00:00Z",
          },
          messages: [],
        };
      }
      if (endpoint === "/api/v1/agencies/rag/chat/threads/thread-1") {
        return {
          thread: {
            id: "thread-1",
            tenant_id: "tenant-1",
            owner_user_id: "user-1",
            title: "Parking policy followup",
            message_count: 2,
            created_at: "2025-01-15T00:00:00Z",
            updated_at: "2025-01-15T00:00:00Z",
            last_message_at: "2025-01-15T00:00:00Z",
          },
          messages: [
            {
              id: "msg-user-1",
              thread_id: "thread-1",
              tenant_id: "tenant-1",
              owner_user_id: "user-1",
              role: "user",
              content: "parking policy?",
              sequence_number: 1,
              created_at: "2025-01-15T00:00:00Z",
            },
            {
              id: "msg-assistant-1",
              thread_id: "thread-1",
              tenant_id: "tenant-1",
              owner_user_id: "user-1",
              role: "assistant",
              content: "Visitor parking is limited to 2 hours in designated areas.",
              sequence_number: 2,
              created_at: "2025-01-15T00:00:01Z",
              answer: {
                status: "answered",
                answer: "Visitor parking is limited to 2 hours in designated areas.\n\n- Use designated visitor bays.\n- After-hours access requires approval.",
                citations: [{
                  document_id: "doc-1", document_filename: "policy.pdf",
                  page_number: 1, source_label: "policy.pdf p.1",
                }],
                evidence: [{
                  chunk_id: "chunk-1", document_id: "doc-1", page_ids: ["page-1"],
                  document_filename: "policy.pdf", page_numbers: [1],
                  source_label: "policy.pdf p.1",
                  vector_rank: 1, vector_score: 0.89,
                  rerank_rank: 1, rerank_score: 0.95,
                  text_preview: "Official policy: visitor parking is limited to 2 hours.",
                  parent_page_text: "Full page text about visitor parking policy.",
                }],
                debug: {
                  reranker_used: true, reranker_provider: "openrouter",
                  fallback_reason: null, confidence_status: "sufficient",
                  retrieval_log_id: "log-1",
                  vector_candidate_count: 8, rerank_candidate_count: 5,
                },
              },
            },
          ],
        };
      }
      if (endpoint === "/api/v1/agencies/rag/chat/threads/thread-new") {
        return {
          thread: {
            id: "thread-new",
            tenant_id: "tenant-1",
            owner_user_id: "user-1",
            title: "New conversation",
            message_count: 0,
            created_at: "2025-01-15T00:00:00Z",
            updated_at: "2025-01-15T00:00:00Z",
            last_message_at: "2025-01-15T00:00:00Z",
          },
          messages: [],
        };
      }
      if (endpoint === "/api/v1/agencies/rag/chat/threads/thread-1/messages") {
        return {
          thread: {
            id: "thread-1",
            tenant_id: "tenant-1",
            owner_user_id: "user-1",
            title: "Parking policy followup",
            message_count: 4,
            created_at: "2025-01-15T00:00:00Z",
            updated_at: "2025-01-15T00:00:02Z",
            last_message_at: "2025-01-15T00:00:02Z",
          },
          user_message: {
            id: "msg-user-2",
            thread_id: "thread-1",
            tenant_id: "tenant-1",
            owner_user_id: "user-1",
            role: "user",
            content: "parking policy?",
            sequence_number: 3,
            created_at: "2025-01-15T00:00:02Z",
          },
          assistant_message: {
            id: "msg-assistant-2",
            thread_id: "thread-1",
            tenant_id: "tenant-1",
            owner_user_id: "user-1",
            role: "assistant",
            content: "Visitor parking is limited to 2 hours in designated areas.",
            sequence_number: 4,
            created_at: "2025-01-15T00:00:03Z",
            answer: {
              status: "answered",
              answer: "Visitor parking is limited to 2 hours in designated areas.\n\n- Use designated visitor bays.\n- After-hours access requires approval.",
              citations: [{
                document_id: "doc-1", document_filename: "policy.pdf",
                page_number: 1, source_label: "policy.pdf p.1",
              }],
              evidence: [{
                chunk_id: "chunk-1", document_id: "doc-1", page_ids: ["page-1"],
                document_filename: "policy.pdf", page_numbers: [1],
                source_label: "policy.pdf p.1",
                vector_rank: 1, vector_score: 0.89,
                rerank_rank: 1, rerank_score: 0.95,
                text_preview: "Official policy: visitor parking is limited to 2 hours.",
                parent_page_text: "Full page text about visitor parking policy.",
              }],
              debug: {
                reranker_used: true, reranker_provider: "openrouter",
                fallback_reason: null, confidence_status: "sufficient",
                retrieval_log_id: "log-2",
                vector_candidate_count: 8, rerank_candidate_count: 5,
              },
            },
          },
        };
      }
      if (endpoint === "/api/v1/agencies/rag/query") {
        return {
          status: "answered",
          answer: "Visitor parking is limited to 2 hours in designated areas.\n\n- Use designated visitor bays.\n- After-hours access requires approval.",
          citations: [{
            document_id: "doc-1", document_filename: "policy.pdf",
            page_number: 1, source_label: "policy.pdf p.1",
          }],
          evidence: [{
            chunk_id: "chunk-1", document_id: "doc-1", page_ids: ["page-1"],
            document_filename: "policy.pdf", page_numbers: [1],
            source_label: "policy.pdf p.1",
            vector_rank: 1, vector_score: 0.89,
            rerank_rank: 1, rerank_score: 0.95,
            text_preview: "Official policy: visitor parking is limited to 2 hours.",
            parent_page_text: "Full page text about visitor parking policy.",
          }],
          debug: {
            reranker_used: true, reranker_provider: "openrouter",
            fallback_reason: null, confidence_status: "sufficient",
            retrieval_log_id: "log-1",
            vector_candidate_count: 8, rerank_candidate_count: 5,
          },
        };
      }
      if (endpoint === "/api/v1/agencies/rag/retrieval-logs") {
        return {
          items: [{
            id: "log-1", tenant_id: "tenant-1", document_id: "doc-1",
            actor_user_id: "user-1", actor_role: "agency_admin",
            query: "parking policy", retrieval_scope: "single_document",
            selected_document_ids: ["doc-1"], selected_chunk_ids: ["chunk-1"],
            selected_page_ids: ["page-1"],
            reranker_used: true, reranker_provider: "openrouter",
            fallback_reason: null, confidence_status: "sufficient",
            retrieved_at: "2025-01-15T00:00:00Z",
            created_at: "2025-01-15T00:00:00Z",
          }],
          total: 1, page: 1, size: 20,
        };
      }
      return { items: [], total: 0, page: 1, size: 20 };
    }),
  };
});

vi.mock("@/lib/session/auth-session", async (importOriginal) => {
  const actual = await importOriginal<typeof import("@/lib/session/auth-session")>();
  return {
    ...actual,
    getSession: vi.fn(() => ({
      accessToken: "token",
      user: {
        id: "user-1", email: "admin@agency.test", name: "Admin",
        is_active: true, created_at: "", updated_at: "",
        role: "agency_admin", permissions: [], tenant_id: "tenant-1",
      },
    })),
    getTenantSession: vi.fn(() => ({
      userId: "user-1", tenantId: "tenant-1",
      role: "agency_admin", permissions: [], isActive: true,
    })),
  };
});

vi.mock("@/features/auth/useTenantSession", () => ({
  useTenantSession: vi.fn(() => ({
    session: {
      userId: "user-1", tenantId: "tenant-1",
      role: "agency_admin", permissions: [], isActive: true,
    },
    isLoading: false, error: null,
  })),
}));

describe("Policy Q&A", () => {
  afterEach(() => {
    vi.clearAllMocks();
  });

  it("renders the Policy Q&A card with heading", async () => {
    renderWithProviders(<RagAssistantPage />);
    await waitFor(() => {
      expect(screen.getAllByText("Policy Assistant").length).toBeGreaterThan(0);
    });
  });

  it("shows the query input form", async () => {
    renderWithProviders(<RagAssistantPage />);
    expect(screen.getByText(/choose a conversation or create a new one/i)).toBeInTheDocument();
  });

  it("loads a selected thread and displays the answer", async () => {
    renderWithProviders(<RagAssistantPage />);
    const user = userEvent.setup();
    await user.click(await screen.findByRole("button", { name: /parking policy followup/i }));

    await waitFor(() => {
      expect(screen.getByText(/visitor parking is limited/i)).toBeInTheDocument();
      expect(screen.getByRole("list")).toBeInTheDocument();
      expect(screen.getByText("parking policy?")).toBeInTheDocument();
    });
  });

  it("shows citations as badges", async () => {
    renderWithProviders(<RagAssistantPage />);
    const user = userEvent.setup();
    await user.click(await screen.findByRole("button", { name: /parking policy followup/i }));

    await waitFor(() => {
      expect(screen.getByText("policy.pdf p.1")).toBeInTheDocument();
    });
  });

  it("shows evidence and debug panel when toggled", async () => {
    renderWithProviders(<RagAssistantPage />);
    const user = userEvent.setup();
    await user.click(await screen.findByRole("button", { name: /parking policy followup/i }));

    await waitFor(() => {
      expect(screen.getByText(/visitor parking is limited/i)).toBeInTheDocument();
    });

    fireEvent.click(screen.getByText(/show evidence & debug/i));

    await waitFor(() => {
      expect(screen.getByText("Ranked Evidence")).toBeInTheDocument();
      expect(screen.getByText("Debug")).toBeInTheDocument();
    });
  });

  it("creates a new conversation and shows the composer", async () => {
    renderWithProviders(<RagAssistantPage />);
    const user = userEvent.setup();
    await user.click(screen.getByRole("button", { name: /new conversation/i }));

    await waitFor(() => {
      expect(screen.getByPlaceholderText(/message the policy assistant/i)).toBeInTheDocument();
    });
  });

  it("shows retrieval history section for admin", async () => {
    renderWithProviders(<RagDocumentsPage />);
    await waitFor(() => {
      expect(screen.getByText("Retrieval History")).toBeInTheDocument();
    });
  });

  it("shows retrieval logs in history table", async () => {
    renderWithProviders(<RagDocumentsPage />);
    await waitFor(() => {
      expect(screen.getByText("parking policy")).toBeInTheDocument();
      expect(screen.getByText("agency_admin")).toBeInTheDocument();
    });
  });
});

describe("Policy Q&A non-admin", () => {
  beforeEach(() => {
    vi.mocked(getTenantSession).mockReturnValue({
      userId: "user-2", tenantId: "tenant-1",
      role: "support_employee", permissions: [], isActive: true,
    });
    vi.mocked(getSession).mockReturnValue({
      accessToken: "token",
      user: {
        id: "user-2", email: "support@agency.test", name: "Support",
        is_active: true, created_at: "", updated_at: "",
        role: "support_employee", permissions: [], tenant_id: "tenant-1",
      },
    });
  });

  afterEach(() => {
    vi.clearAllMocks();
  });

  it("does not show retrieval history for non-admin", async () => {
    renderWithProviders(<RagDocumentsPage />);
    await waitFor(() => {
      expect(screen.queryByText("Retrieval History")).not.toBeInTheDocument();
    });
  });
});

describe("Empty state", () => {
  beforeEach(() => {
    vi.mocked(getTenantSession).mockReturnValue({
      userId: "user-1", tenantId: "tenant-1",
      role: "agency_admin", permissions: [], isActive: true,
    });
  });

  it("shows no-documents state", async () => {
    renderWithProviders(<RagDocumentsPage />);
    await waitFor(() => {
      expect(screen.getByText("Policy Documents")).toBeInTheDocument();
    });
  });
});

describe("Pending assistant bubble", () => {
  let resolveSend: (v: unknown) => void;
  let rejectSend: (e: Error) => void;

  beforeEach(() => {
    vi.mocked(apiClient).mockImplementation(async (endpoint, opts) => {
      if (typeof endpoint === "string" && /\/messages$/.test(endpoint)) {
        return new Promise((res, rej) => { resolveSend = res; rejectSend = rej; });
      }
      if (endpoint === "/api/v1/agencies/rag/documents" && (!opts?.method || opts.method === "GET")) {
        return { items: [{ id: "doc-1", tenant_id: "tenant-1", filename: "policy.pdf", status: "processed", blob_path: "rag-vault/tenant-1/doc-1/original/policy.pdf", created_at: "2025-01-15T00:00:00Z", updated_at: "2025-01-15T00:00:00Z" }], total: 1, page: 1, size: 20 };
      }
      if (endpoint === "/api/v1/agencies/rag/chat/threads" && (!opts?.method || opts.method === "GET")) {
        return { items: [{ id: "thread-1", tenant_id: "tenant-1", owner_user_id: "user-1", title: "Parking policy followup", message_count: 2, created_at: "2025-01-15T00:00:00Z", updated_at: "2025-01-15T00:00:00Z", last_message_at: "2025-01-15T00:00:00Z" }], total: 1, page: 1, size: 20 };
      }
      if (endpoint === "/api/v1/agencies/rag/chat/threads/thread-1") {
        return {
          thread: { id: "thread-1", tenant_id: "tenant-1", owner_user_id: "user-1", title: "Parking policy followup", message_count: 2, created_at: "2025-01-15T00:00:00Z", updated_at: "2025-01-15T00:00:00Z", last_message_at: "2025-01-15T00:00:00Z" },
          messages: [
            { id: "msg-user-1", thread_id: "thread-1", tenant_id: "tenant-1", owner_user_id: "user-1", role: "user", content: "parking policy?", sequence_number: 1, created_at: "2025-01-15T00:00:00Z" },
            { id: "msg-assistant-1", thread_id: "thread-1", tenant_id: "tenant-1", owner_user_id: "user-1", role: "assistant", content: "Visitor parking is limited to 2 hours.", sequence_number: 2, created_at: "2025-01-15T00:00:01Z", answer: { status: "answered", answer: "Visitor parking is limited to 2 hours.", citations: [{ document_id: "doc-1", document_filename: "policy.pdf", page_number: 1, source_label: "policy.pdf p.1" }], evidence: [], debug: { reranker_used: false, reranker_provider: null, fallback_reason: null, confidence_status: "sufficient", retrieval_log_id: "log-1", vector_candidate_count: 8, rerank_candidate_count: 0 } } },
          ],
        };
      }
      return { items: [], total: 0, page: 1, size: 20 };
    });
  });

  afterEach(() => {
    vi.clearAllMocks();
  });

  async function setupAndSubmit() {
    renderWithProviders(<RagAssistantPage />);
    const user = userEvent.setup();
    await user.click(await screen.findByRole("button", { name: /parking policy followup/i }));
    await waitFor(() => expect(screen.getByText("parking policy?")).toBeInTheDocument());
    await user.type(screen.getByPlaceholderText(/message the policy assistant/i), "what about overtime?");
    fireEvent.click(screen.getByRole("button", { name: /send/i }));
    await waitFor(() => expect(screen.getByTestId("pending-assistant-bubble")).toBeInTheDocument());
  }

  it("shows pending assistant bubble immediately after submit", async () => {
    await setupAndSubmit();
    expect(screen.getByTestId("pending-assistant-bubble")).toBeInTheDocument();
  });

  it("displays one of the known status phrases in the pending bubble", async () => {
    await setupAndSubmit();
    const bubble = screen.getByTestId("pending-assistant-bubble");
    expect(PENDING_PHRASES.some((p) => bubble.textContent?.includes(p))).toBe(true);
  });

  it("removes the pending bubble when the response arrives", async () => {
    await setupAndSubmit();
    resolveSend({
      thread: {
        id: "thread-1", tenant_id: "tenant-1", owner_user_id: "user-1",
        title: "Parking policy followup", message_count: 4,
        created_at: "2025-01-15T00:00:00Z", updated_at: "2025-01-15T00:00:02Z",
        last_message_at: "2025-01-15T00:00:02Z",
      },
      user_message: {
        id: "msg-user-2", thread_id: "thread-1", tenant_id: "tenant-1",
        owner_user_id: "user-1", role: "user", content: "what about overtime?",
        sequence_number: 3, created_at: "2025-01-15T00:00:02Z",
      },
      assistant_message: {
        id: "msg-assistant-2", thread_id: "thread-1", tenant_id: "tenant-1",
        owner_user_id: "user-1", role: "assistant", content: "Overtime answer",
        sequence_number: 4, created_at: "2025-01-15T00:00:03Z",
        answer: {
          status: "answered", answer: "Overtime requires manager approval.",
          citations: [], evidence: [],
          debug: {
            reranker_used: false, reranker_provider: null, fallback_reason: null,
            confidence_status: "sufficient", retrieval_log_id: "log-2",
            vector_candidate_count: 8, rerank_candidate_count: 0,
          },
        },
      },
    });
    await waitFor(() => {
      expect(screen.queryByTestId("pending-assistant-bubble")).not.toBeInTheDocument();
    });
  });

  it("removes the pending bubble when send fails", async () => {
    await setupAndSubmit();
    rejectSend(new Error("Network error"));
    await waitFor(() => {
      expect(screen.queryByTestId("pending-assistant-bubble")).not.toBeInTheDocument();
    });
  });
});

describe("Operational assistant answers", () => {
  beforeEach(() => {
    vi.mocked(getTenantSession).mockReturnValue({
      userId: "user-1", tenantId: "tenant-1",
      role: "support_employee", permissions: [], isActive: true,
    });
  });

  afterEach(() => {
    vi.clearAllMocks();
  });

  it("renders operational answer (lead summary) for 'last 5 leads'", async () => {
    let resolveSend: (v: unknown) => void;
    vi.mocked(apiClient).mockImplementation(async (endpoint, opts) => {
      if (typeof endpoint === "string" && /\/messages$/.test(endpoint)) {
        return new Promise((res) => { resolveSend = res; });
      }
      if (endpoint === "/api/v1/agencies/rag/documents" && (!opts?.method || opts.method === "GET")) {
        return {
          items: [
            { id: "doc-1", tenant_id: "tenant-1", filename: "policy.pdf", status: "processed", blob_path: "rag-vault/tenant-1/doc-1/original/policy.pdf", created_at: "2025-01-15T00:00:00Z", updated_at: "2025-01-15T00:00:00Z" },
          ],
          total: 1, page: 1, size: 20,
        };
      }
      if (endpoint === "/api/v1/agencies/rag/chat/threads" && (!opts?.method || opts.method === "GET")) {
        return {
          items: [
            { id: "thread-1", tenant_id: "tenant-1", owner_user_id: "user-1", title: "Operational queries", message_count: 2, created_at: "2025-01-15T00:00:00Z", updated_at: "2025-01-15T00:00:01Z", last_message_at: "2025-01-15T00:00:01Z" },
          ],
          total: 1, page: 1, size: 20,
        };
      }
      if (endpoint === "/api/v1/agencies/rag/chat/threads/thread-1") {
        return {
          thread: { id: "thread-1", tenant_id: "tenant-1", owner_user_id: "user-1", title: "Operational queries", message_count: 2, created_at: "2025-01-15T00:00:00Z", updated_at: "2025-01-15T00:00:01Z", last_message_at: "2025-01-15T00:00:01Z" },
          messages: [
            { id: "msg-user-0", thread_id: "thread-1", tenant_id: "tenant-1", owner_user_id: "user-1", role: "user", content: "hello", sequence_number: 1, created_at: "2025-01-15T00:00:00Z" },
            { id: "msg-assistant-0", thread_id: "thread-1", tenant_id: "tenant-1", owner_user_id: "user-1", role: "assistant", content: "Hi there", sequence_number: 2, created_at: "2025-01-15T00:00:01Z", answer: { status: "answered", answer: "Hi there", citations: [], evidence: [], debug: { reranker_used: false, reranker_provider: null, fallback_reason: null, confidence_status: "sufficient", retrieval_log_id: "log-0", vector_candidate_count: 0, rerank_candidate_count: 0 } } },
          ],
        };
      }
      return { items: [], total: 0, page: 1, size: 20 };
    });

    renderWithProviders(<RagAssistantPage />);
    const user = userEvent.setup();
    await user.click(await screen.findByRole("button", { name: /operational queries/i }));
    await waitFor(() => {
      expect(screen.getByPlaceholderText(/message the policy assistant/i)).toBeInTheDocument();
    });
    await user.type(
      screen.getByPlaceholderText(/message the policy assistant/i),
      "show me the last 5 leads",
    );
    fireEvent.click(screen.getByRole("button", { name: /send/i }));
    await waitFor(() => expect(screen.getByTestId("pending-assistant-bubble")).toBeInTheDocument());

    resolveSend({
      thread: {
        id: "thread-1", tenant_id: "tenant-1", owner_user_id: "user-1",
        title: "Operational queries", message_count: 4,
        created_at: "2025-01-15T00:00:00Z", updated_at: "2025-01-15T00:00:03Z",
        last_message_at: "2025-01-15T00:00:03Z",
      },
      user_message: {
        id: "msg-user-op", thread_id: "thread-1", tenant_id: "tenant-1",
        owner_user_id: "user-1", role: "user",
        content: "show me the last 5 leads", sequence_number: 3,
        created_at: "2025-01-15T00:00:02Z",
      },
      assistant_message: {
        id: "msg-assistant-op", thread_id: "thread-1", tenant_id: "tenant-1",
        owner_user_id: "user-1", role: "assistant",
        content: "Here are the most recent leads in your tenant: Layla status new email layla@example.com",
        sequence_number: 4, created_at: "2025-01-15T00:00:03Z",
        answer: {
          status: "answered",
          answer: "Here are the most recent leads in your tenant: Layla status new email layla@example.com",
          citations: [], evidence: [],
          debug: {
            reranker_used: false, reranker_provider: null, fallback_reason: null,
            confidence_status: "sufficient", retrieval_log_id: "log-op",
            vector_candidate_count: 0, rerank_candidate_count: 0,
            tool_invocations: [
              { tool_name: "list_recent_leads", input_summary: { limit: 5 }, output_summary: { count: 1 } },
            ],
          },
        },
      },
    });
    await waitFor(() => {
      // The assistant answer is rendered as Markdown which may split
      // the text into multiple elements. We check the document body
      // directly for the substring.
      const body = document.body.textContent ?? "";
      expect(body).toContain("Here are the most recent leads");
      expect(body).toContain("Layla");
    });
  });

  it("support employee can navigate to assistant page", async () => {
    vi.mocked(apiClient).mockImplementation(async (endpoint, opts) => {
      if (endpoint === "/api/v1/agencies/rag/documents" && (!opts?.method || opts.method === "GET")) {
        return { items: [], total: 0, page: 1, size: 20 };
      }
      if (endpoint === "/api/v1/agencies/rag/chat/threads" && (!opts?.method || opts.method === "GET")) {
        return { items: [], total: 0, page: 1, size: 20 };
      }
      return { items: [], total: 0, page: 1, size: 20 };
    });

    renderWithProviders(<RagAssistantPage />);
    await waitFor(() => {
      expect(screen.getByText(/Policy Assistant/i)).toBeInTheDocument();
    });
  });
});
