# Python A2A Workflows Guide

**File Path**: `A2A/docs/04-Workflows.md`

## Overview

Python A2A provides a powerful workflow system for orchestrating complex agent interactions. Workflows allow you to define multi-step processes with conditional branching, parallel execution, and automatic agent routing.

## Basic Workflow

Create a simple workflow:

```python
from python_a2a import Flow, A2AClient, Message, TextContent, MessageRole

# Create clients for different agents
math_client = A2AClient(endpoint_url="http://localhost:8000")
code_client = A2AClient(endpoint_url="http://localhost:8001")

# Create workflow
flow = Flow()

# Add steps
flow.add_step(
    QueryStep(
        agent=math_client,
        query="What is 2 + 2?"
    )
).add_step(
    QueryStep(
        agent=code_client,
        query="Write a Python function to add two numbers"
    )
)

# Execute workflow
result = await flow.execute()
```

## Conditional Branching

Route to different agents based on conditions:

```python
from python_a2a import Flow, ConditionStep, QueryStep

flow = Flow()

flow.add_step(
    ConditionStep(
        condition=lambda context: context.get("user_type") == "premium",
        true_step=QueryStep(
            agent=premium_agent,
            query="Premium response"
        ),
        false_step=QueryStep(
            agent=basic_agent,
            query="Basic response"
        )
    )
)
```

## Parallel Execution

Execute multiple steps in parallel:

```python
from python_a2a import Flow, ParallelStep, QueryStep

flow = Flow()

flow.add_step(
    ParallelStep(
        steps=[
            QueryStep(agent=math_agent, query="Calculate 5 + 3"),
            QueryStep(agent=weather_agent, query="What's the weather?"),
            QueryStep(agent=news_agent, query="Latest news")
        ]
    )
)

result = await flow.execute()
```

## Auto-Routing

Automatically route to the best agent:

```python
from python_a2a import Flow, AutoRouteStep, AIAgentRouter

# Create router
router = AIAgentRouter(
    agents=[
        {"name": "math_agent", "skills": ["mathematics"]},
        {"name": "code_agent", "skills": ["programming"]},
        {"name": "weather_agent", "skills": ["weather"]}
    ]
)

flow = Flow()
flow.add_step(
    AutoRouteStep(
        router=router,
        query="What is 2 + 2?"
    )
)
```

## Workflow Context

Pass context between steps:

```python
from python_a2a import Flow, QueryStep, WorkflowContext

flow = Flow()

def process_step(context: WorkflowContext):
    # Access previous results
    previous_result = context.get("previous_step_result")
    
    # Update context
    context["processed"] = True
    
    return QueryStep(
        agent=next_agent,
        query=f"Based on {previous_result}, what should I do next?"
    )

flow.add_step(process_step)
```

## Function Steps

Call functions within workflows:

```python
from python_a2a import Flow, FunctionStep

def calculate_total(items):
    return sum(item["price"] for item in items)

flow = Flow()
flow.add_step(
    FunctionStep(
        function=calculate_total,
        args=[{"price": 10}, {"price": 20}, {"price": 30}]
    )
)
```

## Error Handling in Workflows

Handle errors gracefully:

```python
from python_a2a import Flow, QueryStep

flow = Flow()

flow.add_step(
    QueryStep(
        agent=math_agent,
        query="Calculate 10 / 0"
    )
).on_error(
    lambda error: QueryStep(
        agent=error_handler_agent,
        query=f"Error occurred: {error}"
    )
)
```

## Complete Workflow Example

```python
from python_a2a import Flow, QueryStep, ConditionStep, ParallelStep
import asyncio

async def main():
    # Create clients
    math_client = A2AClient(endpoint_url="http://localhost:8000")
    code_client = A2AClient(endpoint_url="http://localhost:8001")
    
    # Create workflow
    flow = Flow()
    
    # Step 1: Check if it's a math question
    flow.add_step(
        ConditionStep(
            condition=lambda ctx: "calculate" in ctx.get("query", "").lower(),
            true_step=QueryStep(
                agent=math_client,
                query=lambda ctx: ctx["query"]
            ),
            false_step=QueryStep(
                agent=code_client,
                query=lambda ctx: ctx["query"]
            )
        )
    )
    
    # Execute
    result = await flow.execute({"query": "What is 5 + 3?"})
    print(result)

asyncio.run(main())
```

## Next Steps

- Check out [Advanced Features](05-Advanced-Features.md)
- See workflow examples in `A2A/examples/`
