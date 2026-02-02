#!/usr/bin/env python3
"""Simple A2A client example."""

import asyncio
from python_a2a import A2AClient, Message, TextContent, MessageRole

async def main():
    """Main client function."""
    # Create client
    client = A2AClient(
        endpoint_url="http://localhost:8000"
    )
    
    # Create a message
    message = Message(
        role=MessageRole.USER,
        content=[TextContent(text="Hello, A2A agent!")]
    )
    
    # Send message
    print("Sending message to server...")
    response = await client.send_message(message)
    
    # Print response
    print("\nResponse:")
    for content in response.content:
        if isinstance(content, TextContent):
            print(content.text)

if __name__ == "__main__":
    print("Make sure the server is running on http://localhost:8000")
    print("Run: python simple_server.py in another terminal\n")
    asyncio.run(main())
