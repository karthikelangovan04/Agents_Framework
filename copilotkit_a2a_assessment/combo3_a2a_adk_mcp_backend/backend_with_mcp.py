"""
Combo 3: Backend Orchestrator with A2A + MCP Tools
CopilotKit → AG-UI → Orchestrator (MCP tools) → A2A → Remote Agents (MCP tools)

Demonstrates:
1. Orchestrator with direct MCP tool access
2. Remote A2A agents with their own MCP tools
3. Shared state through the orchestrator
"""

from __future__ import annotations

import os
import json
from typing import Dict, List, Any, Optional

from dotenv import load_dotenv
load_dotenv()

from fastapi import FastAPI
from ag_ui_adk import ADKAgent, add_adk_fastapi_endpoint, AGUIToolset

from google.adk.agents import LlmAgent
from google.adk.agents.callback_context import CallbackContext
from google.adk.a2a import RemoteA2aAgent
from google.adk.tools import ToolContext
from google.adk.tools.mcp_tool import McpToolset, StdioConnectionParams, SseConnectionParams
from google.adk.models import LlmResponse, LlmRequest
from google.genai import types

try:
    from mcp import StdioServerParameters
except ImportError:
    StdioServerParameters = None


# ==============================================================================
# MCP Toolsets for the Orchestrator
# ==============================================================================

# Filesystem MCP: read recipe templates, config files
# Uncomment and configure when MCP server is available
# filesystem_toolset = McpToolset(
#     connection_params=StdioConnectionParams(
#         server_params=StdioServerParameters(
#             command="npx",
#             args=["-y", "@modelcontextprotocol/server-filesystem", "/data/recipes"]
#         ),
#         timeout=5.0
#     ),
#     tool_filter=["read_file", "list_directory"]
# )

# Weather/Maps MCP: find local ingredients, seasonal suggestions
# Uncomment and configure when MCP server is available
# weather_toolset = McpToolset(
#     connection_params=SseConnectionParams(
#         url="http://localhost:3006/mcp",
#         timeout=5.0,
#     )
# )


# ==============================================================================
# Remote A2A Agent References (they have their own MCP tools)
# ==============================================================================

remote_recipe_agent = RemoteA2aAgent(
    name="recipe_specialist",
    agent_card_url="http://localhost:8010/agent_card.json",
    description="Recipe specialist with food API MCP access"
)

remote_data_agent = RemoteA2aAgent(
    name="data_agent",
    agent_card_url="http://localhost:8012/agent_card.json",
    description="Data agent with database MCP access"
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
    """Update the recipe in shared state after receiving results from agents or MCP tools."""
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

        current_recipe = tool_context.state.get("recipe", {})
        for key, value in recipe.items():
            if value is not None and value != "" and value != []:
                current_recipe[key] = value

        tool_context.state["recipe"] = current_recipe
        return {"status": "success", "message": "Recipe updated"}
    except Exception as e:
        return {"status": "error", "message": str(e)}


# ==============================================================================
# Callbacks
# ==============================================================================

def on_before_agent(callback_context: CallbackContext):
    if "recipe" not in callback_context.state:
        callback_context.state["recipe"] = {
            "title": "Make Your Recipe",
            "skill_level": "Intermediate",
            "special_preferences": [],
            "cooking_time": "30 min",
            "ingredients": [{"icon": "🍴", "name": "Sample", "amount": "1 unit"}],
            "instructions": ["First step"]
        }
    return None


def before_model_modifier(
    callback_context: CallbackContext, llm_request: LlmRequest
) -> Optional[LlmResponse]:
    if callback_context.agent_name == "OrchestratorWithMCP":
        recipe_json = json.dumps(callback_context.state.get("recipe", {}), indent=2)
        prefix = f"""You are an orchestrator with MCP tool access and remote A2A agents.

Current recipe: {recipe_json}

Capabilities:
- Direct MCP tools: filesystem (read recipe templates), weather (seasonal ingredients)
- Remote agents via A2A:
  - recipe_specialist: creates/modifies recipes (has food API MCP)
  - data_agent: queries recipe database (has PostgreSQL MCP)
- Shared state: update_recipe pushes changes to the frontend UI

Workflow:
1. Use MCP tools for immediate data needs (read files, check weather)
2. Delegate to remote agents for specialized work
3. Always call update_recipe to sync changes to the UI
"""
        original = llm_request.config.system_instruction or types.Content(
            role="system", parts=[]
        )
        if not isinstance(original, types.Content):
            original = types.Content(role="system", parts=[types.Part(text=str(original))])
        if not original.parts:
            original.parts.append(types.Part(text=""))
        original.parts[0].text = prefix + (original.parts[0].text or "")
        llm_request.config.system_instruction = original
    return None


def after_model_modifier(
    callback_context: CallbackContext, llm_response: LlmResponse
) -> Optional[LlmResponse]:
    if callback_context.agent_name == "OrchestratorWithMCP":
        if llm_response.content and llm_response.content.parts:
            if llm_response.content.role == 'model' and llm_response.content.parts[0].text:
                callback_context._invocation_context.end_invocation = True
    return None


# ==============================================================================
# Agent
# ==============================================================================

orchestrator_tools = [
    AGUIToolset(),
    update_recipe,
    # filesystem_toolset,   # Uncomment when MCP server available
    # weather_toolset,      # Uncomment when MCP server available
]

orchestrator_agent = LlmAgent(
    name="OrchestratorWithMCP",
    model="gemini-2.5-pro",
    instruction="""
    You orchestrate recipe creation using MCP tools and remote agents.
    Use MCP tools for direct data access and remote agents for specialized tasks.
    Always update the recipe state for the UI using update_recipe.
    """,
    tools=orchestrator_tools,
    sub_agents=[remote_recipe_agent, remote_data_agent],
    before_agent_callback=on_before_agent,
    before_model_callback=before_model_modifier,
    after_model_callback=after_model_modifier,
)

# ==============================================================================
# FastAPI
# ==============================================================================

adk_orchestrator = ADKAgent(
    adk_agent=orchestrator_agent,
    app_name="combo3_app",
    user_id="demo_user",
    session_timeout_seconds=3600,
    use_in_memory_services=True,
)

app = FastAPI(title="Combo 3: AG-UI + A2A + MCP Backend")
add_adk_fastapi_endpoint(app, adk_orchestrator, path="/")

if __name__ == "__main__":
    import uvicorn
    print("Starting Combo 3 on http://localhost:8001")
    uvicorn.run(app, host="0.0.0.0", port=8001)
