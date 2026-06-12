import { getAccessToken, setAccessToken, setSession, setTenantSession, setUser, clearSession, clearLegacyStorage } from "../session/auth-session";
import type { AgencyUser, ActorSummary } from "./auth";
import type { AgencyTenantSession } from "../session/tenant-session";

function resolveApiBaseUrl(): string {
  const configured = import.meta.env.VITE_API_BASE_URL;
  if (typeof window === "undefined") {
    return configured || "http://127.0.0.1:8000";
  }

  const isLocalHost = window.location.hostname === "localhost" || window.location.hostname === "127.0.0.1";
  if (isLocalHost) {
    return `${window.location.protocol}//${window.location.hostname}:8000`;
  }

  return configured || `${window.location.protocol}//${window.location.hostname}:8000`;
}

const API_BASE_URL = resolveApiBaseUrl();

interface ApiClientOptions extends RequestInit {
  params?: Record<string, string | number | boolean | undefined>;
  skipAuth?: boolean;
  responseType?: "json" | "blob" | "text";
}

class ApiError extends Error {
  public status: number;
  public data: unknown;

  constructor(message: string, status: number, data?: unknown) {
    super(message);
    this.name = "ApiError";
    this.status = status;
    this.data = data;
  }
}

let refreshPromise: Promise<string | null> | null = null;
let restorePromise: Promise<boolean> | null = null;
let csrfToken: string | null = null;

function getCsrfTokenFromCookie(): string | null {
  const match = document.cookie.match(/(?:^|;\s*)akarai_csrf=([^;]*)/);
  return match ? decodeURIComponent(match[1]) : null;
}

async function refreshAccessToken(): Promise<string | null> {
  if (refreshPromise) {
    return refreshPromise;
  }

  refreshPromise = (async () => {
    try {
      const token = csrfToken || getCsrfTokenFromCookie();

      const response = await fetch(`${API_BASE_URL}/auth/refresh`, {
        method: "POST",
        credentials: "include",
        headers: {
          "Content-Type": "application/json",
          ...(token ? { "X-CSRF-Token": token } : {}),
        },
      });

      if (!response.ok) {
        clearSession();
        return null;
      }

      const data = await response.json();
      setAccessToken(data.access_token);
      return data.access_token;
    } catch {
      clearSession();
      return null;
    } finally {
      refreshPromise = null;
    }
  })();

  return refreshPromise;
}

function actorToUser(actor: ActorSummary): AgencyUser {
  return {
    id: actor.id,
    email: actor.email,
    name: actor.email,
    is_active: actor.is_active,
    created_at: "",
    updated_at: "",
    role: actor.role,
    permissions: actor.permissions,
    tenant_id: actor.tenant_id,
  };
}

function actorToTenantSession(actor: ActorSummary): AgencyTenantSession {
  return {
    userId: actor.id,
    tenantId: actor.tenant_id ?? "",
    role: actor.role,
    permissions: actor.permissions,
    isActive: actor.is_active,
  };
}

export async function apiClient<T = unknown>(
  endpoint: string,
  options: ApiClientOptions = {}
): Promise<T> {
  const { params, skipAuth, responseType = "json", ...fetchOptions } = options;

  let url = `${API_BASE_URL}${endpoint}`;

  if (params) {
    const searchParams = new URLSearchParams();
    Object.entries(params).forEach(([key, value]) => {
      if (value !== undefined && value !== null) {
        searchParams.append(key, String(value));
      }
    });
    const queryString = searchParams.toString();
    if (queryString) {
      url += `?${queryString}`;
    }
  }

  const isFormDataBody = typeof FormData !== "undefined" && fetchOptions.body instanceof FormData;
  const headers: Record<string, string> = {
    ...(!isFormDataBody ? { "Content-Type": "application/json" } : {}),
    ...(fetchOptions.headers as Record<string, string>),
  };

  if (!skipAuth) {
    const accessToken = getAccessToken();
    if (accessToken) {
      headers["Authorization"] = `Bearer ${accessToken}`;
    }
  }

  let response = await fetch(url, {
    ...fetchOptions,
    headers,
    credentials: "include",
  });

  if (response.status === 401 && !skipAuth && getAccessToken()) {
    const newToken = await refreshAccessToken();
    if (newToken) {
      headers["Authorization"] = `Bearer ${newToken}`;
      response = await fetch(url, {
        ...fetchOptions,
        headers,
        credentials: "include",
      });
    }
  }

  if (!response.ok) {
    let errorData: unknown;
    try {
      errorData = await response.json();
    } catch {
      errorData = await response.text();
    }
    throw new ApiError(
      `API request failed: ${response.statusText}`,
      response.status,
      errorData
    );
  }

  if (response.status === 204) {
    return {} as T;
  }

  if (responseType === "blob") {
    return response.blob() as Promise<T>;
  }
  if (responseType === "text") {
    return response.text() as Promise<T>;
  }

  return response.json();
}

export async function restoreSession(): Promise<boolean> {
  if (restorePromise) {
    return restorePromise;
  }

  restorePromise = restoreSessionOnce();
  try {
    return await restorePromise;
  } finally {
    restorePromise = null;
  }
}

async function restoreSessionOnce(): Promise<boolean> {
  clearLegacyStorage();

  if (getAccessToken()) {
    return true;
  }

  const token = csrfToken || getCsrfTokenFromCookie();
  if (!token) {
    clearSession();
    return false;
  }

  try {
    const response = await fetch(`${API_BASE_URL}/auth/refresh`, {
      method: "POST",
      credentials: "include",
      headers: {
        "Content-Type": "application/json",
        ...(token ? { "X-CSRF-Token": token } : {}),
      },
    });

    if (!response.ok) {
      clearSession();
      return false;
    }

    const data = await response.json();
    const user = actorToUser(data.actor);
    const tenantSession = actorToTenantSession(data.actor);
    setSession(data.access_token, user, tenantSession);
    setUser(user);
    setTenantSession(tenantSession);
    return true;
  } catch {
    clearSession();
    return false;
  }
}

export async function fetchCsrfToken(): Promise<string | null> {
  try {
    const response = await fetch(`${API_BASE_URL}/auth/csrf-token`, {
      credentials: "include",
    });

    if (!response.ok) {
      return null;
    }

    const data = await response.json();
    csrfToken = data.csrf_token;
    return csrfToken;
  } catch {
    return null;
  }
}

export function setCsrfToken(token: string): void {
  csrfToken = token;
}

export function getCsrfToken(): string | null {
  return csrfToken || getCsrfTokenFromCookie();
}

export function clearCsrfToken(): void {
  csrfToken = null;
}

export { ApiError, API_BASE_URL };
