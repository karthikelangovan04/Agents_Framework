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

interface ProposalState {
  executive_summary: string;
  solution_overview: string;
  benefits: string[];
  pricing: string;
  timeline: string;
  terms: string;
}

interface AgentState {
  deal: DealState;
  proposal: ProposalState;
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

const INITIAL_PROPOSAL: ProposalState = {
  executive_summary: "",
  solution_overview: "",
  benefits: [],
  pricing: "",
  timeline: "",
  terms: "",
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
  const { state: agentState, setState: setAgentState } = useCoAgent<AgentState>({
    name: "deal_builder",
    initialState: { 
      deal: INITIAL_DEAL,
      proposal: INITIAL_PROPOSAL,
    },
  });
  const [deal, setDeal] = useState<DealState>(INITIAL_DEAL);
  const [proposal, setProposal] = useState<ProposalState>(INITIAL_PROPOSAL);
  const { appendMessage, isLoading } = useCopilotChat();

  const updateDeal = (partial: Partial<DealState>) => {
    const next = { ...deal, ...partial };
    setDeal(next);
    setAgentState({ ...agentState, deal: next });
  };

  const updateProposal = (partial: Partial<ProposalState>) => {
    const next = { ...proposal, ...partial };
    setProposal(next);
    setAgentState({ ...agentState, proposal: next });
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

  // Sync proposal from agent state
  useEffect(() => {
    if (agentState?.proposal) {
      const p = agentState.proposal;
      setProposal({
        executive_summary: p.executive_summary ?? "",
        solution_overview: p.solution_overview ?? "",
        benefits: Array.isArray(p.benefits) ? p.benefits : [],
        pricing: p.pricing ?? "",
        timeline: p.timeline ?? "",
        terms: p.terms ?? "",
      });
    }
  }, [agentState?.proposal]);

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

  // Proposal handlers
  const addBenefit = () => updateProposal({ benefits: [...proposal.benefits, ""] });
  const setBenefit = (i: number, v: string) => {
    const b = [...proposal.benefits];
    b[i] = v;
    updateProposal({ benefits: b });
  };
  const removeBenefit = (i: number) => {
    updateProposal({ benefits: proposal.benefits.filter((_, j) => j !== i) });
  };

  const hasProposal = proposal && (
    proposal.executive_summary ||
    proposal.solution_overview ||
    proposal.benefits?.length > 0
  );

  const handleGenerateProposal = () => {
    if (!isLoading) {
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
      appendMessage(
        new TextMessage({ 
          role: MessageRole.User, 
          content: "Generate a comprehensive proposal document for this deal" 
        })
      );
    }
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

      {/* Proposal Section */}
      <div style={{ background: "var(--card)", borderRadius: 12, padding: 24, boxShadow: "0 2px 8px rgba(0,0,0,0.06)", border: "1px solid var(--border)", marginTop: 24 }}>
        <div style={{ display: "flex", justifyContent: "space-between", alignItems: "center", marginBottom: 20, paddingBottom: 16, borderBottom: "2px solid var(--border)" }}>
          <h2 style={{ margin: 0 }}>Proposal</h2>
          {!hasProposal && (
            <button
              type="button"
              disabled={isLoading}
              onClick={handleGenerateProposal}
              style={{
                padding: "8px 16px",
                background: "var(--primary)",
                color: "white",
                border: "none",
                borderRadius: 6,
                fontWeight: 500,
                cursor: isLoading ? "not-allowed" : "pointer",
                opacity: isLoading ? 0.6 : 1,
                fontSize: 14,
              }}
            >
              {isLoading ? "Generating..." : "Generate Proposal"}
            </button>
          )}
        </div>

        {hasProposal ? (
          <div style={{ display: "flex", flexDirection: "column", gap: 20 }}>
            <div style={{ background: "white", padding: 16, borderRadius: 8, border: "1px solid var(--border)" }}>
              <h3 style={{ margin: "0 0 12px 0", fontSize: 16, color: "#495057", fontWeight: 600 }}>Executive Summary</h3>
              <textarea
                value={proposal.executive_summary}
                onChange={(e) => updateProposal({ executive_summary: e.target.value })}
                placeholder="Enter executive summary..."
                rows={4}
                style={{ 
                  width: "100%", 
                  padding: "8px 12px", 
                  borderRadius: 6, 
                  border: "1px solid var(--border)",
                  fontFamily: "inherit",
                  fontSize: 14,
                  lineHeight: 1.6,
                  resize: "vertical"
                }}
              />
            </div>

            <div style={{ background: "white", padding: 16, borderRadius: 8, border: "1px solid var(--border)" }}>
              <h3 style={{ margin: "0 0 12px 0", fontSize: 16, color: "#495057", fontWeight: 600 }}>Solution Overview</h3>
              <textarea
                value={proposal.solution_overview}
                onChange={(e) => updateProposal({ solution_overview: e.target.value })}
                placeholder="Enter solution overview..."
                rows={6}
                style={{ 
                  width: "100%", 
                  padding: "8px 12px", 
                  borderRadius: 6, 
                  border: "1px solid var(--border)",
                  fontFamily: "inherit",
                  fontSize: 14,
                  lineHeight: 1.6,
                  resize: "vertical"
                }}
              />
            </div>

            <div style={{ background: "white", padding: 16, borderRadius: 8, border: "1px solid var(--border)" }}>
              <div style={{ display: "flex", justifyContent: "space-between", alignItems: "center", marginBottom: 12 }}>
                <h3 style={{ margin: 0, fontSize: 16, color: "#495057", fontWeight: 600 }}>Key Benefits</h3>
                <button 
                  type="button" 
                  onClick={addBenefit} 
                  style={{ fontSize: 12, color: "var(--primary)", background: "none", border: "none", cursor: "pointer" }}
                >
                  + Add Benefit
                </button>
              </div>
              {proposal.benefits.map((benefit, idx) => (
                <div key={idx} style={{ display: "flex", gap: 8, marginBottom: 6 }}>
                  <input
                    type="text"
                    value={benefit}
                    onChange={(e) => setBenefit(idx, e.target.value)}
                    placeholder="Benefit description"
                    style={{ 
                      flex: 1, 
                      padding: "8px 12px", 
                      borderRadius: 6, 
                      border: "1px solid var(--border)" 
                    }}
                  />
                  <button 
                    type="button" 
                    onClick={() => removeBenefit(idx)} 
                    style={{ padding: "0 10px", background: "none", border: "none", cursor: "pointer", fontSize: 18 }}
                  >
                    ×
                  </button>
                </div>
              ))}
              {proposal.benefits.length === 0 && (
                <p style={{ fontSize: 12, color: "#6c757d", fontStyle: "italic", margin: 0 }}>
                  No benefits added. Click "+ Add Benefit" to add one.
                </p>
              )}
            </div>

            <div style={{ background: "white", padding: 16, borderRadius: 8, border: "1px solid var(--border)" }}>
              <h3 style={{ margin: "0 0 12px 0", fontSize: 16, color: "#495057", fontWeight: 600 }}>Pricing</h3>
              <textarea
                value={proposal.pricing}
                onChange={(e) => updateProposal({ pricing: e.target.value })}
                placeholder="Enter pricing details..."
                rows={4}
                style={{ 
                  width: "100%", 
                  padding: "8px 12px", 
                  borderRadius: 6, 
                  border: "1px solid var(--border)",
                  fontFamily: "inherit",
                  fontSize: 14,
                  lineHeight: 1.6,
                  resize: "vertical"
                }}
              />
            </div>

            <div style={{ background: "white", padding: 16, borderRadius: 8, border: "1px solid var(--border)" }}>
              <h3 style={{ margin: "0 0 12px 0", fontSize: 16, color: "#495057", fontWeight: 600 }}>Timeline</h3>
              <textarea
                value={proposal.timeline}
                onChange={(e) => updateProposal({ timeline: e.target.value })}
                placeholder="Enter timeline..."
                rows={4}
                style={{ 
                  width: "100%", 
                  padding: "8px 12px", 
                  borderRadius: 6, 
                  border: "1px solid var(--border)",
                  fontFamily: "inherit",
                  fontSize: 14,
                  lineHeight: 1.6,
                  resize: "vertical"
                }}
              />
            </div>

            <div style={{ background: "white", padding: 16, borderRadius: 8, border: "1px solid var(--border)" }}>
              <h3 style={{ margin: "0 0 12px 0", fontSize: 16, color: "#495057", fontWeight: 600 }}>Terms & Conditions</h3>
              <textarea
                value={proposal.terms}
                onChange={(e) => updateProposal({ terms: e.target.value })}
                placeholder="Enter terms and conditions..."
                rows={4}
                style={{ 
                  width: "100%", 
                  padding: "8px 12px", 
                  borderRadius: 6, 
                  border: "1px solid var(--border)",
                  fontFamily: "inherit",
                  fontSize: 14,
                  lineHeight: 1.6,
                  resize: "vertical"
                }}
              />
            </div>
          </div>
        ) : (
          <div style={{ textAlign: "center", padding: "48px 32px", color: "#6c757d" }}>
            <p style={{ fontSize: 16, fontWeight: 500, marginBottom: 8 }}>No proposal generated yet.</p>
            <p style={{ fontSize: 14, fontStyle: "italic", margin: 0 }}>
              Click "Generate Proposal" above or ask the AI: "Generate a proposal for this deal"
            </p>
          </div>
        )}
      </div>
    </div>
  );
}
