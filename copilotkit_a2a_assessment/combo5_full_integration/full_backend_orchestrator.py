"""
Combo 5: Full Integration Backend Orchestrator

CopilotKit → AG-UI → This Orchestrator → A2A → Remote ADK Agents
                                        → MCP → MCP Servers

Features:
1. AG-UI shared state with CopilotKit frontend (useCoAgent)
2. A2A remote agent delegation (recipe, nutrition, data agents)
3. Backend MCP tools (filesystem, weather)
4. Human-in-loop via AGUIToolset (client-side tools)
5. DatabaseSessionService for persistent state
6. Plan creation and approval flow
7. Context filtering for token optimization
"""

from __future__ import annotations

import os
import json
from typing import Dict, List, Any, Optional

from dotenv import load_dotenv
load_dotenv()

from fastapi import FastAPI, Request
from ag_ui.core import RunAgentInput
from ag_ui_adk import ADKAgent, add_adk_fastapi_endpoint, AGUIToolset

from google.adk.agents import LlmAgent
from google.adk.agents.callback_context import CallbackContext
from google.adk.a2a import RemoteA2aAgent
from google.adk.tools import ToolContext
from google.adk.models import LlmResponse, LlmRequest
from google.genai import types

# Uncomment when using persistent sessions:
# from google.adk.sessions import DatabaseSessionService


# ==============================================================================
# MCP Toolsets (uncomment when MCP servers are running)
# ==============================================================================

# from google.adk.tools.mcp_tool import McpToolset, StdioConnectionParams, SseConnectionParams
# from mcp import StdioServerParameters
#
# filesystem_toolset = McpToolset(
#     connection_params=StdioConnectionParams(
#         server_params=StdioServerParameters(
#             command="npx",
#             args=["-y", "@modelcontextprotocol/server-filesystem", "/data/recipes"]
#         )
#     ),
#     tool_filter=["read_file", "list_directory"]
# )
#
# weather_toolset = McpToolset(
#     connection_params=SseConnectionParams(
#         url="http://localhost:3006/mcp",
#         timeout=5.0,
#     )
# )


# ==============================================================================
# Remote A2A Agent References
# ==============================================================================

remote_recipe_agent = RemoteA2aAgent(
    name="recipe_specialist",
    agent_card_url="http://localhost:8010/agent_card.json",
    description="Expert at creating and modifying recipes (has food API MCP)"
)

remote_nutrition_agent = RemoteA2aAgent(
    name="nutrition_analyst",
    agent_card_url="http://localhost:8011/agent_card.json",
    description="Expert at nutritional analysis and health recommendations"
)

remote_data_agent = RemoteA2aAgent(
    name="data_agent",
    agent_card_url="http://localhost:8012/agent_card.json",
    description="Data agent with database access for recipe storage and retrieval"
)


# ==============================================================================
# Tools
# ==============================================================================

def update_recipe(
    tool_context: ToolContext,
    title: str,
    skill_level: str = "Intermediate",
    special_preferences: List[str] = [],
    cooking_time: str = "30 min",
    ingredients: List[dict] = [],
    instructions: List[str] = [],
    changes: str = ""
) -> Dict[str, str]:
    """
    Update the recipe in shared state. Changes sync to the CopilotKit
    frontend via AG-UI state prediction events.
    """
    try:
        recipe = {
            "title": title,
            "skill_level": skill_level,
            "special_preferences": special_preferences,
            "cooking_time": cooking_time,
            "ingredients": ingredients,
            "instructions": instructions,
            "changes": changes
        }

        current = tool_context.state.get("recipe", {})
        for k, v in recipe.items():
            if v is not None and v != "" and v != []:
                current[k] = v

        tool_context.state["recipe"] = current
        return {"status": "success", "message": "Recipe updated in UI"}
    except Exception as e:
        return {"status": "error", "message": str(e)}


def create_plan(
    tool_context: ToolContext,
    plan_steps: List[str],
    agents_to_use: List[str],
    description: str
) -> Dict[str, str]:
    """
    Create an execution plan visible in the frontend UI.
    The user can approve or reject before execution proceeds.
    """
    tool_context.state["plan"] = {
        "steps": plan_steps,
        "agents_to_use": agents_to_use,
        "description": description,
        "status": "pending_approval"
    }
    return {"status": "success", "message": "Plan shown to user for approval"}


def update_nutrition(
    tool_context: ToolContext,
    calories: int = 0,
    protein_g: float = 0,
    carbs_g: float = 0,
    fat_g: float = 0,
    allergens: List[str] = [],
    health_rating: int = 5,
    suggestions: List[str] = []
) -> Dict[str, str]:
    """
    Update nutritional information in shared state.
    Frontend can display this in a nutrition panel.
    """
    tool_context.state["nutrition"] = {
        "calories": calories,
        "protein_g": protein_g,
        "carbs_g": carbs_g,
        "fat_g": fat_g,
        "allergens": allergens,
        "health_rating": health_rating,
        "suggestions": suggestions
    }
    return {"status": "success", "message": "Nutrition info updated in UI"}


# ==============================================================================
# Callbacks
# ==============================================================================

def on_before_agent(callback_context: CallbackContext):
    """Initialize all state sections."""
    defaults = {
        "recipe": {
            "title": "Make Your Recipe",
            "skill_level": "Intermediate",
            "special_preferences": [],
            "cooking_time": "30 min",
            "ingredients": [{"icon": "🍴", "name": "Sample", "amount": "1 unit"}],
            "instructions": ["First step"]
        },
        "plan": None,
        "nutrition": None,
        "agents_used": [],
    }
    for key, default in defaults.items():
        if key not in callback_context.state:
            callback_context.state[key] = default
    return None


def before_model_modifier(
    callback_context: CallbackContext, llm_request: LlmRequest
) -> Optional[LlmResponse]:
    """Inject comprehensive context into the system prompt."""
    if callback_context.agent_name != "FullOrchestrator":
        return None

    state = callback_context.state
    sections = []

    # Recipe state
    recipe = state.get("recipe", {})
    sections.append(f"Current recipe:\n{json.dumps(recipe, indent=2)}")

    # Plan state
    plan = state.get("plan")
    if plan:
        sections.append(f"Current plan:\n{json.dumps(plan, indent=2)}")

    # Nutrition state
    nutrition = state.get("nutrition")
    if nutrition:
        sections.append(f"Nutrition info:\n{json.dumps(nutrition, indent=2)}")

    # User preferences (from user-scoped state)
    user_prefs = {}
    for key in state:
        if isinstance(key, str) and key.startswith("user:"):
            user_prefs[key.replace("user:", "")] = state[key]
    if user_prefs:
        sections.append(f"User preferences:\n{json.dumps(user_prefs, indent=2)}")

    context_block = "\n\n".join(sections)

    prefix = f"""You are the full integration orchestrator with these capabilities:

STATE CONTEXT:
{context_block}

AVAILABLE TOOLS:
- update_recipe: Push recipe changes to the frontend UI
- create_plan: Show execution plan for user approval
- update_nutrition: Push nutrition data to the frontend UI
- AGUIToolset: Call frontend actions (approve_plan, show_nutrition)
- MCP tools: filesystem (read templates), weather (seasonal data)

AVAILABLE REMOTE AGENTS (via A2A):
- recipe_specialist: Creates/modifies recipes (has food API MCP)
- nutrition_analyst: Nutritional analysis and health ratings
- data_agent: Database queries for recipe storage/history

WORKFLOW:
1. Analyze user request and current state
2. Create a plan if the task involves multiple agents
3. Wait for plan approval if status is "pending_approval"
4. Execute plan steps: delegate to agents, use MCP tools
5. Update state (recipe, nutrition) after each step
6. Provide summary to user

RULES:
- Always call update_recipe after receiving recipe from remote agent
- Always call update_nutrition after receiving analysis
- Filter context when delegating to remote agents (send only relevant info)
- Check plan.status before proceeding with approved plans
- Use user preferences to personalize recommendations
"""

    original = llm_request.config.system_instruction or types.Content(
        role="system", parts=[]
    )
    if not isinstance(original, types.Content):
        original = types.Content(
            role="system", parts=[types.Part(text=str(original))]
        )
    if not original.parts:
        original.parts.append(types.Part(text=""))
    original.parts[0].text = prefix + (original.parts[0].text or "")
    llm_request.config.system_instruction = original
    return None


def after_model_modifier(
    callback_context: CallbackContext, llm_response: LlmResponse
) -> Optional[LlmResponse]:
    """Stop after text response to prevent infinite tool loops."""
    if callback_context.agent_name == "FullOrchestrator":
        if llm_response.content and llm_response.content.parts:
            if (llm_response.content.role == 'model'
                    and llm_response.content.parts[0].text):
                callback_context._invocation_context.end_invocation = True
    return None


# ==============================================================================
# Agent Definition
# ==============================================================================

orchestrator_tools = [
    AGUIToolset(),          # Client-side tools for human-in-loop
    update_recipe,          # Shared state: recipe
    create_plan,            # Shared state: plan (for approval UI)
    update_nutrition,       # Shared state: nutrition panel
    # filesystem_toolset,   # MCP: filesystem (uncomment when available)
    # weather_toolset,      # MCP: weather (uncomment when available)
]

full_orchestrator = LlmAgent(
    name="FullOrchestrator",
    model="gemini-2.5-pro",
    instruction="""You are the full integration orchestrator.
    Coordinate remote agents, use MCP tools, and manage shared state with the UI.
    Always update the UI state after receiving results from agents or tools.""",
    tools=orchestrator_tools,
    sub_agents=[
        remote_recipe_agent,
        remote_nutrition_agent,
        remote_data_agent,
    ],
    before_agent_callback=on_before_agent,
    before_model_callback=before_model_modifier,
    after_model_callback=after_model_modifier,
)


# ==============================================================================
# Session Service (switch to DatabaseSessionService for persistence)
# ==============================================================================

# For development:
session_service = None  # Uses InMemory

# For production (uncomment):
# DB_URL = os.getenv("DATABASE_URL",
#     "postgresql+asyncpg://adk_user:adk_password@localhost:5432/adk_db")
# session_service = DatabaseSessionService(db_url=DB_URL)


# ==============================================================================
# User ID Extraction (for multi-user sessions)
# ==============================================================================

def user_id_extractor(input: RunAgentInput) -> str:
    """Extract user ID from AG-UI request state."""
    if isinstance(getattr(input, "state", None), dict):
        uid = input.state.get("_ag_ui_user_id")
        if uid:
            return str(uid)
    return f"thread_user_{getattr(input, 'thread_id', 'default')}"


async def extract_state_from_request(request: Request, input_data: RunAgentInput) -> dict:
    """Extract user/session info from headers into state."""
    state = {}
    user_id = request.headers.get("X-User-Id")
    session_id = request.headers.get("X-Session-Id")
    if user_id:
        state["_ag_ui_user_id"] = user_id
    if session_id:
        state["_ag_ui_session_id"] = session_id
        state["_ag_ui_thread_id"] = session_id
    state["_ag_ui_app_name"] = "combo5_full"
    return state


# ==============================================================================
# FastAPI Application
# ==============================================================================

adk_agent_kwargs = {
    "adk_agent": full_orchestrator,
    "app_name": "combo5_full",
    "session_timeout_seconds": 3600,
}

if session_service:
    adk_agent_kwargs["session_service"] = session_service
    adk_agent_kwargs["user_id_extractor"] = user_id_extractor
    adk_agent_kwargs["use_in_memory_services"] = False
else:
    adk_agent_kwargs["user_id"] = "demo_user"
    adk_agent_kwargs["use_in_memory_services"] = True

adk_orchestrator = ADKAgent(**adk_agent_kwargs)

app = FastAPI(title="Combo 5: Full Integration Orchestrator")

add_adk_fastapi_endpoint(
    app,
    adk_orchestrator,
    path="/",
    extract_state_from_request=extract_state_from_request,
)


@app.get("/health")
async def health():
    return {
        "status": "healthy",
        "combo": 5,
        "features": [
            "AG-UI shared state",
            "A2A remote agents",
            "MCP backend tools",
            "Human-in-loop",
            "Plan approval flow",
            "Nutrition analysis",
        ]
    }


if __name__ == "__main__":
    import uvicorn
    print("=" * 60)
    print("Combo 5: Full Integration Orchestrator")
    print("=" * 60)
    print("CopilotKit → AG-UI → A2A → ADK + MCP")
    print()
    print("Backend: http://localhost:8001")
    print("Health:  http://localhost:8001/health")
    print()
    print("Required remote agents:")
    print("  - Recipe Agent:    http://localhost:8010")
    print("  - Nutrition Agent: http://localhost:8011")
    print("  - Data Agent:      http://localhost:8012")
    print()
    print("Optional MCP servers:")
    print("  - Weather:    http://localhost:3006/mcp")
    print("  - Filesystem: stdio (configured in code)")
    print("=" * 60)
    uvicorn.run(app, host="0.0.0.0", port=8001)
