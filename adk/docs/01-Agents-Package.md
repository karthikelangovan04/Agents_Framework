# Google ADK Agents Package Documentation

**File Path**: `docs/01-Agents-Package.md`  
**Package**: `google.adk.agents`

## Overview

The `google.adk.agents` package is the core of Google ADK, providing the fundamental building blocks for creating AI agents. Agents are intelligent entities that can process user inputs, use tools, interact with LLMs, and coordinate with other agents.

## Package Structure

The agents package contains the following key components:

- **Agent (LlmAgent)**: The main LLM-based agent class
- **BaseAgent**: Base class for all agent types
- **InvocationContext**: Context for agent invocations
- **LiveRequest/LiveRequestQueue**: For live/streaming interactions
- **SequentialAgent**: For sequential agent execution
- **ParallelAgent**: For parallel agent execution
- **LoopAgent**: For looping/iterative agent behavior

## Key Classes

### Agent (LlmAgent)

The `Agent` class (aliased from `LlmAgent`) is the primary class for creating LLM-powered agents.

#### Agent vs LlmAgent: What’s the Difference?

When reading ADK code or docs you may see either `Agent` or `LlmAgent`. In the Google ADK Python library they refer to the **same class**:

| Aspect | `Agent` | `LlmAgent` |
|--------|--------|-------------|
| **Definition** | Type alias for `LlmAgent` | The actual class (`class LlmAgent(BaseAgent)`) |
| **Source** | `google.adk.agents.llm_agent`: `Agent: TypeAlias = LlmAgent` | `google.adk.agents.llm_agent`: `class LlmAgent(BaseAgent)` |
| **Imports** | `from google.adk import Agent` or `from google.adk.agents import Agent` | `from google.adk.agents import LlmAgent` |
| **Usage** | `root_agent = Agent(name="...", model="...", ...)` | `root_agent = LlmAgent(name="...", model="...", ...)` |
| **Behavior** | Identical — both construct the same LLM-based agent | Identical — same class |

**Summary:**

- **`LlmAgent`** is the real class name; it subclasses `BaseAgent` and implements the LLM-based agent (model, instructions, tools, callbacks).
- **`Agent`** is a **type alias** for `LlmAgent` (see `adk-python-lib/src/google/adk/agents/llm_agent.py`: `Agent: TypeAlias = LlmAgent`). It exists so you can write `from google.adk import Agent` and use the shorter name.
- There is **no functional difference**. Use `Agent` for brevity or `LlmAgent` when you want the explicit class name (e.g. type hints, `isinstance(x, LlmAgent)`).

**Example (equivalent):**

```python
# Option 1: Top-level convenience (docs and simple apps)
from google.adk import Agent
root_agent = Agent(name="my_agent", model="gemini-2.5-flash", instruction="...")

# Option 2: Explicit class name (e.g. deal_builder.py, type hints)
from google.adk.agents import Agent, LlmAgent
deal_builder_agent = LlmAgent(name="deal_builder", model="...", tools=[...])
# Agent and LlmAgent are the same type here
```

#### Constructor Parameters

```python
Agent(
    name: str,                                    # Required: Unique agent name
    description: str = '',                        # Agent description
    model: Union[str, BaseLlm] = '',             # LLM model to use (default: 'gemini-2.5-flash')
    instruction: Union[str, Callable] = '',       # Agent instructions
    global_instruction: Union[str, Callable] = '', # Global instructions
    tools: list = [],                            # List of tools available to agent
    sub_agents: list[BaseAgent] = [],            # Child agents
    parent_agent: Optional[BaseAgent] = None,     # Parent agent
    # ... many more configuration options
)
```

#### Key Methods

- `run_async(parent_context)`: Run agent asynchronously via text-based conversation
- `run_live(parent_context)`: Run agent via video/audio-based conversation
- `find_agent(name)`: Find an agent by name in the agent tree
- `clone(update)`: Create a copy of the agent with optional updates

#### Important: Agent Instantiation vs Execution

**Creating an `Agent` instance is just instantiation** - it defines the agent's configuration (model, instructions, tools, etc.) but **does not execute it**. 

To actually run an agent, you need a **`Runner`**:

```python
# This is just instantiation (configuration)
agent = Agent(
    name="simple_agent",
    model="gemini-1.5-flash",
    instruction="You are a helpful assistant."
)

# This creates the execution engine
from google.adk.runners import Runner
runner = Runner(agent=agent, session_service=session_service)

# This actually executes the agent
async for event in runner.run_async(...):
    process(event)
```

**For detailed information about the Runner and how it executes agents, see [Runners Package Documentation](10-Runners-Package.md).**

## Example 1: Simple Agent

Create a basic agent that responds to user queries:

```python
from google.adk import Agent
from google.adk.runners import Runner

# Create a simple agent
agent = Agent(
    name="simple_agent",
    description="A simple helpful assistant",
    model="gemini-1.5-flash",
    instruction="You are a helpful assistant. Answer questions clearly and concisely."
)

# Create a runner
runner = Runner(agent=agent)

# Run the agent
async def main():
    async for event in runner.run("What is the capital of France?")
        if event.type == "agent_response":
            print(event.content)

# Run it
import asyncio
asyncio.run(main())
```

**Runnable Session:**

Save this as `examples/simple_agent.py`:

```python
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
```

Run it:
```bash
python examples/simple_agent.py
```

## Example 2: Agent with Tools

Create an agent that can use tools to perform actions:

```python
from google.adk import Agent
from google.adk.tools import Tool
from google.adk.runners import Runner

# Define a custom tool
def get_current_time():
    """Get the current time."""
    from datetime import datetime
    return datetime.now().strftime("%Y-%m-%d %H:%M:%S")

def calculate(expression: str) -> str:
    """Evaluate a mathematical expression safely."""
    try:
        result = eval(expression, {"__builtins__": {}}, {})
        return str(result)
    except Exception as e:
        return f"Error: {str(e)}"

# Create agent with tools
agent = Agent(
    name="tool_agent",
    description="An agent that can use tools",
    model="gemini-1.5-flash",
    instruction="You are a helpful assistant with access to tools. Use them when appropriate.",
    tools=[get_current_time, calculate]
)

# Use the agent
runner = Runner(agent=agent)

async def main():
    async for event in runner.run("What time is it now?")
        if hasattr(event, 'content'):
            print(event.content)

asyncio.run(main())
```

**Runnable Session:**

Save as `examples/tool_agent.py`:

```python
#!/usr/bin/env python3
"""Agent with tools example."""

import asyncio
from google.adk import Agent
from google.adk.tools import Tool
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
```

## Example 3: Multi-Agent System (Sub-Agents)

Create a parent agent with specialized sub-agents:

```python
from google.adk import Agent
from google.adk.runners import Runner

# Create specialized sub-agents
math_agent = Agent(
    name="math_specialist",
    description="Specializes in mathematical problems",
    model="gemini-1.5-flash",
    instruction="You are a math expert. Solve mathematical problems step by step."
)

coding_agent = Agent(
    name="coding_specialist",
    description="Specializes in programming questions",
    model="gemini-1.5-flash",
    instruction="You are a programming expert. Help with code, debugging, and best practices."
)

# Create parent agent that routes to sub-agents
parent_agent = Agent(
    name="router_agent",
    description="Routes questions to appropriate specialists",
    model="gemini-1.5-flash",
    instruction="""You are a router agent. Analyze the user's question and:
    - For math questions, transfer to math_specialist
    - For coding questions, transfer to coding_specialist
    - Otherwise, answer directly if you can.""",
    sub_agents=[math_agent, coding_agent]
)

# Use the parent agent
runner = Runner(agent=parent_agent)

async def main():
    async for event in runner.run("What is 15 * 23?")
        if hasattr(event, 'content'):
            print(event.content)

asyncio.run(main())
```

**Runnable Session:**

Save as `examples/multi_agent.py`:

```python
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
```

## Example 4: Agent with Callbacks

Use callbacks to monitor and modify agent behavior:

```python
from google.adk import Agent
from google.adk.runners import Runner

# Define callbacks
async def before_tool_callback(tool, args, context):
    """Called before a tool is executed."""
    print(f"[DEBUG] About to call tool: {tool.name}")
    print(f"[DEBUG] Arguments: {args}")
    return None  # Return None to proceed, or dict to override

async def after_tool_callback(tool, args, context, result):
    """Called after a tool is executed."""
    print(f"[DEBUG] Tool {tool.name} returned: {result}")
    return None  # Return None to use result as-is, or dict to modify

# Create agent with callbacks
agent = Agent(
    name="monitored_agent",
    description="An agent with monitoring callbacks",
    model="gemini-1.5-flash",
    instruction="You are a helpful assistant.",
    tools=[get_current_time],  # From previous example
    before_tool_callback=before_tool_callback,
    after_tool_callback=after_tool_callback
)

runner = Runner(agent=agent)

async def main():
    async for event in runner.run("What time is it?")
        if hasattr(event, 'content'):
            print(event.content)

asyncio.run(main())
```

## Example 5: Agent with Input/Output Schemas

Use Pydantic schemas for structured input and output:

```python
from google.adk import Agent
from google.adk.runners import Runner
from pydantic import BaseModel

# Define input schema
class UserQuery(BaseModel):
    question: str
    context: str = ""

# Define output schema
class AgentResponse(BaseModel):
    answer: str
    confidence: float
    sources: list[str] = []

# Create agent with schemas
agent = Agent(
    name="structured_agent",
    description="An agent with structured input/output",
    model="gemini-1.5-flash",
    instruction="Answer questions clearly and provide confidence scores.",
    input_schema=UserQuery,
    output_schema=AgentResponse
)

runner = Runner(agent=agent)

async def main():
    query = UserQuery(question="What is Python?", context="programming")
    async for event in runner.run(query.model_dump_json()):
        if hasattr(event, 'content'):
            print(event.content)

asyncio.run(main())
```

## Advanced Features

### Sequential Agent Execution

Execute agents in sequence:

```python
from google.adk.agents import SequentialAgent

sequential = SequentialAgent(
    name="pipeline",
    agents=[agent1, agent2, agent3]
)
```

### Parallel Agent Execution

Execute agents in parallel:

```python
from google.adk.agents import ParallelAgent

parallel = ParallelAgent(
    name="parallel_team",
    agents=[agent1, agent2, agent3]
)
```

### Agent Transfer

Agents can transfer control to other agents:

```python
from google.adk.tools import transfer_to_agent

# In agent instruction:
# "For complex questions, use transfer_to_agent('specialist_agent')"
```

## Best Practices

1. **Naming**: Use descriptive, unique names for agents
2. **Instructions**: Write clear, specific instructions
3. **Tools**: Only provide tools that are relevant to the agent's purpose
4. **Sub-agents**: Use sub-agents for specialization and modularity
5. **Error Handling**: Implement callbacks for error handling
6. **Testing**: Test agents with various inputs before deployment

## Common Patterns

### Pattern 1: Router Agent
```python
router = Agent(
    name="router",
    instruction="Route to appropriate specialist",
    sub_agents=[specialist1, specialist2]
)
```

### Pattern 2: Tool-Enhanced Agent
```python
agent = Agent(
    name="assistant",
    tools=[search_tool, calculator_tool, api_tool]
)
```

### Pattern 3: Hierarchical Agent System
```python
root = Agent(
    name="root",
    sub_agents=[
        Agent(name="level1", sub_agents=[Agent(name="level2")])
    ]
)
```

## Troubleshooting

### Issue: Agent not responding
- Check model name is correct
- Verify API key is set
- Check instruction clarity

### Issue: Tool not being called
- Ensure tool has proper docstring
- Check tool is in agent's tools list
- Verify tool signature matches expected format

### Issue: Sub-agent not receiving transfer
- Check agent name matches exactly
- Verify sub_agents list includes the target agent
- Check transfer_to_agent syntax

## Related Documentation

- [Runners Package](10-Runners-Package.md) - **How agents are executed**
- [Tools Package](02-Tools-Package.md)
- [Sessions Package](07-Sessions-Package.md)
- [Memory Package](08-Memory-Package.md)
- [A2A Package](04-A2A-Package.md)

## References

- [Google ADK Agents Documentation](https://google.github.io/adk-docs/agents/)
- [Agent Configuration Guide](https://google.github.io/adk-docs/agents/config/)
