# UI Proposal Section Implementation Guide

## Overview
This guide shows how to add a Proposal section to your Deal Builder UI that displays and allows generation of formal proposals based on the deal state.

## Backend Changes ✅ COMPLETED

The following backend changes have been made:

1. ✅ Added `generate_proposal` tool
2. ✅ Updated deal state to include `proposal` object
3. ✅ Added proposal initialization in `on_before_agent`
4. ✅ Updated agent instruction to support proposal generation
5. ✅ Modified context injection to include proposal status

## Frontend Changes Needed

### 1. Update State Interface

Add the proposal interface to your types:

```typescript
// In your types file or component
interface ProposalState {
  executive_summary: string;
  solution_overview: string;
  benefits: string[];
  pricing: string;
  timeline: string;
  terms: string;
}

interface DealState {
  customer_name: string;
  segment: string;
  products: string[];
  estimated_value: string;
  stage: string;
  next_steps: string[];
  changes: string;
}

interface AgentState {
  deal: DealState;
  proposal: ProposalState;
}
```

### 2. Create Proposal Component

Create a new component `ProposalSection.tsx`:

```typescript
import React from 'react';
import { useCopilotAction } from '@copilotkit/react-core';

interface ProposalSectionProps {
  proposal: {
    executive_summary: string;
    solution_overview: string;
    benefits: string[];
    pricing: string;
    timeline: string;
    terms: string;
  };
}

export const ProposalSection: React.FC<ProposalSectionProps> = ({ proposal }) => {
  const [isGenerating, setIsGenerating] = React.useState(false);

  // Add action to trigger proposal generation
  useCopilotAction({
    name: "generate_proposal",
    description: "Generate a formal proposal document for this deal",
    parameters: [],
    handler: async () => {
      setIsGenerating(true);
      // The agent will handle the actual generation
      setIsGenerating(false);
    },
  });

  const hasProposal = proposal && (
    proposal.executive_summary ||
    proposal.solution_overview ||
    proposal.benefits?.length > 0
  );

  return (
    <div className="proposal-section">
      <div className="proposal-header">
        <h2>Proposal</h2>
        {!hasProposal && (
          <button
            onClick={() => {
              // Trigger via chat: "Generate a proposal for this deal"
              setIsGenerating(true);
            }}
            className="generate-btn"
            disabled={isGenerating}
          >
            {isGenerating ? 'Generating...' : 'Generate Proposal'}
          </button>
        )}
      </div>

      {hasProposal ? (
        <div className="proposal-content">
          {proposal.executive_summary && (
            <section className="proposal-section-item">
              <h3>Executive Summary</h3>
              <p>{proposal.executive_summary}</p>
            </section>
          )}

          {proposal.solution_overview && (
            <section className="proposal-section-item">
              <h3>Solution Overview</h3>
              <p>{proposal.solution_overview}</p>
            </section>
          )}

          {proposal.benefits && proposal.benefits.length > 0 && (
            <section className="proposal-section-item">
              <h3>Key Benefits</h3>
              <ul>
                {proposal.benefits.map((benefit, idx) => (
                  <li key={idx}>{benefit}</li>
                ))}
              </ul>
            </section>
          )}

          {proposal.pricing && (
            <section className="proposal-section-item">
              <h3>Pricing</h3>
              <p>{proposal.pricing}</p>
            </section>
          )}

          {proposal.timeline && (
            <section className="proposal-section-item">
              <h3>Timeline</h3>
              <p>{proposal.timeline}</p>
            </section>
          )}

          {proposal.terms && (
            <section className="proposal-section-item">
              <h3>Terms & Conditions</h3>
              <p>{proposal.terms}</p>
            </section>
          )}
        </div>
      ) : (
        <div className="proposal-placeholder">
          <p>No proposal generated yet.</p>
          <p>Ask the AI: "Generate a proposal for this deal" or "Create a formal proposal document"</p>
        </div>
      )}
    </div>
  );
};
```

### 3. Update Main Component

Update your main deal builder component to include the proposal section:

```typescript
import { useCoAgent } from '@copilotkit/react-core';
import { ProposalSection } from './ProposalSection';

export function DealBuilderPage() {
  const { state } = useCoAgent<{
    deal: DealState;
    proposal: ProposalState;
  }>({
    name: "deal_builder",
    initialState: {
      deal: {
        customer_name: "",
        segment: "",
        products: [],
        estimated_value: "",
        stage: "Discovery",
        next_steps: [],
        changes: "",
      },
      proposal: {
        executive_summary: "",
        solution_overview: "",
        benefits: [],
        pricing: "",
        timeline: "",
        terms: "",
      },
    },
  });

  return (
    <div className="deal-builder-container">
      {/* Existing Deal Information Section */}
      <DealInfoSection deal={state.deal} />
      
      {/* NEW: Proposal Section */}
      <ProposalSection proposal={state.proposal} />
      
      {/* Existing Chat/Agent Section */}
      <CopilotChat />
    </div>
  );
}
```

### 4. Add Styling

Add CSS for the proposal section:

```css
.proposal-section {
  margin: 2rem 0;
  padding: 1.5rem;
  background: #f8f9fa;
  border-radius: 8px;
  border: 1px solid #dee2e6;
}

.proposal-header {
  display: flex;
  justify-content: space-between;
  align-items: center;
  margin-bottom: 1.5rem;
  padding-bottom: 1rem;
  border-bottom: 2px solid #dee2e6;
}

.proposal-header h2 {
  margin: 0;
  font-size: 1.5rem;
  color: #212529;
}

.generate-btn {
  padding: 0.5rem 1rem;
  background: #0d6efd;
  color: white;
  border: none;
  border-radius: 4px;
  cursor: pointer;
  font-weight: 500;
}

.generate-btn:hover:not(:disabled) {
  background: #0b5ed7;
}

.generate-btn:disabled {
  opacity: 0.6;
  cursor: not-allowed;
}

.proposal-content {
  display: flex;
  flex-direction: column;
  gap: 1.5rem;
}

.proposal-section-item {
  background: white;
  padding: 1rem;
  border-radius: 6px;
  border: 1px solid #e9ecef;
}

.proposal-section-item h3 {
  margin: 0 0 0.75rem 0;
  font-size: 1.125rem;
  color: #495057;
  font-weight: 600;
}

.proposal-section-item p {
  margin: 0;
  line-height: 1.6;
  color: #212529;
  white-space: pre-wrap;
}

.proposal-section-item ul {
  margin: 0;
  padding-left: 1.5rem;
}

.proposal-section-item li {
  margin-bottom: 0.5rem;
  line-height: 1.6;
}

.proposal-placeholder {
  text-align: center;
  padding: 3rem 2rem;
  color: #6c757d;
}

.proposal-placeholder p:first-child {
  font-size: 1.125rem;
  font-weight: 500;
  margin-bottom: 0.5rem;
}

.proposal-placeholder p:last-child {
  font-size: 0.875rem;
  font-style: italic;
}
```

## Usage Examples

### Generate a Proposal via Chat

Users can now ask the agent:
- "Generate a proposal for this deal"
- "Create a formal proposal document"
- "I need a proposal for Cognizant"
- "Generate a proposal with executive summary and pricing"

### Agent Response

The agent will:
1. Review the current deal information (customer, products, value, segment)
2. Call `generate_proposal` with comprehensive sections
3. Update the proposal state
4. Automatically set deal stage to "Proposal"
5. The UI will reactively display the proposal

## State Synchronization

The proposal state is automatically synchronized via `useCoAgent`:
- Backend calls `generate_proposal` tool → updates `state["proposal"]`
- AG-UI detects state change → pushes to frontend
- React component receives updated `proposal` object → re-renders

## Export/Download (Optional Enhancement)

Add a download button to export the proposal:

```typescript
const handleExportProposal = () => {
  const proposalText = `
PROPOSAL FOR ${state.deal.customer_name}

EXECUTIVE SUMMARY
${state.proposal.executive_summary}

SOLUTION OVERVIEW
${state.proposal.solution_overview}

KEY BENEFITS
${state.proposal.benefits.map(b => `• ${b}`).join('\n')}

PRICING
${state.proposal.pricing}

TIMELINE
${state.proposal.timeline}

TERMS & CONDITIONS
${state.proposal.terms}
  `.trim();

  const blob = new Blob([proposalText], { type: 'text/plain' });
  const url = URL.createObjectURL(blob);
  const a = document.createElement('a');
  a.href = url;
  a.download = `proposal-${state.deal.customer_name.replace(/\s+/g, '-').toLowerCase()}.txt`;
  a.click();
  URL.revokeObjectURL(url);
};
```

## Testing

1. Start the backend: `uvicorn main:app --host 0.0.0.0 --port 8001`
2. Start the frontend: `npm start` (or your dev command)
3. Open the app and navigate to Deal Builder
4. Add some deal information (customer, products, etc.)
5. In the chat, type: "Generate a proposal for this deal"
6. Watch the proposal section populate automatically!

## Summary

✅ Backend supports proposal generation via `generate_proposal` tool
✅ Proposal state is synchronized with frontend
✅ Agent automatically generates professional proposals
✅ UI can display all proposal sections
✅ Deal stage automatically updates to "Proposal"

The agent will now intelligently generate comprehensive proposals based on the deal context!
