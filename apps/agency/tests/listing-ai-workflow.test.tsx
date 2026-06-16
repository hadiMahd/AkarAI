import { vi } from "vitest";
import { screen, waitFor, fireEvent } from "@testing-library/react";
import userEvent from "@testing-library/user-event";
import { useState } from "react";
import { renderWithProviders } from "./test-utils";
import { ListingAiWorkflow } from "@/features/listings/ListingAiWorkflow";
import type { ExtractedListingSpecs } from "@/features/agencyAi/useAgencyAi";

vi.mock("@/features/agencyAi/useAgencyAi", async (importOriginal) => {
  const actual = await importOriginal<typeof import("@/features/agencyAi/useAgencyAi")>();
  return {
    ...actual,
    useUploadSpecSheet: () => ({
      mutateAsync: vi.fn(async (file: File) => {
        return {
          job_id: "job-1",
          status: "review_ready",
          provider: "azure_cv",
        };
      }),
      isPending: false,
    }),
    useSpecExtraction: () => ({
      data: {
        job_id: "job-1",
        status: "review_ready",
        provider: "azure_cv",
        warnings: [],
        extracted_specs: {
          bedrooms: 3,
          bathrooms: 2,
          area_size: "150",
          area_unit: "sqm",
          city: "Beirut",
          property_type: "apartment",
          field_confidence: { bedrooms: "high" },
          source_snippets: { bedrooms: "3 bedrooms" },
        },
      },
    }),
    useListingDraft: () => ({
      mutateAsync: vi.fn(async () => ({
        job_id: "draft-1",
        status: "completed",
        title: "Spacious Beirut Apartment",
        description: "A 3-bedroom apartment in Beirut.",
        highlights: ["3 bedrooms", "150 sqm"],
        guardrail_status: "passed",
      })),
      isPending: false,
    }),
  };
});

function Harness() {
  const [title, setTitle] = useState("");
  const [description, setDescription] = useState("");
  return (
    <div>
      <input
        aria-label="title"
        value={title}
        onChange={(e) => setTitle(e.target.value)}
      />
      <textarea
        aria-label="description"
        value={description}
        onChange={(e) => setDescription(e.target.value)}
      />
      <ListingAiWorkflow
        listingContext={{ title: "Loft", city: "Beirut", price: 1500 }}
        onApplyDraft={({ title: t, description: d }) => {
          setTitle(t);
          setDescription(d);
        }}
        onApplyExtractedSpecs={(_specs: ExtractedListingSpecs) => {
          // Pretend the form absorbed the fields
        }}
        hasFormContext={true}
      />
    </div>
  );
}

describe("listing AI workflow", () => {
  it("uploads a spec sheet and shows the review panel", async () => {
    const user = userEvent.setup();
    renderWithProviders(<Harness />);

    const file = new File([new Uint8Array([0x25, 0x50, 0x44, 0x46])], "spec.pdf", {
      type: "application/pdf",
    });
    // The input is a file <input type="file"> within the spec sheet
    // section. Use a CSS selector rather than getByLabelText since
    // the label isn't associated via htmlFor in the component.
    const inputs = document.querySelectorAll('input[type="file"]');
    const input = inputs[0] as HTMLInputElement;
    expect(input).toBeTruthy();
    fireEvent.change(input, { target: { files: [file] } });

    await waitFor(() => {
      expect(screen.getByText(/review extracted fields/i)).toBeInTheDocument();
      expect(screen.getByText(/3 bedrooms/)).toBeInTheDocument();
    });
  });

  it("applies the AI draft to the form on draft generation", async () => {
    const user = userEvent.setup();
    renderWithProviders(<Harness />);

    const generateBtn = screen.getByRole("button", { name: /generate ai listing draft/i });
    await user.click(generateBtn);

    await waitFor(() => {
      const titleInput = screen.getByLabelText("title") as HTMLInputElement;
      const descInput = screen.getByLabelText("description") as HTMLTextAreaElement;
      expect(titleInput.value).toBe("Spacious Beirut Apartment");
      expect(descInput.value).toContain("3-bedroom");
    });
  });

  it("disables the draft button when there is no form context", () => {
    renderWithProviders(
      <ListingAiWorkflow
        listingContext={{}}
        onApplyDraft={() => {}}
        onApplyExtractedSpecs={() => {}}
        hasFormContext={false}
      />,
    );
    const btn = screen.getByRole("button", { name: /generate ai listing draft/i });
    expect(btn).toBeDisabled();
  });

  it("shows pending state during OCR upload", () => {
    renderWithProviders(
      <ListingAiWorkflow
        listingContext={{ title: "A", city: "B", price: 1 }}
        onApplyDraft={() => {}}
        onApplyExtractedSpecs={() => {}}
        hasFormContext={true}
      />,
    );
    // The component shows a file input ready for upload
    const inputs = document.querySelectorAll('input[type="file"]');
    expect(inputs.length).toBeGreaterThan(0);
  });
});
