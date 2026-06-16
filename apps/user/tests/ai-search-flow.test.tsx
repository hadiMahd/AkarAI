import { describe, it, expect, vi } from "vitest";

describe("AI Search Flow", () => {
  describe("useSearchIntent hook — endpoint paths", () => {
    it("hook exists and is importable", async () => {
      const mod = await import("@/features/search/useSearchIntent");
      expect(mod).toBeDefined();
      expect(typeof mod.useSearchIntent).toBe("function");
      expect(typeof mod.useConfirmationLog).toBe("function");
    });

    it("POSTs to /search/intent (not /api/v1/search/intent) when querying", async () => {
      let capturedUrl = "";
      vi.stubGlobal("fetch", vi.fn((url: string) => {
        capturedUrl = url;
        return Promise.resolve({
          ok: true,
          json: () => Promise.resolve({
            intent: { source_mode: "ai_text", filters: { city: "Beirut" }, confidence: "high" },
          }),
        });
      }));

      const { QueryClient, QueryClientProvider } = await import("@tanstack/react-query");
      const React = await import("react");
      const { renderHook, act } = await import("@testing-library/react");
      const { useSearchIntent } = await import("@/features/search/useSearchIntent");

      const qc = new QueryClient({ defaultOptions: { mutations: { retry: false } } });
      const wrapper = ({ children }: { children: React.ReactNode }) =>
        React.createElement(QueryClientProvider, { client: qc }, children);

      const { result } = renderHook(() => useSearchIntent(), { wrapper });

      await act(async () => {
        result.current.mutate("2BR apartment in Beirut");
        await new Promise((r) => setTimeout(r, 50));
      });

      expect(capturedUrl).toContain("/search/intent");
      expect(capturedUrl).not.toContain("/api/v1");
      vi.restoreAllMocks();
    });
  });

  describe("Vague location handling", () => {
    it("placeholder: vague location warning shown when unclear_location present", () => {
      expect(true).toBe(true);
    });

    it("placeholder: continue without location clears city filter", () => {
      expect(true).toBe(true);
    });
  });

  describe("AI confirmation panel", () => {
    it("placeholder: confirmation panel shown after AI search", () => {
      expect(true).toBe(true);
    });

    it("placeholder: apply search triggers filter update", () => {
      expect(true).toBe(true);
    });
  });
});
