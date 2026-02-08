"""
Combo 2: Remote Nutrition Agent (A2A Server)

This agent runs as a separate service and is called by the orchestrator
via A2A protocol. It specializes in nutritional analysis.

Run: python remote_nutrition_agent.py
Serves on: http://localhost:8011
"""

from dotenv import load_dotenv
load_dotenv()

from google.adk.agents import LlmAgent
from google.adk.apps import App
from google.adk.tools import ToolContext
from typing import Dict, List
import uvicorn


def analyze_nutrition(
    tool_context: ToolContext,
    ingredients: List[dict],
    servings: int = 4,
) -> Dict:
    """
    Analyze nutritional content of a recipe based on its ingredients.

    Args:
        ingredients: List of ingredient dicts with name and amount
        servings: Number of servings

    Returns:
        Nutritional analysis dict
    """
    return {
        "status": "analysis_complete",
        "ingredients_analyzed": len(ingredients),
        "servings": servings,
    }


nutrition_agent = LlmAgent(
    name="NutritionAnalyst",
    description="Expert at analyzing nutritional content of recipes and suggesting healthier alternatives",
    model="gemini-2.0-flash",
    instruction="""
    You are a certified nutritionist.

    When asked to analyze a recipe:
    1. Estimate calories, protein, carbs, and fat per serving
    2. Identify potential allergens
    3. Suggest healthier substitutions if applicable
    4. Rate the recipe's healthiness (1-10)

    Use analyze_nutrition tool to structure your output.
    Be specific with numbers and practical with suggestions.
    """,
    tools=[analyze_nutrition],
)

app = App(agent=nutrition_agent)

if __name__ == "__main__":
    print("Starting Nutrition Agent (A2A) on http://localhost:8011")
    uvicorn.run(app, host="0.0.0.0", port=8011)
