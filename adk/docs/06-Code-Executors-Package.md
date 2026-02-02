# Google ADK Code Executors Package Documentation

**File Path**: `docs/06-Code-Executors-Package.md`  
**Package**: `google.adk.code_executors`

## Overview

The `google.adk.code_executors` package provides safe code execution capabilities for agents. This allows agents to write and execute code dynamically, which is essential for tasks like data analysis, calculations, and automation.

## Key Classes

### BaseCodeExecutor

Abstract base class for all code executors.

### BuiltInCodeExecutor

Built-in code executor with safety features.

### UnsafeLocalCodeExecutor

Local code executor (use with caution).

## Example 1: Agent with Code Execution

Create an agent that can execute Python code:

```python
from google.adk import Agent
from google.adk.code_executors import BuiltInCodeExecutor
from google.adk.runners import Runner

# Create code executor
code_executor = BuiltInCodeExecutor()

# Create agent with code executor
agent = Agent(
    name="code_agent",
    description="An agent that can write and execute code",
    model="gemini-1.5-flash",
    instruction="""You are a coding assistant. 
    When users need calculations or data processing, 
    write Python code and execute it.""",
    code_executor=code_executor
)

runner = Runner(agent=agent)

async def main():
    async for event in runner.run("Calculate the factorial of 10")
        if hasattr(event, 'content'):
            print(event.content)

asyncio.run(main())
```

**Runnable Session:**

Save as `examples/code_executor_agent.py`:

```python
#!/usr/bin/env python3
"""Agent with code execution capabilities."""

import asyncio
from google.adk import Agent
from google.adk.code_executors import BuiltInCodeExecutor
from google.adk.runners import Runner

async def main():
    # Create code executor
    code_executor = BuiltInCodeExecutor()
    
    # Create agent with code execution
    agent = Agent(
        name="code_agent",
        description="An agent that can write and execute Python code",
        model="gemini-1.5-flash",
        instruction="""You are a coding assistant. 
        When users need calculations, data processing, or analysis,
        write Python code and execute it.
        Show the code and results clearly.""",
        code_executor=code_executor
    )
    
    runner = Runner(agent=agent)
    
    print("Code Agent: I can write and execute Python code!")
    print("Try: 'Calculate factorial of 10' or 'Generate first 10 Fibonacci numbers'")
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

## Example 2: Custom Code Executor

Create a custom code executor with specific restrictions:

```python
from google.adk.code_executors import BaseCodeExecutor, CodeExecutorContext

class RestrictedCodeExecutor(BaseCodeExecutor):
    """Code executor with restricted imports."""
    
    async def execute(
        self,
        code: str,
        context: CodeExecutorContext
    ) -> dict:
        """Execute code with restrictions."""
        # Only allow safe imports
        allowed_imports = ['math', 'datetime', 'json']
        
        # Check for disallowed imports
        if 'import' in code:
            for line in code.split('\n'):
                if 'import' in line:
                    import_name = line.split('import')[1].strip().split()[0]
                    if import_name not in allowed_imports:
                        return {
                            "error": f"Import '{import_name}' not allowed"
                        }
        
        # Execute with restrictions
        # ... implementation ...
        return {"result": "executed"}

# Use custom executor
agent = Agent(
    name="restricted_agent",
    code_executor=RestrictedCodeExecutor()
)
```

## Example 3: Data Analysis Agent

Create an agent that performs data analysis:

```python
from google.adk import Agent
from google.adk.code_executors import BuiltInCodeExecutor
from google.adk.runners import Runner

code_executor = BuiltInCodeExecutor()

data_agent = Agent(
    name="data_analyst",
    description="An agent that analyzes data",
    model="gemini-1.5-flash",
    instruction="""You are a data analyst. 
    When given data, write Python code to analyze it.
    Create visualizations, calculate statistics, and provide insights.""",
    code_executor=code_executor
)

runner = Runner(agent=data_agent)

async def main():
    data = [1, 2, 3, 4, 5, 6, 7, 8, 9, 10]
    query = f"Analyze this data: {data}. Calculate mean, median, and standard deviation."
    
    async for event in runner.run(query):
        if hasattr(event, 'content'):
            print(event.content)

asyncio.run(main())
```

## Safety Considerations

1. **Sandboxing**: Code executors should run in sandboxed environments
2. **Resource Limits**: Set memory and CPU limits
3. **Time Limits**: Set execution timeouts
4. **Import Restrictions**: Limit which modules can be imported
5. **File System**: Restrict file system access

## Best Practices

1. **Use BuiltInCodeExecutor**: Prefer built-in executor for safety
2. **Validate Input**: Validate code before execution
3. **Error Handling**: Handle execution errors gracefully
4. **Logging**: Log all code executions
5. **Testing**: Test code executors thoroughly

## Troubleshooting

### Issue: Code execution fails
- Check code syntax
- Verify allowed imports
- Check resource limits
- Review error messages

### Issue: Security concerns
- Use sandboxed executors
- Implement import restrictions
- Set resource limits
- Monitor executions

## Related Documentation

- [Agents Package](01-Agents-Package.md)
- [Tools Package](02-Tools-Package.md)
