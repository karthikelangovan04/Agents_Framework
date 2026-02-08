# Combo 5: Full Integration — CopilotKit + MCP Apps + AG-UI + A2A + ADK + MCP Backend

**Status**: FEASIBLE (most complex architecture, highest capability)  
**Shared State**: Yes, at all layers  
**Human-in-Loop**: Yes, all methods + MCP App interactive UI  
**Multi-Agent**: Yes, A2A remote agents + local sub-agents  
**MCP**: Yes, both frontend (MCP Apps in chat) and backend (ADK McpToolset)

---

## Architecture — The Full Picture

```
┌─────────────────────────────────────────────────────────────────┐
│                      FRONTEND (Browser)                          │
│                                                                  │
│  ┌──────────────────────┐  ┌──────────────────────────────────┐ │
│  │ Recipe Form / Plan   │  │ CopilotChat (v2)                 │ │
│  │ (useCoAgent state)   │  │  - Text messages                 │ │
│  │                      │  │  - MCP App widgets (weather,     │ │
│  │ - Edit ingredients   │  │    maps, charts, PDFs)           │ │
│  │ - Approve/reject plan│  │  - Plan approval prompts         │ │
│  │ - View nutrition info│  │  - Agent status updates          │ │
│  └──────────────────────┘  └──────────────────────────────────┘ │
│                                                                  │
│  Hooks:                                                          │
│  - useCoAgent("orchestrator") → bidirectional state sync        │
│  - useCopilotChat → send messages, track loading                │
│  - useCopilotAction("approve_plan") → human-in-loop             │
│  - useCopilotAction("show_nutrition") → render nutrition panel  │
│  agent="orchestrator" or agent="mcp_apps"                       │
└──────────┬───────────────────────────────────────────────────────┘
           │ POST /api/copilotkit
           ▼
┌─────────────────────────────────────────────────────────────────┐
│                  NEXT.JS API ROUTE                                │
│                                                                  │
│  CopilotRuntime:                                                │
│  agents: {                                                       │
│    orchestrator: HttpAgent → backend:8001                        │
│    mcp_apps: BuiltInAgent + MCPAppsMiddleware                   │
│  }                                                               │
│                                                                  │
│  MCPAppsMiddleware connects to:                                 │
│  - weather-server:3006/mcp (weather cards)                      │
│  - map-server:3102/mcp (interactive maps)                       │
│  - chart-server:3105/mcp (budget/analytics charts)              │
└──────────┬─────────────┬────────────────────────────────────────┘
           │             │
           ▼             ▼
┌──────────────┐  ┌─────────────────────────────────────────────┐
│ MCP App      │  │ FASTAPI BACKEND GATEWAY (ag_ui_adk)         │
│ Servers      │  │                                              │
│              │  │ ADKAgent wrapping OrchestratorAgent          │
│ weather:3006 │  │ ├── AGUIToolset (client-side tools)         │
│ map:3102     │  │ │   - approve_plan → shows approval UI      │
│ chart:3105   │  │ │   - show_nutrition → renders panel        │
│              │  │ ├── McpToolset (filesystem) → read templates │
│              │  │ ├── McpToolset (weather) → seasonal info    │
│              │  │ ├── update_recipe (state sync)              │
│              │  │ ├── create_plan (plan display)              │
│              │  │ └── sub_agents:                             │
│              │  │     ├── RemoteA2aAgent("recipe_specialist") │
│              │  │     │   → port 8010                         │
│              │  │     ├── RemoteA2aAgent("nutrition_analyst") │
│              │  │     │   → port 8011                         │
│              │  │     ├── RemoteA2aAgent("data_agent")        │
│              │  │     │   → port 8012                         │
│              │  │     └── LocalAgent("formatter")             │
│              │  │                                              │
│              │  │ SessionService:                              │
│              │  │ - DatabaseSessionService (PostgreSQL)        │
│              │  │ - app/user/session state scopes             │
│              │  │ - Persistent across sessions                │
│              │  └──────────────────┬───────────────────────────┘
└──────────────┘                     │
                                     │ A2A Protocol
                    ┌────────────────┼────────────────┐
                    ▼                ▼                ▼
┌──────────────────────┐ ┌──────────────────┐ ┌──────────────────┐
│ Recipe Specialist    │ │ Nutrition Analyst │ │ Data Agent       │
│ ADK App, port 8010   │ │ ADK App, port 8011│ │ A2A Server, 8012│
│                      │ │                  │ │                  │
│ LlmAgent(gemini)     │ │ LlmAgent(gemini) │ │ AgentExecutor    │
│ + McpToolset         │ │ + analyze tools   │ │ + McpToolset     │
│   (food-api:3020)    │ │                  │ │   (postgres)     │
│                      │ │ Capabilities:    │ │                  │
│ Capabilities:        │ │ - Calorie calc   │ │ Capabilities:    │
│ - Create recipes     │ │ - Allergen detect│ │ - Query recipes  │
│ - Modify recipes     │ │ - Health rating  │ │ - Store favorites│
│ - Suggest variations │ │ - Substitutions  │ │ - User history   │
└──────────────────────┘ └──────────────────┘ └──────────────────┘
```

---

## Complete Data Flow Example

### Scenario: "Create a healthy vegetarian pasta for dinner tonight in San Francisco"

```
Step 1: USER types message in CopilotChat
        ↓
Step 2: CopilotKit sends to API route (agent="orchestrator")
        ↓
Step 3: HttpAgent forwards via AG-UI to FastAPI backend
        RunAgentInput includes:
        - messages: [{role: "user", content: "Create a healthy..."}]
        - state: { recipe: { ...current form data... } }
        - tools: [{ name: "approve_plan" }, { name: "show_nutrition" }]
        ↓
Step 4: ag_ui_adk.ADKAgent receives, creates/resumes session
        SessionManager loads state from PostgreSQL
        ↓
Step 5: OrchestratorAgent LLM processes request
        System prompt includes current recipe state + tool descriptions
        ↓
Step 6: LLM calls create_plan tool:
        plan = {
          steps: [
            "1. Check weather for outdoor dining suitability",
            "2. Create vegetarian pasta recipe",
            "3. Analyze nutritional content",
            "4. Check for seasonal ingredients"
          ],
          agents_to_use: ["recipe_specialist", "nutrition_analyst"],
          status: "pending_approval"
        }
        tool_context.state["plan"] = plan
        ↓
Step 7: AG-UI SSE stream → state update event → CopilotKit
        useCoAgent receives plan update
        Frontend renders Plan Approval UI
        ↓
Step 8: USER clicks "Approve" button
        setAgentState({ plan: { ...plan, status: "approved" } })
        appendMessage("Plan approved. Proceed.")
        ↓
Step 9: New AG-UI request with updated state (plan.status = "approved")
        ↓
Step 10: OrchestratorAgent sees approved plan, executes steps:

        a) Uses weather McpToolset directly:
           "What's the weather in San Francisco tonight?"
           → MCP server returns: "62°F, clear skies"

        b) Delegates to recipe_specialist via A2A:
           RemoteA2aAgent sends filtered context:
           "Create vegetarian pasta recipe, evening dinner, outdoor-friendly,
            mild weather. Must be healthy with high protein."
           ↓
           Recipe Agent (port 8010):
           - Uses food-api McpToolset to search pasta recipes
           - LLM crafts recipe with seasonal ingredients
           - Returns complete recipe via A2A response
           ↓

        c) Orchestrator receives recipe from A2A
           Calls update_recipe tool → state["recipe"] updated
           AG-UI SSE → useCoAgent → Recipe form updates in real-time
           ↓

        d) Delegates to nutrition_analyst via A2A:
           RemoteA2aAgent sends: recipe ingredients for analysis
           ↓
           Nutrition Agent (port 8011):
           - Analyzes calories, protein, allergens
           - Returns nutritional breakdown
           ↓

        e) Orchestrator receives nutrition data
           Stores in state["nutrition"] = { calories: 480, protein: 22, ... }
           AG-UI SSE → useCoAgent → Nutrition panel updates

        f) LLM calls AGUIToolset "show_nutrition" (client-side tool):
           → AG-UI ToolCallStartEvent → CopilotKit
           → useCopilotAction("show_nutrition") renders nutrition panel
           → User sees interactive nutrition breakdown
           → Result sent back to agent
        ↓
Step 11: OrchestratorAgent generates final text response:
         "I've created a Vegetarian Pesto Pasta with seasonal ingredients
          perfect for tonight's clear weather in SF! The recipe has been
          updated in your form. Nutritional highlights: 480 cal, 22g protein..."
         ↓
Step 12: AG-UI SSE text delta events → CopilotKit renders in chat
         User sees: recipe form updated + nutrition panel + chat summary
```

---

## Session State Architecture (PostgreSQL)

```sql
-- Session state (per conversation)
sessions.state = {
  "recipe": { title, ingredients, instructions, ... },
  "plan": { steps, status, ... },
  "nutrition": { calories, protein, ... },
  "agents_used": ["recipe_specialist", "nutrition_analyst"],
  "weather_context": { temperature, conditions, ... }
}

-- User state (across all sessions)
user_states = {
  "user:favorite_cuisines": ["Italian", "Japanese"],
  "user:dietary_restrictions": ["vegetarian"],
  "user:cooking_skill": "intermediate",
  "user:saved_recipes_count": 15
}

-- App state (shared by all users)
app_states = {
  "app:available_agents": ["recipe", "nutrition", "data"],
  "app:max_recipe_length": 20,
  "app:default_servings": 4
}
```

---

## Running the Full System

### Services to Start

```bash
# Terminal 1: PostgreSQL (for sessions)
docker run -p 5432:5432 -e POSTGRES_PASSWORD=adk_password postgres

# Terminal 2: MCP App Servers (for frontend UI rendering)
cd mcp_app_ext/ext-apps/ext-apps/examples/weather-server && npm start  # port 3006
cd mcp_app_ext/ext-apps/ext-apps/examples/map-server && npm start      # port 3102

# Terminal 3: Remote A2A Agent - Recipe
cd copilotkit_a2a_assessment/combo2_copilotkit_agui_a2a_adk
python remote_recipe_agent.py  # port 8010

# Terminal 4: Remote A2A Agent - Nutrition
python remote_nutrition_agent.py  # port 8011

# Terminal 5: Backend Orchestrator (AG-UI gateway)
python backend_orchestrator.py  # port 8001

# Terminal 6: Frontend (Next.js)
cd frontend && npm run dev  # port 3000
```

### Environment Variables

```bash
# .env
GOOGLE_API_KEY=your-gemini-key
OPENAI_API_KEY=your-openai-key          # For MCP Apps BuiltInAgent
DATABASE_URL=postgresql+asyncpg://adk_user:adk_password@localhost:5432/adk_db
NEXT_PUBLIC_API_URL=http://localhost:8001
```

---

## Capability Matrix

| Capability | How It Works | Layer |
|------------|-------------|-------|
| **Shared State (recipe form)** | `useCoAgent` ↔ AG-UI ↔ `ADKAgent` session state | Frontend ↔ Backend |
| **Human-in-Loop (plan approval)** | `useCopilotAction` or state-based approval buttons | Frontend ↔ Backend |
| **Multi-Agent Delegation** | `RemoteA2aAgent` in orchestrator's `sub_agents` | Backend ↔ Remote |
| **MCP App UI (weather card)** | `MCPAppsMiddleware` + `BuiltInAgent` + MCP server | Frontend ↔ MCP Server |
| **Backend MCP Tools** | `McpToolset` in ADK agent's tools list | Backend ↔ MCP Server |
| **Remote Agent MCP** | `McpToolset` inside remote A2A agent | Remote ↔ MCP Server |
| **Persistent State** | `DatabaseSessionService` with PostgreSQL | Backend ↔ Database |
| **User Preferences** | `user:` prefixed state keys in session | Backend ↔ Database |
| **Agent Discovery** | A2A `AgentCard` at `/agent_card.json` | Backend ↔ Remote |
| **Context Filtering** | Orchestrator filters state before A2A calls | Backend |
| **Token Optimization** | Filtered context + state summaries | Backend |

---

## Trade-offs

### Pros
- **Maximum flexibility** — handles any combination of UI + backend + remote agents
- **Rich UI** — MCP Apps render interactive widgets in chat
- **Scalable** — agents scale independently as separate services
- **Persistent** — PostgreSQL sessions survive restarts
- **Extensible** — add new agents, MCP servers, or UI actions without changing core

### Cons
- **Complexity** — many services to deploy and monitor (6+ processes)
- **Latency** — multiple network hops (Frontend → API → Backend → A2A → Remote)
- **Cost** — multiple LLM calls (orchestrator + remote agents + MCP Apps agent)
- **Two LLM providers** — MCP Apps needs OpenAI, ADK uses Gemini
- **State coordination** — must be careful about state consistency across layers
- **Debugging** — distributed system debugging is harder

### Recommended Starting Point

Start with **Combo 2** (CopilotKit → AG-UI → A2A → ADK) to get the core
architecture working. Then add:
1. **Backend MCP tools** (→ Combo 3) for external data access
2. **Frontend MCP Apps** (→ Combo 4) for rich UI rendering
3. **PostgreSQL sessions** for persistence
4. Scale to Combo 5 when all pieces are proven
