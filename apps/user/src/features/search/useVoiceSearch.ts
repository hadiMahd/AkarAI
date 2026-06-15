import { useState, useCallback, useRef } from "react";
import { useMutation } from "@tanstack/react-query";
import { getAccessToken } from "@/lib/session/auth-session";
import { API_BASE_URL, ApiError } from "@/lib/api/client";
import type { SearchIntentResponse } from "./useSearchIntent";

export type VoiceRecordingState = "idle" | "recording" | "uploading" | "done" | "error";

export type VoiceSearchError = ApiError | Error;

// Silence detection tunables
const SILENCE_THRESHOLD = 0.015;       // RMS below this is considered silence
const WARMUP_MS = 600;                 // must have speech for this long before auto-stop can trigger
const SILENCE_DURATION_MS = 1500;      // sustained silence after warmup → auto-stop
const ANALYSER_FFT = 2048;

function startSilenceDetector(
  stream: MediaStream,
  onSilence: () => void,
): () => void {
  let audioCtx: AudioContext | null = null;
  let animId: number | null = null;
  let hasSpeech = false;
  let speechStartTime = 0;
  let silenceStart: number | null = null;
  let stopped = false;

  try {
    audioCtx = new AudioContext();
    const source = audioCtx.createMediaStreamSource(stream);
    const analyser = audioCtx.createAnalyser();
    analyser.fftSize = ANALYSER_FFT;
    source.connect(analyser);

    const buffer = new Float32Array(analyser.fftSize);

    function tick() {
      if (stopped) return;
      analyser.getFloatTimeDomainData(buffer);
      let sumSq = 0;
      for (let i = 0; i < buffer.length; i++) sumSq += buffer[i] * buffer[i];
      const rms = Math.sqrt(sumSq / buffer.length);

      const now = Date.now();
      if (rms > SILENCE_THRESHOLD) {
        if (!hasSpeech) {
          hasSpeech = true;
          speechStartTime = now;
        }
        silenceStart = null;
      } else if (hasSpeech && now - speechStartTime >= WARMUP_MS) {
        if (silenceStart === null) silenceStart = now;
        if (now - silenceStart >= SILENCE_DURATION_MS) {
          stopped = true;
          onSilence();
          return;
        }
      }

      animId = requestAnimationFrame(tick);
    }

    animId = requestAnimationFrame(tick);
  } catch {
    // Web Audio API unavailable — no auto-stop, manual only
    return () => {};
  }

  return () => {
    stopped = true;
    if (animId !== null) cancelAnimationFrame(animId);
    audioCtx?.close().catch(() => {});
  };
}

export function useVoiceSearch() {
  const [state, setState] = useState<VoiceRecordingState>("idle");
  const [transcript, setTranscript] = useState<string | null>(null);
  const [error, setError] = useState<VoiceSearchError | null>(null);
  const mediaRecorderRef = useRef<MediaRecorder | null>(null);
  const streamRef = useRef<MediaStream | null>(null);
  const chunksRef = useRef<Blob[]>([]);
  const stopDetectorRef = useRef<(() => void) | null>(null);
  // prevents double-submit when auto-stop races with manual stop
  const stoppedRef = useRef(false);
  const abortControllerRef = useRef<AbortController | null>(null);
  // incremented on each upload start and on discard; callbacks check their captured token
  const uploadTokenRef = useRef(0);

  const voiceMutation = useMutation({
    mutationFn: async (audioBlob: Blob): Promise<SearchIntentResponse> => {
      const controller = new AbortController();
      abortControllerRef.current = controller;

      const formData = new FormData();
      formData.append("audio", audioBlob, "voice.webm");

      const headers: Record<string, string> = {};
      const accessToken = getAccessToken();
      if (accessToken) headers["Authorization"] = `Bearer ${accessToken}`;

      const response = await fetch(`${API_BASE_URL}/search/voice`, {
        method: "POST",
        body: formData,
        headers,
        credentials: "include",
        signal: controller.signal,
      });

      if (!response.ok) {
        let errorBody: unknown;
        try {
          errorBody = await response.json();
        } catch {
          try {
            errorBody = await response.text();
          } catch {
            errorBody = null;
          }
        }
        throw new ApiError(
          `Voice search failed: ${response.statusText}`,
          response.status,
          errorBody,
        );
      }
      return response.json();
    },
  });

  const _doStop = useCallback(() => {
    if (stoppedRef.current) return;
    stoppedRef.current = true;
    stopDetectorRef.current?.();
    stopDetectorRef.current = null;
    if (mediaRecorderRef.current && mediaRecorderRef.current.state === "recording") {
      mediaRecorderRef.current.stop();
    }
  }, []);

  const startRecording = useCallback(async () => {
    try {
      const stream = await navigator.mediaDevices.getUserMedia({ audio: true });
      streamRef.current = stream;
      stoppedRef.current = false;

      const recorder = new MediaRecorder(stream, { mimeType: "audio/webm" });
      chunksRef.current = [];
      recorder.ondataavailable = (e) => {
        if (e.data.size > 0) chunksRef.current.push(e.data);
      };
      recorder.onstop = () => {
        streamRef.current?.getTracks().forEach((t) => t.stop());
        const blob = new Blob(chunksRef.current, { type: "audio/webm" });
        setState("uploading");
        const token = ++uploadTokenRef.current;
        voiceMutation.mutate(blob, {
          onSuccess: (data) => {
            if (uploadTokenRef.current !== token) return;
            setTranscript(data.transcript?.transcript ?? null);
            setState("done");
          },
          onError: (err: Error) => {
            if (uploadTokenRef.current !== token) return;
            if (err.name === "AbortError") return;
            setError(err);
            setState("error");
          },
        });
      };
      mediaRecorderRef.current = recorder;
      recorder.start();
      setState("recording");
      setError(null);

      stopDetectorRef.current = startSilenceDetector(stream, _doStop);
    } catch (mediaError) {
      const denied =
        mediaError instanceof Error &&
        (mediaError.name === "NotAllowedError" || mediaError.name === "PermissionDeniedError");
      const unavailable =
        mediaError instanceof Error &&
        (mediaError.name === "NotFoundError" || mediaError.name === "OverconstrainedError");
      const message = denied
        ? "Microphone access was denied. Allow microphone access in your browser to use voice search."
        : unavailable
        ? "No microphone was detected. Connect a microphone and try again."
        : "We couldn't access your microphone. Try again or use the manual search.";
      const wrapped = new Error(message);
      wrapped.name = mediaError instanceof Error ? mediaError.name : "MediaError";
      setError(wrapped);
      setState("error");
    }
  }, [voiceMutation, _doStop]);

  const stopRecording = useCallback(() => {
    _doStop();
  }, [_doStop]);

  const discard = useCallback(() => {
    stoppedRef.current = true;
    uploadTokenRef.current++;
    abortControllerRef.current?.abort();
    abortControllerRef.current = null;
    stopDetectorRef.current?.();
    stopDetectorRef.current = null;
    streamRef.current?.getTracks().forEach((t) => t.stop());
    if (mediaRecorderRef.current && mediaRecorderRef.current.state === "recording") {
      // suppress onstop to avoid uploading discarded audio
      mediaRecorderRef.current.onstop = null;
      mediaRecorderRef.current.stop();
    }
    setState("idle");
    setTranscript(null);
    setError(null);
    chunksRef.current = [];
    streamRef.current = null;
    voiceMutation.reset();
  }, [voiceMutation]);

  return {
    state,
    transcript,
    error,
    isPending: state === "recording" || state === "uploading",
    result: voiceMutation.data ?? null,
    startRecording,
    stopRecording,
    discard,
  };
}
