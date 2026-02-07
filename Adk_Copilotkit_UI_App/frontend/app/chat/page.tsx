"use client";

import { CopilotKit } from "@copilotkit/react-core";
import { CopilotSidebar } from "@copilotkit/react-ui";
import "@copilotkit/react-ui/styles.css";
import Link from "next/link";

export default function ChatPage() {
  return (
    <CopilotKit
      runtimeUrl="/api/copilotkit"
      showDevConsole={false}
      agent="knowledge_qa"
    >
      <div className="min-h-screen w-full flex items-center justify-center">
        <div style={{ padding: 24, maxWidth: 720, width: "100%" }}>
          <div style={{ marginBottom: 16 }}>
            <Link href="/" style={{ color: "var(--primary)", fontSize: 14 }}>
              ← Home
            </Link>
          </div>
          <p style={{ color: "#666", marginBottom: 24 }}>
            Knowledge Q&A: ask about products, pricing, or playbooks. Chat history is stored per session.
          </p>
        </div>
        <CopilotSidebar
          defaultOpen={true}
          labels={{
            title: "Knowledge Q&A",
            initial: "Ask me anything about products, pricing, or playbooks.",
          }}
          clickOutsideToClose={false}
        />
      </div>
    </CopilotKit>
  );
}
