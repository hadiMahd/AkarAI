import { ApiError } from "./client";

/**
 * Maps API failures to product-quality user-facing copy.
 *
 * The backend emits a structured envelope:
 *   { status: "error", detail: string, error_code: string | null, request_id: string | null }
 * which this helper inspects (alongside HTTP status) to pick a message that fits the
 * action the user just attempted.
 *
 * Use `getApiErrorMessage(error, ctx)` from `onError`/error banners/toasts. The
 * `ctx` lets the same error code map to action-specific copy (e.g. 401 during sign-in
 * is "Email or password is incorrect" but 401 elsewhere is "Your session expired").
 */

export type ApiErrorContext =
  | "auth.signin"
  | "auth.signup"
  | "auth.refresh"
  | "search.intent"
  | "search.voice"
  | "search.confirm"
  | "listing.load"
  | "listing.detail"
  | "listing.media"
  | "listing.assistant"
  | "saved.toggle"
  | "compare.update"
  | "inquiry.submit"
  | "viewing.book"
  | "viewing.slots"
  | "profile.activity"
  | "comparison.summary"
  | "generic";

type BackendDetail = {
  detail?: unknown;
  error_code?: unknown;
  errors?: unknown;
  message?: unknown;
};

function extractBackendDetail(error: unknown): BackendDetail | null {
  if (!(error instanceof ApiError)) return null;
  const data = error.data;
  if (data && typeof data === "object") {
    return data as BackendDetail;
  }
  return null;
}

function detailString(error: unknown): string | null {
  const data = extractBackendDetail(error);
  if (!data) return null;
  if (typeof data.detail === "string" && data.detail.trim()) {
    return data.detail.trim();
  }
  if (typeof data.message === "string" && data.message.trim()) {
    return data.message.trim();
  }
  return null;
}

export function getApiErrorStatus(error: unknown): number | null {
  if (error instanceof ApiError) return error.status;
  return null;
}

export function getApiErrorCode(error: unknown): string | null {
  const data = extractBackendDetail(error);
  if (!data) return null;
  if (typeof data.error_code === "string" && data.error_code) {
    return data.error_code;
  }
  return null;
}

export function getApiErrorDetail(error: unknown): string | null {
  return detailString(error);
}

export function isApiError(error: unknown): error is ApiError {
  return error instanceof ApiError;
}

export function isSessionExpired(error: unknown): boolean {
  const status = getApiErrorStatus(error);
  if (status !== 401) return false;
  const code = getApiErrorCode(error);
  if (!code) return true;
  return code === "UNAUTHORIZED" || code.includes("TOKEN") || code.includes("REFRESH");
}

export function isForbidden(error: unknown): boolean {
  return getApiErrorStatus(error) === 403;
}

export function isRateLimited(error: unknown): boolean {
  if (getApiErrorStatus(error) === 429) return true;
  return getApiErrorCode(error) === "RATE_LIMIT_EXCEEDED";
}

export function isNotFound(error: unknown): boolean {
  return getApiErrorStatus(error) === 404;
}

export function isNetworkError(error: unknown): boolean {
  if (error instanceof ApiError) return false;
  if (error instanceof TypeError) return true; // browser fetch failure
  if (error && typeof error === "object" && "name" in error) {
    const name = (error as { name?: unknown }).name;
    if (name === "AbortError") return true;
    if (typeof name === "string" && name.toLowerCase().includes("network")) return true;
  }
  return false;
}

const SESSION_EXPIRED_MESSAGE = "Your session expired. Sign in again to continue.";
const NETWORK_MESSAGE = "Network connection lost. Check your internet and try again.";
const RATE_LIMIT_MESSAGE = "You're doing that too often. Wait a moment and try again.";
const SERVER_MESSAGE = "Something on our side broke. Try again in a moment.";
const GENERIC_MESSAGE = "We couldn't complete that action. Try again in a moment.";

interface MappedMessage {
  message: string;
  /** True when the source error has been understood and the message is specific. */
  isSpecific: boolean;
}

function mapByContext(error: unknown, context: ApiErrorContext): MappedMessage | null {
  const status = getApiErrorStatus(error);
  const code = getApiErrorCode(error);
  const detail = detailString(error);

  switch (context) {
    case "auth.signin": {
      if (status === 401 || code === "INVALID_CREDENTIALS") {
        return { message: "Email or password is incorrect.", isSpecific: true };
      }
      if (isRateLimited(error)) {
        return {
          message: "Too many sign-in attempts. Wait a moment and try again.",
          isSpecific: true,
        };
      }
      if (status === 403) {
        return {
          message: detail ?? "This account isn't allowed to sign in.",
          isSpecific: true,
        };
      }
      return null;
    }

    case "auth.signup": {
      if (code === "USER_EXISTS" || status === 409) {
        return {
          message: "An account with this email already exists. Try signing in instead.",
          isSpecific: true,
        };
      }
      if (status === 422 || code === "VALIDATION_ERROR") {
        return {
          message: detail ?? "Check the form fields and try again.",
          isSpecific: true,
        };
      }
      if (isRateLimited(error)) {
        return {
          message: "Too many sign-up attempts. Wait a moment and try again.",
          isSpecific: true,
        };
      }
      return null;
    }

    case "auth.refresh": {
      if (status === 401) {
        return { message: SESSION_EXPIRED_MESSAGE, isSpecific: true };
      }
      return null;
    }

    case "search.intent": {
      if (isRateLimited(error)) {
        return {
          message: "Too many AI searches in a row. Wait a moment and try again.",
          isSpecific: true,
        };
      }
      if (status === 422 || code === "VALIDATION_ERROR") {
        return {
          message: "Try rephrasing your search.",
          isSpecific: true,
        };
      }
      if (status === 503 || (status != null && status >= 500)) {
        return {
          message: "AI search is unavailable right now. Use the manual filters or try again later.",
          isSpecific: true,
        };
      }
      return null;
    }

    case "search.voice": {
      if (code === "UNSUPPORTED_AUDIO_FORMAT" || status === 415) {
        return {
          message: "Your browser sent an unsupported audio format. Try again or use text search.",
          isSpecific: true,
        };
      }
      if (code === "AUDIO_FILE_TOO_LARGE" || status === 413) {
        return {
          message: "Recording is too long. Try a shorter clip.",
          isSpecific: true,
        };
      }
      if (isRateLimited(error)) {
        return {
          message: "Too many voice searches in a row. Wait a moment and try again.",
          isSpecific: true,
        };
      }
      if (status === 422 || code === "VALIDATION_ERROR") {
        return {
          message: "We couldn't process that recording. Try again or type your search instead.",
          isSpecific: true,
        };
      }
      if (status === 503 || (status != null && status >= 500)) {
        return {
          message: "Voice transcription is unavailable right now. Type your search instead.",
          isSpecific: true,
        };
      }
      return null;
    }

    case "listing.load":
      if (status === 404) {
        return { message: "No listings match these filters yet.", isSpecific: true };
      }
      return null;

    case "listing.detail":
      if (status === 404) {
        return {
          message: "This listing is no longer available.",
          isSpecific: true,
        };
      }
      return null;

    case "listing.media":
      return { message: "We couldn't load the photos. Try refreshing the page.", isSpecific: true };

    case "listing.assistant":
      if (status === 404) {
        return {
          message: "This listing is no longer available.",
          isSpecific: true,
        };
      }
      if (status === 401) {
        return {
          message: "Sign in to continue with that assistant action.",
          isSpecific: true,
        };
      }
      if (isRateLimited(error)) {
        return {
          message: "The listing assistant is busy right now. Wait a moment and try again.",
          isSpecific: true,
        };
      }
      if (status === 503 || (status != null && status >= 500)) {
        return {
          message: "The listing assistant is unavailable right now. Use the forms below or try again later.",
          isSpecific: true,
        };
      }
      return null;

    case "saved.toggle":
      if (status === 404) {
        return {
          message: "This listing is no longer available.",
          isSpecific: true,
        };
      }
      return { message: "We couldn't update your saved listings. Try again in a moment.", isSpecific: true };

    case "compare.update":
      if (status === 409 || code === "CONFLICT") {
        return {
          message: "You've reached the maximum number of items in this comparison.",
          isSpecific: true,
        };
      }
      if (status === 404) {
        return {
          message: "This comparison is no longer available.",
          isSpecific: true,
        };
      }
      return null;

    case "comparison.summary": {
      if (isRateLimited(error)) {
        return {
          message: "You're requesting summaries too quickly. Wait a moment and try again.",
          isSpecific: true,
        };
      }
      if (status === 404) {
        return {
          message: "One of the selected listings is no longer available.",
          isSpecific: true,
        };
      }
      if (status === 503 || (status != null && status >= 500)) {
        return {
          message: "The comparison service is temporarily unavailable. Try again in a moment.",
          isSpecific: true,
        };
      }
      if (status === 401) {
        return { message: SESSION_EXPIRED_MESSAGE, isSpecific: true };
      }
      return null;
    }

    case "inquiry.submit": {
      if (code === "EMPTY_LEAD_MESSAGE") {
        return {
          message: "Write a short message before sending your inquiry.",
          isSpecific: true,
        };
      }
      if (code === "PROFILE_INCOMPLETE_FOR_LEADS") {
        return {
          message: "Complete your profile with your name and a contact method before sending a lead.",
          isSpecific: true,
        };
      }
      if (isRateLimited(error)) {
        return {
          message: "You've sent a lot of inquiries recently. Wait a moment and try again.",
          isSpecific: true,
        };
      }
      if (status === 404) {
        return {
          message: "This listing is no longer available.",
          isSpecific: true,
        };
      }
      return null;
    }

    case "viewing.book": {
      if (isRateLimited(error)) {
        return {
          message: "You've booked a lot of viewings recently. Wait a moment and try again.",
          isSpecific: true,
        };
      }
      if (status === 409 || code === "CONFLICT") {
        return {
          message: "That time slot just filled up. Pick another available slot.",
          isSpecific: true,
        };
      }
      if (status === 404) {
        return {
          message: "That viewing slot is no longer available. Pick another one.",
          isSpecific: true,
        };
      }
      return null;
    }

    case "viewing.slots":
      if (status === 404) {
        return { message: "This listing is no longer available.", isSpecific: true };
      }
      return { message: "We couldn't load viewing slots. Try refreshing the page.", isSpecific: false };

    case "profile.activity":
      return { message: "We couldn't load your activity. Try refreshing the page.", isSpecific: false };

    case "search.confirm":
    case "generic":
    default:
      return null;
  }
}

function mapByStatus(error: unknown): MappedMessage {
  if (isNetworkError(error)) {
    return { message: NETWORK_MESSAGE, isSpecific: true };
  }
  if (isRateLimited(error)) {
    return { message: RATE_LIMIT_MESSAGE, isSpecific: true };
  }
  if (isSessionExpired(error)) {
    return { message: SESSION_EXPIRED_MESSAGE, isSpecific: true };
  }
  const status = getApiErrorStatus(error);
  if (status === 403) {
    return {
      message: "You don't have permission to do that.",
      isSpecific: true,
    };
  }
  if (status === 404) {
    return { message: "We couldn't find what you were looking for.", isSpecific: true };
  }
  if (status != null && status >= 500) {
    return { message: SERVER_MESSAGE, isSpecific: true };
  }
  const detail = detailString(error);
  if (detail && !detail.toLowerCase().startsWith("internal server")) {
    return { message: detail, isSpecific: false };
  }
  return { message: GENERIC_MESSAGE, isSpecific: false };
}

export interface ApiErrorMessageOptions {
  /** Fallback message shown when no contextual or status mapping applies. */
  fallback?: string;
}

export function getApiErrorMessage(
  error: unknown,
  context: ApiErrorContext = "generic",
  options: ApiErrorMessageOptions = {},
): string {
  if (error == null) {
    return options.fallback ?? GENERIC_MESSAGE;
  }

  if (isNetworkError(error)) {
    return NETWORK_MESSAGE;
  }

  const contextual = mapByContext(error, context);
  if (contextual?.isSpecific) {
    return contextual.message;
  }

  const fromStatus = mapByStatus(error);
  if (fromStatus.isSpecific) {
    return fromStatus.message;
  }

  if (contextual) {
    return contextual.message;
  }

  if (options.fallback) {
    return options.fallback;
  }

  return fromStatus.message;
}
