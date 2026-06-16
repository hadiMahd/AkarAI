import { describe, expect, it, vi, beforeEach } from "vitest";
import { fireEvent, render, screen, waitFor } from "@testing-library/react";
import { SearchForm } from "@/features/search/SearchForm";

let extractIntentMock: ReturnType<typeof vi.fn>;
let logConfirmationMock: ReturnType<typeof vi.fn>;
let voiceSearchState: {
  state: "idle" | "recording" | "uploading" | "done" | "error";
  transcript: string | null;
  error: Error | null;
  result: {
    transcript?: { transcript?: string };
    intent: { filters: Record<string, unknown> };
  } | null;
};

vi.mock("@/features/search/useSearchIntent", () => ({
  useSearchIntent: () => ({ mutate: extractIntentMock, isPending: false }),
  useConfirmationLog: () => ({ mutate: logConfirmationMock }),
}));

vi.mock("@/features/search/useVoiceSearch", () => ({
  useVoiceSearch: () => ({
    ...voiceSearchState,
    startRecording: vi.fn(),
    stopRecording: vi.fn(),
    discard: vi.fn(),
  }),
}));

vi.mock("@/features/search/useListingCities", () => ({
  useListingCities: () => ({
    data: ["Beirut", "Jounieh"],
    isLoading: false,
  }),
}));

describe("SearchForm assistant fill behavior", () => {
  beforeEach(() => {
    extractIntentMock = vi.fn();
    logConfirmationMock = vi.fn();
    voiceSearchState = {
      state: "idle",
      transcript: null,
      error: null,
      result: null,
    };
  });

  it("keeps the manual form visible and fills fields from AI search results", async () => {
    const onFilterChange = vi.fn();

    extractIntentMock.mockImplementation((_query, { onSuccess }) => {
      onSuccess({
        intent: {
          filters: {
            city: "Beirut",
            property_type: "apartment",
            max_price: 1000,
            bedrooms: 2,
            listing_purpose: "rent",
          },
        },
      });
    });

    render(<SearchForm filters={{}} onFilterChange={onFilterChange} />);

    expect(screen.getByLabelText("City")).toBeInTheDocument();

    fireEvent.click(screen.getByTestId("ai-search-toggle"));
    fireEvent.change(screen.getByTestId("ai-search-input"), {
      target: { value: "2 bedroom apartment in Beirut under 1000" },
    });
    fireEvent.click(screen.getByTestId("ai-search-submit"));

    await waitFor(() => {
      expect(screen.getByTestId("city-filter-trigger")).toHaveTextContent("Beirut");
      expect(screen.getByTestId("selected-city-chips")).toHaveTextContent("Beirut");
      expect(screen.getByLabelText("Property Type")).toHaveValue("apartment");
      expect(screen.getByLabelText("Max Price")).toHaveValue(1000);
      expect(screen.getByLabelText("Min Bedrooms")).toHaveValue(2);
      expect(screen.getByLabelText("Purpose")).toHaveValue("rent");
    });

    expect(screen.getByTestId("assistant-applied-notice")).toHaveTextContent(
      "AI filters were applied to the search form below.",
    );
    expect(screen.queryByText("Interpreted filters:")).not.toBeInTheDocument();
    expect(onFilterChange).toHaveBeenCalled();
    expect(logConfirmationMock).toHaveBeenCalledWith({
      source_mode: "ai_text",
      confirmed_filters: {
        city: "Beirut",
        property_type: "apartment",
        max_price: 1000,
        bedrooms: 2,
        listing_purpose: "rent",
      },
    });
  });

  it("fills the manual form from voice results instead of rendering raw JSON", async () => {
    const onFilterChange = vi.fn();
    voiceSearchState = {
      state: "done",
      transcript: "2 bedroom apartment in Beirut under 1000 dollars",
      error: null,
      result: {
        intent: {
          filters: {
            city: "Beirut",
            max_price: 1000,
            bedrooms: 2,
          },
        },
      },
    };

    render(<SearchForm filters={{}} onFilterChange={onFilterChange} />);

    await waitFor(() => {
      expect(screen.getByTestId("city-filter-trigger")).toHaveTextContent("Beirut");
      expect(screen.getByLabelText("Max Price")).toHaveValue(1000);
      expect(screen.getByLabelText("Min Bedrooms")).toHaveValue(2);
    });

    expect(screen.getByTestId("assistant-applied-notice")).toHaveTextContent(
      "Voice filters were applied to the search form below.",
    );
    expect(screen.queryByText("Extracted filters:")).not.toBeInTheDocument();
    expect(onFilterChange).toHaveBeenCalled();
    expect(logConfirmationMock).toHaveBeenCalledWith({
      source_mode: "voice",
      confirmed_filters: {
        city: "Beirut",
        max_price: 1000,
        bedrooms: 2,
      },
    });
  });

  it("opens city picker on click and lets the user select multiple cities with checkboxes", async () => {
    const onFilterChange = vi.fn();

    render(<SearchForm filters={{}} onFilterChange={onFilterChange} />);

    fireEvent.click(screen.getByTestId("city-filter-trigger"));
    fireEvent.click(screen.getByRole("checkbox", { name: "Beirut" }));
    fireEvent.click(screen.getByRole("checkbox", { name: "Jounieh" }));

    await waitFor(() => {
      expect(screen.getByTestId("city-filter-trigger")).toHaveTextContent("2 cities selected");
      expect(screen.getByTestId("selected-city-chips")).toHaveTextContent("Beirut");
      expect(screen.getByTestId("selected-city-chips")).toHaveTextContent("Jounieh");
    });
  });
});
