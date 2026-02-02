#!/usr/bin/env python3
"""Agent with tools example."""

import asyncio
from google.adk import Agent
from google.adk.runners import Runner

def get_current_time():
    """Get the current time in a readable format."""
    from datetime import datetime
    return datetime.now().strftime("%Y-%m-%d %H:%M:%S")

def calculate(expression: str) -> str:
    """Evaluate a mathematical expression safely.
    
    Args:
        expression: A mathematical expression like '2 + 2' or '10 * 5'
    
    Returns:
        The result as a string
    """
    try:
        # Safe evaluation with limited builtins
        allowed_names = {
            k: v for k, v in __builtins__.items() 
            if k in ['abs', 'round', 'min', 'max', 'sum', 'pow']
        }
        result = eval(expression, {"__builtins__": allowed_names}, {})
        return str(result)
    except Exception as e:
        return f"Error calculating: {str(e)}"

async def main():
    # Create agent with tools
    agent = Agent(
        name="tool_agent",
        description="An agent that can use tools to help users",
        model="gemini-1.5-flash",
        instruction="You are a helpful assistant with access to tools. Use them when appropriate to help users.",
        tools=[get_current_time, calculate]
    )
    
    # Create runner
    runner = Runner(agent=agent)
    
    print("Agent: Hello! I can help you with time and calculations.")
    print("Try asking: 'What time is it?' or 'Calculate 15 * 23'")
    print("Type 'quit' to exit.\n")
    
    while True:
        user_input = input("You: ")
        if user_input.lower() == 'quit':
            break
        
        print("\nAgent: ", end="", flush=True)
        async for event in runner.run(user_input):
            if hasattr(event, 'content') and event.content:
                print(event.content, end="", flush=True)
        print("\n")

if __name__ == "__main__":
    asyncio.run(main())
