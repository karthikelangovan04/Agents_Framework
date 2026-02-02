#!/usr/bin/env python3
"""Simple A2A server example."""

from python_a2a import A2AServer, Message, TextContent, MessageRole
from python_a2a import create_fastapi_app
import uvicorn

def handle_message(message: Message) -> Message:
    """Handle incoming messages."""
    user_text = ""
    
    # Extract text from message content
    for content in message.content:
        if isinstance(content, TextContent):
            user_text += content.text
    
    # Simple response
    if not user_text:
        response_text = "Hello! I'm an A2A agent. How can I help you?"
    else:
        response_text = f"You said: {user_text}\nI'm here to help!"
    
    return Message(
        role=MessageRole.AGENT,
        content=[TextContent(text=response_text)]
    )

# Create agent card
agent_card = {
    "name": "simple_agent",
    "description": "A simple A2A agent that echoes messages",
    "version": "1.0.0"
}

# Create server
server = A2AServer(
    agent_card=agent_card,
    message_handler=handle_message
)

# Create FastAPI app
app = create_fastapi_app(server)

if __name__ == "__main__":
    print("Starting A2A server on http://localhost:8000")
    print("Agent Card available at: http://localhost:8000/.well-known/agent-card.json")
    uvicorn.run(app, host="0.0.0.0", port=8000)
