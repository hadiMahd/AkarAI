import { vi } from "vitest";
import { screen, waitFor, fireEvent } from "@testing-library/react";
import userEvent from "@testing-library/user-event";
import { useState } from "react";
import { renderWithProviders } from "./test-utils";
import { useLeadReplyDraft } from "@/features/agencyAi/useAgencyAi";

vi.mock("@/features/agencyAi/useAgencyAi", async (importOriginal) => {
  const actual = await importOriginal<typeof import("@/features/agencyAi/useAgencyAi")>();
  return {
    ...actual,
    useLeadReplyDraft: () => ({
      mutateAsync: vi.fn(async (_leadId: string, channel: "email" | "whatsapp") => ({
        job_id: "job-reply-1",
        status: "completed",
        channel,
        subject: channel === "email" ? "Re: Your inquiry" : undefined,
        body: "Hi there, thanks for reaching out...",
        guardrail_status: "passed",
      })),
      isPending: false,
    }),
  };
});

function Harness() {
  const [result, setResult] = useState<{
    body: string;
    subject?: string;
  } | null>(null);
  const mutation = useLeadReplyDraft();
  return (
    <div>
      <button
        type="button"
        onClick={() =>
          mutation.mutateAsync("lead-123", "email").then((r) =>
            setResult({ body: r.body || "", subject: r.subject || "" }),
          )
        }
      >
        Generate email draft
      </button>
      <button
        type="button"
        onClick={() =>
          mutation.mutateAsync("lead-123", "whatsapp").then((r) =>
            setResult({ body: r.body || "" }),
          )
        }
      >
        Generate whatsapp draft
      </button>
      {result && (
        <div data-testid="reply-preview">
          {result.subject && <p data-testid="reply-subject">{result.subject}</p>}
          <p data-testid="reply-body">{result.body}</p>
        </div>
      )}
    </div>
  );
}

describe("lead reply draft UI", () => {
  it("renders an email draft with subject and body", async () => {
    const user = userEvent.setup();
    renderWithProviders(<Harness />);

    await user.click(screen.getByRole("button", { name: /generate email draft/i }));

    await waitFor(() => {
      expect(screen.getByTestId("reply-subject")).toHaveTextContent("Re: Your inquiry");
      expect(screen.getByTestId("reply-body")).toHaveTextContent(/Hi there/);
    });
  });

  it("renders a whatsapp draft with body only", async () => {
    const user = userEvent.setup();
    renderWithProviders(<Harness />);

    await user.click(screen.getByRole("button", { name: /generate whatsapp draft/i }));

    await waitFor(() => {
      expect(screen.getByTestId("reply-body")).toHaveTextContent(/Hi there/);
      expect(screen.queryByTestId("reply-subject")).not.toBeInTheDocument();
    });
  });
});
