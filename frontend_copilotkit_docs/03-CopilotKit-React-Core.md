# CopilotKit React Core

**File path**: `frontend_copilotkit_docs/03-CopilotKit-React-Core.md`  
**Package**: `@copilotkit/react-core` (version 1.51.3 at assessment)

---

## Overview

`@copilotkit/react-core` provides the React **provider** (`CopilotKit`) and **hooks** for chat, co-agent state, and actions. The reference app uses `CopilotKit`, `useCoAgent`, and `useCopilotChat`. Examples are from `Adk_Copilotkit_UI_App/frontend` (read-only).

---

## Main exports used in the reference app

| Export | Purpose |
|--------|---------|
| **CopilotKit** | Provider component; wraps the app or a page and sets runtime URL and agent. |
| **useCoAgent** | Hook for shared state between UI and agent (e.g. deal form state). |
| **useCopilotChat** | Hook to append messages and track loading (e.g. “Improve with AI” button). |

---

## CopilotKit (provider)

**Props (relevant for reference app)**:

- **runtimeUrl**: string — URL of the CopilotKit API route (e.g. `/api/copilotkit`).
- **agent**: string — Name of the agent to use (must match a key in the runtime `agents` object).
- **showDevConsole**: boolean — Whether to show the dev console (reference uses `false`).

Children can include UI components (e.g. from `@copilotkit/react-ui`) and any page content that uses CopilotKit hooks.

### Example: Simple chat page (reference `app/chat/page.tsx`)

```tsx
"use client";

import { CopilotKit } from "@copilotkit/react-core";
import { CopilotSidebar } from "@copilotkit/react-ui";
import "@copilotkit/react-ui/styles.css";

export default function ChatPage() {
  return (
    <CopilotKit
      runtimeUrl="/api/copilotkit"
      showDevConsole={false}
      agent="knowledge_qa"
    >
      <div className="min-h-screen w-full flex items-center justify-center">
        {/* page content */}
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
```

### Example: Page with co-agent state (reference `app/deal/page.tsx`)

```tsx
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
```

---

## useCoAgent

**Purpose**: Share state between the UI and the agent (e.g. form data the agent can read and update).

**Signature (conceptually)**: `useCoAgent<T>(options) => { state, setState }`

- **options.name**: Agent name (same as `agent` on CopilotKit).
- **options.initialState**: Initial state object (e.g. `{ deal: INITIAL_DEAL }`).
- **Returns**: `state` (current agent state), `setState` (update state; backend receives it with requests).

### Example: Deal form state (reference `app/deal/page.tsx`)

```tsx
import { useCoAgent } from "@copilotkit/react-core";

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

function DealForm() {
  const { state: agentState, setState: setAgentState } = useCoAgent<{ deal: DealState }>({
    name: "deal_builder",
    initialState: { deal: INITIAL_DEAL },
  });
  const [deal, setDeal] = useState<DealState>(INITIAL_DEAL);

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

  // ... form fields and "Improve with AI" button using setAgentState + appendMessage
}
```

---

## useCopilotChat

**Purpose**: Append messages and know when the agent is loading (e.g. for a custom “Improve with AI” button).

**Returns (relevant)**: `appendMessage`, `isLoading`.

- **appendMessage(message)**: Add a user (or other) message; the agent will respond.
- **isLoading**: true while the agent is generating a response.

Messages are typically built with types from `@copilotkit/runtime-client-gql` (e.g. `TextMessage`, `MessageRole`).

### Example: Append user message and disable button (reference `app/deal/page.tsx`)

```tsx
import { useCopilotChat } from "@copilotkit/react-core";
import { TextMessage, MessageRole } from "@copilotkit/runtime-client-gql";

function DealForm() {
  const { appendMessage, isLoading } = useCopilotChat();

  // On "Improve with AI" click:
  const currentDeal = { /* ... */ };
  setAgentState({ ...agentState, deal: currentDeal });
  const dealSummary = [/* ... */].filter(Boolean).join(". ");
  const content = dealSummary
    ? `Improve this deal and suggest next steps. Current deal: ${dealSummary}`
    : "Improve this deal and suggest next steps";
  appendMessage(new TextMessage({ role: MessageRole.User, content }));

  return (
    <button
      type="button"
      disabled={isLoading}
      onClick={() => { /* ... append and setState ... */ }}
    >
      {isLoading ? "Thinking…" : "Improve with AI"}
    </button>
  );
}
```

---

## Other react-core exports (for reference)

The package also exports:

- **useCopilotAction** — Register custom actions the agent can call.
- **useCopilotReadable** / **useMakeCopilotDocumentReadable** — Expose context to the agent.
- **useCopilotContext** — Access Copilot context.
- **useCopilotChatSuggestions** — Chat suggestions.
- **ThreadsContext**, **useThreads** — Thread management.
- **CopilotMessagesContext**, **useCopilotMessagesContext** — Messages context.
- Types: CopilotContextParams, FrontendAction, etc.

The reference app does not use these in the assessed files.

---

## Related

- [04-CopilotKit-React-UI.md](04-CopilotKit-React-UI.md) — CopilotSidebar and UI components.
- [01-CopilotKit-Overview-and-Wiring.md](01-CopilotKit-Overview-and-Wiring.md) — Runtime URL and agent names.
