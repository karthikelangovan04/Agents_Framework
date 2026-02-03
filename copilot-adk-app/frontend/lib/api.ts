/**
 * API client for backend communication
 */

import { getApiUrl } from "./auth";

export type SessionItem = {
  id: string;
  user_id: number;
  created_at?: string;
};

/**
 * List all sessions for the authenticated user
 */
export async function listSessions(token: string): Promise<SessionItem[]> {
  const res = await fetch(`${getApiUrl()}/api/sessions`, {
    headers: {
      Authorization: `Bearer ${token}`,
    },
  });
  if (!res.ok) {
    throw new Error(`Failed to list sessions: ${res.status}`);
  }
  const data = await res.json();
  // Backend returns: { sessions: Array<{ id, create_time, update_time }> }
  return (data.sessions || []).map((s: any) => ({
    id: s.id,
    user_id: 0, // Will be set by backend
    created_at: s.create_time,
  }));
}

/**
 * Create a new session for the authenticated user
 */
export async function createSession(token: string): Promise<SessionItem> {
  const res = await fetch(`${getApiUrl()}/api/sessions`, {
    method: "POST",
    headers: {
      Authorization: `Bearer ${token}`,
      "Content-Type": "application/json",
    },
  });
  if (!res.ok) {
    throw new Error(`Failed to create session: ${res.status}`);
  }
  const data = await res.json();
  // Backend returns: { id: string, create_time: string, update_time: string }
  return {
    id: data.id,
    user_id: 0, // Will be set by backend
    created_at: data.create_time,
  };
}

/**
 * Set user and session cookies for AG-UI
 */
export async function setUserAndSessionCookies(
  userId: number,
  sessionId: string
): Promise<void> {
  await fetch("/api/session", {
    method: "POST",
    headers: {
      "Content-Type": "application/json",
    },
    body: JSON.stringify({ user_id: userId, session_id: sessionId }),
  });
}
