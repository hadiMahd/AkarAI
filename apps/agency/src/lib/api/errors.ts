import { ApiError } from "./client";

/**
 * Maps API failures to product-quality user-facing copy for the agency app.
 *
 * The backend emits a structured envelope:
 *   { status: "error", detail: string, error_code: string | null, request_id: string | null }
 * which this helper inspects (alongside HTTP status) to pick a message that fits the
 * action the user just attempted.
 *
 * Use `getApiErrorMessage(error, ctx)` from `onError`/error banners. The `ctx` lets the
 * same error code map to action-specific copy (e.g. 401 during sign-in is
 * "Email or password is incorrect" but 401 elsewhere is "Your session expired").
 */

export type ApiErrorContext =
  | "auth.signin"
  | "auth.refresh"
  | "employee.create"
  | "employee.deactivate"
  | "listing.load"
  | "listing.create"
  | "listing.update"
  | "listing.media.load"
  | "listing.media.upload"
  | "listing.publish"
  | "viewing.slot.create"
  | "viewing.update"
  | "lead.load"
  | "lead.review"
  | "agency.profile.load"
  | "agency.profile.update"
  | "dashboard.summary"
  | "dashboard.forecast"
  | "rag.documents.load"
  | "rag.document.upload"
  | "rag.document.replace"
  | "rag.document.download"
  | "rag.chat.thread"
  | "rag.chat.message"
  | "rag.retrieval.logs"
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
  if (error instanceof TypeError) return true;
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
const PERMISSION_MESSAGE = "You don't have permission to do that.";

interface MappedMessage {
  message: string;
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

    case "auth.refresh":
      if (status === 401) {
        return { message: SESSION_EXPIRED_MESSAGE, isSpecific: true };
      }
      return null;

    case "employee.create": {
      if (code === "EMPLOYEE_EMAIL_EXISTS" || status === 409) {
        return {
          message: "An account with this email already exists.",
          isSpecific: true,
        };
      }
      if (status === 422 || code === "VALIDATION_ERROR") {
        return { message: detail ?? "Check the form fields and try again.", isSpecific: true };
      }
      if (status === 403) {
        return { message: "You don't have permission to add employees.", isSpecific: true };
      }
      return null;
    }

    case "employee.deactivate":
      if (status === 404) {
        return { message: "This employee no longer exists.", isSpecific: true };
      }
      if (status === 403) {
        return { message: "You don't have permission to deactivate this employee.", isSpecific: true };
      }
      return null;

    case "listing.load":
      return { message: "We couldn't load your listings. Try refreshing the page.", isSpecific: true };

    case "listing.create":
    case "listing.update": {
      if (status === 422 || code === "VALIDATION_ERROR") {
        return { message: detail ?? "Check the listing fields and try again.", isSpecific: true };
      }
      if (status === 404) {
        return { message: "This listing no longer exists.", isSpecific: true };
      }
      if (status === 403) {
        return { message: "You don't have permission to edit this listing.", isSpecific: true };
      }
      return null;
    }

    case "listing.media.load":
      return { message: "We couldn't load the photos for this listing. Try refreshing.", isSpecific: true };

    case "listing.media.upload":
      if (status === 422 || code === "VALIDATION_ERROR") {
        return {
          message: detail ?? "This photo can't be uploaded. Use a JPG, PNG, or WebP under 10MB.",
          isSpecific: true,
        };
      }
      if (code === "PHOTO_STORAGE_FAILED" || status === 503) {
        return {
          message: "We couldn't store this photo right now. Try again in a moment.",
          isSpecific: true,
        };
      }
      if (status === 413) {
        return { message: "This photo is too large. Use one under 10MB.", isSpecific: true };
      }
      return null;

    case "listing.publish":
      if (status === 422 || code === "VALIDATION_ERROR") {
        return {
          message: detail ?? "This listing can't be published yet.",
          isSpecific: true,
        };
      }
      return null;

    case "viewing.slot.create":
      if (status === 422 || code === "VALIDATION_ERROR") {
        return { message: detail ?? "Check the slot times and try again.", isSpecific: true };
      }
      return null;

    case "viewing.update":
      if (status === 422 || code === "VALIDATION_ERROR") {
        return { message: detail ?? "Pick a valid status transition.", isSpecific: true };
      }
      if (status === 404) {
        return { message: "This viewing no longer exists.", isSpecific: true };
      }
      return null;

    case "lead.review":
      if (status === 404) {
        return { message: "This lead no longer exists.", isSpecific: true };
      }
      return null;

    case "lead.load":
      return { message: "We couldn't load leads. Try refreshing the page.", isSpecific: true };

    case "agency.profile.load":
      if (status === 404) {
        return { message: "Your agency profile hasn't been set up yet.", isSpecific: true };
      }
      return null;

    case "agency.profile.update":
      if (status === 422 || code === "VALIDATION_ERROR") {
        return { message: detail ?? "Check the profile fields and try again.", isSpecific: true };
      }
      return null;

    case "dashboard.summary":
      return { message: "We couldn't load the dashboard right now.", isSpecific: true };

    case "dashboard.forecast":
      if (status === 503 || code === "SERVICE_UNAVAILABLE") {
        return {
          message: "Not enough history yet to generate a forecast.",
          isSpecific: true,
        };
      }
      if (status === 403) {
        return { message: "Only agency admins can view the forecast.", isSpecific: true };
      }
      return null;

    case "rag.documents.load":
      return { message: "We couldn't load your policy documents. Try refreshing the page.", isSpecific: true };

    case "rag.document.upload":
    case "rag.document.replace": {
      if (code === "PDF_TOO_LARGE" || status === 413) {
        return {
          message: detail ?? "This PDF is too large. Use a file under 50MB.",
          isSpecific: true,
        };
      }
      if (code === "PDF_WRONG_TYPE" || status === 415) {
        return { message: "Only PDF files are accepted.", isSpecific: true };
      }
      if (code === "PDF_INVALID") {
        return { message: "That file doesn't look like a valid PDF.", isSpecific: true };
      }
      if (code === "PDF_EMPTY") {
        return { message: "That PDF is empty.", isSpecific: true };
      }
      if (code === "PDF_NO_TEXT") {
        return {
          message: "This PDF has no extractable text. Scanned documents aren't supported yet.",
          isSpecific: true,
        };
      }
      if (code === "PDF_UNREADABLE") {
        return {
          message: "We couldn't open that PDF. It may be corrupted.",
          isSpecific: true,
        };
      }
      if (code === "DOCUMENT_PROCESSING" || status === 409) {
        return {
          message: "This document is still processing. Wait until it finishes before replacing it.",
          isSpecific: true,
        };
      }
      if (code === "DOCUMENT_STORAGE_FAILED" || code === "PDF_EXTRACTION_UNAVAILABLE" || status === 503) {
        return {
          message: "Document storage is temporarily unavailable. Try again in a moment.",
          isSpecific: true,
        };
      }
      if (status === 403) {
        return {
          message: "Only agency admins can upload policy documents.",
          isSpecific: true,
        };
      }
      return null;
    }

    case "rag.document.download":
      if (status === 404) {
        return { message: "This document file is no longer available.", isSpecific: true };
      }
      return { message: "We couldn't open the document. Try again in a moment.", isSpecific: true };

    case "rag.chat.thread":
      if (status === 404) {
        return { message: "This conversation no longer exists.", isSpecific: true };
      }
      if (status === 401) {
        return { message: SESSION_EXPIRED_MESSAGE, isSpecific: true };
      }
      return null;

    case "rag.chat.message": {
      if (status === 401) {
        return { message: SESSION_EXPIRED_MESSAGE, isSpecific: true };
      }
      if (status === 404) {
        return { message: "This conversation no longer exists.", isSpecific: true };
      }
      if (status === 503 || (status != null && status >= 500)) {
        return {
          message: "The policy assistant is unavailable right now. Try again in a moment.",
          isSpecific: true,
        };
      }
      if (isRateLimited(error)) {
        return {
          message: "Too many questions in a row. Wait a moment and try again.",
          isSpecific: true,
        };
      }
      return null;
    }

    case "rag.retrieval.logs":
      if (status === 403) {
        return { message: "Only agency admins can view retrieval history.", isSpecific: true };
      }
      return { message: "We couldn't load retrieval history. Try refreshing the page.", isSpecific: true };

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
    return { message: PERMISSION_MESSAGE, isSpecific: true };
  }
  if (status === 404) {
    return { message: "We couldn't find what you were looking for.", isSpecific: true };
  }
  if (status != null && status >= 500) {
    return { message: SERVER_MESSAGE, isSpecific: true };
  }
  const detail = detailString(error);
  if (detail && !detail.toLowerCase().startsWith("internal server")) {
    return { message: detail, isSpecific: true };
  }
  return { message: GENERIC_MESSAGE, isSpecific: true };
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
