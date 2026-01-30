#!/usr/bin/env python3
"""Multi-agent chat example with A2A."""

import asyncio
from python_a2a import A2AClient, Message, TextContent, MessageRole
from python_a2a import Conversation

async def chat_with_agent(client: A2AClient, agent_name: str):
    """Chat with an agent."""
    print(f"\n=== Chatting with {agent_name} ===")
    
    conversation = Conversation(messages=[])
    
    # Initial message
    user_message = Message(
        role=MessageRole.USER,
        content=[TextContent(text="Hello! Tell me about yourself.")]
    )
    conversation.messages.append(user_message)
    
    # Send and get response
    response = await client.send_message(user_message)
    conversation.messages.append(response)
    
    # Print response
    for content in response.content:
        if isinstance(content, TextContent):
            print(f"{agent_name}: {content.text}")
    
    # Follow-up
    follow_up = Message(
        role=MessageRole.USER,
        content=[TextContent(text="What can you help me with?")]
    )
    conversation.messages.append(follow_up)
    
    response = await client.send_message(follow_up)
    conversation.messages.append(response)
    
    for content in response.content:
        if isinstance(content, TextContent):
            print(f"{agent_name}: {content.text}")
    
    return conversation

async def main():
    """Main function."""
    print("Multi-Agent A2A Chat Example")
    print("=" * 50)
    
    # Create clients for different agents
    agents = {
        "Math Agent": A2AClient(endpoint_url="http://localhost:8000"),
        "Code Agent": A2AClient(endpoint_url="http://localhost:8001"),
    }
    
    # Chat with each agent
    conversations = {}
    for name, client in agents.items():
        try:
            conversations[name] = await chat_with_agent(client, name)
        except Exception as e:
            print(f"Error chatting with {name}: {e}")
    
    print("\n=== All Conversations Complete ===")
    print(f"Total agents: {len(conversations)}")

if __name__ == "__main__":
    print("Make sure agents are running:")
    print("  - Math Agent: http://localhost:8000")
    print("  - Code Agent: http://localhost:8001")
    print("\nStarting chat...\n")
    asyncio.run(main())
