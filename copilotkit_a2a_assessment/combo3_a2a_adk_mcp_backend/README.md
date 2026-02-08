# Combo 3: CopilotKit → AG-UI → A2A → ADK + MCP Tools (Backend MCP)

**Status**: FEASIBLE (architecture validated)  
**Shared State**: Yes, via orchestrator  
**Human-in-Loop**: Yes, all three CopilotKit methods  
**Multi-Agent**: Yes, A2A remote agents  
**MCP**: Yes, backend MCP tools on both orchestrator and remote agents

---

## Architecture

```
┌────────────────────────────────┐
│   CopilotKit Frontend          │
│   - useCoAgent("orchestrator") │
│   - useCopilotChat             │
│   agent="orchestrator"         │
└──────────┬─────────────────────┘
           │ POST /api/copilotkit (AG-UI)
           ▼
┌────────────────────────────────┐
│   Next.js API Route            │
│   HttpAgent → backend:8001/    │
└──────────┬─────────────────────┘
           │ POST / (AG-UI, SSE)
           ▼
┌──────────────────────────────────────────────────────────────┐
│   FastAPI Backend (ag_ui_adk)                                │
│                                                              │
│   ADKAgent wrapping OrchestratorAgent                       │
│   ├── AGUIToolset (client-side tools)                       │
│   ├── McpToolset("filesystem") ← MCP Server (stdio)        │
│   ├── McpToolset("google-maps") ← MCP Server (SSE)         │
│   ├── update_recipe tool                                    │
│   └── sub_agents:                                           │
│       ├── RemoteA2aAgent("recipe_agent")                    │
│       │   → port 8010 (with its own McpToolset)            │
│       └── RemoteA2aAgent("data_agent")                      │
│           → port 8012 (with database MCP tools)             │
└──────────────────────┬──────────────────────────────────────┘
                       │ A2A Protocol
          ┌────────────┼────────────────┐
          ▼            ▼                ▼
┌─────────────┐ ┌──────────────────┐ ┌──────────────────┐
│ Recipe Agent │ │ Data Agent       │ │ MCP Servers       │
│ port 8010   │ │ port 8012        │ │ (stdio/SSE)      │
│ + McpToolset│ │ + McpToolset     │ │                  │
│   (food API)│ │   (PostgreSQL)   │ │ - filesystem     │
└─────────────┘ └──────────────────┘ │ - google-maps    │
                                      │ - food-api       │
                                      │ - postgresql     │
                                      └──────────────────┘
```

## MCP Integration Points

### 1. Orchestrator-Level MCP Tools
The orchestrator agent can directly use MCP tools for general capabilities:

```python
from google.adk.tools.mcp_tool import McpToolset, StdioConnectionParams, SseConnectionParams
from mcp import StdioServerParameters

# Filesystem MCP (for reading recipe files, images, etc.)
filesystem_toolset = McpToolset(
    connection_params=StdioConnectionParams(
        server_params=StdioServerParameters(
            command="npx",
            args=["-y", "@modelcontextprotocol/server-filesystem", "/data/recipes"]
        )
    ),
    tool_filter=["read_file", "list_directory"]  # Read-only
)

# Google Maps MCP (for restaurant/ingredient source lookups)
maps_toolset = McpToolset(
    connection_params=SseConnectionParams(
        url="http://localhost:3001/mcp",
        headers={"Authorization": f"Bearer {os.getenv('MAPS_API_KEY')}"}
    )
)

orchestrator_agent = LlmAgent(
    name="OrchestratorAgent",
    model="gemini-2.5-pro",
    tools=[
        AGUIToolset(),
        filesystem_toolset,  # MCP: filesystem access
        maps_toolset,        # MCP: maps access
        update_recipe,
    ],
    sub_agents=[remote_recipe_agent, remote_data_agent],
)
```

### 2. Remote Agent-Level MCP Tools
Each remote A2A agent can have its own MCP tools:

```python
# Remote Recipe Agent with Food API MCP tool
food_api_toolset = McpToolset(
    connection_params=SseConnectionParams(
        url="http://localhost:3002/mcp",
    ),
    tool_filter=["search_recipes", "get_nutritional_info"]
)

recipe_agent = LlmAgent(
    name="RecipeSpecialist",
    model="gemini-2.0-flash",
    tools=[food_api_toolset],  # MCP tools for this agent
)

# Remote Data Agent with PostgreSQL MCP tool
db_toolset = McpToolset(
    connection_params=StdioConnectionParams(
        server_params=StdioServerParameters(
            command="npx",
            args=["-y", "@modelcontextprotocol/server-postgres"],
            env={"DATABASE_URL": os.getenv("DATABASE_URL")}
        )
    )
)

data_agent = LlmAgent(
    name="DataAgent",
    model="gemini-2.0-flash",
    tools=[db_toolset],  # MCP tools for database queries
)
```

### 3. Dynamic MCP Tool Loading (Per-User)

Using the patterns from the ADK MCP docs, you can dynamically load
MCP tools based on user context:

```python
# Context-based filtering
def user_tool_filter(tool, context):
    """Only show tools the user has access to."""
    user_role = context.state.get("user:role", "viewer")
    if user_role == "admin":
        return True
    if user_role == "editor":
        return not tool.name.startswith("delete_")
    return tool.name.startswith("read_") or tool.name.startswith("list_")

toolset = McpToolset(
    connection_params=...,
    tool_filter=user_tool_filter
)
```

## Shared State Flow with MCP

```
1. User: "Find pasta recipes from Italian cuisine"
2. Frontend → AG-UI → Orchestrator
3. Orchestrator reads state["recipe"] for context
4. Orchestrator delegates to recipe_agent (A2A)
5. recipe_agent uses food_api MCP tool to search recipes
6. recipe_agent returns results via A2A
7. Orchestrator uses update_recipe tool → state["recipe"] updated
8. State flows back via AG-UI → useCoAgent → UI updates
9. User sees recipe in the form, can modify ingredients
10. User: "Find stores near me that sell these ingredients"
11. Orchestrator uses maps MCP tool directly
12. Results shown in chat (text) or stored in state for UI rendering
```

## Benefits of MCP in A2A Architecture

1. **Tool reuse** — MCP servers are shared across agents
2. **Separation of concerns** — each agent has tools relevant to its specialty
3. **Dynamic capabilities** — MCP tools can be added/removed at runtime
4. **Security** — tool_filter controls which tools each agent can access
5. **Protocol standard** — MCP tools work with any MCP-compatible server

## Limitations

- **MCP tool latency** — adds time for tool server connection
- **MCP server management** — need to run and monitor MCP servers
- **No frontend MCP rendering** — MCP tool UIs don't render in chat (see Combo 4)
- **Authentication complexity** — MCP servers may need per-user auth
