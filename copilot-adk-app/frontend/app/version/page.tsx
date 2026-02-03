"use client";

export default function VersionPage() {
  const VERSION = "v2.1-cookie-fix-2026-02-03";
  const FEATURES = [
    "✅ Triple cookie setting (login + restore + chat)",
    "✅ Console logging for debugging",
    "✅ cookiesReady state guard",
    "✅ Synchronous cookie setting",
  ];

  return (
    <div style={{ padding: "2rem", fontFamily: "monospace", maxWidth: "800px" }}>
      <h1 style={{ fontSize: "2rem", marginBottom: "1rem" }}>
        🔢 Version Check
      </h1>
      
      <div style={{ 
        padding: "1rem", 
        background: "#e8f5e9", 
        border: "2px solid #4CAF50",
        borderRadius: "8px",
        marginBottom: "2rem"
      }}>
        <h2 style={{ margin: 0, color: "#2e7d32" }}>
          Current Version: {VERSION}
        </h2>
      </div>

      <div style={{ marginBottom: "2rem" }}>
        <h3>Features in this version:</h3>
        <ul>
          {FEATURES.map((feature, i) => (
            <li key={i} style={{ marginBottom: "0.5rem" }}>{feature}</li>
          ))}
        </ul>
      </div>

      <div style={{ 
        padding: "1rem", 
        background: "#fff3cd", 
        borderRadius: "8px",
        marginBottom: "2rem"
      }}>
        <h3>❓ Is this the version you expected?</h3>
        <p><strong>If you see an OLD version number or this page shows an error:</strong></p>
        <ol>
          <li>Close ALL tabs with localhost:3000</li>
          <li>Open NEW Private/Incognito window (Cmd+Shift+N)</li>
          <li>Go to: http://localhost:3000/version</li>
          <li>You should see: <code>{VERSION}</code></li>
        </ol>
      </div>

      <div style={{ marginTop: "2rem" }}>
        <a href="/debug" style={{ 
          display: "inline-block",
          padding: "0.75rem 1.5rem", 
          background: "#2196F3", 
          color: "white", 
          textDecoration: "none",
          borderRadius: "4px",
          marginRight: "1rem"
        }}>
          Go to Debug Page
        </a>
        <a href="/chat" style={{ 
          display: "inline-block",
          padding: "0.75rem 1.5rem", 
          background: "#4CAF50", 
          color: "white", 
          textDecoration: "none",
          borderRadius: "4px"
        }}>
          Go to Chat
        </a>
      </div>

      <div style={{ marginTop: "3rem", padding: "1rem", background: "#f5f5f5", borderRadius: "4px" }}>
        <h3>🧪 Quick Test:</h3>
        <p>After confirming this is the right version:</p>
        <ol>
          <li>Go to <a href="/debug" style={{ color: "#2196F3" }}>/debug</a></li>
          <li>Check cookies are set (should see copilot_adk_user_id=3)</li>
          <li>Go to <a href="/chat" style={{ color: "#4CAF50" }}>/chat</a></li>
          <li>Open Console (F12) - look for 🔐 or 🍪 log messages</li>
          <li>Send a message</li>
          <li>Run: <code>./verify-chat-data.sh</code></li>
        </ol>
      </div>
    </div>
  );
}
