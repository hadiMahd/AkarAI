import type { AgencyUser } from "../api/auth";
import type { AgencyTenantSession } from "./tenant-session";

const LEGACY_KEYS = ["access_token", "refresh_token", "user"] as const;

let memoryAccessToken: string | null = null;
let memoryUser: AgencyUser | null = null;
let memoryTenantSession: AgencyTenantSession | null = null;

export function clearLegacyStorage(): void {
  for (const key of LEGACY_KEYS) {
    try {
      localStorage.removeItem(key);
    } catch {
      // ignore
    }
    try {
      sessionStorage.removeItem(key);
    } catch {
      // ignore
    }
  }
}

export function setSession(
  accessToken: string,
  user: AgencyUser,
  tenantSession: AgencyTenantSession | null = null
): void {
  memoryAccessToken = accessToken;
  memoryUser = user;
  memoryTenantSession = tenantSession;
  clearLegacyStorage();
}

export function getSession(): { accessToken: string | null; user: AgencyUser | null } {
  return {
    accessToken: memoryAccessToken,
    user: memoryUser,
  };
}

export function clearSession(): void {
  memoryAccessToken = null;
  memoryUser = null;
  memoryTenantSession = null;
  clearLegacyStorage();
}

export function isAuthenticated(): boolean {
  return !!memoryAccessToken;
}

export function getAccessToken(): string | null {
  return memoryAccessToken;
}

export function setAccessToken(token: string): void {
  memoryAccessToken = token;
}

export function getUser(): AgencyUser | null {
  return memoryUser;
}

export function setUser(user: AgencyUser): void {
  memoryUser = user;
}

export function getTenantSession(): AgencyTenantSession | null {
  return memoryTenantSession;
}

export function setTenantSession(session: AgencyTenantSession | null): void {
  memoryTenantSession = session;
}
