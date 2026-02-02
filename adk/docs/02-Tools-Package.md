# Google ADK Tools Package Documentation

**File Path**: `docs/02-Tools-Package.md`  
**Package**: `google.adk.tools`  
**Subpackages**: bigquery, bigtable, spanner, pubsub, google_api_tool, mcp_tool, openapi_tool, apihub_tool, application_integration_tool, retrieval, computer_use

## Overview

The `google.adk.tools` package provides a comprehensive set of tools that agents can use to interact with the world, perform computations, access APIs, and extend their capabilities. Tools are essential for making agents functional and useful beyond just text generation.

## Package Structure

The tools package includes:

- **BaseTool**: Base class for all tools
- **FunctionTool**: Convert Python functions into tools
- **AgentTool**: Tools that invoke other agents
- **Built-in Tool Sets**: Google Search, BigQuery, Vertex AI Search, etc.
- **Special Tools**: TransferToAgentTool, exit_loop, etc.

## Key Classes

### BaseTool

The abstract base class for all tools. All tools inherit from this class.

```python
BaseTool(
    name: str,                    # Tool name
    description: str,             # Tool description (used by LLM)
    is_long_running: bool = False, # Whether tool takes long time
    custom_metadata: dict = None   # Custom metadata
)
```

### FunctionTool

Converts Python functions into tools automatically.

## Example 1: Simple Function Tool

Convert a Python function into a tool:

```python
from google.adk import Agent
from google.adk.tools import FunctionTool
from google.adk.runners import Runner

# Define a simple function
def get_weather(city: str) -> str:
    """Get the weather for a given city.
    
    Args:
        city: The name of the city
    
    Returns:
        Weather information as a string
    """
    # In a real implementation, this would call a weather API
    return f"The weather in {city} is sunny, 72°F"

# Create agent with the tool
agent = Agent(
    name="weather_agent",
    description="An agent that can check weather",
    model="gemini-1.5-flash",
    instruction="You are a weather assistant. Use the get_weather tool to check weather.",
    tools=[get_weather]  # FunctionTool automatically wraps this
)

# Use the agent
runner = Runner(agent=agent)

async def main():
    async for event in runner.run("What's the weather in San Francisco?")
        if hasattr(event, 'content'):
            print(event.content)

asyncio.run(main())
```

**Runnable Session:**

Save as `examples/weather_tool.py`:

```python
#!/usr/bin/env python3
"""Weather tool example."""

import asyncio
from google.adk import Agent
from google.adk.runners import Runner

def get_weather(city: str) -> str:
    """Get the weather for a given city.
    
    Args:
        city: The name of the city (e.g., "San Francisco", "New York")
    
    Returns:
        Weather information as a string
    """
    # Simulated weather data - in production, call a real API
    weather_data = {
        "San Francisco": "Sunny, 65°F",
        "New York": "Cloudy, 58°F",
        "London": "Rainy, 52°F",
        "Tokyo": "Clear, 75°F"
    }
    return weather_data.get(city, f"Weather data not available for {city}")

async def main():
    agent = Agent(
        name="weather_agent",
        description="An agent that can check weather",
        model="gemini-1.5-flash",
        instruction="You are a helpful weather assistant. Use the get_weather tool to check weather for cities.",
        tools=[get_weather]
    )
    
    runner = Runner(agent=agent)
    
    print("Weather Agent: Hello! I can check the weather for any city.")
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

## Example 2: Multiple Tools

Create an agent with multiple tools:

```python
from google.adk import Agent
from google.adk.runners import Runner
from datetime import datetime
import math

# Define multiple tools
def get_current_time() -> str:
    """Get the current date and time."""
    return datetime.now().strftime("%Y-%m-%d %H:%M:%S")

def calculate(expression: str) -> str:
    """Evaluate a mathematical expression safely.
    
    Args:
        expression: A mathematical expression like '2 + 2' or 'sqrt(16)'
    
    Returns:
        The result as a string
    """
    try:
        # Safe math operations
        safe_dict = {
            "__builtins__": {},
            "abs": abs,
            "round": round,
            "min": min,
            "max": max,
            "sum": sum,
            "pow": pow,
            "sqrt": math.sqrt,
            "sin": math.sin,
            "cos": math.cos,
            "tan": math.tan,
            "pi": math.pi,
            "e": math.e
        }
        result = eval(expression, safe_dict, {})
        return str(result)
    except Exception as e:
        return f"Error: {str(e)}"

def convert_units(value: float, from_unit: str, to_unit: str) -> str:
    """Convert between units.
    
    Args:
        value: The numeric value to convert
        from_unit: Source unit (e.g., 'miles', 'km', 'celsius', 'fahrenheit')
        to_unit: Target unit
    
    Returns:
        Converted value as string
    """
    conversions = {
        ('miles', 'km'): lambda x: x * 1.60934,
        ('km', 'miles'): lambda x: x / 1.60934,
        ('celsius', 'fahrenheit'): lambda x: (x * 9/5) + 32,
        ('fahrenheit', 'celsius'): lambda x: (x - 32) * 5/9,
    }
    
    key = (from_unit.lower(), to_unit.lower())
    if key in conversions:
        result = conversions[key](value)
        return f"{value} {from_unit} = {result:.2f} {to_unit}"
    return f"Conversion from {from_unit} to {to_unit} not supported"

# Create agent with multiple tools
agent = Agent(
    name="multi_tool_agent",
    description="An agent with multiple utility tools",
    model="gemini-1.5-flash",
    instruction="You are a helpful assistant with access to time, calculator, and unit conversion tools.",
    tools=[get_current_time, calculate, convert_units]
)

runner = Runner(agent=agent)

async def main():
    async for event in runner.run("What time is it and convert 100 km to miles")
        if hasattr(event, 'content'):
            print(event.content)

asyncio.run(main())
```

**Runnable Session:**

Save as `examples/multi_tool_agent.py`:

```python
#!/usr/bin/env python3
"""Multi-tool agent example."""

import asyncio
import math
from datetime import datetime
from google.adk import Agent
from google.adk.runners import Runner

def get_current_time() -> str:
    """Get the current date and time in a readable format."""
    return datetime.now().strftime("%Y-%m-%d %H:%M:%S")

def calculate(expression: str) -> str:
    """Evaluate a mathematical expression safely.
    
    Args:
        expression: A mathematical expression like '2 + 2' or 'sqrt(16)'
    
    Returns:
        The result as a string
    """
    try:
        safe_dict = {
            "__builtins__": {},
            "abs": abs, "round": round, "min": min, "max": max,
            "sum": sum, "pow": pow, "sqrt": math.sqrt,
            "sin": math.sin, "cos": math.cos, "tan": math.tan,
            "pi": math.pi, "e": math.e
        }
        result = eval(expression, safe_dict, {})
        return str(result)
    except Exception as e:
        return f"Error: {str(e)}"

def convert_units(value: float, from_unit: str, to_unit: str) -> str:
    """Convert between units.
    
    Args:
        value: The numeric value to convert
        from_unit: Source unit (miles, km, celsius, fahrenheit)
        to_unit: Target unit
    """
    conversions = {
        ('miles', 'km'): lambda x: x * 1.60934,
        ('km', 'miles'): lambda x: x / 1.60934,
        ('celsius', 'fahrenheit'): lambda x: (x * 9/5) + 32,
        ('fahrenheit', 'celsius'): lambda x: (x - 32) * 5/9,
    }
    
    key = (from_unit.lower(), to_unit.lower())
    if key in conversions:
        result = conversions[key](value)
        return f"{value} {from_unit} = {result:.2f} {to_unit}"
    return f"Conversion from {from_unit} to {to_unit} not supported"

async def main():
    agent = Agent(
        name="multi_tool_agent",
        description="An agent with multiple utility tools",
        model="gemini-1.5-flash",
        instruction="You are a helpful assistant with access to time, calculator, and unit conversion tools. Use them appropriately.",
        tools=[get_current_time, calculate, convert_units]
    )
    
    runner = Runner(agent=agent)
    
    print("Multi-Tool Agent: I can help with time, calculations, and unit conversions!")
    print("Try: 'What time is it?', 'Calculate 15 * 23', or 'Convert 100 km to miles'")
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

## Example 3: Custom BaseTool

Create a custom tool by extending BaseTool:

```python
from google.adk.tools import BaseTool, ToolContext
from google.adk.models import LlmRequest

class DatabaseQueryTool(BaseTool):
    """A tool for querying a database."""
    
    def __init__(self):
        super().__init__(
            name="query_database",
            description="Query a database with SQL. Returns results as JSON."
        )
        # Initialize database connection here
    
    async def run_async(self, *, args: dict, tool_context: ToolContext) -> dict:
        """Execute the database query."""
        query = args.get("query", "")
        # Execute query and return results
        return {"results": [], "row_count": 0}

# Use the custom tool
agent = Agent(
    name="db_agent",
    tools=[DatabaseQueryTool()]
)
```

## Example 4: Google Search Tool

Use built-in Google Search tool:

```python
from google.adk import Agent
from google.adk.tools import google_search

agent = Agent(
    name="search_agent",
    description="An agent that can search the web",
    model="gemini-1.5-flash",
    instruction="You are a helpful assistant with web search capabilities.",
    tools=[google_search]
)

runner = Runner(agent=agent)

async def main():
    async for event in runner.run("Search for the latest news about AI")
        if hasattr(event, 'content'):
            print(event.content)

asyncio.run(main())
```

## Example 5: Agent Tool (Tool that Calls Other Agents)

Create a tool that invokes another agent:

```python
from google.adk import Agent
from google.adk.tools import AgentTool
from google.adk.runners import Runner

# Create a specialized agent
specialist = Agent(
    name="specialist",
    model="gemini-1.5-flash",
    instruction="You are a specialist in complex problem solving."
)

# Create an agent tool
specialist_tool = AgentTool(
    agent=specialist,
    name="consult_specialist",
    description="Consult with a specialist for complex problems"
)

# Create main agent with the agent tool
main_agent = Agent(
    name="main_agent",
    model="gemini-1.5-flash",
    instruction="You are a general assistant. Use consult_specialist for complex questions.",
    tools=[specialist_tool]
)

runner = Runner(agent=main_agent)

async def main():
    async for event in runner.run("Solve this complex problem: ...")
        if hasattr(event, 'content'):
            print(event.content)

asyncio.run(main())
```

## Example 6: Transfer to Agent Tool

Allow agents to transfer control to other agents:

```python
from google.adk import Agent
from google.adk.tools import transfer_to_agent
from google.adk.runners import Runner

# Create sub-agents
math_agent = Agent(
    name="math_agent",
    model="gemini-1.5-flash",
    instruction="You are a math expert."
)

coding_agent = Agent(
    name="coding_agent",
    model="gemini-1.5-flash",
    instruction="You are a coding expert."
)

# Create router agent with transfer capability
router = Agent(
    name="router",
    model="gemini-1.5-flash",
    instruction="""Route questions appropriately:
    - Math questions: use transfer_to_agent('math_agent')
    - Coding questions: use transfer_to_agent('coding_agent')""",
    sub_agents=[math_agent, coding_agent],
    tools=[transfer_to_agent]  # Enable transfer functionality
)

runner = Runner(agent=router)

async def main():
    async for event in runner.run("What is 15 * 23?")
        if hasattr(event, 'content'):
            print(event.content)

asyncio.run(main())
```

## Example 7: Long-Running Tool

Create a tool that takes a long time to execute:

```python
from google.adk.tools import BaseTool, FunctionTool, ToolContext
import asyncio

async def long_running_task(data: str) -> str:
    """Process data - this takes a while."""
    await asyncio.sleep(5)  # Simulate long operation
    return f"Processed: {data}"

# Mark as long-running
long_tool = FunctionTool(
    func=long_running_task,
    is_long_running=True
)

agent = Agent(
    name="async_agent",
    tools=[long_tool]
)
```

## Built-in Tool Sets

Google ADK provides several built-in tool sets:

### Google Search
```python
from google.adk.tools import google_search

agent = Agent(tools=[google_search])
```

### Vertex AI Search
```python
from google.adk.tools import VertexAiSearchTool

search_tool = VertexAiSearchTool(
    data_store="projects/.../locations/.../dataStores/..."
)
agent = Agent(tools=[search_tool])
```

### BigQuery Tool
```python
from google.adk.tools.bigquery import BigQueryTool

bq_tool = BigQueryTool(project_id="your-project")
agent = Agent(tools=[bq_tool])
```

### MCP Tools
```python
from google.adk.tools import McpToolset

mcp_tools = McpToolset(server_url="http://localhost:8000")
agent = Agent(tools=[mcp_tools])
```

## Tool Best Practices

1. **Clear Descriptions**: Write detailed docstrings - the LLM uses these to decide when to call tools
2. **Type Hints**: Use type hints for better parameter understanding
3. **Error Handling**: Handle errors gracefully and return informative messages
4. **Idempotency**: Make tools idempotent when possible
5. **Validation**: Validate inputs before processing
6. **Documentation**: Document all parameters and return values

## Tool Patterns

### Pattern 1: Function Wrapper
```python
def my_function(param: str) -> str:
    """Tool description."""
    return result

agent = Agent(tools=[my_function])
```

### Pattern 2: Custom Tool Class
```python
class MyTool(BaseTool):
    def __init__(self):
        super().__init__(name="my_tool", description="...")
    
    async def run_async(self, *, args, tool_context):
        return result
```

### Pattern 3: Tool with Context
```python
async def context_aware_tool(query: str, tool_context: ToolContext) -> str:
    """Tool that uses context."""
    session_id = tool_context.session_id
    # Use session context
    return result
```

## Troubleshooting

### Issue: Tool not being called
- Check tool description is clear and relevant
- Verify function signature matches expected format
- Ensure tool is in agent's tools list
- Check docstring includes parameter descriptions

### Issue: Tool errors
- Add try/except blocks in tool functions
- Return error messages as strings
- Log errors for debugging

### Issue: Tool taking too long
- Mark long-running tools with `is_long_running=True`
- Consider async implementations
- Add timeout handling

## Related Documentation

- [Agents Package](01-Agents-Package.md)
- [Code Executors Package](06-Code-Executors-Package.md)
- [A2A Package](04-A2A-Package.md)

## References

- [Google ADK Tools Documentation](https://google.github.io/adk-docs/tools/)
- [Tool Configuration Guide](https://google.github.io/adk-docs/tools/config/)
