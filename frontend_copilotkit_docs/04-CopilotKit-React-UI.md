# CopilotKit React UI

**File path**: `frontend_copilotkit_docs/04-CopilotKit-React-UI.md`  
**Package**: `@copilotkit/react-ui` (version 1.51.3 at assessment)

---

## Overview

`@copilotkit/react-ui` provides ready-made **UI components** for chat (sidebar, popup, inline chat) and shared **styles**. The reference app uses **CopilotSidebar** and the default styles. All examples are from `Adk_Copilotkit_UI_App/frontend` (read-only).

---

## Main exports used in the reference app

| Export | Purpose |
|--------|---------|
| **CopilotSidebar** | Sidebar chat panel (open/close, labels). |
| **styles.css** | Default CopilotKit styles; import once (e.g. in a layout or page). |

---

## CopilotSidebar

**Purpose**: Renders a chat sidebar that uses the current CopilotKit context (runtime URL and agent from the parent `<CopilotKit>`).

**Props (used in reference app)**:

- **defaultOpen**: boolean — Whether the sidebar is open on first render (e.g. `true`).
- **labels**: object — `title`, `initial` (placeholder/initial message text).
- **clickOutsideToClose**: boolean — Whether clicking outside closes the sidebar (reference uses `false`).

### Example: Chat page (reference `app/chat/page.tsx`)

```tsx
import { CopilotSidebar } from "@copilotkit/react-ui";
import "@copilotkit/react-ui/styles.css";

export default function ChatPage() {
  return (
    <CopilotKit runtimeUrl="/api/copilotkit" showDevConsole={false} agent="knowledge_qa">
      <div className="min-h-screen w-full flex items-center justify-center">
        <div style={{ padding: 24, maxWidth: 720, width: "100%" }}>
          <p style={{ color: "#666", marginBottom: 24 }}>
            Knowledge Q&A: ask about products, pricing, or playbooks.
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
```

### Example: Deal page (reference `app/deal/page.tsx`)

```tsx
<CopilotSidebar
  defaultOpen={true}
  labels={{
    title: "Deal Builder",
    initial: "Ask me to improve this deal or suggest next steps.",
  }}
  clickOutsideToClose={false}
/>
```

---

## Styles

Import the default styles once so CopilotSidebar (and other CopilotKit UI components) render correctly:

```tsx
import "@copilotkit/react-ui/styles.css";
```

The reference app imports this in both `app/chat/page.tsx` and `app/deal/page.tsx`. It could alternatively be imported in a shared layout or `_app`.

---

## Other react-ui exports (for reference)

The package also exports:

- **CopilotPopup** — Popup-style chat.
- **CopilotChat** — Inline chat component.
- **Markdown**, **AssistantMessage**, **UserMessage**, **ImageRenderer** — Message rendering.
- **Suggestions**, **Suggestion** — Suggestion list components.
- **CopilotDevConsole** — Dev console UI.
- **useChatContext**, **useCopilotChatSuggestions** — Hooks for chat context and suggestions.
- **CopilotKitCSSProperties**, **CopilotChatSuggestion** — Types.

The reference app only uses CopilotSidebar and `styles.css`.

---

## Related

- [03-CopilotKit-React-Core.md](03-CopilotKit-React-Core.md) — CopilotKit provider and hooks.
- [01-CopilotKit-Overview-and-Wiring.md](01-CopilotKit-Overview-and-Wiring.md) — Overall wiring.
