# Google ADK A2A (Agent-to-Agent) Package Documentation

**File Path**: `docs/04-A2A-Package.md`  
**Package**: `google.adk.a2a`  
**Subpackages**: converters, executor, logs, utils

## Overview

The `google.adk.a2a` package enables agent-to-agent communication, allowing agents to communicate with each other over networks, share capabilities, and create distributed agent systems. A2A (Agent-to-Agent) protocol enables agents to discover, invoke, and collaborate with remote agents.

## Key Concepts

- **Agent Cards**: Metadata describing agent capabilities
- **Remote Agents**: Agents running on different servers/processes
- **A2A Protocol**: Standard protocol for agent communication
- **Agent Discovery**: Finding and connecting to remote agents

## Example 1: Creating a Remote Agent Server

Create an agent that can be accessed remotely:

```python
#!/usr/bin/env python3
"""Remote agent server example."""

from google.adk import Agent
from google.adk.apps import App
import uvicorn

# Create a specialized agent
math_agent = Agent(
    name="remote_math_agent",
    description="A remote agent specialized in mathematics",
    model="gemini-1.5-flash",
    instruction="You are a math expert. Solve mathematical problems step by step."
)

# Create an app with the agent
app = App(agent=math_agent)

# Run the server
if __name__ == "__main__":
    uvicorn.run(app, host="0.0.0.0", port=8000)
```

**Runnable Session:**

Save as `examples/remote_agent_server.py`:

```python
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
```

Run it:
```bash
python examples/remote_agent_server.py
```

## Example 2: Consuming a Remote Agent

Create an agent that uses a remote agent:

```python
from google.adk import Agent
from google.adk.a2a import RemoteA2aAgent
from google.adk.runners import Runner

# Create a remote agent reference
remote_math = RemoteA2aAgent(
    name="remote_math",
    agent_card_url="http://localhost:8000/agent_card.json"
)

# Create local agent that uses remote agent
local_agent = Agent(
    name="local_agent",
    description="Local agent that uses remote math agent",
    model="gemini-1.5-flash",
    instruction="You are a coordinator. Use remote_math for math questions.",
    sub_agents=[remote_math]
)

runner = Runner(agent=local_agent)

async def main():
    async for event in runner.run("What is 15 * 23?")
        if hasattr(event, 'content'):
            print(event.content)

asyncio.run(main())
```

**Runnable Session:**

Save as `examples/remote_agent_client.py`:

```python
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
```

## Example 3: Agent Card Configuration

Create an agent card (agent_card.json) for your remote agent:

```json
{
  "name": "remote_math_agent",
  "description": "A remote agent specialized in mathematics",
  "version": "1.0.0",
  "endpoint": "http://localhost:8000",
  "capabilities": [
    "mathematics",
    "problem_solving"
  ]
}
```

## Example 4: Multiple Remote Agents

Coordinate multiple remote agents:

```python
from google.adk import Agent
from google.adk.a2a import RemoteA2aAgent
from google.adk.runners import Runner

# Create multiple remote agent references
remote_math = RemoteA2aAgent(
    name="remote_math",
    agent_card_url="http://localhost:8000/agent_card.json"
)

remote_coding = RemoteA2aAgent(
    name="remote_coding",
    agent_card_url="http://localhost:8001/agent_card.json"
)

# Create coordinator
coordinator = Agent(
    name="coordinator",
    model="gemini-1.5-flash",
    instruction="""Route questions:
    - Math: transfer to remote_math
    - Coding: transfer to remote_coding""",
    sub_agents=[remote_math, remote_coding]
)

runner = Runner(agent=coordinator)
```

## Best Practices

1. **Agent Cards**: Always provide clear, accurate agent cards
2. **Error Handling**: Handle network errors gracefully
3. **Security**: Use HTTPS in production, authenticate requests
4. **Discovery**: Implement agent discovery mechanisms
5. **Versioning**: Version your agent cards and APIs

## Troubleshooting

### Issue: Cannot connect to remote agent
- Verify remote server is running
- Check agent_card_url is correct
- Ensure network connectivity
- Check firewall settings

### Issue: Agent card not found
- Verify agent_card.json exists at the URL
- Check JSON format is valid
- Ensure server serves the card correctly

## Related Documentation

- [Agents Package](01-Agents-Package.md)
- [Apps Package](05-Apps-Package.md)

## References

- [A2A Protocol Documentation](https://google.github.io/adk-docs/a2a/)
