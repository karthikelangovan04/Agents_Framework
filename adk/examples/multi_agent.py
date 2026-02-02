#!/usr/bin/env python3
"""Multi-agent system example."""

import asyncio
from google.adk import Agent
from google.adk.runners import Runner

async def main():
    # Create specialized sub-agents
    math_agent = Agent(
        name="math_specialist",
        description="Specializes in mathematical problems",
        model="gemini-1.5-flash",
        instruction="You are a math expert. Solve mathematical problems step by step, showing your work."
    )
    
    coding_agent = Agent(
        name="coding_specialist",
        description="Specializes in programming questions",
        model="gemini-1.5-flash",
        instruction="You are a programming expert. Help with code, debugging, and best practices. Provide clear examples."
    )
    
    # Create parent router agent
    parent_agent = Agent(
        name="router_agent",
        description="Routes questions to appropriate specialists",
        model="gemini-1.5-flash",
        instruction="""You are a router agent. Analyze the user's question and:
        - For math questions, transfer to math_specialist
        - For coding/programming questions, transfer to coding_specialist
        - Otherwise, answer directly if you can.""",
        sub_agents=[math_agent, coding_agent]
    )
    
    # Create runner
    runner = Runner(agent=parent_agent)
    
    print("Agent: I'm a router agent with math and coding specialists.")
    print("Ask me math or coding questions!")
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
