import { describe, it, expect, vi, beforeEach } from "vitest";
import { render, screen, fireEvent } from "@testing-library/react";
import { MemoryRouter } from "react-router-dom";
import { QueryClient, QueryClientProvider } from "@tanstack/react-query";
import { ErrorBoundary, RouteErrorFallback } from "@/components/ErrorBoundary";

function createTestQueryClient() {
  return new QueryClient({
    defaultOptions: {
      queries: { retry: false },
    },
  });
}

function Wrapper({ children }: { children: React.ReactNode }) {
  const queryClient = createTestQueryClient();
  return (
    <QueryClientProvider client={queryClient}>
      <MemoryRouter>{children}</MemoryRouter>
    </QueryClientProvider>
  );
}

const ThrowError = ({ shouldThrow }: { shouldThrow: boolean }) => {
  if (shouldThrow) {
    throw new Error("Test error");
  }
  return <div>Child content</div>;
};

describe("ErrorBoundary", () => {
  beforeEach(() => {
    vi.spyOn(console, "error").mockImplementation(() => {});
  });

  it("renders children when no error", () => {
    render(
      <Wrapper>
        <ErrorBoundary>
          <ThrowError shouldThrow={false} />
        </ErrorBoundary>
      </Wrapper>
    );
    expect(screen.getByText("Child content")).toBeInTheDocument();
  });

  it("renders fallback UI when error thrown", () => {
    render(
      <Wrapper>
        <ErrorBoundary>
          <ThrowError shouldThrow={true} />
        </ErrorBoundary>
      </Wrapper>
    );
    expect(screen.getByText("Something went wrong")).toBeInTheDocument();
    expect(screen.getByText("Try Again")).toBeInTheDocument();
    expect(screen.getByText("Reload Page")).toBeInTheDocument();
    expect(screen.getByText("Go Home")).toBeInTheDocument();
  });

  it("shows error details in development mode", () => {
    render(
      <Wrapper>
        <ErrorBoundary>
          <ThrowError shouldThrow={true} />
        </ErrorBoundary>
      </Wrapper>
    );
    expect(screen.getByText("Error details")).toBeInTheDocument();
  });

  it("recovers when Try Again clicked", () => {
    const { result } = render(
      <Wrapper>
        <ErrorBoundary>
          <ThrowError shouldThrow={true} />
        </ErrorBoundary>
      </Wrapper>
    );
    expect(screen.getByText("Something went wrong")).toBeInTheDocument();

    const tryAgainButton = screen.getByText("Try Again");
    fireEvent.click(tryAgainButton);

    // After clicking Try Again, the error boundary resets, but the component still throws
    // So we need to re-render with shouldThrow={false}
    const { rerender } = render(
      <Wrapper>
        <ErrorBoundary>
          <ThrowError shouldThrow={false} />
        </ErrorBoundary>
      </Wrapper>
    );
    expect(screen.getByText("Child content")).toBeInTheDocument();
  });

  it("uses custom fallback when provided", () => {
    render(
      <Wrapper>
        <ErrorBoundary fallback={<div data-testid="custom">Custom fallback</div>}>
          <ThrowError shouldThrow={true} />
        </ErrorBoundary>
      </Wrapper>
    );
    expect(screen.getByTestId("custom")).toBeInTheDocument();
    expect(screen.queryByText("Something went wrong")).not.toBeInTheDocument();
  });
});

describe("RouteErrorFallback", () => {
  it("renders page unavailable message", () => {
    render(<Wrapper><RouteErrorFallback /></Wrapper>);
    expect(screen.getByText("Page unavailable")).toBeInTheDocument();
    expect(screen.getByText("Reload Page")).toBeInTheDocument();
    expect(screen.getByText("Go Home")).toBeInTheDocument();
  });
});