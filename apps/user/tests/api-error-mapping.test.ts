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

describe("api error mapping (user app)", () => {
  describe("getApiErrorCode / getApiErrorStatus", () => {
    it("returns the backend error_code when present", () => {
      const err = backendError(401, { detail: "Invalid credentials", error_code: "INVALID_CREDENTIALS" });
      expect(getApiErrorCode(err)).toBe("INVALID_CREDENTIALS");
      expect(getApiErrorStatus(err)).toBe(401);
    });

    it("returns null code when the body has no error_code", () => {
      const err = backendError(500, { detail: "boom" });
      expect(getApiErrorCode(err)).toBeNull();
    });

    it("returns null for non-ApiError values", () => {
      expect(getApiErrorCode(new Error("boom"))).toBeNull();
      expect(getApiErrorStatus(new Error("boom"))).toBeNull();
    });
  });

  describe("predicates", () => {
    it("isSessionExpired matches 401 envelopes", () => {
      expect(isSessionExpired(backendError(401, { detail: "x", error_code: "UNAUTHORIZED" }))).toBe(true);
      expect(isSessionExpired(backendError(401, { detail: "x", error_code: "INVALID_REFRESH_TOKEN" }))).toBe(true);
      expect(isSessionExpired(backendError(403, { detail: "x", error_code: "FORBIDDEN" }))).toBe(false);
    });

    it("isSessionExpired does NOT match auth login failures with INVALID_CREDENTIALS", () => {
      // INVALID_CREDENTIALS is a 401 but represents bad password, not expired session.
      // The predicate is intentionally loose for 401 with unknown code; the contextual
      // mapper for auth.signin overrides to the credentials message.
      expect(isSessionExpired(backendError(401, { detail: "x", error_code: "INVALID_CREDENTIALS" }))).toBe(false);
    });

    it("isForbidden matches 403", () => {
      expect(isForbidden(backendError(403, { detail: "x", error_code: "FORBIDDEN" }))).toBe(true);
      expect(isForbidden(backendError(404, { detail: "x" }))).toBe(false);
    });

    it("isRateLimited matches 429 or RATE_LIMIT_EXCEEDED code", () => {
      expect(isRateLimited(backendError(429, { detail: "x", error_code: "RATE_LIMIT_EXCEEDED" }))).toBe(true);
      expect(isRateLimited(backendError(200, { detail: "x", error_code: "RATE_LIMIT_EXCEEDED" }))).toBe(true);
      expect(isRateLimited(backendError(500, { detail: "x" }))).toBe(false);
    });

    it("isNetworkError matches TypeError (fetch failure)", () => {
      expect(isNetworkError(new TypeError("Failed to fetch"))).toBe(true);
      expect(isNetworkError(backendError(500, { detail: "x" }))).toBe(false);
    });
  });

  describe("getApiErrorMessage — auth.signin context", () => {
    it("maps invalid credentials to a specific message", () => {
      const err = backendError(401, { detail: "Invalid credentials", error_code: "INVALID_CREDENTIALS" });
      expect(getApiErrorMessage(err, "auth.signin")).toBe("Email or password is incorrect.");
    });

    it("maps 429 to rate-limited signin copy", () => {
      const err = backendError(429, { detail: "Too many", error_code: "RATE_LIMIT_EXCEEDED" });
      expect(getApiErrorMessage(err, "auth.signin")).toMatch(/sign-in attempts/i);
    });

    it("maps 5xx to a generic server message", () => {
      const err = backendError(500, { detail: "Internal" });
      expect(getApiErrorMessage(err, "auth.signin")).toMatch(/on our side broke/i);
    });
  });

  describe("getApiErrorMessage — auth.signup context", () => {
    it("maps USER_EXISTS to an explicit account-already-exists message", () => {
      const err = backendError(409, { detail: "User with this email already exists", error_code: "USER_EXISTS" });
      expect(getApiErrorMessage(err, "auth.signup")).toBe(
        "An account with this email already exists. Try signing in instead.",
      );
    });

    it("maps validation errors back to the backend detail when available", () => {
      const err = backendError(422, {
        detail: "email: value is not a valid email address",
        error_code: "VALIDATION_ERROR",
      });
      expect(getApiErrorMessage(err, "auth.signup")).toBe("email: value is not a valid email address");
    });

    it("falls back to a friendly validation message when detail is generic", () => {
      const err = backendError(422, { detail: "", error_code: "VALIDATION_ERROR" });
      expect(getApiErrorMessage(err, "auth.signup")).toMatch(/check the form fields/i);
    });
  });

  describe("getApiErrorMessage — search.voice context", () => {
    it("maps UNSUPPORTED_AUDIO_FORMAT to a clear copy", () => {
      const err = backendError(415, {
        detail: "Unsupported audio format: audio/x-foo",
        error_code: "UNSUPPORTED_AUDIO_FORMAT",
      });
      expect(getApiErrorMessage(err, "search.voice")).toMatch(/unsupported audio format/i);
    });

    it("maps AUDIO_FILE_TOO_LARGE to a 'recording too long' copy", () => {
      const err = backendError(413, {
        detail: "Audio recording exceeds the 10MB limit.",
        error_code: "AUDIO_FILE_TOO_LARGE",
      });
      expect(getApiErrorMessage(err, "search.voice")).toMatch(/recording is too long/i);
    });

    it("maps 503 to a 'voice transcription unavailable' copy", () => {
      const err = backendError(503, { detail: "down", error_code: "SERVICE_UNAVAILABLE" });
      expect(getApiErrorMessage(err, "search.voice")).toMatch(/voice transcription is unavailable/i);
    });

    it("maps a TypeError (browser fetch failure) to the network message", () => {
      expect(getApiErrorMessage(new TypeError("Failed to fetch"), "search.voice")).toMatch(/network/i);
    });
  });

  describe("getApiErrorMessage — viewing.book context", () => {
    it("maps 409 to 'slot just filled up'", () => {
      const err = backendError(409, { detail: "Viewing slot is fully booked", error_code: "CONFLICT" });
      expect(getApiErrorMessage(err, "viewing.book")).toMatch(/that time slot just filled up/i);
    });

    it("maps 404 to 'slot no longer available'", () => {
      const err = backendError(404, { detail: "Slot gone", error_code: "NOT_FOUND" });
      expect(getApiErrorMessage(err, "viewing.book")).toMatch(/no longer available/i);
    });
  });

  describe("getApiErrorMessage — inquiry.submit context", () => {
    it("maps EMPTY_LEAD_MESSAGE to a specific inquiry message", () => {
      const err = backendError(422, {
        detail: "Write a short message before sending a lead.",
        error_code: "EMPTY_LEAD_MESSAGE",
      });
      expect(getApiErrorMessage(err, "inquiry.submit")).toMatch(/write a short message/i);
    });

    it("maps PROFILE_INCOMPLETE_FOR_LEADS to a profile-completion message", () => {
      const err = backendError(422, {
        detail: "Complete your profile with your name and at least one contact method before sending a lead.",
        error_code: "PROFILE_INCOMPLETE_FOR_LEADS",
        missing_fields: ["name"],
      });
      expect(getApiErrorMessage(err, "inquiry.submit")).toMatch(/complete your profile/i);
    });
  });

  describe("getApiErrorMessage — generic fallbacks", () => {
    it("maps a network error to the network message regardless of context", () => {
      expect(getApiErrorMessage(new TypeError("Failed to fetch"), "generic")).toMatch(/network/i);
    });

    it("maps a 401 with no specific context to 'session expired'", () => {
      expect(getApiErrorMessage(backendError(401, { detail: "x", error_code: "UNAUTHORIZED" }), "generic"))
        .toMatch(/session expired/i);
    });

    it("maps a 403 with no specific context to 'no permission'", () => {
      expect(getApiErrorMessage(backendError(403, { detail: "x", error_code: "FORBIDDEN" }), "generic"))
        .toMatch(/permission/i);
    });

    it("maps a 5xx to the server fallback", () => {
      expect(getApiErrorMessage(backendError(500, { detail: "x" }), "generic"))
        .toMatch(/something on our side broke/i);
    });

    it("uses the backend detail when no contextual or status mapping applies", () => {
      const err = backendError(418, { detail: "I'm a teapot", error_code: "TEAPOT" });
      expect(getApiErrorMessage(err, "generic")).toBe("I'm a teapot");
    });

    it("never returns a literal 'Error' or 'Request failed' fallback", () => {
      const errors = [
        new TypeError("Failed to fetch"),
        backendError(500, { detail: "Internal server error" }),
        backendError(503, { detail: "" }),
        new Error("plain js error"),
        backendError(0, {}),
      ];
      for (const err of errors) {
        const message = getApiErrorMessage(err);
        expect(message).not.toBe("Error");
        expect(message).not.toBe("Request failed");
        expect(message).not.toMatch(/^API request failed/);
        expect(message.length).toBeGreaterThan(10);
      }
    });
  });
});
