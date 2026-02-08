"""
Combo 2: Backend Orchestrator with A2A Remote Agents
CopilotKit → AG-UI → This Orchestrator → A2A → Remote ADK Agents

This orchestrator:
1. Receives requests from CopilotKit via AG-UI protocol
2. Maintains shared state (recipe) with the frontend
3. Delegates to remote A2A agents for specialized tasks
4. Supports human-in-loop via AGUIToolset (client-side tools)
"""

from __future__ import annotations

import json
from typing import Dict, List, Any, Optional

from dotenv import load_dotenv
load_dotenv()

from fastapi import FastAPI
from ag_ui_adk import ADKAgent, add_adk_fastapi_endpoint, AGUIToolset

# ADK imports
from google.adk.agents import LlmAgent
from google.adk.agents.callback_context import CallbackContext
from google.adk.a2a import RemoteA2aAgent
from google.adk.tools import FunctionTool, ToolContext
from google.adk.models import LlmResponse, LlmRequest
from google.genai import types


# ==============================================================================
# Remote A2A Agent References
# ==============================================================================

# These agents run as separate services (see remote_recipe_agent.py, etc.)
remote_recipe_agent = RemoteA2aAgent(
    name="recipe_specialist",
    agent_card_url="http://localhost:8010/agent_card.json",
    description="Specialized agent for creating and modifying recipes"
)

remote_nutrition_agent = RemoteA2aAgent(
    name="nutrition_analyst",
    agent_card_url="http://localhost:8011/agent_card.json",
    description="Specialized agent for nutritional analysis"
)


# ==============================================================================
# Tools: State Management + Plan Generation
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
    Update the recipe in shared state. Called after receiving results from
    remote agents or after local processing.

    Args:
        title: Recipe title
        skill_level: Beginner, Intermediate, or Advanced
        special_preferences: Dietary preferences list
        cooking_time: Cooking time string
        ingredients: List of ingredient objects with icon, name, amount
        instructions: List of instruction strings
        changes: Description of changes made

    Returns:
        Status dict
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

        current_recipe = tool_context.state.get("recipe", {})
        if current_recipe:
            for key, value in recipe.items():
                if value is not None and value != "" and value != []:
                    current_recipe[key] = value
        else:
            current_recipe = recipe

        tool_context.state["recipe"] = current_recipe
        return {"status": "success", "message": "Recipe updated successfully"}

    except Exception as e:
        return {"status": "error", "message": f"Error: {str(e)}"}


def create_plan(
    tool_context: ToolContext,
    plan_steps: List[str],
    agents_to_use: List[str],
    description: str
) -> Dict[str, str]:
    """
    Create an execution plan and store it in shared state for frontend display.
    The frontend can show this plan to the user for approval before execution.

    Args:
        plan_steps: Ordered list of steps to execute
        agents_to_use: Which agents will be involved
        description: Brief description of the plan

    Returns:
        Status dict
    """
    tool_context.state["plan"] = {
        "steps": plan_steps,
        "agents_to_use": agents_to_use,
        "description": description,
        "status": "pending_approval"
    }
    return {"status": "success", "message": "Plan created. Waiting for user approval."}


# ==============================================================================
# Callbacks: State Initialization + System Prompt Injection
# ==============================================================================

def on_before_agent(callback_context: CallbackContext):
    """Initialize recipe and plan state if not present."""
    if "recipe" not in callback_context.state:
        callback_context.state["recipe"] = {
            "title": "Make Your Recipe",
            "skill_level": "Intermediate",
            "special_preferences": [],
            "cooking_time": "30 min",
            "ingredients": [
                {"icon": "🍴", "name": "Sample Ingredient", "amount": "1 unit"}
            ],
            "instructions": ["First step instruction"]
        }

    if "plan" not in callback_context.state:
        callback_context.state["plan"] = None

    return None


def before_model_modifier(
    callback_context: CallbackContext, llm_request: LlmRequest
) -> Optional[LlmResponse]:
    """Inject current state into the system prompt for context awareness."""
    agent_name = callback_context.agent_name
    if agent_name == "OrchestratorAgent":
        recipe_json = "No recipe yet"
        if "recipe" in callback_context.state and callback_context.state["recipe"]:
            try:
                recipe_json = json.dumps(callback_context.state["recipe"], indent=2)
            except Exception as e:
                recipe_json = f"Error: {str(e)}"

        plan_json = "No active plan"
        if "plan" in callback_context.state and callback_context.state["plan"]:
            try:
                plan_json = json.dumps(callback_context.state["plan"], indent=2)
            except Exception as e:
                plan_json = f"Error: {str(e)}"

        prefix = f"""You are an orchestrator agent that coordinates specialized agents.

Current recipe state:
{recipe_json}

Current plan state:
{plan_json}

Available remote agents:
- recipe_specialist: Expert at creating and modifying recipes
- nutrition_analyst: Expert at nutritional analysis

You can:
1. Create a plan using create_plan tool (shows in UI for approval)
2. Delegate to remote agents for specialized tasks
3. Update the recipe using update_recipe tool
4. Use client-side tools from AGUIToolset for human-in-loop
"""
        original_instruction = llm_request.config.system_instruction or types.Content(
            role="system", parts=[]
        )
        if not isinstance(original_instruction, types.Content):
            original_instruction = types.Content(
                role="system", parts=[types.Part(text=str(original_instruction))]
            )
        if not original_instruction.parts:
            original_instruction.parts.append(types.Part(text=""))

        modified_text = prefix + (original_instruction.parts[0].text or "")
        original_instruction.parts[0].text = modified_text
        llm_request.config.system_instruction = original_instruction

    return None


def after_model_modifier(
    callback_context: CallbackContext, llm_response: LlmResponse
) -> Optional[LlmResponse]:
    """Stop consecutive tool calling after text response."""
    agent_name = callback_context.agent_name
    if agent_name == "OrchestratorAgent":
        if llm_response.content and llm_response.content.parts:
            if llm_response.content.role == 'model' and llm_response.content.parts[0].text:
                callback_context._invocation_context.end_invocation = True
    return None


# ==============================================================================
# Agent Definition
# ==============================================================================

orchestrator_agent = LlmAgent(
    name="OrchestratorAgent",
    model="gemini-2.5-pro",
    instruction="""
    You are an orchestrator that helps users create recipes.

    WORKFLOW:
    1. When user asks for a recipe or modification, first create a plan
    2. If the plan involves specialized work, delegate to appropriate agents:
       - recipe_specialist: for recipe creation and modification
       - nutrition_analyst: for nutritional analysis
    3. After receiving results, use update_recipe to update the shared state
    4. Summarize what was done for the user

    IMPORTANT:
    - Always use update_recipe tool to push changes to the UI
    - Use create_plan to show the user what you intend to do
    - Check plan status - if "approved", proceed; if "rejected", ask for changes
    - When the user modifies the recipe in the UI, you'll see the updated state
    """,
    tools=[
        AGUIToolset(),      # Client-side tools for human-in-loop
        update_recipe,      # Update shared state
        create_plan,        # Show plans in UI
    ],
    sub_agents=[
        remote_recipe_agent,    # A2A: remote recipe specialist
        remote_nutrition_agent, # A2A: remote nutrition analyst
    ],
    before_agent_callback=on_before_agent,
    before_model_callback=before_model_modifier,
    after_model_callback=after_model_modifier,
)


# ==============================================================================
# AG-UI Middleware + FastAPI
# ==============================================================================

adk_orchestrator = ADKAgent(
    adk_agent=orchestrator_agent,
    app_name="combo2_app",
    user_id="demo_user",
    session_timeout_seconds=3600,
    use_in_memory_services=True,
)

app = FastAPI(title="Combo 2: CopilotKit → AG-UI → A2A → ADK")

add_adk_fastapi_endpoint(app, adk_orchestrator, path="/")

if __name__ == "__main__":
    import uvicorn
    print("Starting Combo 2 Orchestrator on http://localhost:8001")
    print("Make sure remote agents are running on ports 8010, 8011")
    uvicorn.run(app, host="0.0.0.0", port=8001)
