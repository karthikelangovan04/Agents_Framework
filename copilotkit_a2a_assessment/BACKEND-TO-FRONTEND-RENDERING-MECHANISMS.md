# Backend-to-Frontend Rendering Mechanisms: ADK Agent → MCP App UI in CopilotKit

**Date**: February 12, 2026  
**Scope**: All viable mechanisms for a Python ADK backend agent to trigger MCP App iframe / rich UI rendering in the CopilotKit frontend — including A2A protocol as a data transport layer.  
**Prerequisite**: [UNIFIED-ORCHESTRATOR-ASSESSMENT.md](./UNIFIED-ORCHESTRATOR-ASSESSMENT.md)

---

## Table of Contents

1. [Problem Statement](#problem-statement)
2. [Why Direct MCPAppsMiddleware Invocation from Python Fails](#why-direct-invocation-fails)
3. [Mechanism 1: useCopilotAction with render Prop (ClientProxyTool)](#mechanism-1-usecopilotaction-with-render-prop)
4. [Mechanism 2: Shared State Trigger Pattern](#mechanism-2-shared-state-trigger-pattern)
5. [Mechanism 3: Unified Gateway (BuiltInAgent Delegation)](#mechanism-3-unified-gateway)
6. [Mechanism 4: A2A Protocol as Rich Data Transport](#mechanism-4-a2a-protocol-as-rich-data-transport)
7. [Comparison Matrix](#comparison-matrix)
8. [Recommendation](#recommendation)
9. [A2A Protocol Deep Dive (Appendix)](#a2a-protocol-deep-dive)

---

## Problem Statement

We want a Python ADK backend agent to:
1. Generate content (e.g., mermaid code, research data, PDF content)
2. Trigger an MCP App server to render that content as an interactive iframe widget in the CopilotKit chat

The challenge: `MCPAppsMiddleware` is a **JavaScript middleware** running in the Next.js process. The AG-UI SSE protocol from Python has **no `RENDER_IFRAME` event type**. The Python backend cannot directly invoke `MCPAppsMiddleware`.

### AG-UI Protocol Events (Source: `ag_ui/core/events.py`)

```python
class EventType(str, Enum):
    TEXT_MESSAGE_START = "TEXT_MESSAGE_START"
    TEXT_MESSAGE_CONTENT = "TEXT_MESSAGE_CONTENT"
    TEXT_MESSAGE_END = "TEXT_MESSAGE_END"
    TOOL_CALL_START = "TOOL_CALL_START"
    TOOL_CALL_ARGS = "TOOL_CALL_ARGS"
    TOOL_CALL_END = "TOOL_CALL_END"
    TOOL_CALL_RESULT = "TOOL_CALL_RESULT"
    STATE_SNAPSHOT = "STATE_SNAPSHOT"
    STATE_DELTA = "STATE_DELTA"
    CUSTOM = "CUSTOM"
    RUN_STARTED = "RUN_STARTED"
    RUN_FINISHED = "RUN_FINISHED"
    RUN_ERROR = "RUN_ERROR"
    STEP_STARTED = "STEP_STARTED"
    STEP_FINISHED = "STEP_FINISHED"
```

**No `RENDER_IFRAME`, `MCP_APP_UI`, or `GENERATIVE_UI` event type exists.** Iframe rendering happens at a completely different layer — inside CopilotKit's React runtime.

---

## Why Direct Invocation Fails

### Architecture Boundary Analysis

```
┌─────────────────────────────────────────────────────────────────┐
│  FRONTEND (Next.js / React)                                     │
│                                                                  │
│  ┌──────────────────────┐     ┌─────────────────────────────┐   │
│  │ MCPAppsMiddleware     │     │ useCopilotAction hooks       │   │
│  │ (JS middleware)       │     │ (React hooks with render)    │   │
│  │                       │     │                              │   │
│  │ • Connects to MCP App │     │ • Triggered by AG-UI events  │   │
│  │   servers             │     │ • render prop returns JSX    │   │
│  │ • Fetches ui://       │     │ • Renders in chat inline     │   │
│  │   resources           │     │                              │   │
│  │ • Packages for iframe │     │                              │   │
│  └──────────┬───────────┘     └──────────────┬──────────────┘   │
│             │                                 │                   │
│  ═══════════╤═════════════════════════════════╤═══════════════   │
│             │  AG-UI SSE / HTTP Boundary      │                   │
│  ═══════════╧═════════════════════════════════╧═══════════════   │
│                                                                  │
└─────────────────────────────────────────────────────────────────┘
                           │
                     AG-UI SSE Stream
                     (TOOL_CALL_START,
                      TOOL_CALL_ARGS,
                      TOOL_CALL_END,
                      TEXT_MESSAGE, ...)
                           │
┌─────────────────────────────────────────────────────────────────┐
│  BACKEND (Python / FastAPI)                                      │
│                                                                  │
│  ┌──────────────────────┐     ┌─────────────────────────────┐   │
│  │ ADK Custom Agent      │     │ ag_ui_adk (EventTranslator)  │   │
│  │                       │     │                              │   │
│  │ • Orchestrates agents │     │ • Converts ADK events to     │   │
│  │ • Calls McpToolset    │     │   AG-UI events               │   │
│  │ • Uses ClientProxy    │     │ • No iframe/UI event mapping │   │
│  │   Tools for frontend  │     │                              │   │
│  └───────────────────────┘     └──────────────────────────────┘   │
│                                                                  │
└─────────────────────────────────────────────────────────────────┘
```

**Key**: `MCPAppsMiddleware` lives ABOVE the HTTP boundary. Python lives BELOW. The AG-UI SSE protocol connecting them has no UI rendering primitives.

### Evidence from Source Code

**EventTranslator** (`ag_ui_adk/event_translator.py`):
- Converts ADK `FunctionCall` → AG-UI `ToolCallStartEvent` + `ToolCallArgsEvent` + `ToolCallEndEvent`
- Converts ADK `FunctionResponse` → AG-UI `ToolCallResultEvent`
- Converts ADK text content → AG-UI `TextMessageContentEvent`
- **Does NOT parse `_meta.ui.resourceUri`** or generate UI-specific rendering instructions

**ClientProxyTool** (`ag_ui_adk/client_proxy_tool.py`):
- Emits `TOOL_CALL_START` → `TOOL_CALL_ARGS` → `TOOL_CALL_END` via AG-UI SSE
- CopilotKit receives these events and matches them to `useCopilotAction` on the frontend
- **This IS the bridge** — but it triggers client-side code, not `MCPAppsMiddleware` directly

---

## Mechanism 1: useCopilotAction with render Prop

**Rating: BEST for direct ADK control over frontend rendering**

This mechanism uses `ClientProxyTool` (via `AGUIToolset`) to emit tool call events that trigger `useCopilotAction` hooks on the frontend. The hook's `render` property returns React JSX directly into the chat — which can be an MCP App iframe or any custom visualization.

### Architecture

```
ADK Agent generates mermaid code
  → Agent calls "render_mermaid" (a client-side tool via AGUIToolset)
  → ag_ui_adk emits: TOOL_CALL_START → TOOL_CALL_ARGS({mermaid_code}) → TOOL_CALL_END
  → CopilotKit SSE client receives events
  → useCopilotAction("render_mermaid").render({args}) fires
  → React component creates iframe loading MCP App's mcp-app.html
  → User sees interactive diagram IN the chat
```

### Backend (Python ADK Agent)

```python
from google.adk.agents import LlmAgent
from ag_ui_adk import AGUIToolset

orchestrator = LlmAgent(
    name="orchestrator",
    model="gemini-2.5-pro",
    instruction="""You are a research and visualization orchestrator.

    When the user asks you to create a visual diagram:
    1. Generate the mermaid code for the diagram
    2. Call the `render_mermaid` tool with the generated code

    When the user asks for deep research:
    1. Use the research sub-agents to gather data
    2. Summarize and present findings
    
    The `render_mermaid` tool will display an interactive diagram 
    in the user's chat window.""",
    tools=[
        AGUIToolset(),  # Makes frontend-registered tools available
        # ... other backend tools and sub-agents
    ],
)
```

### Frontend (Next.js/React)

```tsx
"use client";
import { useCopilotAction } from "@copilotkit/react-core";

// MCP App iframe renderer component
function MermaidDiagramWidget({ mermaidCode, title }: { 
  mermaidCode: string; 
  title: string 
}) {
  // Option A: Load MCP App server's HTML resource with the data
  const iframeSrc = `http://localhost:3007/mcp-app.html?code=${
    encodeURIComponent(mermaidCode)
  }`;

  return (
    <div style={{ 
      border: '1px solid #e2e8f0', 
      borderRadius: '12px', 
      padding: '16px', 
      margin: '8px 0',
      backgroundColor: '#f8fafc' 
    }}>
      <h4 style={{ margin: '0 0 8px 0' }}>{title}</h4>
      <iframe 
        src={iframeSrc}
        style={{ width: '100%', height: '400px', border: 'none', borderRadius: '8px' }}
        sandbox="allow-scripts"
        title={title}
      />
    </div>
  );
}

// Register the client-side action that the backend agent triggers
export function useMermaidRenderAction() {
  useCopilotAction({
    name: "render_mermaid",
    description: "Renders a mermaid diagram as an interactive widget",
    parameters: [
      { name: "mermaid_code", type: "string", description: "Mermaid diagram code" },
      { name: "title", type: "string", description: "Title for the diagram" },
    ],
    // THIS is what renders in the chat — like MCPAppsMiddleware would
    render: ({ args, status }) => {
      if (status === "executing" || status === "complete") {
        return (
          <MermaidDiagramWidget
            mermaidCode={args.mermaid_code || ""}
            title={args.title || "Diagram"}
          />
        );
      }
      return <div>Generating diagram...</div>;
    },
    handler: async ({ mermaid_code, title }) => {
      // Backend already processed. Frontend just acknowledges.
      return `Diagram "${title}" rendered successfully.`;
    },
  });
}
```

### How ClientProxyTool Makes This Work

From the library source (`ag_ui_adk/client_proxy_tool.py`):

```python
async def _execute_proxy_tool(self, args: Dict[str, Any], tool_context: Any) -> Any:
    tool_call_id = str(uuid.uuid4())
    
    # 1. Emit TOOL_CALL_START → tells CopilotKit "a tool is being called"
    start_event = ToolCallStartEvent(
        type=EventType.TOOL_CALL_START,
        tool_call_id=tool_call_id,
        tool_call_name=self.ag_ui_tool.name  # "render_mermaid"
    )
    await self.event_queue.put(start_event)
    
    # 2. Emit TOOL_CALL_ARGS → sends the mermaid_code and title to frontend
    args_json = json.dumps(args)  # {"mermaid_code": "...", "title": "..."}
    args_event = ToolCallArgsEvent(
        type=EventType.TOOL_CALL_ARGS,
        tool_call_id=tool_call_id,
        delta=args_json
    )
    await self.event_queue.put(args_event)
    
    # 3. Emit TOOL_CALL_END → triggers useCopilotAction.render()
    end_event = ToolCallEndEvent(
        type=EventType.TOOL_CALL_END,
        tool_call_id=tool_call_id
    )
    await self.event_queue.put(end_event)
```

### Pros
- ADK agent has FULL control over when/what to render
- No intermediate routing agent needed
- Works with any React component — can embed MCP App iframes, native Mermaid libs, charts, etc.
- Single backend endpoint (Python ADK via AG-UI)
- The `render` prop places content directly IN the chat stream

### Cons
- Each render type needs a corresponding `useCopilotAction` registered on the frontend
- Frontend must know about all possible visualization types upfront
- Does not use `MCPAppsMiddleware` directly (implements its own iframe logic)

---

## Mechanism 2: Shared State Trigger Pattern

**Rating: GOOD for decoupled architectures**

The ADK agent stores rendering instructions in the shared state. The frontend watches state changes and renders MCP App widgets when it detects rendering payloads.

### Backend (Python)

```python
from google.adk.tools import ToolContext
import time
import uuid

def prepare_mermaid_render(
    tool_context: ToolContext, 
    mermaid_code: str, 
    title: str
) -> dict:
    """Generate mermaid code and signal frontend to render it."""
    render_id = str(uuid.uuid4())
    tool_context.state["pending_renders"] = tool_context.state.get("pending_renders", [])
    tool_context.state["pending_renders"].append({
        "id": render_id,
        "type": "mermaid",
        "server_url": "http://localhost:3007/mcp",
        "args": {"code": mermaid_code, "title": title},
        "timestamp": time.time(),
    })
    return {"status": "queued", "render_id": render_id}
```

### Frontend (React)

```tsx
import { useCoAgent } from "@copilotkit/react-core";
import { useEffect, useState } from "react";

function RenderWatcher() {
  const { state } = useCoAgent({ name: "orchestrator" });
  const [renderedIds, setRenderedIds] = useState<Set<string>>(new Set());

  useEffect(() => {
    const pending = state?.pending_renders || [];
    pending.forEach((render: any) => {
      if (!renderedIds.has(render.id)) {
        // Trigger rendering — add to chat or a render panel
        setRenderedIds(prev => new Set([...prev, render.id]));
      }
    });
  }, [state?.pending_renders]);

  return (
    <>
      {(state?.pending_renders || []).map((render: any) => (
        <MermaidDiagramWidget
          key={render.id}
          mermaidCode={render.args.code}
          title={render.args.title}
        />
      ))}
    </>
  );
}
```

### Pros
- Decoupled — backend doesn't need to know about frontend tools
- State persists across sessions (can re-render on page refresh)
- Multiple renders can be queued

### Cons
- Renders appear outside the chat stream (not inline with messages)
- Requires additional state management logic
- No `render` prop placement in chat — needs custom UI layout
- More complex synchronization

---

## Mechanism 3: Unified Gateway (BuiltInAgent Delegation)

**Rating: BEST for native MCP App iframe rendering**

This is the architecture from `UNIFIED-ORCHESTRATOR-ASSESSMENT.md`. A `BuiltInAgent` in Next.js serves as the single entry point, with `MCPAppsMiddleware` for native iframe rendering and a custom `delegate_to_adk` tool for calling the Python ADK backend.

### Next.js API Route

```typescript
import { CopilotRuntime, ExperimentalEmptyAdapter } from "@copilotkit/runtime";
import { BuiltInAgent } from "@copilotkit/runtime/v2";
import { MCPAppsMiddleware } from "@ag-ui/mcp-apps-middleware";

const mcpMiddleware = new MCPAppsMiddleware({
  mcpServers: [
    { type: "http", url: "http://localhost:3007/mcp", serverId: "mermaid" },
    { type: "http", url: "http://localhost:3008/mcp", serverId: "pdf-viewer" },
  ],
});

const agent = new BuiltInAgent({
  model: "openai/gpt-4o",
  prompt: `You are a unified orchestrator that can:
1. RENDER VISUALS: Use MCP App tools for diagrams, PDFs, charts (renders in-chat)
2. DELEGATE COMPLEX TASKS: Use delegate_to_adk for research, analysis, generation

Example flow:
- "Research X" → delegate_to_adk → ADK backend processes → returns results
- "Show diagram" → delegate_to_adk (generates mermaid code) → render-mermaid MCP tool
`,
  tools: [{
    name: "delegate_to_adk",
    description: "Delegate tasks to the ADK orchestrator backend",
    parameters: {
      type: "object",
      properties: {
        task: { type: "string", description: "Task description" },
        context: { type: "string", description: "Additional context" },
      },
      required: ["task"],
    },
    handler: async ({ task, context }) => {
      const response = await fetch("http://localhost:8001/run", {
        method: "POST",
        headers: { "Content-Type": "application/json" },
        body: JSON.stringify({ task, context }),
      });
      return await response.json();
    },
  }],
}).use(mcpMiddleware);

export async function POST(req: Request) {
  const runtime = new CopilotRuntime();
  return runtime.streamEvents(req, new ExperimentalEmptyAdapter(), {
    agents: [{ name: "orchestrator", agent }],
  });
}
```

### Pros
- Uses `MCPAppsMiddleware` **natively** — full MCP App iframe rendering with `ui://` resources
- Single conversational endpoint for the user
- MCP App iframes render exactly as designed (sandboxed, with `@modelcontextprotocol/ext-apps` client SDK)

### Cons
- Requires a TypeScript/JS routing agent (BuiltInAgent) in the middle
- ADK agent loses some direct control — the BuiltInAgent decides what to render
- Two-hop architecture: User → BuiltInAgent → ADK Backend → Back to BuiltInAgent → MCP App
- More complex deployment

---

## Mechanism 4: A2A Protocol as Rich Data Transport

**Rating: EXCELLENT — potentially the cleanest architecture**

This is a new mechanism explored by examining the A2A SDK. The A2A protocol natively supports **multi-format data transfer** through its `Part` system (`TextPart`, `FilePart`, `DataPart`) and `Artifact` model. CopilotKit already has A2A integration via the `with-a2a-middleware` pattern.

### Key Insight: A2A's Rich Part System

The A2A protocol (v0.3.22+) defines three part types that can carry ANY content:

```python
# From a2a/types.py — The A2A Part union type
class Part(RootModel[TextPart | FilePart | DataPart]):
    root: TextPart | FilePart | DataPart

# TextPart — plain text
class TextPart(A2ABaseModel):
    kind: Literal['text'] = 'text'
    text: str
    metadata: dict[str, Any] | None = None

# FilePart — files with MIME types (including text/html!)
class FilePart(A2ABaseModel):
    kind: Literal['file'] = 'file'
    file: FileWithBytes | FileWithUri
    metadata: dict[str, Any] | None = None

# Where files can be inline bytes or URIs:
class FileWithBytes(A2ABaseModel):
    bytes: str          # base64-encoded content
    mime_type: str | None = None  # e.g., "text/html", "image/svg+xml"
    name: str | None = None

class FileWithUri(A2ABaseModel):
    uri: str            # URL pointing to content
    mime_type: str | None = None
    name: str | None = None

# DataPart — structured JSON data
class DataPart(A2ABaseModel):
    kind: Literal['data'] = 'data'
    data: dict[str, Any]  # arbitrary JSON
    metadata: dict[str, Any] | None = None

# Artifact — a rich output container
class Artifact(A2ABaseModel):
    artifact_id: str
    name: str | None = None
    description: str | None = None
    parts: list[Part]     # Can contain text + files + data
    metadata: dict[str, Any] | None = None
    extensions: list[str] | None = None
```

### Why This Matters for MCP App Rendering

The A2A protocol can carry:

1. **`FilePart` with `mime_type: "text/html"`** — The ADK backend can generate an HTML bundle (or fetch it from an MCP App server) and send it as a `FilePart` with base64-encoded HTML content
2. **`FilePart` with `FileWithUri`** — Point to an MCP App server's `mcp-app.html` resource URL
3. **`DataPart` with rendering metadata** — Structured JSON with `mermaid_code`, `title`, `render_type`, etc.
4. **`Artifact` combining multiple parts** — A complete rendering package: HTML template + data + metadata
5. **`TaskArtifactUpdateEvent`** — Stream artifacts incrementally during long tasks

### Architecture: ADK → A2A Server → CopilotKit A2A Client → Frontend Rendering

```
┌──────────────────────────────────────────────────────────────────────┐
│  FRONTEND (Next.js / React / CopilotKit)                             │
│                                                                       │
│  CopilotKit with A2A Middleware (from CopilotKit/with-a2a-middleware) │
│      │                                                                │
│      ├── useCopilotAction("send_message_to_a2a_agent")               │
│      │     render: ({ args }) => <A2AResponseRenderer parts={...} /> │
│      │                                                                │
│      └── A2AResponseRenderer component                               │
│            │                                                          │
│            ├── TextPart → renders as text in chat                    │
│            ├── FilePart (text/html) → renders as sandboxed iframe    │
│            ├── FilePart (image/*) → renders as <img>                 │
│            ├── DataPart (mermaid) → renders via Mermaid.js           │
│            └── DataPart (custom) → renders via custom React widget   │
│                                                                       │
└──────────────────────────────────────────────────┬───────────────────┘
                                                    │
                                          A2A Protocol
                                          (JSON-RPC / REST / SSE)
                                                    │
┌──────────────────────────────────────────────────┴───────────────────┐
│  BACKEND (Python)                                                     │
│                                                                       │
│  ADK Custom Agent (orchestrator)                                      │
│      │                                                                │
│      ├── LlmAgent (research)                                         │
│      ├── SequentialAgent (multi-step analysis)                       │
│      ├── McpToolset (backend MCP tools — data)                       │
│      │                                                                │
│      └── A2A Server (a2a-sdk)                                        │
│            │                                                          │
│            ├── AgentCard: declares output_modes ["text/plain",       │
│            │   "text/html", "application/json", "image/svg+xml"]     │
│            │                                                          │
│            ├── on_message: runs ADK orchestrator                     │
│            │                                                          │
│            └── response: Message with parts:                         │
│                  ├── TextPart("Here's your diagram:")                │
│                  ├── FilePart(text/html, <mermaid HTML bundle>)      │
│                  └── DataPart({type: "mermaid", code: "..."})        │
│                                                                       │
└──────────────────────────────────────────────────────────────────────┘
```

### Backend: ADK Agent Wrapped as A2A Server

```python
import asyncio
import uuid
import base64
from a2a.server.apps.jsonrpc.fastapi_app import A2AFastAPI
from a2a.server.request_handlers.jsonrpc_handler import JSONRPCHandler
from a2a.server.agent_execution.agent_executor import AgentExecutor
from a2a.types import (
    AgentCard, AgentCapabilities, AgentSkill, Message, Part,
    TextPart, FilePart, DataPart, FileWithBytes, FileWithUri,
    Artifact, TaskArtifactUpdateEvent, Role
)
from google.adk.agents import LlmAgent
from google.adk.tools.mcp_tool.mcp_toolset import McpToolset

# --- ADK Agent Setup ---
research_agent = LlmAgent(
    name="researcher",
    model="gemini-2.5-pro",
    instruction="You are a deep research agent...",
)

mermaid_generator = LlmAgent(
    name="mermaid_gen",
    model="gemini-2.5-pro",
    instruction="Generate valid mermaid diagram code...",
)

# --- A2A Agent Card ---
agent_card = AgentCard(
    name="adk-orchestrator",
    description="ADK orchestrator with research, analysis, and visualization capabilities",
    url="http://localhost:9000/",
    version="1.0.0",
    capabilities=AgentCapabilities(streaming=True),
    # KEY: Declare rich output modes
    default_input_modes=["text/plain", "application/json"],
    default_output_modes=[
        "text/plain",
        "text/html",           # Can return HTML for iframe rendering
        "application/json",     # Can return structured data
        "image/svg+xml",        # Can return SVG diagrams
    ],
    skills=[
        AgentSkill(
            id="deep-research",
            name="Deep Research",
            description="Performs multi-step research on any topic",
        ),
        AgentSkill(
            id="generate-diagram",
            name="Generate Diagram",
            description="Generates mermaid diagrams and returns them as renderable HTML",
            output_modes=["text/html", "application/json"],
        ),
        AgentSkill(
            id="render-pdf",
            name="Render PDF",
            description="Generates PDF content for viewing",
            output_modes=["text/html", "application/pdf"],
        ),
    ],
)

# --- A2A Agent Executor ---
async def execute_agent(context):
    """Execute ADK agent and return A2A-formatted response with rich parts."""
    user_input = context.get_user_input()
    user_text = ""
    if user_input and user_input.parts:
        for part in user_input.parts:
            if isinstance(part.root, TextPart):
                user_text = part.root.text
                break

    # --- Example: Mermaid Diagram Generation ---
    if "diagram" in user_text.lower() or "mermaid" in user_text.lower():
        # ADK agent generates mermaid code
        mermaid_code = """graph TD
    A[User Request] --> B{Orchestrator Agent}
    B --> C[Research Agent]
    B --> D[Analysis Agent]
    B --> E[Visualization Agent]
    C --> F[Artifact Store]
    D --> F
    E --> G[MCP App Renderer]
    G --> H[CopilotKit Frontend]"""

        # Build an HTML bundle that renders the mermaid diagram
        html_content = f"""<!DOCTYPE html>
<html>
<head>
  <script src="https://cdn.jsdelivr.net/npm/mermaid/dist/mermaid.min.js"></script>
  <style>body {{ margin: 0; padding: 16px; font-family: sans-serif; }}</style>
</head>
<body>
  <div class="mermaid">{mermaid_code}</div>
  <script>mermaid.initialize({{ startOnLoad: true }});</script>
</body>
</html>"""

        html_bytes = base64.b64encode(html_content.encode('utf-8')).decode('utf-8')

        # Return A2A Message with multiple parts
        return Message(
            message_id=str(uuid.uuid4()),
            role=Role.agent,
            parts=[
                # Part 1: Text explanation
                Part(root=TextPart(
                    text="Here's the architecture diagram you requested:"
                )),
                # Part 2: Renderable HTML (for iframe)
                Part(root=FilePart(
                    file=FileWithBytes(
                        bytes=html_bytes,
                        mime_type="text/html",
                        name="diagram.html",
                    ),
                    metadata={
                        "render_type": "iframe",
                        "width": "100%",
                        "height": "500px",
                    }
                )),
                # Part 3: Structured data (for programmatic access)
                Part(root=DataPart(
                    data={
                        "type": "mermaid",
                        "code": mermaid_code,
                        "title": "Architecture Diagram",
                    },
                    metadata={"render_hint": "mermaid_diagram"}
                )),
            ],
        )

    # --- Default: text response ---
    return Message(
        message_id=str(uuid.uuid4()),
        role=Role.agent,
        parts=[Part(root=TextPart(text=f"Processed: {user_text}"))],
    )

# --- A2A Server Setup ---
agent_executor = AgentExecutor(execute_fn=execute_agent)
handler = JSONRPCHandler(
    agent_card=agent_card,
    agent_executor=agent_executor,
)
app = A2AFastAPI(handler=handler)

# Run with: uvicorn main:app --host 0.0.0.0 --port 9000
```

### Frontend: CopilotKit with A2A Middleware + Smart Part Renderer

Based on CopilotKit's `with-a2a-middleware` pattern and the blog tutorial:

```typescript
// app/api/copilotkit/route.ts
import { CopilotRuntime, ExperimentalEmptyAdapter } from "@copilotkit/runtime";
import { HttpAgent } from "@ag-ui/client";

// Connect to the ADK A2A backend
const adkAgent = new HttpAgent({
  url: "http://localhost:9000",
});

export async function POST(req: Request) {
  const runtime = new CopilotRuntime();
  return runtime.streamEvents(req, new ExperimentalEmptyAdapter(), {
    agents: [
      { name: "orchestrator", agent: adkAgent },
    ],
  });
}
```

```tsx
// components/A2APartRenderer.tsx — Smart renderer for A2A parts
"use client";
import { useCopilotAction } from "@copilotkit/react-core";
import React, { useMemo } from "react";

interface A2APart {
  kind: "text" | "file" | "data";
  text?: string;
  file?: {
    bytes?: string;
    uri?: string;
    mime_type?: string;
    name?: string;
  };
  data?: Record<string, any>;
  metadata?: Record<string, any>;
}

function RenderPart({ part }: { part: A2APart }) {
  // Text part — render as text
  if (part.kind === "text" && part.text) {
    return <p>{part.text}</p>;
  }

  // File part — render based on MIME type
  if (part.kind === "file" && part.file) {
    const { mime_type, bytes, uri, name } = part.file;

    // HTML files → render as iframe
    if (mime_type === "text/html") {
      const htmlContent = bytes 
        ? atob(bytes)  // decode base64
        : null;
      const iframeSrc = htmlContent
        ? `data:text/html;charset=utf-8,${encodeURIComponent(htmlContent)}`
        : uri;

      return (
        <div style={{
          border: '1px solid #e2e8f0',
          borderRadius: '12px',
          overflow: 'hidden',
          margin: '8px 0',
        }}>
          <iframe
            src={iframeSrc}
            style={{
              width: part.metadata?.width || '100%',
              height: part.metadata?.height || '400px',
              border: 'none',
            }}
            sandbox="allow-scripts"
            title={name || "Rendered Content"}
          />
        </div>
      );
    }

    // SVG files → render inline
    if (mime_type === "image/svg+xml" && bytes) {
      const svgContent = atob(bytes);
      return (
        <div 
          dangerouslySetInnerHTML={{ __html: svgContent }}
          style={{ margin: '8px 0' }}
        />
      );
    }

    // Images → render as img
    if (mime_type?.startsWith("image/") && bytes) {
      return (
        <img 
          src={`data:${mime_type};base64,${bytes}`}
          alt={name || "Image"}
          style={{ maxWidth: '100%', borderRadius: '8px', margin: '8px 0' }}
        />
      );
    }

    // PDF → render in iframe
    if (mime_type === "application/pdf") {
      const pdfSrc = uri || (bytes ? `data:application/pdf;base64,${bytes}` : null);
      if (pdfSrc) {
        return (
          <iframe
            src={pdfSrc}
            style={{ width: '100%', height: '600px', border: 'none', borderRadius: '8px' }}
            title={name || "PDF Document"}
          />
        );
      }
    }

    // Fallback: download link
    return (
      <a href={uri || `data:${mime_type};base64,${bytes}`} download={name}>
        Download {name || "file"}
      </a>
    );
  }

  // Data part — render based on metadata hints
  if (part.kind === "data" && part.data) {
    const renderHint = part.metadata?.render_hint;

    // Mermaid diagram data → could use a native Mermaid React component
    if (renderHint === "mermaid_diagram" || part.data.type === "mermaid") {
      return (
        <div style={{
          backgroundColor: '#f0f9ff',
          borderRadius: '8px',
          padding: '12px',
          margin: '8px 0',
        }}>
          <strong>{part.data.title || "Diagram"}</strong>
          <pre style={{ 
            whiteSpace: 'pre-wrap', 
            backgroundColor: '#fff',
            padding: '8px',
            borderRadius: '4px',
            fontSize: '12px',
          }}>
            {part.data.code}
          </pre>
        </div>
      );
    }

    // Generic JSON data
    return (
      <pre style={{ 
        backgroundColor: '#f8fafc', 
        padding: '12px', 
        borderRadius: '8px',
        fontSize: '12px',
        margin: '8px 0',
      }}>
        {JSON.stringify(part.data, null, 2)}
      </pre>
    );
  }

  return null;
}

// Register CopilotKit action that renders A2A response parts
export function useA2AResponseRenderer() {
  useCopilotAction({
    name: "send_message_to_a2a_agent",
    description: "Sends a message to the A2A agent and renders the response",
    parameters: [
      { name: "message", type: "string" },
      { name: "response_parts", type: "object[]", description: "A2A response parts" },
    ],
    render: ({ args, status }) => {
      const parts: A2APart[] = args.response_parts || [];
      return (
        <div>
          {parts.map((part, index) => (
            <RenderPart key={index} part={part} />
          ))}
          {status === "executing" && <div>Processing...</div>}
        </div>
      );
    },
    handler: async ({ message }) => {
      return `Processed: ${message}`;
    },
  });
}
```

### How A2A Artifacts Enable Streaming Rich Content

For long-running tasks, the A2A protocol supports `TaskArtifactUpdateEvent`:

```python
# Backend streams artifacts incrementally
from a2a.types import TaskArtifactUpdateEvent, Artifact, Part, TextPart

# During a long research task, the server can stream artifact updates:
artifact_event = TaskArtifactUpdateEvent(
    task_id="task_123",
    context_id="ctx_456",
    artifact=Artifact(
        artifact_id="research_result_1",
        name="Research Summary",
        description="Deep research results on quantum computing",
        parts=[
            Part(root=TextPart(text="## Key Findings\n\n1. ...")),
            Part(root=FilePart(
                file=FileWithBytes(
                    bytes=base64.b64encode(html_report.encode()).decode(),
                    mime_type="text/html",
                    name="research_report.html"
                )
            )),
        ],
    ),
    append=False,      # Full artifact (not partial)
    last_chunk=True,   # This is the final chunk
)
```

### CopilotKit A2A Client Integration

From the CopilotKit blog and `with-a2a-middleware` example, the frontend connects to A2A agents via:

```typescript
// The CopilotKit A2A middleware bridges A2A protocol to CopilotKit
// Step 2 from the blog: "Configure CopilotKit API Route with A2A Middleware"

// In app/api/copilotkit/route.ts:
import { CopilotRuntime } from "@copilotkit/runtime";

// The A2A agent URL is configured here:
const a2aAgents = [
  {
    name: "adk-orchestrator",
    url: "http://localhost:9000",  // A2A server endpoint
    // CopilotKit discovers agent capabilities via the AgentCard
  },
];

// CopilotKit handles the A2A protocol communication:
// 1. Sends messages to A2A server
// 2. Receives Messages with Parts (TextPart, FilePart, DataPart)
// 3. Receives TaskArtifactUpdateEvent for streaming artifacts
// 4. Frontend renders each Part type appropriately
```

### AgentCard Output Modes = Content Negotiation

The A2A protocol's `AgentCard` declares what output formats an agent supports:

```python
agent_card = AgentCard(
    # ...
    default_output_modes=[
        "text/plain",       # Standard text responses
        "text/html",        # HTML for iframe rendering ← KEY
        "application/json", # Structured data
        "image/svg+xml",    # SVG diagrams
        "application/pdf",  # PDF documents
    ],
    # Per-skill output mode overrides:
    skills=[
        AgentSkill(
            id="generate-diagram",
            output_modes=["text/html", "application/json"],
        ),
    ],
)
```

The client (CopilotKit) can negotiate via `MessageSendConfiguration`:

```python
config = MessageSendConfiguration(
    accepted_output_modes=["text/html", "text/plain"],  # "I can render HTML and text"
)
```

This is a proper content negotiation mechanism — the client tells the server what it can render, and the server responds with appropriate part types.

### Pros
- A2A is a **standard protocol** — not a custom hack
- Native support for multi-format parts: text, files (any MIME), structured data
- `AgentCard` declares output capabilities — content negotiation built in
- `Artifact` model perfectly represents complex outputs (research report + chart + data)
- Streaming via `TaskArtifactUpdateEvent` — incremental artifact delivery
- CopilotKit already has A2A middleware support (`with-a2a-middleware`, `a2a-travel`)
- Backend ADK agent remains the single source of truth for orchestration
- `FilePart(mime_type="text/html")` can carry rendered MCP App HTML or generated diagrams
- Works with ADK's `RemoteA2aAgent` for agent-to-agent communication

### Cons
- Requires building a smart `A2APartRenderer` on the frontend to handle different part types
- Not as "zero-config" as `MCPAppsMiddleware` (which auto-discovers UI resources from MCP App servers)
- A2A SDK is still evolving (v0.3.22) — some patterns may change
- Need to wrap ADK agent execution within A2A server framework

---

## Comparison Matrix

| Feature | Mech 1: useCopilotAction | Mech 2: State Trigger | Mech 3: Unified Gateway | Mech 4: A2A Protocol |
|---------|--------------------------|----------------------|------------------------|---------------------|
| **Uses MCPAppsMiddleware?** | No (custom React) | No (custom React) | YES (native) | No (custom renderer) |
| **Backend triggers rendering?** | YES (ClientProxyTool) | YES (state sync) | Indirect (delegation) | YES (A2A Parts) |
| **Iframe in chat?** | YES | Partial (outside chat) | YES | YES |
| **ADK agent control** | HIGH | HIGH | MEDIUM | HIGH |
| **Multi-format support** | Per-action | Per-state-schema | Per-MCP-server | Native (any MIME) |
| **Standard protocol?** | AG-UI (proprietary) | AG-UI + State | AG-UI + MCP Apps | A2A (Google standard) |
| **Streaming artifacts?** | No | No | No | YES (TaskArtifactUpdate) |
| **Content negotiation?** | No | No | No | YES (AgentCard modes) |
| **Setup complexity** | Medium | Medium | High | Medium-High |
| **Single backend endpoint** | YES | YES | NO (2 layers) | YES |
| **CopilotKit integration** | Native (useCopilotAction) | Native (useCoAgent) | Native (BuiltInAgent) | Via A2A middleware |

---

## Recommendation

### For Your Specific Use Case

Your goal: Python ADK backend → generate content → render as interactive widget in CopilotKit chat

**Primary Recommendation: Mechanism 4 (A2A Protocol) + Mechanism 1 (useCopilotAction render)**

Combine both for the strongest architecture:

1. **A2A Protocol as the transport layer**: Wrap your ADK orchestrator as an A2A Server. This gives you:
   - Standard multi-format data transfer (text, HTML, files, JSON)
   - `AgentCard` for capability discovery
   - `Artifact` model for rich outputs
   - Streaming support via `TaskArtifactUpdateEvent`
   - Content negotiation between CopilotKit and the backend

2. **`useCopilotAction` with render for visualization**: Register frontend actions that interpret A2A response parts:
   - `FilePart(text/html)` → render as sandboxed iframe
   - `DataPart(mermaid)` → render via Mermaid.js
   - `DataPart(chart)` → render via Chart.js / Recharts
   - Each part type gets a dedicated React renderer

### Why This Beats the Others

| Criterion | A2A + useCopilotAction | Unified Gateway (Mech 3) |
|-----------|----------------------|-------------------------|
| Single Python backend? | YES | NO (needs BuiltIn agent) |
| Standard protocol? | YES (A2A spec) | Partly (MCP Apps spec) |
| ADK agent control? | FULL | Shared with BuiltInAgent |
| Extensible output? | Any MIME type via Parts | Limited to MCP App tools |
| Streaming? | YES (artifact events) | NO |

### Implementation Roadmap

```
Phase 1: A2A Server Setup (1-2 days)
├── Wrap ADK orchestrator as A2A server using a2a-sdk
├── Define AgentCard with output_modes
├── Implement execute_agent that returns rich Parts
└── Test with A2A client

Phase 2: CopilotKit A2A Integration (1-2 days)
├── Set up CopilotKit with A2A middleware (from with-a2a-middleware)
├── Configure API route to connect to A2A server
├── Build A2APartRenderer component
└── Register useCopilotAction hooks for visual parts

Phase 3: ADK Agent Orchestration (2-3 days)
├── Build ADK CustomAgent with sub-agents
├── Add McpToolset for backend MCP tools
├── Implement artifact generation (mermaid, HTML, PDF)
└── Connect to MCP App servers for data (not UI)

Phase 4: MCP App Integration (1-2 days)
├── Build MCP App servers (mermaid-server, pdf-viewer)
├── ADK agent calls MCP tools → gets data
├── ADK agent packages data as FilePart(text/html)
├── Frontend renders iframe from FilePart
└── Optional: Also support MCPAppsMiddleware for hybrid use
```

---

## A2A Protocol Deep Dive (Appendix)

### A2A SDK Overview (v0.3.22)

**Source**: `/Users/karthike/Desktop/Vibe Coding/Google-ADK-A2A-Explore/a2a_sdk/`

The A2A (Agent-to-Agent) Protocol is a Google-backed standard for agent interoperability. Unlike AG-UI (which is frontend-backend), A2A is backend-to-backend — enabling any agent to call any other agent regardless of framework.

### Package Structure

```
a2a-sdk/
├── a2a.client/           # Client for calling A2A agents
│   ├── Client            # Main client class
│   ├── ClientConfig      # Transport configuration
│   ├── ClientTaskManager # Task lifecycle tracking
│   ├── ClientCallContext  # Request context/state
│   └── transports/       # REST, JSON-RPC, gRPC
│
├── a2a.server/           # Server for building A2A agents
│   ├── RequestHandler    # Base request handler
│   ├── JSONRPCHandler    # JSON-RPC protocol handler
│   ├── RESTHandler       # REST protocol handler
│   ├── AgentExecutor     # Agent execution logic
│   ├── TaskManager       # Task lifecycle management
│   └── apps/             # FastAPI, Starlette integrations
│
├── a2a.types/            # 96 protobuf-generated types
│   ├── Message           # Conversation message
│   ├── Part              # TextPart | FilePart | DataPart
│   ├── Artifact          # Rich output container
│   ├── Task              # Task with status and artifacts
│   ├── AgentCard         # Agent capability manifest
│   └── Events            # TaskStatusUpdateEvent, TaskArtifactUpdateEvent
│
└── a2a.utils/            # Utilities
    ├── message           # Message helpers
    ├── artifact          # Artifact helpers
    └── errors            # Error classes
```

### A2A vs AG-UI: Protocol Comparison

| Aspect | AG-UI | A2A |
|--------|-------|-----|
| **Direction** | Frontend ↔ Backend | Backend ↔ Backend |
| **Transport** | SSE (Server-Sent Events) | JSON-RPC, REST, gRPC |
| **Content Model** | Text events, Tool calls | Parts (Text, File, Data) |
| **Rich Content** | Limited (text + tool args) | Native (any MIME type) |
| **Artifacts** | No native concept | First-class citizen |
| **Streaming** | SSE event stream | TaskArtifactUpdateEvent |
| **Discovery** | No standard discovery | AgentCard + well-known path |
| **Content Negotiation** | No | accepted_output_modes |

### ADK's RemoteA2aAgent — Built-in A2A Client

ADK already has a built-in A2A client: `RemoteA2aAgent`. From `adk-python-lib/src/google/adk/agents/remote_a2a_agent.py`:

```python
from google.adk.agents import RemoteA2aAgent

# Use in your ADK orchestrator to call other A2A agents:
remote_research_agent = RemoteA2aAgent(
    name="research_agent",
    agent_card="http://research-agent:9001/.well-known/agent.json",
)

# The orchestrator can delegate to this remote agent,
# and it handles all A2A protocol communication internally.
```

The `RemoteA2aAgent` handles:
- Agent card resolution (URL, file, or direct object)
- A2A message construction from ADK session events
- Part conversion: `A2APart` ↔ `GenAIPart` (text, files, data, function calls)
- Task tracking: `TaskStatusUpdateEvent`, `TaskArtifactUpdateEvent`
- Context management: passes `ClientCallContext(state=session.state)`

### Part Converter (How A2A Parts Map to ADK Parts)

From `adk-python-lib/src/google/adk/a2a/converters/part_converter.py`:

```python
# A2A → ADK (GenAI) conversion:
TextPart     → genai_types.Part(text=...)
FilePart(URI) → genai_types.Part(file_data=FileData(file_uri=..., mime_type=...))
FilePart(Bytes) → genai_types.Part(inline_data=Blob(data=..., mime_type=...))
DataPart(function_call) → genai_types.Part(function_call=FunctionCall(...))
DataPart(function_response) → genai_types.Part(function_response=FunctionResponse(...))
DataPart(generic) → genai_types.Part(inline_data=Blob(data=<json>, mime_type="text/plain"))

# ADK (GenAI) → A2A conversion:
genai text → TextPart(text=...)
genai file_data → FilePart(FileWithUri(uri=..., mime_type=...))
genai inline_data → FilePart(FileWithBytes(bytes=base64(...), mime_type=...))
genai function_call → DataPart(data={...}, metadata={type: "function_call"})
genai function_response → DataPart(data={...}, metadata={type: "function_response"})
```

### CopilotKit A2A Integration Patterns

From the CopilotKit blog tutorial and examples:

**Pattern 1: A2A Middleware (from `with-a2a-middleware`)**
```
CopilotKit Frontend
  → API Route with A2A middleware
  → A2A Client sends messages to backend
  → Backend A2A Server processes with ADK agent
  → Returns A2A Message with Parts
  → Frontend renders parts (via useCopilotAction render)
```

**Pattern 2: A2A + Generative UI (from `with-a2a-a2ui`)**
```
CopilotKit Frontend
  → API Route with A2A agent
  → Backend returns A2UI declarative JSON (via A2A DataPart)
  → A2UIRenderer renders dynamic UI components
  → User interacts with generated UI
```

**Pattern 3: A2A Travel (multi-agent from `a2a-travel`)**
```
CopilotKit Frontend (CopilotChat)
  → Orchestrator Agent (ADK + AG-UI on port 9000)
  → Orchestrator delegates via A2A to:
    ├── Itinerary Agent (LangGraph on port 9001)
    ├── Budget Agent (ADK on port 9002)
    └── Restaurant Agent (ADK on port 9003)
  → Results flow back through orchestrator
  → useCopilotAction("send_message_to_a2a_agent") renders responses
```

### Key CopilotKit Integration Code (from blog tutorial)

```tsx
// Step 5 from blog: "Render Agent-to-Agent communication using Generative UI"

// In components/travel-chat.tsx:
useCopilotAction({
  name: "send_message_to_a2a_agent",
  description: "Send message to remote A2A agent and render response",
  parameters: [
    { name: "agent_name", type: "string" },
    { name: "message", type: "string" },
    { name: "task_id", type: "string" },
  ],
  render: ({ args, status }) => {
    // This renders the A2A agent's response inline in the chat
    // The response can contain rich Parts that are rendered accordingly
    return (
      <div className="a2a-response">
        <AgentBadge name={args.agent_name} />
        <ResponseRenderer parts={args.response_parts} />
        {status === "executing" && <LoadingSpinner />}
      </div>
    );
  },
  handler: async ({ agent_name, message, task_id }) => {
    // CopilotKit handles the actual A2A communication via middleware
    return `Message sent to ${agent_name}`;
  },
});
```

### Streaming via A2A (TaskArtifactUpdateEvent)

```python
# In A2A streaming response, the server sends events:

# 1. Task created
TaskStatusUpdateEvent(
    task_id="task_123",
    context_id="ctx_456",
    status=TaskStatus(state=TaskState.working, message=Message(...)),
    final=False,
)

# 2. Artifact generated (streamed incrementally)
TaskArtifactUpdateEvent(
    task_id="task_123",
    context_id="ctx_456",
    artifact=Artifact(
        artifact_id="diagram_1",
        name="Architecture Diagram",
        parts=[
            Part(root=FilePart(file=FileWithBytes(
                bytes=base64_html,
                mime_type="text/html",
            ))),
        ],
    ),
    append=False,
    last_chunk=True,
)

# 3. Task completed
TaskStatusUpdateEvent(
    task_id="task_123",
    context_id="ctx_456",
    status=TaskStatus(state=TaskState.completed),
    final=True,
)
```

The CopilotKit frontend receives these events via the A2A client and can render artifacts as they arrive — enabling progressive rendering of complex multi-part outputs.

---

## Summary

| Mechanism | When to Use |
|-----------|-------------|
| **1. useCopilotAction render** | When ADK agent needs direct control over what renders in chat. Best for specific, well-defined visualization types. |
| **2. State Trigger** | When you need decoupled, persistent rendering instructions that survive page refreshes. |
| **3. Unified Gateway** | When you MUST use `MCPAppsMiddleware` natively for MCP App servers with `ui://` resources. |
| **4. A2A Protocol** | When you want a standard, extensible, multi-format transport with streaming and content negotiation. Best for the long-term. |

**The strongest architecture combines Mechanism 4 (A2A as transport) + Mechanism 1 (useCopilotAction for rendering)**, giving you standard protocol compliance, rich multi-format content, and precise frontend rendering control — all from a single Python ADK backend.

---

**Last Updated**: February 12, 2026  
**Related Documents**:
- [UNIFIED-ORCHESTRATOR-ASSESSMENT.md](./UNIFIED-ORCHESTRATOR-ASSESSMENT.md) — Original architecture assessment
- [ASSESSMENT.md](./ASSESSMENT.md) — Initial CopilotKit + A2A + ADK feasibility study  
- [combo5_full_integration/README.md](./combo5_full_integration/README.md) — Full integration architecture

**Source References**:
- `a2a_sdk/docs/` — A2A SDK documentation (v0.3.22)
- `a2a_sdk/venv/lib/python3.13/site-packages/a2a/types.py` — A2A type definitions
- `adk-python-lib/src/google/adk/agents/remote_a2a_agent.py` — ADK's A2A client
- `adk-python-lib/src/google/adk/a2a/converters/part_converter.py` — A2A ↔ ADK part conversion
- `Adk_Copilotkit_UI_App/backend/.venv/.../ag_ui_adk/client_proxy_tool.py` — ClientProxyTool mechanism
- CopilotKit blog: "How to Make Agents Talk to Each Other Using A2A + AG-UI"
- CopilotKit examples: `with-a2a-middleware`, `a2a-travel`, `with-a2a-a2ui`
