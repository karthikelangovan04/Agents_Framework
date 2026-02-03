/**
 * Authentication utilities for client-side storage
 */

export type UserInfo = {
  user_id: number;
  username: string;
};

const TOKEN_KEY = "copilot_adk_token";
const USER_KEY = "copilot_adk_user";

export function getApiUrl(): string {
  return process.env.NEXT_PUBLIC_API_URL || "http://localhost:8000";
}

export function getToken(): string | null {
  if (typeof window === "undefined") return null;
  return localStorage.getItem(TOKEN_KEY);
}

export function setToken(token: string): void {
  if (typeof window === "undefined") return;
  localStorage.setItem(TOKEN_KEY, token);
}

export function getUser(): UserInfo | null {
  if (typeof window === "undefined") return null;
  const userJson = localStorage.getItem(USER_KEY);
  if (!userJson) return null;
  try {
    return JSON.parse(userJson) as UserInfo;
  } catch {
    return null;
  }
}

export function setUser(user: UserInfo): void {
  if (typeof window === "undefined") return;
  localStorage.setItem(USER_KEY, JSON.stringify(user));
}

export async function logout(): Promise<void> {
  if (typeof window === "undefined") return;
  localStorage.removeItem(TOKEN_KEY);
  localStorage.removeItem(USER_KEY);
  
  // Clear cookies via API to ensure they're properly removed
  await fetch("/api/session", {
    method: "POST",
    headers: {
      "Content-Type": "application/json",
    },
    body: JSON.stringify({ user_id: null, session_id: null }),
  }).catch(() => {});
  
  // Also clear client-side as backup
  document.cookie = "copilot_adk_user_id=; path=/; max-age=0";
  document.cookie = "copilot_adk_session_id=; path=/; max-age=0";
}
