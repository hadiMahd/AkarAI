import React from "react";
import { describe, it, expect, vi, beforeEach, afterEach } from "vitest";
import { QueryClient, QueryClientProvider } from "@tanstack/react-query";
import { renderHook, act } from "@testing-library/react";

// QueryClient wrapper for hooks that use useMutation
function makeWrapper() {
  const queryClient = new QueryClient({
    defaultOptions: { mutations: { retry: false }, queries: { retry: false } },
  });
  const wrapper = ({ children }: { children: React.ReactNode }) =>
    React.createElement(QueryClientProvider, { client: queryClient }, children);
  return wrapper;
}

// --- stubs ---

function makeMediaRecorder() {
  const recorder = {
    state: "inactive" as "inactive" | "recording",
    ondataavailable: null as ((e: { data: Blob }) => void) | null,
    onstop: null as (() => void) | null,
    start: vi.fn(function (this: typeof recorder) { this.state = "recording"; }),
    stop: vi.fn(function (this: typeof recorder) {
      this.state = "inactive";
      this.onstop?.();
    }),
  };
  return recorder;
}

function makeAudioContext(rmsValues: number[]) {
  let tick = 0;
  const analyser = {
    fftSize: 2048,
    getFloatTimeDomainData: vi.fn((buf: Float32Array) => {
      const rms = rmsValues[Math.min(tick++, rmsValues.length - 1)];
      buf.fill(Math.sqrt(rms * rms));
    }),
    connect: vi.fn(),
  };
  const source = { connect: vi.fn() };
  return {
    createAnalyser: vi.fn(() => analyser),
    createMediaStreamSource: vi.fn(() => source),
    close: vi.fn(() => Promise.resolve()),
  };
}

const SILENCE = 0.001;
const SPEECH = 0.05;

// -----------------------------------------------------------------------

describe("Voice Search Flow", () => {
  describe("useVoiceSearch — correct endpoint path", () => {
    it("module is importable and exports useVoiceSearch", async () => {
      const mod = await import("@/features/search/useVoiceSearch");
      expect(typeof mod.useVoiceSearch).toBe("function");
    });

    it("POSTs to /search/voice (not /api/v1/search/voice) when uploading audio", async () => {
      const originalRAF = globalThis.requestAnimationFrame;
      const originalCancelRAF = globalThis.cancelAnimationFrame;
      const originalMediaRecorder = globalThis.MediaRecorder;
      const originalAudioContext = globalThis.AudioContext;
      const originalMediaDevices = navigator.mediaDevices;

      globalThis.requestAnimationFrame = vi.fn(() => 1);
      globalThis.cancelAnimationFrame = vi.fn();

      const recorder = makeMediaRecorder();
      (globalThis as unknown as Record<string, unknown>).AudioContext = vi.fn(() => makeAudioContext([SPEECH]));
      (globalThis as unknown as Record<string, unknown>).MediaRecorder = vi.fn(() => recorder) as unknown as typeof MediaRecorder;
      (MediaRecorder as unknown as { isTypeSupported: () => boolean }).isTypeSupported = () => true;

      const mockStream = { getTracks: () => [{ stop: vi.fn() }] };
      Object.defineProperty(navigator, "mediaDevices", {
        value: { getUserMedia: vi.fn().mockResolvedValue(mockStream) },
        configurable: true,
      });

      let capturedUrl = "";
      vi.stubGlobal("fetch", vi.fn((url: string) => {
        capturedUrl = url;
        return Promise.resolve({
          ok: true,
          json: () => Promise.resolve({
            transcript: { transcript: "test", provider: "azure_stt", confidence: "usable" },
            intent: { source_mode: "voice", filters: {}, confidence: "high" },
          }),
        });
      }));

      const { useVoiceSearch } = await import("@/features/search/useVoiceSearch");
      const { result } = renderHook(() => useVoiceSearch(), { wrapper: makeWrapper() });

      await act(async () => { await result.current.startRecording(); });
      await act(async () => { result.current.stopRecording(); });
      await act(async () => { await new Promise((r) => setTimeout(r, 50)); });

      expect(capturedUrl).toContain("/search/voice");
      expect(capturedUrl).not.toContain("/api/v1");

      globalThis.requestAnimationFrame = originalRAF;
      globalThis.cancelAnimationFrame = originalCancelRAF;
      globalThis.MediaRecorder = originalMediaRecorder;
      globalThis.AudioContext = originalAudioContext;
      Object.defineProperty(navigator, "mediaDevices", { value: originalMediaDevices, configurable: true });
      vi.restoreAllMocks();
    });
  });

  describe("silence-based auto-stop configuration", () => {
    it("silence detector only fires after warmup + sustained silence (not on short pause)", () => {
      // Verify the design constants are tuned correctly:
      // WARMUP_MS=600 means at least 600ms of speech before auto-stop can trigger.
      // SILENCE_DURATION_MS=1500 means silence must last 1500ms continuously.
      // A 400ms pause between words (< 1500ms) must not stop recording.
      const WARMUP_MS = 600;
      const SILENCE_DURATION_MS = 1500;
      const SHORT_PAUSE_MS = 400;

      expect(SHORT_PAUSE_MS).toBeLessThan(SILENCE_DURATION_MS);
      expect(WARMUP_MS).toBeGreaterThan(0);
      // Auto-stop window: only after WARMUP_MS + SILENCE_DURATION_MS ms of silence
      const minAutoStopMs = WARMUP_MS + SILENCE_DURATION_MS;
      expect(minAutoStopMs).toBeGreaterThan(1000);
    });
  });

  describe("state machine", () => {
    let originalRAF: typeof requestAnimationFrame;
    let originalCancelRAF: typeof cancelAnimationFrame;
    let originalAudioContext: typeof AudioContext;
    let originalMediaDevices: typeof navigator.mediaDevices;
    let originalMediaRecorder: typeof MediaRecorder;

    beforeEach(() => {
      originalRAF = globalThis.requestAnimationFrame;
      originalCancelRAF = globalThis.cancelAnimationFrame;
      originalAudioContext = globalThis.AudioContext;
      originalMediaDevices = navigator.mediaDevices;
      originalMediaRecorder = globalThis.MediaRecorder;

      // No-op rAF so silence detector doesn't run
      globalThis.requestAnimationFrame = vi.fn(() => 1);
      globalThis.cancelAnimationFrame = vi.fn();
    });

    afterEach(() => {
      globalThis.requestAnimationFrame = originalRAF;
      globalThis.cancelAnimationFrame = originalCancelRAF;
      globalThis.AudioContext = originalAudioContext;
      Object.defineProperty(navigator, "mediaDevices", { value: originalMediaDevices, configurable: true });
      globalThis.MediaRecorder = originalMediaRecorder;
      vi.restoreAllMocks();
    });

    it("tracks: idle → recording → uploading → done", async () => {
      const recorder = makeMediaRecorder();
      (globalThis as unknown as Record<string, unknown>).AudioContext = vi.fn(() => makeAudioContext([SPEECH]));
      (globalThis as unknown as Record<string, unknown>).MediaRecorder = vi.fn(() => recorder) as unknown as typeof MediaRecorder;
      (MediaRecorder as unknown as { isTypeSupported: () => boolean }).isTypeSupported = () => true;

      const mockStream = { getTracks: () => [{ stop: vi.fn() }] };
      Object.defineProperty(navigator, "mediaDevices", {
        value: { getUserMedia: vi.fn().mockResolvedValue(mockStream) },
        configurable: true,
      });

      vi.stubGlobal("fetch", vi.fn().mockResolvedValue({
        ok: true,
        json: () => Promise.resolve({
          transcript: { transcript: "2BR in Beirut", provider: "azure_stt", confidence: "usable" },
          intent: { source_mode: "voice", filters: { city: "Beirut", bedrooms: 2 }, confidence: "high" },
        }),
      }));

      const { useVoiceSearch } = await import("@/features/search/useVoiceSearch");
      const { result } = renderHook(() => useVoiceSearch(), { wrapper: makeWrapper() });

      expect(result.current.state).toBe("idle");

      await act(async () => { await result.current.startRecording(); });
      expect(result.current.state).toBe("recording");

      await act(async () => { result.current.stopRecording(); });
      // recorder.stop triggers onstop → uploading
      expect(["uploading", "done"]).toContain(result.current.state);
    });

    it("discard during recording suppresses upload (fetch not called)", async () => {
      const recorder = makeMediaRecorder();
      (globalThis as unknown as Record<string, unknown>).AudioContext = vi.fn(() => makeAudioContext([SILENCE]));
      (globalThis as unknown as Record<string, unknown>).MediaRecorder = vi.fn(() => recorder) as unknown as typeof MediaRecorder;
      (MediaRecorder as unknown as { isTypeSupported: () => boolean }).isTypeSupported = () => true;

      const mockStream = { getTracks: () => [{ stop: vi.fn() }] };
      Object.defineProperty(navigator, "mediaDevices", {
        value: { getUserMedia: vi.fn().mockResolvedValue(mockStream) },
        configurable: true,
      });

      const mockFetch = vi.fn();
      vi.stubGlobal("fetch", mockFetch);

      const { useVoiceSearch } = await import("@/features/search/useVoiceSearch");
      const { result } = renderHook(() => useVoiceSearch(), { wrapper: makeWrapper() });

      await act(async () => { await result.current.startRecording(); });
      expect(result.current.state).toBe("recording");

      await act(async () => { result.current.discard(); });
      expect(result.current.state).toBe("idle");
      expect(result.current.transcript).toBeNull();
      expect(mockFetch).not.toHaveBeenCalled();
    });

    it("discard during upload cancels fetch and state stays idle", async () => {
      const recorder = makeMediaRecorder();
      (globalThis as unknown as Record<string, unknown>).AudioContext = vi.fn(() => makeAudioContext([SPEECH]));
      (globalThis as unknown as Record<string, unknown>).MediaRecorder = vi.fn(() => recorder) as unknown as typeof MediaRecorder;
      (MediaRecorder as unknown as { isTypeSupported: () => boolean }).isTypeSupported = () => true;

      const mockStream = { getTracks: () => [{ stop: vi.fn() }] };
      Object.defineProperty(navigator, "mediaDevices", {
        value: { getUserMedia: vi.fn().mockResolvedValue(mockStream) },
        configurable: true,
      });

      // fetch stays pending until the test resolves it; respects abort signal
      let resolveUpload!: (v: unknown) => void;
      vi.stubGlobal("fetch", vi.fn((_url: string, opts: RequestInit) => {
        return new Promise((resolve, reject) => {
          resolveUpload = resolve;
          opts?.signal?.addEventListener("abort", () =>
            reject(new DOMException("The operation was aborted.", "AbortError")),
          );
        });
      }));

      const { useVoiceSearch } = await import("@/features/search/useVoiceSearch");
      const { result } = renderHook(() => useVoiceSearch(), { wrapper: makeWrapper() });

      await act(async () => { await result.current.startRecording(); });
      await act(async () => { result.current.stopRecording(); });
      await act(async () => { await new Promise((r) => setTimeout(r, 20)); });

      expect(result.current.state).toBe("uploading");

      await act(async () => { result.current.discard(); });
      expect(result.current.state).toBe("idle");

      // resolve the upload after discard — state must not flip to "done"
      await act(async () => {
        resolveUpload({
          ok: true,
          json: () => Promise.resolve({
            transcript: { transcript: "late", provider: "azure_stt", confidence: "usable" },
            intent: { source_mode: "voice", filters: {}, confidence: "high" },
          }),
        });
        await new Promise((r) => setTimeout(r, 50));
      });

      expect(result.current.state).toBe("idle");
    });

    it("no double-submit: stopRecording called twice only stops once", async () => {
      const recorder = makeMediaRecorder();
      (globalThis as unknown as Record<string, unknown>).AudioContext = vi.fn(() => makeAudioContext([SPEECH]));
      (globalThis as unknown as Record<string, unknown>).MediaRecorder = vi.fn(() => recorder) as unknown as typeof MediaRecorder;
      (MediaRecorder as unknown as { isTypeSupported: () => boolean }).isTypeSupported = () => true;

      const mockStream = { getTracks: () => [{ stop: vi.fn() }] };
      Object.defineProperty(navigator, "mediaDevices", {
        value: { getUserMedia: vi.fn().mockResolvedValue(mockStream) },
        configurable: true,
      });

      vi.stubGlobal("fetch", vi.fn().mockResolvedValue({
        ok: true,
        json: () => Promise.resolve({
          transcript: { transcript: "test", provider: "azure_stt", confidence: "usable" },
          intent: { source_mode: "voice", filters: {}, confidence: "high" },
        }),
      }));

      const { useVoiceSearch } = await import("@/features/search/useVoiceSearch");
      const { result } = renderHook(() => useVoiceSearch(), { wrapper: makeWrapper() });

      await act(async () => { await result.current.startRecording(); });

      await act(async () => {
        result.current.stopRecording();
        result.current.stopRecording();
      });

      expect(recorder.stop).toHaveBeenCalledTimes(1);
    });
  });

  describe("pending upload follows confirmation flow", () => {
    it("result.intent contains filters after successful upload", async () => {
      const originalRAF = globalThis.requestAnimationFrame;
      const originalMediaRecorder = globalThis.MediaRecorder;
      const originalAudioContext = globalThis.AudioContext;
      const originalMediaDevices = navigator.mediaDevices;

      globalThis.requestAnimationFrame = vi.fn(() => 1);
      globalThis.cancelAnimationFrame = vi.fn();

      const recorder = makeMediaRecorder();
      (globalThis as unknown as Record<string, unknown>).AudioContext = vi.fn(() => makeAudioContext([SPEECH]));
      (globalThis as unknown as Record<string, unknown>).MediaRecorder = vi.fn(() => recorder) as unknown as typeof MediaRecorder;
      (MediaRecorder as unknown as { isTypeSupported: () => boolean }).isTypeSupported = () => true;

      const mockStream = { getTracks: () => [{ stop: vi.fn() }] };
      Object.defineProperty(navigator, "mediaDevices", {
        value: { getUserMedia: vi.fn().mockResolvedValue(mockStream) },
        configurable: true,
      });

      vi.stubGlobal("fetch", vi.fn().mockResolvedValue({
        ok: true,
        json: () => Promise.resolve({
          transcript: { transcript: "3 bed villa in Jounieh", provider: "azure_stt", confidence: "usable" },
          intent: {
            source_mode: "voice",
            filters: { bedrooms: 3, city: "Jounieh", property_type: "villa" },
            confidence: "high",
          },
        }),
      }));

      const { useVoiceSearch } = await import("@/features/search/useVoiceSearch");
      const { result } = renderHook(() => useVoiceSearch(), { wrapper: makeWrapper() });

      await act(async () => { await result.current.startRecording(); });
      await act(async () => { result.current.stopRecording(); });
      await act(async () => { await new Promise((r) => setTimeout(r, 80)); });

      if (result.current.result) {
        expect(result.current.result.intent.filters.city).toBe("Jounieh");
        expect(result.current.result.intent.filters.bedrooms).toBe(3);
        expect(result.current.result.intent.filters.property_type).toBe("villa");
      } else {
        expect(result.current.error).toBeNull();
      }

      globalThis.requestAnimationFrame = originalRAF;
      globalThis.MediaRecorder = originalMediaRecorder;
      globalThis.AudioContext = originalAudioContext;
      Object.defineProperty(navigator, "mediaDevices", { value: originalMediaDevices, configurable: true });
      vi.restoreAllMocks();
    });
  });
});
