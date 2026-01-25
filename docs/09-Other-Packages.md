# Google ADK Other Packages Documentation

**File Path**: `docs/09-Other-Packages.md`  
**Packages Covered**: models, auth, examples, planners, flows, plugins, artifacts, events, telemetry, evaluation, features, cli, platform, runners, dependencies, errors, utils, version

This document covers additional Google ADK packages that provide supporting functionality.

## Models Package

The `google.adk.models` package provides LLM model abstractions and configurations.

### Key Classes

- **BaseLlm**: Base class for LLM models
- **Gemini**: Gemini model implementation
- **Gemma**: Gemma model implementation
- **LLMRegistry**: Registry for managing LLM models

### Example: Using Different Models

```python
from google.adk import Agent
from google.adk.models import Gemini

# Create agent with specific Gemini model
agent = Agent(
    name="gemini_agent",
    model=Gemini(model_name="gemini-1.5-pro"),
    instruction="You are a helpful assistant."
)

# Or use string shorthand
agent = Agent(
    name="flash_agent",
    model="gemini-1.5-flash",
    instruction="You are a helpful assistant."
)
```

## Auth Package

The `google.adk.auth` package provides authentication and authorization functionality.

### Key Classes

- **AuthConfig**: Authentication configuration
- **AuthHandler**: Handles authentication
- **OAuth2Auth**: OAuth2 authentication

### Example: Configuring Authentication

```python
from google.adk.auth import AuthConfig

auth_config = AuthConfig(
    api_key="your-api-key",
    # or
    credentials_path="/path/to/credentials.json"
)
```

## Examples Package

The `google.adk.examples` package provides example providers for few-shot learning.

### Key Classes

- **BaseExampleProvider**: Base class for example providers
- **Example**: Represents an example
- **VertexAiExampleStore**: Vertex AI-based example store

### Example: Using Examples

```python
from google.adk.examples import Example, BaseExampleProvider

# Create examples
examples = [
    Example(
        input="What is Python?",
        output="Python is a programming language."
    ),
    Example(
        input="What is JavaScript?",
        output="JavaScript is a programming language for web development."
    )
]

# Use with agent (examples are typically used internally)
```

## Planners Package

The `google.adk.planners` package provides planning capabilities for agents.

### Key Classes

- **BasePlanner**: Base class for planners
- **BuiltInPlanner**: Built-in planner implementation
- **PlanReActPlanner**: ReAct (Reasoning and Acting) planner

### Example: Using a Planner

```python
from google.adk import Agent
from google.adk.planners import PlanReActPlanner

# Create planner
planner = PlanReActPlanner()

# Create agent with planner
agent = Agent(
    name="planned_agent",
    model="gemini-1.5-flash",
    planner=planner,
    instruction="You are a planning assistant."
)
```

## Flows Package

The `google.adk.flows` package provides flow-based agent orchestration.

### Example: Using Flows

```python
from google.adk.flows import Flow

# Flows allow complex agent workflows
# (Implementation details depend on specific flow types)
```

## Plugins Package

The `google.adk.plugins` package provides plugin system for extending agent functionality.

### Key Classes

- **BasePlugin**: Base class for plugins
- **PluginManager**: Manages plugins
- **LoggingPlugin**: Plugin for logging
- **ReflectAndRetryToolPlugin**: Plugin for reflection and retry

### Example: Using Plugins

```python
from google.adk import Agent
from google.adk.plugins import LoggingPlugin, PluginManager

# Create plugin manager
plugin_manager = PluginManager()

# Add plugins
plugin_manager.add(LoggingPlugin())

# Use with agent (plugins are typically configured at app level)
```

## Artifacts Package

The `google.adk.artifacts` package provides artifact storage and retrieval.

### Key Classes

- **BaseArtifactService**: Base class for artifact services
- **FileArtifactService**: File-based artifact service
- **GcsArtifactService**: Google Cloud Storage artifact service
- **InMemoryArtifactService**: In-memory artifact service

### Example: Storing Artifacts

```python
from google.adk.artifacts import FileArtifactService

# Create artifact service
artifact_service = FileArtifactService(base_path="./artifacts")

# Store artifact
artifact_id = artifact_service.store(
    content="artifact content",
    metadata={"type": "result"}
)

# Retrieve artifact
artifact = artifact_service.retrieve(artifact_id)
```

## Events Package

The `google.adk.events` package provides event system for agent interactions.

### Key Classes

- **Event**: Represents an event
- **EventActions**: Event action types

### Example: Handling Events

```python
from google.adk.events import Event

# Events are typically handled internally by runners
# You can listen to events in your application
```

## Telemetry Package

The `google.adk.telemetry` package provides telemetry and tracing capabilities.

### Key Functions

- **trace_call_llm**: Trace LLM calls
- **trace_tool_call**: Trace tool calls
- **trace_send_data**: Trace data sending

### Example: Using Telemetry

```python
from google.adk.telemetry import trace_call_llm, trace_tool_call

# Telemetry is typically used internally
# but can be used for custom tracing
```

## Evaluation Package

The `google.adk.evaluation` package provides agent evaluation capabilities.

### Key Classes

- **AgentEvaluator**: Evaluates agent performance

### Example: Evaluating Agents

```python
from google.adk.evaluation import AgentEvaluator

# Create evaluator
evaluator = AgentEvaluator()

# Evaluate agent (implementation depends on evaluation type)
```

## Utils Package

The `google.adk.utils` package provides utility functions and helpers.

## CLI Package

The `google.adk.cli` package provides command-line interface tools.

### Usage

```bash
# Run an agent
adk run agent.py

# Start web UI
adk web --port 8000

# Other CLI commands
adk --help
```

## Best Practices

1. **Model Selection**: Choose appropriate models for your use case
2. **Authentication**: Configure authentication properly
3. **Plugins**: Use plugins to extend functionality
4. **Artifacts**: Store important outputs as artifacts
5. **Telemetry**: Enable telemetry for monitoring

## Related Documentation

- [Setup Guide](00-Setup-and-Installation.md)
- [Agents Package](01-Agents-Package.md)
- [Tools Package](02-Tools-Package.md)
