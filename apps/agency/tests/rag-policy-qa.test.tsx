import { vi } from "vitest";
import { screen, waitFor, fireEvent } from "@testing-library/react";
import userEvent from "@testing-library/user-event";
import { renderWithProviders } from "./test-utils";
import { RagAssistantPage, RagDocumentsPage } from "@/pages/rag/RagDocumentsPage";
import { getTenantSession, getSession } from "@/lib/session/auth-session";

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
