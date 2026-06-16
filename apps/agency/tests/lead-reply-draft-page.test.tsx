import { describe, it, expect, vi } from "vitest";
import { render, screen, waitFor } from "@testing-library/react";
import userEvent from "@testing-library/user-event";
import { MemoryRouter, Route, Routes } from "react-router-dom";
import { LeadReviewForm } from "@/features/leads/LeadReviewForm";

vi.mock("@/features/leads/useAgencyLeads", () => ({
  useLeadDetail: () => ({
    lead: {
      id: "lead-123",
      name: "Amin",
      email: "amin@example.com",
      phone: "123",
      status: "new",
      message: "Need details",
      created_at: new Date().toISOString(),
    },
    isLoading: false,
    reviewLead: vi.fn(),
    isReviewing: false,
  }),
}));

vi.mock("@/features/agencyAi/useAgencyAi", () => ({
  useLeadReplyDraft: () => ({
    mutateAsync: vi.fn(async ({ channel }: { leadId: string; channel: "email" | "whatsapp" }) => ({
      job_id: "reply-1",
      status: "completed",
      channel,
      subject: channel === "email" ? "Re: Inquiry" : undefined,
      body: channel === "email" ? "Thanks for reaching out." : "Thanks for reaching out.",
    })),
    isPending: false,
    error: null,
  }),
}));

describe("LeadReviewForm", () => {
  it("shows AI reply draft actions and renders a draft preview", async () => {
    const user = userEvent.setup();
    render(
      <MemoryRouter initialEntries={["/leads/lead-123"]}>
        <Routes>
          <Route path="/leads/:leadId" element={<LeadReviewForm />} />
        </Routes>
      </MemoryRouter>,
    );

    await user.click(screen.getByRole("button", { name: /draft email reply/i }));

    await waitFor(() => {
      expect(screen.getByText(/ai reply draft/i)).toBeInTheDocument();
      expect(screen.getByText(/Re: Inquiry/i)).toBeInTheDocument();
      expect(screen.getByText(/Thanks for reaching out/i)).toBeInTheDocument();
    });
  });
});
