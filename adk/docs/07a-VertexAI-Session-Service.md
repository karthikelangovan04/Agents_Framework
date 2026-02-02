# Vertex AI Session Service - Complete Guide

**File Path**: `docs/07a-VertexAI-Session-Service.md`  
**Package**: `google.adk.sessions.VertexAiSessionService`

## Overview

`VertexAiSessionService` is a production-ready session service that uses **Google Cloud Vertex AI Agent Engine** to store and manage conversation sessions. It provides enterprise-grade session persistence, scalability, and integration with Google Cloud services.

Unlike `DatabaseSessionService` which uses SQL databases, `VertexAiSessionService` leverages Google's managed Vertex AI infrastructure, providing automatic scaling, high availability, and seamless integration with other Vertex AI services.

## Key Features

- ✅ **Managed Service**: No database setup or maintenance required
- ✅ **Automatic Scaling**: Handles high concurrency automatically
- ✅ **High Availability**: Built on Google Cloud's reliable infrastructure
- ✅ **Integrated with Vertex AI**: Seamless integration with Vertex AI Agent Engine
- ✅ **Express Mode Support**: Can use API keys for simplified authentication
- ✅ **Enterprise Security**: Leverages Google Cloud IAM and security features
- ✅ **Session State Management**: Automatic state persistence and retrieval
- ✅ **Event Streaming**: Efficient event storage and retrieval

## Google Cloud Services Integration

`VertexAiSessionService` connects to the following Google Cloud services:

### 1. **Vertex AI Agent Engine**
   - **Primary Service**: Stores and manages sessions through the Agent Engine API
   - **API Endpoint**: `projects/{project}/locations/{location}/reasoningEngines/{engine_id}/sessions`
   - **Documentation**: https://cloud.google.com/vertex-ai/generative-ai/docs/agent-engine/sessions/overview
   - **What it does**: 
     - Creates and manages session resources
     - Stores session metadata and state
     - Manages event streams (conversation history)
     - Provides session lifecycle management

### 2. **Vertex AI Reasoning Engines**
   - **Service**: The underlying reasoning engine that powers the session service
   - **Resource Format**: `projects/{project}/locations/{location}/reasoningEngines/{engine_id}`
   - **Documentation**: https://cloud.google.com/vertex-ai/generative-ai/docs/agent-engine/overview
   - **What it does**:
     - Provides the agent runtime environment
     - Manages agent execution context
     - Handles session-to-agent binding

### 3. **Google Cloud IAM (Identity and Access Management)**
   - **Service**: Authentication and authorization
   - **Documentation**: https://cloud.google.com/iam/docs
   - **What it does**:
     - Authenticates requests using Application Default Credentials (ADC)
     - Enforces permissions for session operations
     - Manages service account access

### 4. **Vertex AI Express Mode** (Optional)
   - **Service**: Simplified API key-based authentication
   - **Documentation**: https://cloud.google.com/vertex-ai/generative-ai/docs/start/express-mode/overview
   - **What it does**:
     - Provides API key authentication (alternative to IAM)
     - Simplifies development and testing
     - Enables access without full GCP project setup

### 5. **Cloud Storage** (Backend - Managed)
   - **Service**: Underlying storage for session data (managed by Google)
   - **Note**: You don't directly interact with this - it's managed by Vertex AI
   - **What it does**:
     - Stores session data persistently
     - Provides durability and backup
     - Handles data replication

## Architecture

```
┌─────────────────────────────────────────────────────────────┐
│                    Your Application                          │
│  ┌────────────────────────────────────────────────────────┐  │
│  │         VertexAiSessionService                         │  │
│  │  - create_session()                                     │  │
│  │  - get_session()                                        │  │
│  │  - append_event()                                       │  │
│  │  - list_sessions()                                      │  │
│  └────────────────────────────────────────────────────────┘  │
└───────────────────────┬───────────────────────────────────────┘
                        │
                        │ Vertex AI SDK
                        │ (vertexai.Client)
                        │
┌───────────────────────▼───────────────────────────────────────┐
│              Google Cloud Vertex AI                           │
│  ┌────────────────────────────────────────────────────────┐  │
│  │      Vertex AI Agent Engine API                        │  │
│  │  - Sessions API                                        │  │
│  │  - Events API                                          │  │
│  │  - Reasoning Engines API                               │  │
│  └────────────────────────────────────────────────────────┘  │
│                                                               │
│  ┌────────────────────────────────────────────────────────┐  │
│  │      Managed Storage (Backend)                         │  │
│  │  - Session metadata                                    │  │
│  │  - Event streams                                       │  │
│  │  - Session state                                       │  │
│  └────────────────────────────────────────────────────────┘  │
└───────────────────────────────────────────────────────────────┘
```

## Installation and Setup

### Prerequisites

1. **Google Cloud Project**: You need a GCP project with Vertex AI API enabled
2. **Authentication**: Set up Application Default Credentials (ADC) or use Express Mode
3. **Python Package**: The `google-adk` package (already includes Vertex AI SDK)

### Required APIs

Enable the following APIs in your Google Cloud project:

```bash
# Enable Vertex AI API
gcloud services enable aiplatform.googleapis.com

# Enable Agent Engine API (if separate)
gcloud services enable aiplatform.googleapis.com
```

### Authentication Setup

#### Option 1: Application Default Credentials (Recommended for Production)

```bash
# Authenticate using gcloud
gcloud auth application-default login

# Or set environment variable
export GOOGLE_APPLICATION_CREDENTIALS="/path/to/service-account-key.json"
```

#### Option 2: Express Mode (For Development/Testing)

```bash
# Set API key environment variable
export GOOGLE_API_KEY="your-api-key-here"
export GOOGLE_GENAI_USE_VERTEXAI=true
```

**Note**: Express Mode API keys are different from Google AI Studio API keys. Get them from:
https://cloud.google.com/vertex-ai/generative-ai/docs/start/express-mode/overview

## Basic Usage

### Example 1: Basic Vertex AI Session Service

```python
#!/usr/bin/env python3
"""Basic Vertex AI session service example."""

import asyncio
from google.adk import Agent
from google.adk.sessions import VertexAiSessionService
from google.adk.runners import Runner
from google.genai import types

async def main():
    # Create Vertex AI session service
    session_service = VertexAiSessionService(
        project="your-project-id",      # Your GCP project ID
        location="us-central1"          # Vertex AI region
    )
    
    # Create agent
    agent = Agent(
        name="vertex_agent",
        model="gemini-1.5-flash",
        instruction="You are a helpful assistant that remembers conversations."
    )
    
    # Create runner
    runner = Runner(
        app_name="vertex_app",          # App name (maps to reasoning engine)
        agent=agent,
        session_service=session_service
    )
    
    # Create session
    session = await session_service.create_session(
        app_name="vertex_app",
        user_id="user123"
        # Note: session_id is auto-generated by Vertex AI
    )
    
    print(f"Session created: {session.id}")
    
    # Use session
    async for event in runner.run_async(
        user_id="user123",
        session_id=session.id,
        new_message=types.UserContent(parts=[types.Part(text="Hello!")])
    ):
        if event.content and event.content.parts:
            for part in event.content.parts:
                if part.text:
                    print(part.text)

if __name__ == "__main__":
    asyncio.run(main())
```

### Example 2: Using Express Mode

```python
#!/usr/bin/env python3
"""Vertex AI session service with Express Mode."""

import asyncio
import os
from google.adk import Agent
from google.adk.sessions import VertexAiSessionService
from google.adk.runners import Runner
from google.genai import types

async def main():
    # Create Vertex AI session service with Express Mode
    session_service = VertexAiSessionService(
        project="your-project-id",
        location="us-central1",
        express_mode_api_key=os.getenv("GOOGLE_API_KEY")  # Express Mode API key
    )
    
    agent = Agent(
        name="express_agent",
        model="gemini-1.5-flash",
        instruction="You are a helpful assistant."
    )
    
    runner = Runner(
        app_name="express_app",
        agent=agent,
        session_service=session_service
    )
    
    # Create and use session
    session = await session_service.create_session(
        app_name="express_app",
        user_id="user123"
    )
    
    async for event in runner.run_async(
        user_id="user123",
        session_id=session.id,
        new_message=types.UserContent(parts=[types.Part(text="Hi there!")])
    ):
        if event.content and event.content.parts:
            for part in event.content.parts:
                if part.text:
                    print(part.text)

if __name__ == "__main__":
    asyncio.run(main())
```

### Example 3: Using Existing Reasoning Engine

```python
#!/usr/bin/env python3
"""Using Vertex AI session service with existing reasoning engine."""

import asyncio
from google.adk import Agent
from google.adk.sessions import VertexAiSessionService
from google.adk.runners import Runner
from google.genai import types

async def main():
    # If you have an existing reasoning engine, specify its ID
    session_service = VertexAiSessionService(
        project="your-project-id",
        location="us-central1",
        agent_engine_id="123456789"  # Your reasoning engine ID
    )
    
    # Or use full resource name as app_name
    session_service = VertexAiSessionService(
        project="your-project-id",
        location="us-central1"
    )
    
    agent = Agent(
        name="engine_agent",
        model="gemini-1.5-flash",
        instruction="You are a helpful assistant."
    )
    
    runner = Runner(
        # Use full resource name or just the engine ID
        app_name="projects/your-project-id/locations/us-central1/reasoningEngines/123456789",
        agent=agent,
        session_service=session_service
    )
    
    session = await session_service.create_session(
        app_name="projects/your-project-id/locations/us-central1/reasoningEngines/123456789",
        user_id="user123"
    )
    
    async for event in runner.run_async(
        user_id="user123",
        session_id=session.id,
        new_message=types.UserContent(parts=[types.Part(text="Hello!")])
    ):
        if event.content and event.content.parts:
            for part in event.content.parts:
                if part.text:
                    print(part.text)

if __name__ == "__main__":
    asyncio.run(main())
```

## Advanced Configuration

### Constructor Parameters

```python
VertexAiSessionService(
    project: Optional[str] = None,              # GCP project ID
    location: Optional[str] = None,             # Vertex AI region (e.g., "us-central1")
    agent_engine_id: Optional[str] = None,     # Reasoning engine ID (optional)
    express_mode_api_key: Optional[str] = None  # Express Mode API key (optional)
)
```

### Parameter Details

#### `project` (Optional)
- **Type**: `str`
- **Description**: Your Google Cloud project ID
- **Default**: Uses project from Application Default Credentials
- **Example**: `"my-gcp-project-123"`

#### `location` (Optional)
- **Type**: `str`
- **Description**: Vertex AI region where your resources are located
- **Default**: Uses default from credentials or environment
- **Common Values**: 
  - `"us-central1"` (Iowa, USA)
  - `"us-east1"` (South Carolina, USA)
  - `"us-west1"` (Oregon, USA)
  - `"europe-west1"` (Belgium)
  - `"asia-northeast1"` (Tokyo, Japan)
- **Full List**: https://cloud.google.com/vertex-ai/generative-ai/docs/learn/locations

#### `agent_engine_id` (Optional)
- **Type**: `str`
- **Description**: The resource ID of an existing reasoning engine
- **Default**: `None` (will be derived from `app_name`)
- **Use Case**: When you have a pre-existing reasoning engine
- **Example**: `"123456789"`

#### `express_mode_api_key` (Optional)
- **Type**: `str`
- **Description**: API key for Vertex AI Express Mode
- **Default**: Uses `GOOGLE_API_KEY` environment variable if `GOOGLE_GENAI_USE_VERTEXAI=true`
- **Note**: Different from Google AI Studio API keys
- **Documentation**: https://cloud.google.com/vertex-ai/generative-ai/docs/start/express-mode/overview

## Session Management Operations

### Creating Sessions

```python
session = await session_service.create_session(
    app_name="my_app",           # Required: Application name
    user_id="user123",            # Required: User identifier
    state={"key": "value"},      # Optional: Initial session state
    session_id=None,              # Optional: Not supported (auto-generated)
    expire_time="2025-12-31T23:59:59Z"  # Optional: Session expiration
)
```

**Important Notes**:
- `session_id` is **not supported** - Vertex AI auto-generates session IDs
- Session IDs are unique and managed by Vertex AI
- Sessions can have expiration times set via `expire_time` parameter

### Retrieving Sessions

```python
session = await session_service.get_session(
    app_name="my_app",
    user_id="user123",
    session_id="auto-generated-id",
    config=GetSessionConfig(
        num_recent_events=10,        # Optional: Limit events
        after_timestamp=1234567890   # Optional: Filter by timestamp
    )
)
```

### Listing Sessions

```python
response = await session_service.list_sessions(
    app_name="my_app",
    user_id="user123"  # Optional: Filter by user
)

for session in response.sessions:
    print(f"Session ID: {session.id}, User: {session.user_id}")
```

### Deleting Sessions

```python
await session_service.delete_session(
    app_name="my_app",
    user_id="user123",
    session_id="session-id-to-delete"
)
```

### Appending Events

Events are automatically appended when using `Runner.run_async()`, but you can also append manually:

```python
from google.adk.events import Event, EventActions
from google.genai import types

event = Event(
    author="user",
    content=types.Content(parts=[types.Part(text="Hello")]),
    actions=EventActions()
)

appended_event = await session_service.append_event(
    session=session,
    event=event
)
```

## Real-World Examples

### Example 4: Multi-User Chat Application

```python
#!/usr/bin/env python3
"""Multi-user chat application with Vertex AI sessions."""

import asyncio
from google.adk import Agent
from google.adk.sessions import VertexAiSessionService
from google.adk.runners import Runner
from google.genai import types

class ChatApplication:
    def __init__(self):
        self.session_service = VertexAiSessionService(
            project="my-chat-app",
            location="us-central1"
        )
        
        self.agent = Agent(
            name="chat_agent",
            model="gemini-1.5-flash",
            instruction="You are a friendly chat assistant. Remember previous conversations."
        )
        
        self.runner = Runner(
            app_name="chat_app",
            agent=self.agent,
            session_service=self.session_service
        )
    
    async def get_or_create_session(self, user_id: str):
        """Get existing session or create new one for user."""
        # List user's sessions
        response = await self.session_service.list_sessions(
            app_name="chat_app",
            user_id=user_id
        )
        
        # Return most recent session if exists
        if response.sessions:
            return response.sessions[0]
        
        # Create new session
        return await self.session_service.create_session(
            app_name="chat_app",
            user_id=user_id,
            state={"message_count": 0}
        )
    
    async def send_message(self, user_id: str, message: str):
        """Send a message and get response."""
        session = await self.get_or_create_session(user_id)
        
        # Update state
        session.state["message_count"] = session.state.get("message_count", 0) + 1
        
        response_text = ""
        async for event in self.runner.run_async(
            user_id=user_id,
            session_id=session.id,
            new_message=types.UserContent(parts=[types.Part(text=message)])
        ):
            if event.content and event.content.parts:
                for part in event.content.parts:
                    if part.text:
                        response_text += part.text
        
        return response_text

async def main():
    app = ChatApplication()
    
    # Simulate multiple users
    users = ["alice", "bob", "charlie"]
    
    for user in users:
        response = await app.send_message(user, f"Hello from {user}!")
        print(f"{user}: {response[:50]}...")

if __name__ == "__main__":
    asyncio.run(main())
```

### Example 5: Session with State Management

```python
#!/usr/bin/env python3
"""Session with persistent state management."""

import asyncio
from google.adk import Agent
from google.adk.sessions import VertexAiSessionService
from google.adk.runners import Runner
from google.genai import types

async def main():
    session_service = VertexAiSessionService(
        project="my-project",
        location="us-central1"
    )
    
    agent = Agent(
        name="state_agent",
        model="gemini-1.5-flash",
        instruction="You are a shopping assistant. Track user preferences."
    )
    
    runner = Runner(
        app_name="shopping_app",
        agent=agent,
        session_service=session_service
    )
    
    # Create session with initial state
    session = await session_service.create_session(
        app_name="shopping_app",
        user_id="customer_123",
        state={
            "cart": [],
            "preferences": {"theme": "dark"},
            "total_spent": 0.0
        }
    )
    
    # First interaction
    async for event in runner.run_async(
        user_id="customer_123",
        session_id=session.id,
        new_message=types.UserContent(parts=[types.Part(text="I like electronics")]),
        state_delta={"preferences": {"category": "electronics"}}
    ):
        if event.content and event.content.parts:
            for part in event.content.parts:
                if part.text:
                    print(part.text)
    
    # Retrieve session later - state is preserved
    retrieved_session = await session_service.get_session(
        app_name="shopping_app",
        user_id="customer_123",
        session_id=session.id
    )
    
    print(f"Retrieved state: {retrieved_session.state}")

if __name__ == "__main__":
    asyncio.run(main())
```

### Example 6: Session Expiration and Cleanup

```python
#!/usr/bin/env python3
"""Managing session expiration and cleanup."""

import asyncio
from datetime import datetime, timedelta
from google.adk import Agent
from google.adk.sessions import VertexAiSessionService
from google.adk.runners import Runner
from google.genai import types

async def main():
    session_service = VertexAiSessionService(
        project="my-project",
        location="us-central1"
    )
    
    agent = Agent(
        name="temp_agent",
        model="gemini-1.5-flash",
        instruction="You are a temporary assistant."
    )
    
    runner = Runner(
        app_name="temp_app",
        agent=agent,
        session_service=session_service
    )
    
    # Create session with expiration (24 hours from now)
    expire_time = (datetime.utcnow() + timedelta(hours=24)).isoformat() + "Z"
    
    session = await session_service.create_session(
        app_name="temp_app",
        user_id="user123",
        expire_time=expire_time
    )
    
    print(f"Session {session.id} expires at {expire_time}")
    
    # Use session
    async for event in runner.run_async(
        user_id="user123",
        session_id=session.id,
        new_message=types.UserContent(parts=[types.Part(text="Hello")])
    ):
        if event.content and event.content.parts:
            for part in event.content.parts:
                if part.text:
                    print(part.text)
    
    # Cleanup: Delete old sessions
    response = await session_service.list_sessions(
        app_name="temp_app",
        user_id="user123"
    )
    
    for old_session in response.sessions:
        # Delete sessions older than 7 days (example logic)
        # In production, use proper timestamp comparison
        await session_service.delete_session(
            app_name="temp_app",
            user_id="user123",
            session_id=old_session.id
        )

if __name__ == "__main__":
    asyncio.run(main())
```

### Example 7: Error Handling and Retry Logic

```python
#!/usr/bin/env python3
"""Robust error handling for Vertex AI sessions."""

import asyncio
import logging
from google.adk import Agent
from google.adk.sessions import VertexAiSessionService
from google.adk.runners import Runner
from google.genai import types
from google.api_core import exceptions

logging.basicConfig(level=logging.INFO)
logger = logging.getLogger(__name__)

async def create_session_with_retry(session_service, app_name, user_id, max_retries=3):
    """Create session with retry logic."""
    for attempt in range(max_retries):
        try:
            return await session_service.create_session(
                app_name=app_name,
                user_id=user_id
            )
        except exceptions.ServiceUnavailable as e:
            if attempt < max_retries - 1:
                wait_time = 2 ** attempt  # Exponential backoff
                logger.warning(f"Service unavailable, retrying in {wait_time}s...")
                await asyncio.sleep(wait_time)
            else:
                logger.error(f"Failed to create session after {max_retries} attempts")
                raise
        except exceptions.PermissionDenied as e:
            logger.error(f"Permission denied: {e}")
            raise
        except Exception as e:
            logger.error(f"Unexpected error: {e}")
            raise

async def main():
    session_service = VertexAiSessionService(
        project="my-project",
        location="us-central1"
    )
    
    agent = Agent(
        name="robust_agent",
        model="gemini-1.5-flash",
        instruction="You are a helpful assistant."
    )
    
    runner = Runner(
        app_name="robust_app",
        agent=agent,
        session_service=session_service
    )
    
    try:
        # Create session with retry
        session = await create_session_with_retry(
            session_service,
            "robust_app",
            "user123"
        )
        
        # Use session with error handling
        try:
            async for event in runner.run_async(
                user_id="user123",
                session_id=session.id,
                new_message=types.UserContent(parts=[types.Part(text="Hello")])
            ):
                if event.content and event.content.parts:
                    for part in event.content.parts:
                        if part.text:
                            print(part.text)
        except exceptions.NotFound:
            logger.error("Session not found - may have been deleted")
        except exceptions.InvalidArgument as e:
            logger.error(f"Invalid argument: {e}")
        except Exception as e:
            logger.error(f"Unexpected error during execution: {e}")
            
    except Exception as e:
        logger.error(f"Failed to initialize: {e}")

if __name__ == "__main__":
    asyncio.run(main())
```

## Comparison: VertexAiSessionService vs DatabaseSessionService

| Feature | VertexAiSessionService | DatabaseSessionService |
|---------|----------------------|----------------------|
| **Setup Complexity** | Low (managed service) | Medium (database setup required) |
| **Scaling** | Automatic | Manual configuration |
| **Maintenance** | None (Google managed) | Database maintenance required |
| **Cost** | Pay-per-use | Database hosting costs |
| **Latency** | Optimized for Vertex AI | Depends on database location |
| **Customization** | Limited to Vertex AI features | Full database control |
| **Multi-region** | Built-in | Manual replication setup |
| **Backup/Recovery** | Automatic | Manual setup |
| **Session ID Control** | Auto-generated only | Custom session IDs supported |
| **Best For** | Production, Google Cloud deployments | Custom requirements, existing databases |

## Best Practices

### 1. **Project and Location Selection**
```python
# Use consistent project and location across your application
session_service = VertexAiSessionService(
    project=os.getenv("GCP_PROJECT_ID"),
    location=os.getenv("VERTEX_AI_LOCATION", "us-central1")
)
```

### 2. **Error Handling**
```python
from google.api_core import exceptions

try:
    session = await session_service.create_session(...)
except exceptions.PermissionDenied:
    # Handle authentication issues
    pass
except exceptions.ServiceUnavailable:
    # Handle temporary service issues
    pass
except exceptions.InvalidArgument:
    # Handle invalid parameters
    pass
```

### 3. **Session Lifecycle Management**
```python
# Create sessions when needed
session = await session_service.create_session(...)

# Use sessions actively
# ... run conversations ...

# Clean up expired sessions periodically
async def cleanup_old_sessions():
    response = await session_service.list_sessions(...)
    for session in response.sessions:
        # Check expiration and delete if needed
        await session_service.delete_session(...)
```

### 4. **State Management**
```python
# Keep state small and focused
session = await session_service.create_session(
    app_name="app",
    user_id="user",
    state={
        "user_preferences": {...},  # Small, essential data
        "session_metadata": {...}   # Session-specific info
    }
)

# Avoid storing large data in state
# Use external storage (Cloud Storage, etc.) for large files
```

### 5. **Authentication**
```python
# Production: Use Application Default Credentials
# gcloud auth application-default login

# Development: Use Express Mode
session_service = VertexAiSessionService(
    project="project-id",
    location="us-central1",
    express_mode_api_key=os.getenv("GOOGLE_API_KEY")
)
```

## Troubleshooting

### Issue: Permission Denied

**Error**: `403 Permission Denied`

**Solutions**:
1. Verify Application Default Credentials are set up correctly
2. Check IAM permissions for the service account:
   ```bash
   gcloud projects add-iam-policy-binding PROJECT_ID \
     --member="serviceAccount:SERVICE_ACCOUNT@PROJECT_ID.iam.gserviceaccount.com" \
     --role="roles/aiplatform.user"
   ```
3. For Express Mode, verify API key is valid and has proper permissions

### Issue: Project Not Found

**Error**: `404 Project not found`

**Solutions**:
1. Verify project ID is correct
2. Ensure Vertex AI API is enabled:
   ```bash
   gcloud services enable aiplatform.googleapis.com --project=PROJECT_ID
   ```
3. Check project billing is enabled

### Issue: Location Not Available

**Error**: `Location not available`

**Solutions**:
1. Verify location string is correct (e.g., `"us-central1"`)
2. Check Vertex AI is available in that region:
   https://cloud.google.com/vertex-ai/generative-ai/docs/learn/locations
3. Use a supported region

### Issue: Session ID Not Supported

**Error**: `User-provided Session id is not supported`

**Solution**: Vertex AI auto-generates session IDs. Don't provide `session_id` when creating sessions:
```python
# ❌ Wrong
session = await session_service.create_session(
    app_name="app",
    user_id="user",
    session_id="custom-id"  # Not supported!
)

# ✅ Correct
session = await session_service.create_session(
    app_name="app",
    user_id="user"
    # session_id is auto-generated
)
```

### Issue: Express Mode Not Working

**Error**: Express Mode authentication fails

**Solutions**:
1. Verify `GOOGLE_GENAI_USE_VERTEXAI=true` is set
2. Use correct Express Mode API key (not Google AI Studio key)
3. Get API key from: https://cloud.google.com/vertex-ai/generative-ai/docs/start/express-mode/overview

## API Reference Links

### Official Documentation

1. **Vertex AI Agent Engine Sessions Overview**
   - https://cloud.google.com/vertex-ai/generative-ai/docs/agent-engine/sessions/overview

2. **Managing Sessions via API**
   - https://cloud.google.com/vertex-ai/generative-ai/docs/agent-engine/sessions/manage-sessions-api

3. **Vertex AI API Reference**
   - https://cloud.google.com/vertex-ai/generative-ai/docs/reference/rest/v1beta1/projects.locations.reasoningEngines.sessions

4. **Express Mode Documentation**
   - https://cloud.google.com/vertex-ai/generative-ai/docs/start/express-mode/overview

5. **Vertex AI Locations**
   - https://cloud.google.com/vertex-ai/generative-ai/docs/learn/locations

6. **IAM and Authentication**
   - https://cloud.google.com/iam/docs
   - https://cloud.google.com/docs/authentication

### Code Examples

- **Google ADK Examples**: Check the `examples/` directory in your project
- **Vertex AI Python SDK**: https://github.com/googleapis/python-aiplatform

## Cost Considerations

### Pricing Model

Vertex AI Session Service pricing is based on:
- **Storage**: Session data storage (per GB-month)
- **API Calls**: Create, get, list, delete operations
- **Data Transfer**: Network egress (if applicable)

### Cost Optimization Tips

1. **Clean up old sessions**: Delete sessions that are no longer needed
2. **Set expiration times**: Use `expire_time` to auto-expire sessions
3. **Minimize state size**: Keep session state small
4. **Batch operations**: When possible, batch session operations
5. **Monitor usage**: Use Cloud Monitoring to track session usage

**Pricing Details**: https://cloud.google.com/vertex-ai/pricing

## Security Considerations

1. **IAM Roles**: Use least-privilege IAM roles
2. **Service Accounts**: Use dedicated service accounts for production
3. **API Keys**: Rotate Express Mode API keys regularly
4. **Data Encryption**: Vertex AI encrypts data at rest and in transit
5. **Audit Logging**: Enable Cloud Audit Logs for session operations

## Related Documentation

- [Sessions Package Overview](07-Sessions-Package.md)
- [DatabaseSessionService Guide](07-Sessions-Package.md#example-4-databasesessionservice---postgresql)
- [Runners Package](10-Runners-Package.md) - How sessions are used in runners
- [State Management](11-State-Management.md) - Session state management

## Summary

`VertexAiSessionService` provides a production-ready, managed solution for session storage in Google Cloud. It integrates seamlessly with Vertex AI services, offers automatic scaling, and requires minimal setup. Use it when:

- ✅ You're deploying on Google Cloud
- ✅ You need managed, scalable session storage
- ✅ You want minimal operational overhead
- ✅ You need integration with other Vertex AI services

For custom database requirements or existing database infrastructure, consider `DatabaseSessionService` instead.
