#!/usr/bin/env python3
"""Calculator A2A agent with function calling."""

from python_a2a import A2AServer, Message, TextContent, MessageRole
from python_a2a import FunctionCallContent, FunctionResponseContent
from python_a2a import create_fastapi_app
import uvicorn

def calculate(a: float, b: float, operation: str) -> float:
    """Perform a calculation.
    
    Args:
        a: First number
        b: Second number
        operation: Operation to perform (add, subtract, multiply, divide)
    
    Returns:
        Calculation result
    """
    operations = {
        "add": lambda x, y: x + y,
        "subtract": lambda x, y: x - y,
        "multiply": lambda x, y: x * y,
        "divide": lambda x, y: x / y if y != 0 else float('inf')
    }
    
    if operation not in operations:
        raise ValueError(f"Unknown operation: {operation}")
    
    return operations[operation](a, b)

def handle_message(message: Message) -> Message:
    """Handle messages, including function calls."""
    responses = []
    
    for content in message.content:
        if isinstance(content, FunctionCallContent):
            # Handle function call
            try:
                params = content.parameters
                result = calculate(
                    params.get("a", 0),
                    params.get("b", 0),
                    params.get("operation", "add")
                )
                
                responses.append(
                    FunctionResponseContent(
                        name=content.name,
                        response={"result": result}
                    )
                )
            except Exception as e:
                responses.append(
                    FunctionResponseContent(
                        name=content.name,
                        response={"error": str(e)}
                    )
                )
        
        elif isinstance(content, TextContent):
            # Handle text - provide instructions
            responses.append(
                TextContent(
                    text="I'm a calculator agent. Use function calls to perform calculations:\n"
                         "- calculate(a, b, operation) where operation is: add, subtract, multiply, divide"
                )
            )
    
    return Message(
        role=MessageRole.AGENT,
        content=responses
    )

# Create agent card
agent_card = {
    "name": "calculator_agent",
    "description": "An agent that performs mathematical calculations",
    "version": "1.0.0",
    "skills": ["mathematics", "calculation"]
}

# Create server
server = A2AServer(
    agent_card=agent_card,
    message_handler=handle_message
)

# Create FastAPI app
app = create_fastapi_app(server)

if __name__ == "__main__":
    print("Starting Calculator A2A Agent on http://localhost:8000")
    print("Agent Card: http://localhost:8000/.well-known/agent-card.json")
    uvicorn.run(app, host="0.0.0.0", port=8000)
