import { describe, it, expect } from "vitest";
import { ApiError } from "@/lib/api/client";
import {
  getApiErrorMessage,
  getApiErrorCode,
  getApiErrorStatus,
  isSessionExpired,
  isForbidden,
  isRateLimited,
  isNetworkError,
} from "@/lib/api/errors";

function backendError(status: number, body: Record<string, unknown>) {
  return new ApiError(`API request failed: status ${status}`, status, body);
}

describe("api error mapping (agency app)", () => {
  describe("getApiErrorCode / getApiErrorStatus", () => {
    it("returns the backend error_code when present", () => {
      const err = backendError(409, { detail: "Already exists", error_code: "EMPLOYEE_EMAIL_EXISTS" });
      expect(getApiErrorCode(err)).toBe("EMPLOYEE_EMAIL_EXISTS");
      expect(getApiErrorStatus(err)).toBe(409);
    });
  });

  describe("predicates", () => {
    it("isSessionExpired matches 401 with UNAUTHORIZED-style codes", () => {
      expect(isSessionExpired(backendError(401, { detail: "x", error_code: "UNAUTHORIZED" }))).toBe(true);
      expect(isSessionExpired(backendError(401, { detail: "x", error_code: "INVALID_REFRESH_TOKEN" }))).toBe(true);
      expect(isSessionExpired(backendError(401, { detail: "x", error_code: "INVALID_CREDENTIALS" }))).toBe(false);
    });

    it("isForbidden / isRateLimited / isNetworkError behave as expected", () => {
      expect(isForbidden(backendError(403, { detail: "x" }))).toBe(true);
      expect(isRateLimited(backendError(429, { detail: "x", error_code: "RATE_LIMIT_EXCEEDED" }))).toBe(true);
      expect(isNetworkError(new TypeError("Failed to fetch"))).toBe(true);
    });
  });

  describe("auth.signin context", () => {
    it("maps invalid credentials to the explicit copy", () => {
      const err = backendError(401, { detail: "Invalid credentials", error_code: "INVALID_CREDENTIALS" });
      expect(getApiErrorMessage(err, "auth.signin")).toBe("Email or password is incorrect.");
    });

    it("does NOT leak the raw ApiError message ('API request failed: ...')", () => {
      const err = backendError(401, { detail: "Invalid credentials", error_code: "INVALID_CREDENTIALS" });
      expect(getApiErrorMessage(err, "auth.signin")).not.toContain("API request failed");
    });
  });

  describe("employee.create context", () => {
    it("maps EMPLOYEE_EMAIL_EXISTS (409) to an explicit message", () => {
      const err = backendError(409, {
        detail: "An account with this email already exists.",
        error_code: "EMPLOYEE_EMAIL_EXISTS",
      });
      expect(getApiErrorMessage(err, "employee.create")).toBe("An account with this email already exists.");
    });

    it("maps 403 to a permission message", () => {
      const err = backendError(403, { detail: "Support employees cannot manage employees", error_code: "FORBIDDEN" });
      expect(getApiErrorMessage(err, "employee.create")).toMatch(/don't have permission/i);
    });

    it("maps 422 detail through (so backend can override)", () => {
      const err = backendError(422, { detail: "work_email is required", error_code: "VALIDATION_ERROR" });
      expect(getApiErrorMessage(err, "employee.create")).toBe("work_email is required");
    });
  });

  describe("rag.document.upload context", () => {
    it("maps PDF_TOO_LARGE to a clear size message", () => {
      const err = backendError(413, {
        detail: "This PDF exceeds the 50MB upload limit.",
        error_code: "PDF_TOO_LARGE",
      });
      expect(getApiErrorMessage(err, "rag.document.upload")).toMatch(/50MB/i);
    });

    it("maps PDF_NO_TEXT to a scanned-document message", () => {
      const err = backendError(400, {
        detail: "This PDF has no extractable text.",
        error_code: "PDF_NO_TEXT",
      });
      expect(getApiErrorMessage(err, "rag.document.upload")).toMatch(/scanned documents/i);
    });

    it("maps PDF_WRONG_TYPE to a 'only PDF' message", () => {
      const err = backendError(415, {
        detail: "Only PDF files are accepted.",
        error_code: "PDF_WRONG_TYPE",
      });
      expect(getApiErrorMessage(err, "rag.document.upload")).toMatch(/only pdf/i);
    });

    it("maps DOCUMENT_STORAGE_FAILED to a temporary-failure message", () => {
      const err = backendError(503, {
        detail: "We couldn't store this document right now.",
        error_code: "DOCUMENT_STORAGE_FAILED",
      });
      expect(getApiErrorMessage(err, "rag.document.upload")).toMatch(/temporarily unavailable/i);
    });

    it("maps DOCUMENT_PROCESSING (409 on replace) to a 'still processing' message", () => {
      const err = backendError(409, {
        detail: "This document is still processing.",
        error_code: "DOCUMENT_PROCESSING",
      });
      expect(getApiErrorMessage(err, "rag.document.replace")).toMatch(/still processing/i);
    });
  });

  describe("rag.chat.message context", () => {
    it("maps 401 to session-expired", () => {
      const err = backendError(401, { detail: "x", error_code: "UNAUTHORIZED" });
      expect(getApiErrorMessage(err, "rag.chat.message")).toMatch(/session expired/i);
    });

    it("maps 503 to assistant-unavailable", () => {
      const err = backendError(503, { detail: "x", error_code: "SERVICE_UNAVAILABLE" });
      expect(getApiErrorMessage(err, "rag.chat.message")).toMatch(/policy assistant is unavailable/i);
    });

    it("maps 429 to rate-limit copy", () => {
      const err = backendError(429, { detail: "x", error_code: "RATE_LIMIT_EXCEEDED" });
      expect(getApiErrorMessage(err, "rag.chat.message")).toMatch(/too many questions/i);
    });
  });

  describe("rag.retrieval.logs context", () => {
    it("maps 403 to admin-only message", () => {
      const err = backendError(403, { detail: "x", error_code: "ROLE_DENIED" });
      expect(getApiErrorMessage(err, "rag.retrieval.logs")).toMatch(/only agency admins/i);
    });
  });

  describe("generic fallbacks", () => {
    it("returns the backend detail for unknown codes", () => {
      const err = backendError(418, { detail: "I'm a teapot", error_code: "TEAPOT" });
      expect(getApiErrorMessage(err, "generic")).toBe("I'm a teapot");
    });

    it("never leaks 'API request failed: ...' or 'Error' to the user", () => {
      const errors = [
        new TypeError("Failed to fetch"),
        backendError(500, { detail: "Internal server error" }),
        backendError(503, { detail: "" }),
        new Error("plain js error"),
      ];
      for (const err of errors) {
        const message = getApiErrorMessage(err);
        expect(message).not.toBe("Error");
        expect(message).not.toMatch(/^API request failed/);
        expect(message.length).toBeGreaterThan(10);
      }
    });
  });
});
