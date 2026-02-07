"use client";

import { CopilotKit, useCoAgent, useCopilotChat } from "@copilotkit/react-core";
import { CopilotSidebar } from "@copilotkit/react-ui";
import { TextMessage, MessageRole } from "@copilotkit/runtime-client-gql";
import React, { useState, useEffect } from "react";
import "@copilotkit/react-ui/styles.css";
import Link from "next/link";

interface DealState {
  customer_name: string;
  segment: string;
  products: string[];
  estimated_value: string;
  stage: string;
  next_steps: string[];
  changes: string;
}

const INITIAL_DEAL: DealState = {
  customer_name: "",
  segment: "",
  products: [],
  estimated_value: "",
  stage: "Discovery",
  next_steps: [],
  changes: "",
};

const STAGES = ["Discovery", "Qualification", "Proposal", "Negotiation", "Closed Won", "Closed Lost"];

export default function DealPage() {
  return (
    <CopilotKit
      runtimeUrl="/api/copilotkit"
      showDevConsole={false}
      agent="deal_builder"
    >
      <div className="min-h-screen w-full flex items-center justify-center">
        <DealForm />
        <CopilotSidebar
          defaultOpen={true}
          labels={{
            title: "Deal Builder",
            initial: "Ask me to improve this deal or suggest next steps.",
          }}
          clickOutsideToClose={false}
        />
      </div>
    </CopilotKit>
  );
}

function DealForm() {
  const { state: agentState, setState: setAgentState } = useCoAgent<{ deal: DealState }>({
    name: "deal_builder",
    initialState: { deal: INITIAL_DEAL },
  });
  const [deal, setDeal] = useState<DealState>(INITIAL_DEAL);
  const { appendMessage, isLoading } = useCopilotChat();

  const updateDeal = (partial: Partial<DealState>) => {
    const next = { ...deal, ...partial };
    setDeal(next);
    setAgentState({ ...agentState, deal: next });
  };

  // Sync from agent state to local when agent updates
  useEffect(() => {
    if (agentState?.deal) {
      const d = agentState.deal;
      setDeal({
        customer_name: d.customer_name ?? "",
        segment: d.segment ?? "",
        products: Array.isArray(d.products) ? d.products : [],
        estimated_value: d.estimated_value ?? "",
        stage: d.stage ?? "Discovery",
        next_steps: Array.isArray(d.next_steps) ? d.next_steps : [],
        changes: d.changes ?? "",
      });
    }
  }, [agentState?.deal]);

  const addProduct = () => updateDeal({ products: [...deal.products, ""] });
  const setProduct = (i: number, v: string) => {
    const p = [...deal.products];
    p[i] = v;
    updateDeal({ products: p });
  };
  const removeProduct = (i: number) => {
    updateDeal({ products: deal.products.filter((_, j) => j !== i) });
  };
  const addNextStep = () => updateDeal({ next_steps: [...deal.next_steps, ""] });
  const setNextStep = (i: number, v: string) => {
    const n = [...deal.next_steps];
    n[i] = v;
    updateDeal({ next_steps: n });
  };
  const removeNextStep = (i: number) => {
    updateDeal({ next_steps: deal.next_steps.filter((_, j) => j !== i) });
  };

  return (
    <div style={{ marginBottom: 120, padding: 24, maxWidth: 720, width: "100%" }}>
      <div style={{ marginBottom: 16 }}>
        <Link href="/" style={{ color: "var(--primary)", fontSize: 14 }}>
          ← Home
        </Link>
      </div>
      <div style={{ background: "var(--card)", borderRadius: 12, padding: 24, boxShadow: "0 2px 8px rgba(0,0,0,0.06)", border: "1px solid var(--border)" }}>
        <h2 style={{ marginTop: 0, marginBottom: 20 }}>Deal / Opportunity</h2>

        <div style={{ marginBottom: 16 }}>
          <label style={{ display: "block", fontSize: 12, color: "#666", marginBottom: 4 }}>Customer name</label>
          <input
            type="text"
            value={deal.customer_name}
            onChange={(e) => updateDeal({ customer_name: e.target.value })}
            placeholder="Account or customer name"
            style={{ width: "100%", padding: "8px 12px", borderRadius: 8, border: "1px solid var(--border)" }}
          />
        </div>
        <div style={{ marginBottom: 16 }}>
          <label style={{ display: "block", fontSize: 12, color: "#666", marginBottom: 4 }}>Segment</label>
          <input
            type="text"
            value={deal.segment}
            onChange={(e) => updateDeal({ segment: e.target.value })}
            placeholder="e.g. Enterprise, SMB"
            style={{ width: "100%", padding: "8px 12px", borderRadius: 8, border: "1px solid var(--border)" }}
          />
        </div>
        <div style={{ marginBottom: 16 }}>
          <label style={{ display: "block", fontSize: 12, color: "#666", marginBottom: 4 }}>Estimated value</label>
          <input
            type="text"
            value={deal.estimated_value}
            onChange={(e) => updateDeal({ estimated_value: e.target.value })}
            placeholder="e.g. $50k"
            style={{ width: "100%", padding: "8px 12px", borderRadius: 8, border: "1px solid var(--border)" }}
          />
        </div>
        <div style={{ marginBottom: 16 }}>
          <label style={{ display: "block", fontSize: 12, color: "#666", marginBottom: 4 }}>Stage</label>
          <select
            value={deal.stage}
            onChange={(e) => updateDeal({ stage: e.target.value })}
            style={{ width: "100%", padding: "8px 12px", borderRadius: 8, border: "1px solid var(--border)" }}
          >
            {STAGES.map((s) => (
              <option key={s} value={s}>{s}</option>
            ))}
          </select>
        </div>
        <div style={{ marginBottom: 16 }}>
          <div style={{ display: "flex", justifyContent: "space-between", alignItems: "center", marginBottom: 8 }}>
            <label style={{ fontSize: 12, color: "#666" }}>Products</label>
            <button type="button" onClick={addProduct} style={{ fontSize: 12, color: "var(--primary)" }}>+ Add</button>
          </div>
          {deal.products.map((p, i) => (
            <div key={i} style={{ display: "flex", gap: 8, marginBottom: 6 }}>
              <input
                type="text"
                value={p}
                onChange={(e) => setProduct(i, e.target.value)}
                placeholder="Product name"
                style={{ flex: 1, padding: "8px 12px", borderRadius: 8, border: "1px solid var(--border)" }}
              />
              <button type="button" onClick={() => removeProduct(i)} style={{ padding: "0 10px" }}>×</button>
            </div>
          ))}
        </div>
        <div style={{ marginBottom: 20 }}>
          <div style={{ display: "flex", justifyContent: "space-between", alignItems: "center", marginBottom: 8 }}>
            <label style={{ fontSize: 12, color: "#666" }}>Next steps</label>
            <button type="button" onClick={addNextStep} style={{ fontSize: 12, color: "var(--primary)" }}>+ Add</button>
          </div>
          {deal.next_steps.map((s, i) => (
            <div key={i} style={{ display: "flex", gap: 8, marginBottom: 6 }}>
              <input
                type="text"
                value={s}
                onChange={(e) => setNextStep(i, e.target.value)}
                placeholder="Next step"
                style={{ flex: 1, padding: "8px 12px", borderRadius: 8, border: "1px solid var(--border)" }}
              />
              <button type="button" onClick={() => removeNextStep(i)} style={{ padding: "0 10px" }}>×</button>
            </div>
          ))}
        </div>

        <div style={{ display: "flex", justifyContent: "center", marginTop: 24 }}>
          <button
            type="button"
            disabled={isLoading}
            onClick={() => {
              if (!isLoading) {
                // Sync current form deal to agent state so the backend receives it with the message
                const currentDeal = {
                  customer_name: deal.customer_name ?? "",
                  segment: deal.segment ?? "",
                  products: [...deal.products],
                  estimated_value: deal.estimated_value ?? "",
                  stage: deal.stage ?? "Discovery",
                  next_steps: [...deal.next_steps],
                  changes: deal.changes ?? "",
                };
                setAgentState({ ...agentState, deal: currentDeal });
                // Include deal in message so the agent has it even if state sync is delayed
                const dealSummary = [
                  currentDeal.customer_name && `Customer: ${currentDeal.customer_name}`,
                  currentDeal.segment && `Segment: ${currentDeal.segment}`,
                  currentDeal.estimated_value && `Value: ${currentDeal.estimated_value}`,
                  currentDeal.stage && `Stage: ${currentDeal.stage}`,
                  currentDeal.products.filter(Boolean).length > 0 && `Products: ${currentDeal.products.filter(Boolean).join(", ")}`,
                  currentDeal.next_steps.filter(Boolean).length > 0 && `Next steps: ${currentDeal.next_steps.filter(Boolean).join(", ")}`,
                ].filter(Boolean).join(". ");
                const content = dealSummary
                  ? `Improve this deal and suggest next steps. Current deal: ${dealSummary}`
                  : "Improve this deal and suggest next steps";
                appendMessage(
                  new TextMessage({ role: MessageRole.User, content })
                );
              }
            }}
            style={{
              padding: "12px 24px",
              background: "var(--primary)",
              color: "white",
              border: "none",
              borderRadius: 8,
              fontWeight: 600,
              cursor: isLoading ? "not-allowed" : "pointer",
              opacity: isLoading ? 0.8 : 1,
            }}
          >
            {isLoading ? "Thinking…" : "Improve with AI"}
          </button>
        </div>
      </div>
    </div>
  );
}
