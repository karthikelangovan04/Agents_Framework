#!/usr/bin/env python3
"""Simple agent example."""

import asyncio
from google.adk import Agent
from google.adk.runners import Runner

async def main():
    # Create agent
    agent = Agent(
        name="simple_agent",
        description="A simple helpful assistant",
        model="gemini-1.5-flash",
        instruction="You are a helpful assistant. Answer questions clearly and concisely."
    )
    
    # Create runner
    runner = Runner(agent=agent)
    
    # Run conversation
    print("Agent: Hello! I'm a simple assistant. Ask me anything!")
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
