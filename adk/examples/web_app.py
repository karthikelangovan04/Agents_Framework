#!/usr/bin/env python3
"""Web application example."""

from google.adk import Agent
from google.adk.apps import App
import uvicorn

# Create agent
agent = Agent(
    name="web_agent",
    description="A web-based assistant",
    model="gemini-1.5-flash",
    instruction="You are a helpful web assistant. Answer questions clearly."
)

# Create FastAPI app
app = App(agent=agent)

if __name__ == "__main__":
    print("Starting web app on http://localhost:8000")
    print("Visit http://localhost:8000/docs for API documentation")
    uvicorn.run(app, host="0.0.0.0", port=8000)
