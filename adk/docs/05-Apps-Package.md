# Google ADK Apps Package Documentation

**File Path**: `docs/05-Apps-Package.md`  
**Package**: `google.adk.apps`

## Overview

The `google.adk.apps` package provides the `App` class for creating web applications and APIs that expose agents. This is essential for deploying agents as services and integrating them into web applications.

## Key Classes

### App

The main class for creating agent-based web applications.

```python
App(
    agent: BaseAgent,              # The root agent
    resumability_config: Optional[ResumabilityConfig] = None
)
```

## Example 1: Simple Web App

Create a basic web application with an agent:

```python
#!/usr/bin/env python3
"""Simple web app with agent."""

from google.adk import Agent
from google.adk.apps import App
import uvicorn

# Create agent
agent = Agent(
    name="web_agent",
    description="A web-based assistant",
    model="gemini-1.5-flash",
    instruction="You are a helpful web assistant."
)

# Create app
app = App(agent=agent)

# Run server
if __name__ == "__main__":
    uvicorn.run(app, host="0.0.0.0", port=8000)
```

**Runnable Session:**

Save as `examples/web_app.py`:

```python
#!/usr/bin/env python3
"""Web application example."""

from google.adk import Agent
from google.adk.apps import App
import uvicorn

# Create agent
agent = Agent(
    name="web_agent",
    description="A web-based assistant",
    model="gemini-1.5-flash",
    instruction="You are a helpful web assistant. Answer questions clearly."
)

# Create FastAPI app
app = App(agent=agent)

if __name__ == "__main__":
    print("Starting web app on http://localhost:8000")
    print("Visit http://localhost:8000/docs for API documentation")
    uvicorn.run(app, host="0.0.0.0", port=8000)
```

Run it:
```bash
python examples/web_app.py
```

Then visit `http://localhost:8000/docs` for interactive API documentation.

## Example 2: App with Resumability

Create an app with session resumability:

```python
from google.adk import Agent
from google.adk.apps import App, ResumabilityConfig
from google.adk.sessions import VertexAiSessionService

# Create session service
session_service = VertexAiSessionService(
    project_id="your-project-id",
    location="us-central1"
)

# Create resumability config
resumability_config = ResumabilityConfig(
    session_service=session_service
)

# Create agent
agent = Agent(
    name="resumable_agent",
    model="gemini-1.5-flash",
    instruction="You are a helpful assistant."
)

# Create app with resumability
app = App(
    agent=agent,
    resumability_config=resumability_config
)
```

## Example 3: Multi-Agent App

Create an app with multiple agents:

```python
from google.adk import Agent
from google.adk.apps import App

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

# Create root agent
root_agent = Agent(
    name="root",
    model="gemini-1.5-flash",
    instruction="Route to appropriate specialist.",
    sub_agents=[math_agent, coding_agent]
)

# Create app
app = App(agent=root_agent)
```

## API Endpoints

When you create an App, it automatically provides:

- `POST /chat` - Chat with the agent
- `GET /agent_card.json` - Get agent card (for A2A)
- `GET /docs` - Interactive API documentation
- `GET /health` - Health check endpoint

## Example 4: Custom API Integration

Use the app in your own FastAPI application:

```python
from fastapi import FastAPI
from google.adk import Agent
from google.adk.apps import App

# Create your FastAPI app
fastapi_app = FastAPI()

# Create ADK app
adk_agent = Agent(
    name="api_agent",
    model="gemini-1.5-flash",
    instruction="You are an API assistant."
)

adk_app = App(agent=adk_agent)

# Mount ADK app
fastapi_app.mount("/agent", adk_app)

@fastapi_app.get("/")
def root():
    return {"message": "API with agent at /agent"}
```

## Best Practices

1. **Error Handling**: Implement proper error handling
2. **Authentication**: Add authentication for production
3. **Rate Limiting**: Implement rate limiting
4. **Logging**: Add comprehensive logging
5. **Monitoring**: Set up monitoring and alerts

## Related Documentation

- [Agents Package](01-Agents-Package.md)
- [Sessions Package](07-Sessions-Package.md)
- [A2A Package](04-A2A-Package.md)
