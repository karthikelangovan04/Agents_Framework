"""
Combo 2: Remote Recipe Agent (A2A Server)

This agent runs as a separate service and is called by the orchestrator
via A2A protocol. It specializes in recipe creation and modification.

Run: python remote_recipe_agent.py
Serves on: http://localhost:8010
"""

from dotenv import load_dotenv
load_dotenv()

from google.adk.agents import LlmAgent
from google.adk.apps import App
from google.adk.tools import ToolContext
from typing import Dict, List
import uvicorn


def craft_recipe(
    tool_context: ToolContext,
    title: str,
    cuisine: str = "",
    dietary_requirements: List[str] = [],
    cooking_time_minutes: int = 30,
    servings: int = 4,
) -> Dict:
    """
    Craft a complete recipe based on requirements.

    Args:
        title: Name of the dish
        cuisine: Type of cuisine (Italian, Japanese, etc.)
        dietary_requirements: List of dietary requirements
        cooking_time_minutes: Target cooking time
        servings: Number of servings

    Returns:
        Complete recipe dict with ingredients and instructions
    """
    # The LLM generates the actual recipe content; this tool
    # structures the response for the orchestrator to consume
    return {
        "status": "recipe_crafted",
        "title": title,
        "cuisine": cuisine,
        "dietary_requirements": dietary_requirements,
        "cooking_time_minutes": cooking_time_minutes,
        "servings": servings,
    }


recipe_agent = LlmAgent(
    name="RecipeSpecialist",
    description="Expert at creating and modifying recipes with detailed ingredients and instructions",
    model="gemini-2.0-flash",
    instruction="""
    You are a world-class chef and recipe specialist.

    When asked to create or modify a recipe:
    1. Consider dietary requirements, cooking time, and skill level
    2. Provide detailed ingredients with amounts and emoji icons
    3. Write clear, step-by-step instructions
    4. Suggest variations or tips when appropriate

    Always respond with complete, practical recipes that users can actually cook.
    Use craft_recipe tool to structure your output.
    """,
    tools=[craft_recipe],
)

# ADK App serves the agent via A2A protocol
# This automatically provides /agent_card.json and handles A2A requests
app = App(agent=recipe_agent)

if __name__ == "__main__":
    print("Starting Recipe Agent (A2A) on http://localhost:8010")
    uvicorn.run(app, host="0.0.0.0", port=8010)
