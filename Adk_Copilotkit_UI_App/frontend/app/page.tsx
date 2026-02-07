import Link from "next/link";

export default function Home() {
  return (
    <div style={{ padding: "2rem", maxWidth: 600, margin: "0 auto" }}>
      <h1 style={{ marginBottom: "1rem" }}>ADK CopilotKit App</h1>
      <p style={{ color: "#666", marginBottom: "1.5rem" }}>
        Choose an agent to get started.
      </p>
      <ul style={{ listStyle: "none", padding: 0 }}>
        <li style={{ marginBottom: "0.75rem" }}>
          <Link
            href="/deal"
            style={{ color: "var(--primary)", fontWeight: 600 }}
          >
            Deal Builder
          </Link>
          <span style={{ color: "#666", marginLeft: "0.5rem" }}>
            — Build and improve deals with shared state + AI
          </span>
        </li>
        <li>
          <Link
            href="/chat"
            style={{ color: "var(--primary)", fontWeight: 600 }}
          >
            Knowledge Q&A
          </Link>
          <span style={{ color: "#666", marginLeft: "0.5rem" }}>
            — Persistent chat for product/pricing Q&A
          </span>
        </li>
      </ul>
    </div>
  );
}
