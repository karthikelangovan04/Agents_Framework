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

/**
 * Fetch session history (state and messages) from the backend
 */
export interface SessionHistory {
  threadId: string;
  threadExists: boolean;
  state: Record<string, any>;
  messages: Array<{
    role: string;
    content: string;
  }>;
}

export async function getSessionHistory(
  sessionId: string,
  userId: number
): Promise<SessionHistory | null> {
  try {
    // In AG-UI protocol, threadId is used to lookup sessions
    // We use sessionId as threadId (configured in CopilotKit threadId prop)
    const res = await fetch(`${getApiUrl()}/agents/state`, {
      method: "POST",
      headers: {
        "Content-Type": "application/json",
      },
      body: JSON.stringify({
        threadId: sessionId, // Use sessionId as threadId
        appName: "copilot_adk_app",
        userId: String(userId),
      }),
    });

    if (!res.ok) {
      console.error(`Failed to fetch session history: ${res.status}`);
      return null;
    }

    const data = await res.json();
    
    // If thread doesn't exist, it might be a new session or not yet used
    if (!data.threadExists) {
      console.log(`Session ${sessionId.slice(0, 8)}... has no messages yet (new session)`);
      return {
        threadId: sessionId,
        threadExists: false,
        state: {},
        messages: [],
      };
    }

    return {
      threadId: data.threadId,
      threadExists: data.threadExists,
      state: JSON.parse(data.state || "{}"),
      messages: JSON.parse(data.messages || "[]"),
    };
  } catch (error) {
    console.error("Error fetching session history:", error);
    return null;
  }
}
