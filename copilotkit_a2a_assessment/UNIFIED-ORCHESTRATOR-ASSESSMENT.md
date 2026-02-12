# Unified Orchestrator Assessment: ADK Custom Agent + MCP Apps + CopilotKit

**Date**: February 12, 2026  
**Scope**: Can we build ONE backend endpoint where CopilotKit (via AG-UI) connects to an ADK Custom Agent that orchestrates both ADK built-in agents AND MCP Apps — including iframe rendering back to the frontend?

---

## Executive Summary

**YES, with a hybrid architecture.** The assessment reveals that a single ADK Custom Agent can orchestrate both ADK agents (LlmAgent, ParallelAgent, SequentialAgent) AND use MCP servers as tools. However, **MCP App iframe rendering** (the interactive UI widgets) **cannot be triggered from the Python backend alone** — it requires the CopilotKit `MCPAppsMiddleware` + `BuiltInAgent` on the frontend/Next.js layer. The solution is a **Unified Gateway** pattern where one Next.js API route handles both the ADK backend agent AND MCP App UI rendering through agent routing.

### Three Key Questions Answered

| Question | Answer | Details |
|----------|--------|---------|
| Can MCP servers be used as ADK agent tools? | **YES** | ADK `McpToolset` natively wraps any MCP server's tools into ADK-compatible tools. The custom agent can call them like any other tool. |
| Can an ADK Custom Agent orchestrate both ADK agents and MCP tools? | **YES** | A `BaseAgent` subclass with `_run_async_impl` can call sub-agents (LlmAgent, SequentialAgent, ParallelAgent) and use MCP tools in the same workflow. |
| Can MCP App iframe UI render through this pipeline to CopilotKit? | **PARTIALLY** | MCP App iframes are rendered by `MCPAppsMiddleware` in the Next.js layer, NOT by the Python backend. The backend ADK agent can trigger the *data* fetch via MCP, but the *UI rendering* requires the frontend middleware. A routing/delegation pattern solves this. |

---

## Architecture Deep Dive

### What We Want

```
User asks: "Do deep research on topic X"
  → ADK agents do research → store as artifact

User asks: "Show me the PDF"
  → MCP App renders PDF viewer in iframe inside CopilotKit chat
```

### The Problem: Two Different MCP Integration Points

There are **two fundamentally different ways** MCP servers integrate:

| Integration | Where | What It Does | UI Rendering? |
|------------|-------|--------------|---------------|
| **ADK McpToolset** (Backend) | Python backend | Wraps MCP server tools as ADK agent tools. Agent calls tool, gets JSON/text response. | **NO** — returns data only |
| **MCPAppsMiddleware** (Frontend) | Next.js API route | CopilotKit middleware that connects to MCP App servers, fetches UI resources, renders iframes in chat. | **YES** — renders interactive HTML in sandboxed iframe |

**Key Insight**: ADK `McpToolset` connects to a standard MCP server and gets tool *results* (data). CopilotKit `MCPAppsMiddleware` connects to an MCP App server (which uses `@modelcontextprotocol/ext-apps`) and gets both the tool *results* AND the *UI resource* (`ui://` scheme) to render as an iframe.

### The Solution: Unified Gateway with Agent Routing

```
┌──────────────────────────────────────────────────────────────────────┐
│                      FRONTEND (Browser)                               │
│                                                                       │
│  CopilotKit React v2                                                 │
│  ├── CopilotChat — renders text messages + MCP App iframes          │
│  ├── useCoAgent("orchestrator") — bidirectional state sync           │
│  └── useCopilotAction — human-in-loop approvals                     │
│                                                                       │
│  KEY: CopilotChat v2 renders MCP App HTML in sandboxed iframes      │
│       via MCPAppsMiddleware tool results with _meta.ui.resourceUri  │
└──────────┬────────────────────────────────────────────────────────────┘
           │ POST /api/copilotkit (AG-UI SSE)
           ▼
┌──────────────────────────────────────────────────────────────────────┐
│              NEXT.JS API ROUTE (Unified Gateway)                      │
│                                                                       │
│  CopilotRuntime with SINGLE intelligent routing:                     │
│                                                                       │
│  ┌─────────────────────────────────────────────────────────────┐    │
│  │ DEFAULT Agent: BuiltInAgent + MCPAppsMiddleware             │    │
│  │                                                              │    │
│  │ This agent has access to:                                    │    │
│  │ 1. MCP App tools (weather, PDF, mermaid, charts, maps)      │    │
│  │    → These render interactive iframes in CopilotChat         │    │
│  │ 2. A "delegate_to_adk" tool that forwards to the backend    │    │
│  │    ADK orchestrator for research/agent work                  │    │
│  │                                                              │    │
│  │ System Prompt: "For research tasks, deep analysis, or       │    │
│  │  anything requiring multiple agents, use delegate_to_adk.   │    │
│  │  For showing PDFs, weather, charts, maps, or visual         │    │
│  │  content, use the MCP App tools directly."                  │    │
│  └───────────────┬─────────────────────────┬────────────────────┘    │
│                  │                         │                          │
│         MCP App tools               delegate_to_adk tool             │
│         (iframe UI)                  (HTTP call to backend)           │
└──────────┬───────────────────────────┬────────────────────────────────┘
           │                           │
           ▼                           ▼
┌─────────────────────┐   ┌────────────────────────────────────────────┐
│  MCP App Servers     │   │  FASTAPI BACKEND (ADK Custom Agent)        │
│                      │   │                                            │
│  weather:3006/mcp    │   │  ADK CustomOrchestratorAgent               │
│  pdf-viewer:3003/mcp │   │  (extends BaseAgent)                       │
│  mermaid:3007/mcp    │   │                                            │
│  charts:3105/mcp     │   │  _run_async_impl orchestrates:             │
│  maps:3102/mcp       │   │  ├── LlmAgent("researcher")               │
│                      │   │  │   └── deep research, web search         │
│ Each has:            │   │  ├── SequentialAgent("pipeline")           │
│ - registerAppTool()  │   │  │   ├── LlmAgent("analyzer")             │
│ - registerAppResource│   │  │   └── LlmAgent("summarizer")           │
│ - UI HTML via ui://  │   │  ├── ParallelAgent("parallel_tasks")      │
│                      │   │  │   ├── LlmAgent("factcheck")            │
│                      │   │  │   └── LlmAgent("source_gather")        │
│                      │   │  ├── McpToolset (backend MCP tools)        │
│                      │   │  │   └── filesystem, database, etc.        │
│                      │   │  ├── Artifact storage (save_artifact)      │
│                      │   │  └── State management → AG-UI → frontend   │
│                      │   │                                            │
│                      │   │  Session: InMemory or PostgreSQL           │
│                      │   │  Endpoint: AG-UI compatible via ag_ui_adk  │
└─────────────────────┘   └────────────────────────────────────────────┘
```

---

## Three Architecture Patterns Assessed

### Pattern A: Single Backend Endpoint (Partial — No iframe)

```python
# The ADK Custom Agent uses McpToolset to call MCP servers as tools
# BUT: it only gets data back, NOT the UI resource for iframe rendering

from google.adk.tools.mcp_tool import McpToolset, SseConnectionParams

weather_toolset = McpToolset(
    connection_params=SseConnectionParams(
        url="http://localhost:3006/mcp",
    )
)

pdf_toolset = McpToolset(
    connection_params=SseConnectionParams(
        url="http://localhost:3003/mcp",
    )
)

orchestrator = LlmAgent(
    name="Orchestrator",
    model="gemini-2.5-pro",
    tools=[weather_toolset, pdf_toolset, research_tool, ...],
    sub_agents=[research_agent, analysis_agent, ...],
)
```

**Verdict**: The ADK agent CAN call the MCP App server's tools (like `get-forecast` or `render-pdf`). It will get the JSON data response. BUT it **cannot** render the iframe UI — that's a frontend concern handled by `MCPAppsMiddleware`.

**Use when**: You only need the MCP tool data (not the visual UI). Good for backend processing.

### Pattern B: Two Separate Agents (Current Combo 4 — Works but Split)

```typescript
// Next.js API route with TWO agents
const runtime = new CopilotRuntime({
  agents: {
    mcp_apps: mcpAppsAgent,        // BuiltInAgent + MCPAppsMiddleware
    orchestrator: adkOrchestratorAgent, // HttpAgent → ADK backend
  },
});
```

**Verdict**: Works, but the frontend must decide which agent to talk to. No unified conversation flow. User can't ask "do research AND show me the PDF" in one seamless interaction.

**Use when**: Clean separation is acceptable. MCP App interactions and ADK research are independent tasks.

### Pattern C: Unified Gateway (RECOMMENDED — New Architecture)

```typescript
// Next.js API route with ONE intelligent agent
// that can both render MCP App UIs AND delegate to ADK backend

import { CopilotRuntime, ExperimentalEmptyAdapter } from "@copilotkit/runtime";
import { BuiltInAgent } from "@copilotkit/runtime/v2";
import { MCPAppsMiddleware } from "@ag-ui/mcp-apps-middleware";

// MCP App servers for UI rendering
const mcpMiddleware = new MCPAppsMiddleware({
  mcpServers: [
    { type: "http", url: "http://localhost:3006/mcp", serverId: "weather" },
    { type: "http", url: "http://localhost:3003/mcp", serverId: "pdf-viewer" },
    { type: "http", url: "http://localhost:3007/mcp", serverId: "mermaid" },
    { type: "http", url: "http://localhost:3105/mcp", serverId: "charts" },
  ],
});

// Custom tool that delegates to the ADK backend
const delegateToAdk = {
  name: "delegate_to_adk_orchestrator",
  description: `Delegate complex tasks to the ADK backend orchestrator.
    Use this for: deep research, multi-step analysis, data gathering,
    artifact creation, or any task requiring multiple specialized agents.
    The ADK orchestrator has access to: research agents, analysis pipelines,
    database tools, and artifact storage.`,
  parameters: {
    type: "object",
    properties: {
      task: { type: "string", description: "The task to delegate" },
      context: { type: "string", description: "Any context or parameters" },
    },
    required: ["task"],
  },
  handler: async ({ task, context }) => {
    // Call the ADK backend via HTTP (AG-UI protocol)
    const response = await fetch("http://localhost:8001/", {
      method: "POST",
      headers: { "Content-Type": "application/json" },
      body: JSON.stringify({
        messages: [{ role: "user", content: `${task}\n\nContext: ${context}` }],
        state: {}, // Can pass shared state here
      }),
    });
    // Parse the SSE stream or get final response
    return await parseAdkResponse(response);
  },
};

const agent = new BuiltInAgent({
  model: "openai/gpt-4o",
  prompt: `You are a unified orchestrator that can both:

1. RENDER VISUAL CONTENT: Use MCP App tools to show weather, PDFs, charts,
   diagrams, and maps as interactive widgets in the chat.
   
2. DELEGATE COMPLEX TASKS: Use delegate_to_adk_orchestrator for deep research,
   multi-step analysis, data gathering, and any task requiring multiple
   specialized AI agents working together.

WORKFLOW EXAMPLES:
- "Research topic X" → delegate_to_adk_orchestrator
- "Show me a weather forecast" → use get-forecast MCP tool (renders in chat)
- "Research X then show me a PDF summary" → first delegate research, then
  use pdf-viewer MCP tool to render the result
- "Show me a diagram of the research" → use render-mermaid MCP tool

Always prefer MCP App tools when the user wants VISUAL output.
Use delegation when the task requires ANALYSIS or RESEARCH.`,
}).use(mcpMiddleware);

const runtime = new CopilotRuntime({
  agents: { default: agent },
});
```

**Verdict**: This is the optimal architecture. One conversational agent that:
- Renders MCP App iframes for visual content (PDF, charts, weather, maps)
- Delegates to the ADK backend for complex multi-agent research/analysis
- Maintains a single conversation flow

---

## How MCP App iframe Rendering Works (Key Understanding)

### The Full Pipeline

```
1. User: "Show me the weather in San Francisco"

2. CopilotKit sends to Next.js API route

3. BuiltInAgent (GPT-4o) decides to call "get-forecast" tool

4. MCPAppsMiddleware intercepts the tool call:
   a. Connects to weather MCP App server (localhost:3006/mcp)
   b. Calls "get-forecast" tool → gets JSON weather data
   c. Reads the tool's _meta.ui.resourceUri → "ui://get-forecast/mcp-app.html"
   d. Fetches the resource → gets the HTML/JS bundle
   e. Returns BOTH the tool result AND the UI resource to CopilotKit

5. CopilotKit React v2 (CopilotChat component):
   a. Sees the tool result has an associated UI resource
   b. Creates a sandboxed iframe
   c. Loads the HTML/JS bundle into the iframe
   d. The iframe app (React/vanilla JS) communicates with host via postMessage
   e. Host passes tool result data to the iframe app via ontoolresult
   f. Iframe renders the interactive weather card

6. User sees: interactive weather widget IN the chat
```

### Why Backend-Only Can't Do This

The ADK `McpToolset` in Python calls the same MCP server and gets the same JSON weather data. But it **does not**:
- Read the `_meta.ui.resourceUri` metadata
- Fetch the UI HTML resource
- Create an iframe
- Use the `@modelcontextprotocol/ext-apps` client protocol

That's because iframe rendering is a **frontend concern**. The Python backend has no DOM, no browser, no iframe capability.

### What the Backend CAN Do

The backend ADK agent CAN:
1. Call any MCP server tool via `McpToolset` and get the data
2. Process that data (analyze, summarize, store as artifact)
3. Return the processed data to the frontend via AG-UI state
4. The frontend can then decide to render it visually

---

## ADK Custom Agent: Orchestrating Everything

### BaseAgent Implementation

```python
"""
ADK Custom Agent that orchestrates:
1. LlmAgent sub-agents for research, analysis, summarization
2. SequentialAgent / ParallelAgent for complex workflows
3. McpToolset for backend MCP server tools (data only, no UI)
4. Artifact storage for research results
5. State management for CopilotKit frontend sync
"""

from __future__ import annotations
import json
from typing import AsyncGenerator, Optional

from google.adk.agents import BaseAgent, LlmAgent, SequentialAgent, ParallelAgent
from google.adk.agents.invocation_context import InvocationContext
from google.adk.tools.mcp_tool import McpToolset, SseConnectionParams
from google.adk.tools import ToolContext
from google.adk.events import Event

# MCP Toolsets (backend data tools — NOT for UI rendering)
research_mcp = McpToolset(
    connection_params=SseConnectionParams(url="http://localhost:3010/mcp"),
    tool_filter=["web_search", "fetch_url", "extract_text"]
)

database_mcp = McpToolset(
    connection_params=SseConnectionParams(url="http://localhost:3011/mcp"),
    tool_filter=["query_db", "store_result"]
)


class UnifiedOrchestratorAgent(BaseAgent):
    """Custom orchestrator that combines ADK agents + MCP backend tools."""

    def __init__(
        self,
        researcher: LlmAgent,
        analyzer: LlmAgent,
        summarizer: LlmAgent,
        research_pipeline: SequentialAgent,
        parallel_tasks: ParallelAgent,
    ):
        super().__init__(
            name="UnifiedOrchestrator",
            sub_agents=[
                researcher,
                research_pipeline,
                parallel_tasks,
            ]
        )
        self.researcher = researcher
        self.analyzer = analyzer
        self.summarizer = summarizer
        self.research_pipeline = research_pipeline
        self.parallel_tasks = parallel_tasks

    async def _run_async_impl(
        self, ctx: InvocationContext
    ) -> AsyncGenerator[Event, None]:
        """Custom orchestration logic."""
        
        user_request = ctx.session.state.get("user_request", "")
        task_type = ctx.session.state.get("task_type", "research")

        if task_type == "research":
            # Step 1: Run researcher agent (has McpToolset for web search)
            ctx.session.state["status"] = "researching"
            async for event in self.researcher.run_async(ctx):
                yield event

            # Step 2: Run analysis pipeline (Sequential: analyze → summarize)
            ctx.session.state["status"] = "analyzing"
            async for event in self.research_pipeline.run_async(ctx):
                yield event

            # Step 3: Store result as artifact
            research_result = ctx.session.state.get("research_summary", "")
            ctx.session.state["artifact_ready"] = True
            ctx.session.state["artifact_content"] = research_result
            ctx.session.state["status"] = "complete"

        elif task_type == "parallel_analysis":
            # Run multiple analysis agents in parallel
            ctx.session.state["status"] = "parallel_processing"
            async for event in self.parallel_tasks.run_async(ctx):
                yield event
            ctx.session.state["status"] = "complete"

        else:
            # Default: single researcher
            async for event in self.researcher.run_async(ctx):
                yield event


# Sub-agent definitions
researcher = LlmAgent(
    name="Researcher",
    model="gemini-2.5-pro",
    instruction="""You are a deep research agent. Use web_search and fetch_url
    tools to gather comprehensive information on the topic in state['topic'].
    Store your findings in state['research_findings'].""",
    tools=[research_mcp],
    output_key="research_findings",
)

analyzer = LlmAgent(
    name="Analyzer",
    model="gemini-2.5-flash",
    instruction="""Analyze the research findings in state['research_findings'].
    Identify key insights, patterns, and conclusions.
    Store analysis in state['analysis'].""",
    output_key="analysis",
)

summarizer = LlmAgent(
    name="Summarizer",
    model="gemini-2.5-flash",
    instruction="""Create a comprehensive summary from state['analysis'].
    Format it as a well-structured report.
    Store in state['research_summary'].""",
    output_key="research_summary",
)

research_pipeline = SequentialAgent(
    name="ResearchPipeline",
    sub_agents=[analyzer, summarizer],
)

factchecker = LlmAgent(
    name="FactChecker",
    model="gemini-2.5-flash",
    instruction="Verify facts in state['research_findings'].",
    output_key="fact_check_results",
)

source_gatherer = LlmAgent(
    name="SourceGatherer",
    model="gemini-2.5-flash",
    instruction="Compile all sources from state['research_findings'].",
    output_key="sources",
)

parallel_tasks = ParallelAgent(
    name="ParallelAnalysis",
    sub_agents=[factchecker, source_gatherer],
)

# Instantiate the custom orchestrator
orchestrator = UnifiedOrchestratorAgent(
    researcher=researcher,
    analyzer=analyzer,
    summarizer=summarizer,
    research_pipeline=research_pipeline,
    parallel_tasks=parallel_tasks,
)
```

---

## MCP App as ADK Tool: What Actually Happens

### YES: MCP Server Tools Work as ADK Tools

```python
from google.adk.tools.mcp_tool import McpToolset, SseConnectionParams

# Connect to the SAME weather MCP App server
weather_toolset = McpToolset(
    connection_params=SseConnectionParams(
        url="http://localhost:3006/mcp",  # Same server CopilotKit connects to
    )
)

# ADK agent can call get-forecast, geocode-location
# It gets the JSON data back (temperature, conditions, etc.)
# But it does NOT get the UI resource or render an iframe
```

The `McpToolset` calls `session.list_tools()` on the MCP server, discovers tools like `get-forecast`, wraps them as `McpTool` instances (which extend `BaseTool`), and makes them callable by the ADK agent. The agent calls `get-forecast` → MCP server returns JSON → agent processes it.

**What's missing for UI**: The MCP App server also registers a resource at `ui://get-forecast/mcp-app.html` containing the HTML/JS bundle. The ADK `McpToolset` never fetches this resource. Only the `MCPAppsMiddleware` in CopilotKit does.

### The Bridge: Backend Data + Frontend UI

The correct pattern is:

```
ADK Backend Agent:
  1. Does deep research using multiple agents
  2. Stores result as artifact / in session state
  3. Returns: { status: "complete", artifact_key: "research_report" }

Frontend Gateway (BuiltInAgent + MCPAppsMiddleware):
  1. Receives "artifact is ready" signal from ADK
  2. When user says "show me the PDF" or "visualize this":
     a. Retrieves the artifact data from ADK state
     b. Calls the appropriate MCP App tool (pdf-viewer, charts, mermaid)
     c. MCPAppsMiddleware renders the iframe in CopilotChat
```

---

## Can MCP App iframe Be Wired with CopilotKit?

### YES — It Already Works

The `copilotkit-weather` example at `/Users/karthike/Desktop/Vibe Coding/mcp_app_ext/ext-apps/ext-apps/examples/copilotkit-weather` proves this:

1. **CopilotChat v2** (`@copilotkit/react-core/v2`) renders MCP App iframes natively
2. **MCPAppsMiddleware** (`@ag-ui/mcp-apps-middleware`) bridges MCP App servers to CopilotKit
3. **BuiltInAgent** (`@copilotkit/runtime/v2`) uses the middleware to discover and call MCP App tools

The iframe rendering flow:
- MCP server registers tool with `_meta: { ui: { resourceUri: "ui://tool-name/mcp-app.html" } }`
- MCP server registers resource at that URI containing bundled HTML/JS
- MCPAppsMiddleware fetches both tool result and UI resource
- CopilotChat v2 renders the HTML in a sandboxed iframe
- Iframe communicates with host via `postMessage` (JSON-RPC)
- Iframe app uses `@modelcontextprotocol/ext-apps/react` hook (`useApp`) to receive tool data

### Building a Custom MCP App Server for Research PDF Rendering

```typescript
// research-pdf-server/server.ts
import { registerAppResource, registerAppTool, RESOURCE_MIME_TYPE } from "@modelcontextprotocol/ext-apps/server";
import { McpServer } from "@modelcontextprotocol/sdk/server/mcp.js";
import { z } from "zod";
import fs from "node:fs/promises";
import path from "node:path";

export function createServer(): McpServer {
  const server = new McpServer({
    name: "Research PDF Viewer",
    version: "1.0.0",
  });

  const resourceUri = "ui://render-research-report/mcp-app.html";

  registerAppTool(server,
    "render-research-report",
    {
      title: "Render Research Report",
      description: "Displays a research report as a formatted, interactive document in the chat. Pass the research content and metadata.",
      inputSchema: z.object({
        title: z.string().describe("Report title"),
        content: z.string().describe("The full research report content (markdown or HTML)"),
        sources: z.array(z.string()).optional().describe("List of source URLs"),
        metadata: z.object({
          topic: z.string(),
          date: z.string(),
          agent_used: z.string().optional(),
        }).optional(),
      }),
      _meta: { ui: { resourceUri } },
    },
    async (args) => {
      // The tool just passes through the data — the UI renders it
      return {
        content: [{
          type: "text",
          text: JSON.stringify(args),
        }],
      };
    },
  );

  registerAppResource(server,
    resourceUri,
    resourceUri,
    { mimeType: RESOURCE_MIME_TYPE },
    async () => {
      const html = await fs.readFile(path.join(DIST_DIR, "mcp-app.html"), "utf-8");
      return {
        contents: [{ uri: resourceUri, mimeType: RESOURCE_MIME_TYPE, text: html }],
      };
    },
  );

  return server;
}
```

---

## Complete End-to-End Flow

### Scenario: "Research AI trends and show me a PDF report"

```
Step 1: USER types "Research the latest AI trends for 2026"
        ↓
Step 2: CopilotKit → POST /api/copilotkit → Unified Gateway
        ↓
Step 3: BuiltInAgent (GPT-4o) analyzes request
        Decides: This is a research task → calls delegate_to_adk_orchestrator
        ↓
Step 4: delegate_to_adk_orchestrator tool → HTTP POST → ADK Backend (port 8001)
        ↓
Step 5: ADK CustomOrchestratorAgent._run_async_impl() executes:
        a) researcher agent uses web_search MCP tool → gathers data
        b) SequentialAgent runs: analyzer → summarizer
        c) Stores result in session state:
           state["research_summary"] = "# AI Trends 2026\n\n..."
           state["artifact_ready"] = True
           state["status"] = "complete"
        ↓
Step 6: ADK response returns to delegate_to_adk_orchestrator
        Tool returns: { status: "complete", summary: "AI Trends 2026..." }
        ↓
Step 7: BuiltInAgent streams text response:
        "I've completed the research on AI trends for 2026. Here's a summary:
         [streams key findings]
         Would you like me to show the full report as an interactive document?"
        ↓
Step 8: USER says "Yes, show me the PDF report"
        ↓
Step 9: BuiltInAgent decides: Visual content → calls render-research-report MCP App tool
        ↓
Step 10: MCPAppsMiddleware:
         a) Connects to research-pdf-server (localhost:3003/mcp)
         b) Calls render-research-report with { title, content, sources }
         c) Fetches UI resource at ui://render-research-report/mcp-app.html
         d) Returns tool result + UI resource to CopilotKit
         ↓
Step 11: CopilotChat v2:
         a) Creates sandboxed iframe
         b) Loads the research report viewer HTML/JS bundle
         c) Passes the research data to the iframe via postMessage
         d) Iframe renders the formatted report with:
            - Title, date, topic
            - Formatted content (markdown → HTML)
            - Source links
            - Interactive features (collapse sections, search, download)
         ↓
Step 12: USER sees: interactive research report widget IN the chat
         Can scroll, search, and interact with the report
```

---

## Architecture Comparison

### Option 1: Two Separate Agents (Simple but Disconnected)

```
Pros:
  + Simple to implement
  + Clean separation of concerns
  + Each agent has focused responsibility

Cons:
  - User must switch between agents or the frontend must route
  - No unified conversation context
  - Research results from ADK don't automatically flow to MCP App rendering
  - Two separate state management systems
```

### Option 2: Unified Gateway (Recommended)

```
Pros:
  + Single conversation flow
  + BuiltInAgent decides when to research vs when to render
  + Research results can be passed directly to MCP App rendering
  + One endpoint, one agent from the user's perspective
  + MCP App iframes render seamlessly in the same chat

Cons:
  - Requires two LLMs (OpenAI for BuiltInAgent, Gemini for ADK agents)
  - More complex routing logic
  - delegate_to_adk tool needs to handle SSE streaming properly
  - Higher latency for research tasks (two LLM hops)
```

### Option 3: ADK-Only with Frontend State Rendering (No iframe)

```
Pros:
  + Single LLM (Gemini via ADK)
  + Simplest backend architecture
  + Full ADK agent orchestration

Cons:
  - NO MCP App iframe rendering
  - Must build custom React components for data visualization
  - Loses the MCP Apps ecosystem of pre-built UI widgets
  - More frontend work
```

---

## Implementation Roadmap

### Phase 1: Backend ADK Custom Agent (Week 1)

1. Build `UnifiedOrchestratorAgent` extending `BaseAgent`
2. Implement `_run_async_impl` with:
   - Research workflow (LlmAgent with web search MCP)
   - Analysis pipeline (SequentialAgent)
   - Parallel tasks (ParallelAgent)
3. Connect to backend MCP tools via `McpToolset`
4. Expose via `ag_ui_adk.ADKAgent` + FastAPI
5. Test with CopilotKit frontend (no iframe yet)

### Phase 2: MCP App Servers (Week 1-2)

1. Build `research-report-viewer` MCP App server
   - Uses `@modelcontextprotocol/ext-apps/server`
   - Renders research reports as formatted interactive documents
   - React-based UI with `useApp` hook
2. Optionally build `data-chart-viewer` MCP App server
   - Renders charts/graphs from research data
3. Test with standalone CopilotKit (copilotkit-weather pattern)

### Phase 3: Unified Gateway (Week 2)

1. Build Next.js API route with:
   - `BuiltInAgent` + `MCPAppsMiddleware` (for MCP App UI rendering)
   - `delegate_to_adk_orchestrator` custom tool (HTTP to ADK backend)
2. Configure MCP App servers in middleware
3. Implement the delegation tool with proper SSE handling
4. Test end-to-end: research → artifact → render PDF in chat

### Phase 4: Polish & Production (Week 3)

1. Add shared state sync between gateway and ADK backend
2. Implement artifact persistence (save research to DB)
3. Add human-in-loop approval for research plans
4. Add error handling and retry logic
5. PostgreSQL session service for production

---

## Key Libraries and Versions

| Component | Package | Version | Purpose |
|-----------|---------|---------|---------|
| CopilotKit Frontend | `@copilotkit/react-core` | 1.51.x | Chat UI, useCoAgent, v2 CopilotChat |
| CopilotKit Runtime | `@copilotkit/runtime` | 1.51.x | BuiltInAgent, CopilotRuntime |
| MCP Apps Middleware | `@ag-ui/mcp-apps-middleware` | 0.0.3+ | Bridges MCP App servers to CopilotKit |
| MCP Apps Server SDK | `@modelcontextprotocol/ext-apps` | 1.0.x | Build MCP App servers with UI |
| MCP SDK | `@modelcontextprotocol/sdk` | 1.24+ | Core MCP protocol |
| AG-UI Client | `@ag-ui/client` | 0.0.44+ | HttpAgent for backend connections |
| Google ADK | `google-adk` | 1.22.1+ | BaseAgent, LlmAgent, McpToolset |
| AG-UI ADK Bridge | `ag_ui_adk` | 0.1.0+ | ADKAgent, add_adk_fastapi_endpoint |
| FastAPI | `fastapi` | 0.100+ | Backend HTTP server |

---

## Conclusion

The unified architecture is **feasible and powerful**. The key insight is understanding that MCP has two distinct integration points:

1. **Backend MCP tools** (ADK `McpToolset`) = data only, used for agent capabilities
2. **Frontend MCP Apps** (CopilotKit `MCPAppsMiddleware`) = data + UI rendering via iframe

By building a **Unified Gateway** in the Next.js API route that combines:
- `BuiltInAgent` with `MCPAppsMiddleware` for visual MCP App rendering
- A delegation tool that calls the ADK backend for complex orchestration

...we achieve the goal of **one endpoint** where CopilotKit can both:
- Trigger deep research via ADK agents (LlmAgent, SequentialAgent, ParallelAgent)
- Render interactive visual content (PDF, charts, maps, weather) via MCP App iframes

The conversation flows naturally: "Research X" → agents work → "Show me the results" → iframe renders in chat.
