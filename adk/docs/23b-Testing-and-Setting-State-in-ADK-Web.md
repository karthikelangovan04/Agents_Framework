# Testing and Setting State in ADK Web: Complete Guide

**File Path**: `docs/23b-Testing-and-Setting-State-in-ADK-Web.md`  
**Related Docs**: 
- [State Updates Guide](23-State-Updates-in-ADK-Web-and-Programmatically.md)
- [State Prefixes and Database Storage](23a-State-Prefixes-and-Database-Storage-Mapping.md)
- [ADK Web Interface](14-ADK-Web-Interface-Analysis.md)

## Overview

This document provides a practical, step-by-step guide for testing and setting state in ADK Web through multiple methods, with real examples showing how state impacts agent responses.

---

## Table of Contents

1. [Quick Start](#quick-start)
2. [Setting State via URL Parameters](#setting-state-via-url-parameters)
3. [Setting State via Web UI](#setting-state-via-web-ui)
4. [Setting State Programmatically (REST API)](#setting-state-programmatically-rest-api)
5. [Setting State Programmatically (Python SDK)](#setting-state-programmatically-python-sdk)
6. [Verifying State Updates](#verifying-state-updates)
7. [Seeing State Impact on Agent Responses](#seeing-state-impact-on-agent-responses)
8. [Complete Testing Workflow](#complete-testing-workflow)
9. [Troubleshooting](#troubleshooting)

---

## Quick Start

### Your ADK Web Setup

```bash
# Your ADK Web server
URL: http://127.0.0.1:10000
App: adk_web_testing
User: user
Session: a923c682-5ab8-45dd-82d1-9482cf25d5d7
```

### Quick Test Commands

```bash
# 1. Get current state
curl -s "http://127.0.0.1:10000/apps/adk_web_testing/users/user/sessions/a923c682-5ab8-45dd-82d1-9482cf25d5d7" | jq '.state'

# 2. Update state
curl -X PATCH "http://127.0.0.1:10000/apps/adk_web_testing/users/user/sessions/a923c682-5ab8-45dd-82d1-9482cf25d5d7" \
  -H "Content-Type: application/json" \
  -d '{"state_delta": {"test_key": "test_value"}}'

# 3. Send message with state_delta
curl -X POST "http://127.0.0.1:10000/run" \
  -H "Content-Type: application/json" \
  -d '{
    "app_name": "adk_web_testing",
    "user_id": "user",
    "session_id": "a923c682-5ab8-45dd-82d1-9482cf25d5d7",
    "new_message": {"role": "user", "parts": [{"text": "Hello"}]},
    "state_delta": {"message_count": 1}
  }'
```

---

## Setting State via URL Parameters

### ADK Web UI URL Structure

ADK Web UI URLs can include session parameters:

```
http://127.0.0.1:10000/dev-ui/?app={app_name}&session={session_id}&userId={user_id}
```

### Example URL

```
http://127.0.0.1:10000/dev-ui/?app=adk_web_testing&session=a923c682-5ab8-45dd-82d1-9482cf25d5d7&userId=user
```

### Limitations

**Note**: URL parameters don't directly set state. They only:
- Navigate to a specific session
- Set the active app, user, and session context

To actually set state, you need to:
1. Use the Web UI state editor (see below)
2. Use REST API (see below)
3. Include `state_delta` when sending messages

---

## Setting State via Web UI

### Step-by-Step: Using ADK Web UI State Editor

#### 1. Access the State Editor

1. **Open ADK Web UI**:
   ```
   http://127.0.0.1:10000/dev-ui/
   ```

2. **Navigate to Your Session**:
   - Select the session from the session list, OR
   - Use URL: `http://127.0.0.1:10000/dev-ui/?app=adk_web_testing&session=a923c682-5ab8-45dd-82d1-9482cf25d5d7&userId=user`

3. **Open State Editor**:
   - Click the **three dots (⋮) menu** button in the session interface
   - Select **"Update State"** or **"Edit State"**
   - A JSON editor panel opens showing current state

#### 2. Edit State in JSON Editor

The state editor shows state as JSON. You can:

**Example State to Set**:
```json
{
  "conversation_topic": "time_queries",
  "last_city_asked": "Chennai",
  "message_count": 2,
  "user_preference_timezone": "Asia/Kolkata",
  "user:preferred_language": "en",
  "user:time_format": "24h",
  "user:greeting_style": "formal",
  "app:include_timezone": true,
  "app:include_date": true
}
```

**Steps**:
1. Click in the JSON editor
2. Paste or type your state JSON
3. Click **Save** or **Update**
4. State is saved to the session

#### 3. Verify State Was Saved

After saving:
1. **Refresh the state editor** (reopen it)
2. **Check the JSON** - your values should be there
3. **Or use API** to verify:
   ```bash
   curl -s "http://127.0.0.1:10000/apps/adk_web_testing/users/user/sessions/a923c682-5ab8-45dd-82d1-9482cf25d5d7" | jq '.state'
   ```

#### 4. Test State Impact

Send a message in the chat and observe:
- Does the agent reference state values?
- Does behavior change based on state?
- Check event history for `stateDelta` in user events

---

## Setting State Programmatically (REST API)

### Method 1: PATCH Endpoint (Update State Directly)

#### Basic Syntax

```bash
curl -X PATCH "http://127.0.0.1:10000/apps/{app_name}/users/{user_id}/sessions/{session_id}" \
  -H "Content-Type: application/json" \
  -d '{
    "state_delta": {
      "key1": "value1",
      "key2": "value2"
    }
  }'
```

#### Real Example

```bash
curl -X PATCH "http://127.0.0.1:10000/apps/adk_web_testing/users/user/sessions/a923c682-5ab8-45dd-82d1-9482cf25d5d7" \
  -H "Content-Type: application/json" \
  -d '{
    "state_delta": {
      "conversation_topic": "time_queries",
      "last_city_asked": "Chennai",
      "message_count": 2,
      "user_preference_timezone": "Asia/Kolkata"
    }
  }'
```

#### Response

```json
{
  "id": "a923c682-5ab8-45dd-82d1-9482cf25d5d7",
  "appName": "adk_web_testing",
  "userId": "user",
  "state": {
    "conversation_topic": "time_queries",
    "last_city_asked": "Chennai",
    "message_count": 2,
    "user_preference_timezone": "Asia/Kolkata"
  },
  "events": [...]
}
```

### Method 2: POST /run with state_delta (Update State When Sending Message)

#### Basic Syntax

```bash
curl -X POST "http://127.0.0.1:10000/run" \
  -H "Content-Type: application/json" \
  -d '{
    "app_name": "{app_name}",
    "user_id": "{user_id}",
    "session_id": "{session_id}",
    "new_message": {
      "role": "user",
      "parts": [{"text": "Your message here"}]
    },
    "state_delta": {
      "key1": "value1",
      "key2": "value2"
    }
  }'
```

#### Real Example

```bash
curl -X POST "http://127.0.0.1:10000/run" \
  -H "Content-Type: application/json" \
  -d '{
    "app_name": "adk_web_testing",
    "user_id": "user",
    "session_id": "a923c682-5ab8-45dd-82d1-9482cf25d5d7",
    "new_message": {
      "role": "user",
      "parts": [{"text": "What time is it in Mumbai?"}]
    },
    "state_delta": {
      "last_city_asked": "Mumbai",
      "message_count": 5,
      "conversation_topic": "time_queries"
    }
  }'
```

#### Response

Returns an array of events. The **user event** will contain `stateDelta`:

```json
[
  {
    "content": {
      "parts": [{"text": "What time is it in Mumbai?"}],
      "role": "user"
    },
    "author": "user",
    "actions": {
      "stateDelta": {
        "last_city_asked": "Mumbai",
        "message_count": 5,
        "conversation_topic": "time_queries"
      }
    },
    "id": "...",
    "timestamp": 1770303582.422828
  },
  {
    "author": "root_agent",
    "content": {
      "parts": [{"text": "The current time in Mumbai is 10:30 AM."}]
    },
    "actions": {
      "stateDelta": {}
    }
  }
]
```

**Key Point**: The `stateDelta` appears in the **user event** (author: "user"), not in agent events.

### Method 3: Using Python httpx

```python
import httpx
import asyncio

BASE_URL = "http://127.0.0.1:10000"
APP_NAME = "adk_web_testing"
USER_ID = "user"
SESSION_ID = "a923c682-5ab8-45dd-82d1-9482cf25d5d7"

async def update_state_via_patch():
    """Update state using PATCH endpoint."""
    async with httpx.AsyncClient() as client:
        response = await client.patch(
            f"{BASE_URL}/apps/{APP_NAME}/users/{USER_ID}/sessions/{SESSION_ID}",
            json={
                "state_delta": {
                    "conversation_topic": "time_queries",
                    "last_city_asked": "Chennai",
                    "message_count": 2
                }
            }
        )
        session = response.json()
        print("Updated state:", session["state"])
        return session

async def send_message_with_state():
    """Send message with state_delta."""
    async with httpx.AsyncClient() as client:
        response = await client.post(
            f"{BASE_URL}/run",
            json={
                "app_name": APP_NAME,
                "user_id": USER_ID,
                "session_id": SESSION_ID,
                "new_message": {
                    "role": "user",
                    "parts": [{"text": "What time is it in Mumbai?"}]
                },
                "state_delta": {
                    "last_city_asked": "Mumbai",
                    "message_count": 5
                }
            }
        )
        events = response.json()
        
        # Find user event with stateDelta
        for event in events:
            if event.get("author") == "user" and event.get("actions", {}).get("stateDelta"):
                print("State Delta:", event["actions"]["stateDelta"])
        
        return events

# Run
asyncio.run(update_state_via_patch())
asyncio.run(send_message_with_state())
```

---

## Setting State Programmatically (Python SDK)

### Using ADK Python SDK

```python
import asyncio
from google.adk.sessions import InMemorySessionService, DatabaseSessionService
from google.adk.sessions.state import State
from google.adk import Agent
from google.adk.runners import Runner
from google.genai import types

async def set_state_with_sdk():
    """Set state using ADK Python SDK."""
    
    # Initialize session service
    session_service = DatabaseSessionService(
        db_url="sqlite:///./.adk/session.db"
    )
    
    # Create agent
    agent = Agent(
        name="time_agent",
        model="gemini-3-flash-preview",
        instruction="You are a helpful assistant that tells the current time in cities."
    )
    
    # Create runner
    runner = Runner(
        app_name="adk_web_testing",
        agent=agent,
        session_service=session_service
    )
    
    # Method 1: Create session with initial state
    session = await session_service.create_session(
        app_name="adk_web_testing",
        user_id="user",
        session_id="test_session_001",
        state={
            "conversation_topic": "time_queries",
            "message_count": 0,
            State.USER_PREFIX + "preferred_language": "en",
            State.APP_PREFIX + "include_timezone": True
        }
    )
    print("Session created with state:", session.state.to_dict())
    
    # Method 2: Update state via state_delta in run_async
    async for event in runner.run_async(
        user_id="user",
        session_id="test_session_001",
        new_message=types.UserContent(parts=[types.Part(text="What time is it in Chennai?")]),
        state_delta={
            "last_city_asked": "Chennai",
            "message_count": 1,
            State.USER_PREFIX + "last_interaction": "2024-01-15"
        }
    ):
        if event.content:
            print("Agent response:", event.content.parts[0].text)
    
    # Method 3: Get updated session
    updated_session = await session_service.get_session(
        app_name="adk_web_testing",
        user_id="user",
        session_id="test_session_001"
    )
    print("Updated state:", updated_session.state.to_dict())

asyncio.run(set_state_with_sdk())
```

---

## Verifying State Updates

### Method 1: Check Session State via API

```bash
# Get full session with state
curl -s "http://127.0.0.1:10000/apps/adk_web_testing/users/user/sessions/a923c682-5ab8-45dd-82d1-9482cf25d5d7" | \
  jq '.state'

# Get specific state keys
curl -s "http://127.0.0.1:10000/apps/adk_web_testing/users/user/sessions/a923c682-5ab8-45dd-82d1-9482cf25d5d7" | \
  jq '.state | {last_city_asked, message_count, conversation_topic}'
```

### Method 2: Check Events with stateDelta

```bash
# Find all user events with stateDelta
curl -s "http://127.0.0.1:10000/apps/adk_web_testing/users/user/sessions/a923c682-5ab8-45dd-82d1-9482cf25d5d7" | \
  jq '.events[] | select(.author == "user" and .actions.stateDelta != null and .actions.stateDelta != {}) | {
    timestamp,
    message: .content.parts[0].text,
    stateDelta: .actions.stateDelta
  }'
```

**Important**: The API uses `stateDelta` (camelCase), not `state_delta` (snake_case).

### Method 3: Complete State Verification Script

```bash
#!/bin/bash

BASE_URL="http://127.0.0.1:10000"
APP_NAME="adk_web_testing"
USER_ID="user"
SESSION_ID="a923c682-5ab8-45dd-82d1-9482cf25d5d7"

echo "=== Current Session State ==="
curl -s "${BASE_URL}/apps/${APP_NAME}/users/${USER_ID}/sessions/${SESSION_ID}" | \
  jq '.state'

echo -e "\n=== Events with stateDelta ==="
curl -s "${BASE_URL}/apps/${APP_NAME}/users/${USER_ID}/sessions/${SESSION_ID}" | \
  jq '.events[] | select(.actions.stateDelta != null and .actions.stateDelta != {}) | {
    id,
    author,
    timestamp,
    stateDelta: .actions.stateDelta
  }' | tail -5
```

---

## Seeing State Impact on Agent Responses

### Understanding How State Affects Responses

State impacts agent responses in two ways:

1. **Direct State Access**: Agent reads state values (requires callback or tool access)
2. **Context Enhancement**: State is used to modify prompts/instructions (via callbacks)

### Example: Agent That Uses State

To see state impact, modify your agent to read and use state:

```python
from google.adk.agents import LlmAgent
from google.adk.agents.callback_context import CallbackContext
from google.adk.models import LlmRequest
from google.adk.sessions.state import State
from typing import Optional

def before_model_use_state(
    callback_context: CallbackContext,
    llm_request: LlmRequest
) -> Optional[LlmResponse]:
    """Use state to enhance LLM request."""
    session = callback_context.session
    state = session.state
    
    # Get state values
    last_city = state.get("last_city_asked", "")
    conversation_topic = state.get("conversation_topic", "")
    timezone = state.get("user_preference_timezone", "UTC")
    time_format = state.get("user:time_format", "24h")
    greeting_style = state.get("user:greeting_style", "friendly")
    
    # Enhance system instruction
    if llm_request.config.system_instruction:
        original = llm_request.config.system_instruction.parts[0].text if llm_request.config.system_instruction.parts else ""
        
        enhanced = f"""
        {original}
        
        Context from conversation:
        - Last city asked: {last_city}
        - Conversation topic: {conversation_topic}
        - User timezone preference: {timezone}
        - Time format preference: {time_format}
        - Greeting style: {greeting_style}
        
        Use this context to provide personalized responses.
        If last_city_asked is set, you can reference it.
        Adapt your response style based on greeting_style.
        """
        
        llm_request.config.system_instruction.parts[0].text = enhanced
    
    return None

# Use in agent
agent = LlmAgent(
    name="time_agent",
    model="gemini-3-flash-preview",
    instruction="You are a helpful assistant that tells the current time in cities.",
    before_model_callback=before_model_use_state
)
```

### Testing State Impact

#### Test 1: Set State, Then Ask Question

```bash
# Step 1: Set state
curl -X PATCH "http://127.0.0.1:10000/apps/adk_web_testing/users/user/sessions/a923c682-5ab8-45dd-82d1-9482cf25d5d7" \
  -H "Content-Type: application/json" \
  -d '{
    "state_delta": {
      "last_city_asked": "Chennai",
      "conversation_topic": "time_queries",
      "user:greeting_style": "formal"
    }
  }'

# Step 2: Ask question that should reference state
curl -X POST "http://127.0.0.1:10000/run" \
  -H "Content-Type: application/json" \
  -d '{
    "app_name": "adk_web_testing",
    "user_id": "user",
    "session_id": "a923c682-5ab8-45dd-82d1-9482cf25d5d7",
    "new_message": {
      "role": "user",
      "parts": [{"text": "What about the last city I asked about?"}]
    }
  }' | jq '.[] | select(.author == "root_agent") | .content.parts[0].text'
```

**Expected**: If agent uses state, it should mention "Chennai".

#### Test 2: Compare Responses With/Without State

```bash
# Without state
curl -X POST "http://127.0.0.1:10000/run" \
  -H "Content-Type: application/json" \
  -d '{
    "app_name": "adk_web_testing",
    "user_id": "user",
    "session_id": "a923c682-5ab8-45dd-82d1-9482cf25d5d7",
    "new_message": {
      "role": "user",
      "parts": [{"text": "What time is it in Mumbai?"}]
    }
  }' | jq '.[] | select(.author == "root_agent") | .content.parts[0].text'

# With state (formal style)
curl -X POST "http://127.0.0.1:10000/run" \
  -H "Content-Type: application/json" \
  -d '{
    "app_name": "adk_web_testing",
    "user_id": "user",
    "session_id": "a923c682-5ab8-45dd-82d1-9482cf25d5d7",
    "new_message": {
      "role": "user",
      "parts": [{"text": "What time is it in Mumbai?"}]
    },
    "state_delta": {
      "user:greeting_style": "formal"
    }
  }' | jq '.[] | select(.author == "root_agent") | .content.parts[0].text'
```

**Expected**: Responses should differ based on `greeting_style` state.

---

## Complete Testing Workflow

### End-to-End Test Script

```bash
#!/bin/bash

BASE_URL="http://127.0.0.1:10000"
APP_NAME="adk_web_testing"
USER_ID="user"
SESSION_ID="a923c682-5ab8-45dd-82d1-9482cf25d5d7"

echo "=== Step 1: Get Current State ==="
curl -s "${BASE_URL}/apps/${APP_NAME}/users/${USER_ID}/sessions/${SESSION_ID}" | \
  jq '.state'

echo -e "\n=== Step 2: Update State via PATCH ==="
curl -X PATCH "${BASE_URL}/apps/${APP_NAME}/users/${USER_ID}/sessions/${SESSION_ID}" \
  -H "Content-Type: application/json" \
  -d '{
    "state_delta": {
      "conversation_topic": "time_queries",
      "last_city_asked": "Chennai",
      "message_count": 2,
      "user_preference_timezone": "Asia/Kolkata"
    }
  }' | jq '.state'

echo -e "\n=== Step 3: Verify State Update ==="
curl -s "${BASE_URL}/apps/${APP_NAME}/users/${USER_ID}/sessions/${SESSION_ID}" | \
  jq '.state | {conversation_topic, last_city_asked, message_count}'

echo -e "\n=== Step 4: Send Message with state_delta ==="
RESPONSE=$(curl -s -X POST "${BASE_URL}/run" \
  -H "Content-Type: application/json" \
  -d "{
    \"app_name\": \"${APP_NAME}\",
    \"user_id\": \"${USER_ID}\",
    \"session_id\": \"${SESSION_ID}\",
    \"new_message\": {
      \"role\": \"user\",
      \"parts\": [{\"text\": \"What time is it in Mumbai?\"}]
    },
    \"state_delta\": {
      \"last_city_asked\": \"Mumbai\",
      \"message_count\": 3
    }
  }")

echo "=== User Event with stateDelta ==="
echo "$RESPONSE" | jq '.[] | select(.author == "user") | {
  message: .content.parts[0].text,
  stateDelta: .actions.stateDelta
}'

echo -e "\n=== Agent Response ==="
echo "$RESPONSE" | jq '.[] | select(.author == "root_agent" and .content.parts[0].text) | .content.parts[0].text'

echo -e "\n=== Step 5: Verify Final State ==="
curl -s "${BASE_URL}/apps/${APP_NAME}/users/${USER_ID}/sessions/${SESSION_ID}" | \
  jq '.state | {last_city_asked, message_count}'
```

### Python Testing Script

```python
import httpx
import asyncio
import json

BASE_URL = "http://127.0.0.1:10000"
APP_NAME = "adk_web_testing"
USER_ID = "user"
SESSION_ID = "a923c682-5ab8-45dd-82d1-9482cf25d5d7"

async def complete_state_test():
    """Complete workflow for testing state."""
    async with httpx.AsyncClient() as client:
        # Step 1: Get current state
        print("=== Step 1: Current State ===")
        response = await client.get(
            f"{BASE_URL}/apps/{APP_NAME}/users/{USER_ID}/sessions/{SESSION_ID}"
        )
        session = response.json()
        print("Current state:", json.dumps(session["state"], indent=2))
        
        # Step 2: Update state via PATCH
        print("\n=== Step 2: Update State via PATCH ===")
        response = await client.patch(
            f"{BASE_URL}/apps/{APP_NAME}/users/{USER_ID}/sessions/{SESSION_ID}",
            json={
                "state_delta": {
                    "conversation_topic": "time_queries",
                    "last_city_asked": "Chennai",
                    "message_count": 2
                }
            }
        )
        updated_session = response.json()
        print("Updated state:", json.dumps(updated_session["state"], indent=2))
        
        # Step 3: Send message with state_delta
        print("\n=== Step 3: Send Message with state_delta ===")
        response = await client.post(
            f"{BASE_URL}/run",
            json={
                "app_name": APP_NAME,
                "user_id": USER_ID,
                "session_id": SESSION_ID,
                "new_message": {
                    "role": "user",
                    "parts": [{"text": "What time is it in Mumbai?"}]
                },
                "state_delta": {
                    "last_city_asked": "Mumbai",
                    "message_count": 3
                }
            }
        )
        events = response.json()
        
        # Find user event with stateDelta
        print("\n=== User Event with stateDelta ===")
        for event in events:
            if event.get("author") == "user" and event.get("actions", {}).get("stateDelta"):
                print("Message:", event["content"]["parts"][0]["text"])
                print("State Delta:", json.dumps(event["actions"]["stateDelta"], indent=2))
        
        # Find agent response
        print("\n=== Agent Response ===")
        for event in events:
            if event.get("author") == "root_agent" and event.get("content", {}).get("parts"):
                text = event["content"]["parts"][0].get("text", "")
                if text:
                    print("Response:", text)
        
        # Step 4: Verify final state
        print("\n=== Step 4: Final State ===")
        response = await client.get(
            f"{BASE_URL}/apps/{APP_NAME}/users/{USER_ID}/sessions/{SESSION_ID}"
        )
        final_session = response.json()
        print("Final state:", json.dumps({
            "last_city_asked": final_session["state"].get("last_city_asked"),
            "message_count": final_session["state"].get("message_count")
        }, indent=2))

asyncio.run(complete_state_test())
```

---

## Troubleshooting

### Issue 1: stateDelta is null or empty in events

**Symptom**: Events show `"stateDelta": null` or `"stateDelta": {}`

**Causes**:
- PATCH endpoint updates state but doesn't create events with stateDelta
- state_delta wasn't included in the `/run` request

**Solution**:
- Include `state_delta` in POST `/run` requests
- Check user events, not agent events (agent events don't have stateDelta unless agent updates state)

### Issue 2: State not updating

**Symptom**: State values don't change after update

**Check**:
```bash
# Verify state was updated
curl -s "http://127.0.0.1:10000/apps/adk_web_testing/users/user/sessions/a923c682-5ab8-45dd-82d1-9482cf25d5d7" | jq '.state'
```

**Solutions**:
- Ensure JSON is valid
- Check session ID is correct
- Verify app_name and user_id match

### Issue 3: stateDelta not visible in ADK Web UI

**Symptom**: Can't see stateDelta in Web UI

**Solutions**:
1. **Expand event details** - Click on user events to see full JSON
2. **Check browser console** - Look for API responses
3. **Use API directly** - Verify via curl commands
4. **Refresh page** - UI might need refresh to show updates

### Issue 4: Field name confusion (stateDelta vs state_delta)

**Important**: 
- **Request**: Use `state_delta` (snake_case) in API requests
- **Response**: API returns `stateDelta` (camelCase) in events

**Example**:
```bash
# Request uses snake_case
curl -X POST "http://127.0.0.1:10000/run" \
  -d '{"state_delta": {"key": "value"}}'

# Response uses camelCase
# events[].actions.stateDelta
```

### Issue 5: State not affecting agent responses

**Symptom**: Agent doesn't use state values

**Causes**:
- Agent code doesn't read state
- No callbacks to use state
- State keys don't match what agent expects

**Solution**: Add callback to use state (see "Seeing State Impact" section above)

---

## Key Takeaways

1. **State Updates Work**: State can be updated via PATCH or included in `/run` requests
2. **stateDelta Location**: Appears in **user events**, not agent events
3. **Field Naming**: Request uses `state_delta`, response uses `stateDelta`
4. **Verification**: Always verify state updates via API or Web UI
5. **Agent Impact**: Agent needs callbacks to actually use state values
6. **Testing**: Use complete workflow scripts to test end-to-end

---

## Related Documentation

- [State Updates Guide](23-State-Updates-in-ADK-Web-and-Programmatically.md) - Comprehensive state management
- [State Prefixes and Database Storage](23a-State-Prefixes-and-Database-Storage-Mapping.md) - How state is stored
- [ADK Web Interface](14-ADK-Web-Interface-Analysis.md) - Web UI details
- [Callbacks Documentation](https://google.github.io/adk-docs/callbacks/) - Using callbacks to access state

---

**Last Updated**: 2025-02-05  
**Tested With**: ADK Web Server on `http://127.0.0.1:10000`, App: `adk_web_testing`
