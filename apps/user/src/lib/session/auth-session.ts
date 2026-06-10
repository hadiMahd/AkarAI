import type { User } from "../api/auth";

const LEGACY_KEYS = ["access_token", "refresh_token", "user"] as const;

let memoryAccessToken: string | null = null;
let memoryUser: User | null = null;

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

export function setSession(accessToken: string, user: User): void {
  memoryAccessToken = accessToken;
  memoryUser = user;
  clearLegacyStorage();
}

export function getSession(): { accessToken: string | null; user: User | null } {
  return { accessToken: memoryAccessToken, user: memoryUser };
}

export function clearSession(): void {
  memoryAccessToken = null;
  memoryUser = null;
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

export function getUser(): User | null {
  return memoryUser;
}

export function setUser(user: User): void {
  memoryUser = user;
}
