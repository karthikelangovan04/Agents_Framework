#!/usr/bin/env python3
"""Client that consumes a remote agent via A2A."""

import asyncio
from google.adk import Agent
from google.adk.a2a import RemoteA2aAgent
from google.adk.runners import Runner

async def main():
    # Create remote agent reference
    remote_math = RemoteA2aAgent(
        name="remote_math",
        agent_card_url="http://localhost:8000/agent_card.json"
    )
    
    # Create local coordinator agent
    local_agent = Agent(
        name="local_coordinator",
        description="Local agent that coordinates with remote agents",
        model="gemini-1.5-flash",
        instruction="""You are a coordinator agent. 
        When users ask math questions, transfer to remote_math agent.
        Otherwise, answer directly if you can.""",
        sub_agents=[remote_math]
    )
    
    runner = Runner(agent=local_agent)
    
    print("Local Coordinator: I can help with general questions and math!")
    print("(Make sure remote_agent_server.py is running)")
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
