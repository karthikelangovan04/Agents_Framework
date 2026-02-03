"use client";

import { useEffect, useState, useRef } from "react";
import { useRouter } from "next/navigation";
import { useAuth } from "@/contexts/AuthContext";
import { listSessions, createSession, setSessionCookie, SessionItem } from "@/lib/api";
import { CopilotKit } from "@copilotkit/react-core";
import { CopilotSidebar } from "@copilotkit/react-ui";
import "@copilotkit/react-ui/styles.css";

const styles = {
  layout: {
    display: "flex",
    height: "100vh",
    background: "var(--background)",
  },
  sidebar: {
    width: 260,
    background: "var(--card)",
    borderRight: "1px solid var(--border)",
    display: "flex",
    flexDirection: "column" as const,
  },
  sidebarHeader: {
    padding: "1rem",
    borderBottom: "1px solid var(--border)",
    display: "flex",
    justifyContent: "space-between",
    alignItems: "center",
  },
  newChatBtn: {
    padding: "0.5rem 0.75rem",
    background: "var(--primary)",
    border: "none",
    borderRadius: 6,
    color: "white",
    cursor: "pointer",
    fontSize: 14,
  },
  logoutBtn: {
    padding: "0.4rem 0.6rem",
    background: "transparent",
    border: "1px solid var(--border)",
    borderRadius: 6,
    color: "var(--foreground)",
    cursor: "pointer",
    fontSize: 12,
  },
  sessionList: {
    flex: 1,
    overflow: "auto",
    padding: "0.5rem",
  },
  sessionItem: {
    padding: "0.6rem 0.75rem",
    borderRadius: 6,
    cursor: "pointer",
    marginBottom: 2,
    fontSize: 14,
    background: "transparent",
    border: "none",
    color: "var(--foreground)",
    textAlign: "left" as const,
    width: "100%",
  },
  sessionItemActive: {
    background: "var(--border)",
  },
  main: {
    flex: 1,
    display: "flex",
    flexDirection: "column" as const,
    overflow: "hidden",
  },
  mainHeader: {
    padding: "0.75rem 1rem",
    borderBottom: "1px solid var(--border)",
    fontSize: 14,
    color: "var(--foreground)",
  },
  mainContent: {
    flex: 1,
    padding: "1rem",
    overflow: "auto",
  },
};

export default function ChatPage() {
  const { user, token, loading, logout } = useAuth();
  const router = useRouter();
  const [sessions, setSessions] = useState<SessionItem[]>([]);
  const [currentSessionId, setCurrentSessionId] = useState<string | null>(null);
  const [sessionsLoading, setSessionsLoading] = useState(true);
  const initializedRef = useRef(false);
  const redirectedRef = useRef(false);

  // Check auth and redirect if needed
  useEffect(() => {
    if (loading) return;
    if (!user || !token) {
      if (!redirectedRef.current) {
        redirectedRef.current = true;
        router.replace("/login");
      }
    }
  }, [user, token, loading, router]);

  // Load sessions only once when component mounts and user is authenticated
  useEffect(() => {
    if (loading) return;
    if (!user || !token) return;

    // Prevent running multiple times
    if (initializedRef.current) return;
    initializedRef.current = true;

    let mounted = true;

    async function initSessions() {
      setSessionsLoading(true);
      try {
        let list = await listSessions(token);
        if (!mounted) return;

        if (list.length === 0) {
          const newSession = await createSession(token);
          if (!mounted) return;
          list = [newSession];
        }

        setSessions(list);
        
        // Set first session as current
        if (list.length > 0) {
          const first = list[0];
          setCurrentSessionId(first.id);
          await setSessionCookie(first.id);
        }
      } catch (err) {
        if (mounted) setSessions([]);
      } finally {
        if (mounted) setSessionsLoading(false);
      }
    }

    initSessions();

    return () => {
      mounted = false;
    };
  }, [user, token, loading]); // Only depends on user, token, and loading

  useEffect(() => {
    if (!currentSessionId) return;
    setSessionCookie(currentSessionId);
  }, [currentSessionId]);

  async function handleNewChat() {
    if (!token) return;
    try {
      const newSession = await createSession(token);
      setSessions((prev) => [newSession, ...prev]);
      setCurrentSessionId(newSession.id);
      await setSessionCookie(newSession.id);
    } catch {
      // ignore
    }
  }

  async function handleSelectSession(sessionId: string) {
    setCurrentSessionId(sessionId);
    await setSessionCookie(sessionId);
  }

  function handleLogout() {
    logout();
    router.replace("/login");
  }

  if (loading || !user) {
    return (
      <main style={{ padding: "2rem", textAlign: "center" }}>
        <p>Loading...</p>
      </main>
    );
  }

  return (
    <CopilotKit runtimeUrl="/api/copilotkit" agent="my_agent">
      <div style={styles.layout}>
        <aside style={styles.sidebar}>
          <div style={styles.sidebarHeader}>
            <span style={{ fontWeight: 600 }}>Chats</span>
            <button type="button" style={styles.newChatBtn} onClick={handleNewChat}>
              New chat
            </button>
          </div>
          <div style={styles.sidebarHeader}>
            <span style={{ fontSize: 12, color: "var(--foreground)" }}>{user.username}</span>
            <button type="button" style={styles.logoutBtn} onClick={handleLogout}>
              Logout
            </button>
          </div>
          <div style={styles.sessionList}>
            {sessionsLoading ? (
              <p style={{ padding: "1rem", fontSize: 14 }}>Loading...</p>
            ) : (
              sessions.map((s) => (
                <button
                  key={s.id}
                  type="button"
                  style={{
                    ...styles.sessionItem,
                    ...(currentSessionId === s.id ? styles.sessionItemActive : {}),
                  }}
                  onClick={() => handleSelectSession(s.id)}
                >
                  {s.id.slice(0, 8)}…
                </button>
              ))
            )}
          </div>
        </aside>
        <div style={styles.main}>
          <header style={styles.mainHeader}>
            {currentSessionId ? `Session ${currentSessionId.slice(0, 8)}…` : "Select or start a chat"}
          </header>
          <div style={styles.mainContent}>
            <p style={{ margin: 0, color: "var(--foreground)", fontSize: 14 }}>
              Use the chat panel on the right to talk to the assistant. Messages are stored per session; switching chats loads that conversation&apos;s context.
            </p>
          </div>
        </div>
        <CopilotSidebar
          defaultOpen={true}
          clickOutsideToClose={false}
          labels={{
            title: "Assistant",
            initial: "Ask anything…",
          }}
        />
      </div>
    </CopilotKit>
  );
}
