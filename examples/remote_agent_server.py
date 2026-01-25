#!/usr/bin/env python3
"""Remote agent server for A2A communication."""

from google.adk import Agent
from google.adk.apps import App
import uvicorn

# Create specialized remote agent
math_agent = Agent(
    name="remote_math_agent",
    description="A remote agent specialized in mathematical problem solving",
    model="gemini-1.5-flash",
    instruction="""You are a math expert. 
    Solve mathematical problems step by step.
    Show your work clearly."""
)

# Create app
app = App(agent=math_agent)

if __name__ == "__main__":
    print("Starting remote math agent server on http://localhost:8000")
    uvicorn.run(app, host="0.0.0.0", port=8000)
