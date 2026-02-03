"use client";

import { useEffect, useState } from "react";

export default function DebugPage() {
  const [cookies, setCookies] = useState<string>("");
  const [timestamp, setTimestamp] = useState<string>("");

  useEffect(() => {
    setTimestamp(new Date().toISOString());
    if (typeof document !== "undefined") {
      setCookies(document.cookie || "(no cookies)");
    }
  }, []);

  function refreshCookies() {
    if (typeof document !== "undefined") {
      setCookies(document.cookie || "(no cookies)");
      setTimestamp(new Date().toISOString());
    }
  }

  function testSetCookie() {
    if (typeof document !== "undefined") {
      document.cookie = `test_cookie=${Date.now()}; path=/; max-age=3600; samesite=lax`;
      document.cookie = `copilot_adk_user_id=3; path=/; max-age=${60 * 60 * 24 * 7}; samesite=lax`;
      document.cookie = `copilot_adk_session_id=test-session-${Date.now()}; path=/; max-age=${60 * 60 * 24 * 7}; samesite=lax`;
      alert("Cookies set! Refresh the page to see them.");
    }
  }

  return (
    <div style={{ padding: "2rem", fontFamily: "monospace" }}>
      <h1>🐛 Cookie Debug Page</h1>
      <p>Last updated: {timestamp}</p>
      
      <div style={{ marginTop: "1rem" }}>
        <button onClick={refreshCookies} style={{ marginRight: "1rem", padding: "0.5rem 1rem" }}>
          Refresh Cookies
        </button>
        <button onClick={testSetCookie} style={{ padding: "0.5rem 1rem", background: "#4CAF50", color: "white", border: "none", cursor: "pointer" }}>
          Test Set Cookies
        </button>
        <button onClick={() => window.location.href = "/chat"} style={{ marginLeft: "1rem", padding: "0.5rem 1rem" }}>
          Go to Chat
        </button>
      </div>

      <div style={{ marginTop: "2rem", padding: "1rem", background: "#f5f5f5", borderRadius: "4px" }}>
        <h2>Current Cookies:</h2>
        <pre style={{ whiteSpace: "pre-wrap", wordBreak: "break-all" }}>
          {cookies.split("; ").map((cookie, i) => (
            <div key={i} style={{ 
              padding: "0.25rem", 
              marginBottom: "0.25rem",
              background: cookie.startsWith("copilot_adk") ? "#e8f5e9" : "transparent",
              borderLeft: cookie.startsWith("copilot_adk") ? "3px solid #4CAF50" : "none",
              paddingLeft: cookie.startsWith("copilot_adk") ? "0.5rem" : "0.25rem"
            }}>
              {cookie}
            </div>
          ))}
        </pre>
      </div>

      <div style={{ marginTop: "2rem", padding: "1rem", background: "#fff3cd", borderRadius: "4px" }}>
        <h2>✅ Expected Cookies:</h2>
        <pre>
          copilot_adk_user_id=3{"\n"}
          copilot_adk_session_id=&lt;uuid&gt;
        </pre>
      </div>

      <div style={{ marginTop: "2rem", padding: "1rem", background: "#f8d7da", borderRadius: "4px" }}>
        <h2>❌ If You See:</h2>
        <pre>No copilot_adk_* cookies</pre>
        <p><strong>Cause:</strong> Browser cache or cookies not being set</p>
        <p><strong>Fix:</strong></p>
        <ol>
          <li>Click "Test Set Cookies" button above</li>
          <li>Hard refresh: Cmd+Shift+R (Mac) or Ctrl+Shift+R (Windows)</li>
          <li>Clear site data: DevTools → Application → Clear site data</li>
        </ol>
      </div>

      <div style={{ marginTop: "2rem" }}>
        <h2>Debug Checklist:</h2>
        <ol>
          <li>Check if copilot_adk_user_id = 3 ✓/✗</li>
          <li>Check if copilot_adk_session_id exists ✓/✗</li>
          <li>Open browser console (F12) and check for 🍪 log messages</li>
          <li>Go to /chat and check console logs</li>
        </ol>
      </div>
    </div>
  );
}
