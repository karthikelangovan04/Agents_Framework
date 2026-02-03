# AG-UI Library Analysis & Fix

## 🔍 Root Cause Analysis

### Problem
AG-UI creates `thread_user_xxx` IDs instead of using our authenticated user IDs from `X-User-Id` header.

### Investigation Results

#### 1. **Where `thread_user_xxx` is Created**
**File:** `.venv/lib/python3.13/site-packages/ag_ui_adk/adk_agent.py`
**Lines:** 352-355

```python
def _default_user_extractor(self, input: RunAgentInput) -> str:
    """Default user extraction logic."""
    # Use thread_id as default (assumes thread per user)
    return f"thread_user_{input.thread_id}"
```

#### 2. **User ID Resolution Logic**
**File:** `adk_agent.py`
**Lines:** 343-350

```python
def _get_user_id(self, input: RunAgentInput) -> str:
    """Resolve user ID with clear precedence."""
    if self._static_user_id:
        return self._static_user_id
    elif self._user_id_extractor:
        return self._user_id_extractor(input)
    else:
        return self._default_user_extractor(input)
```

**Precedence:**
1. `_static_user_id` (hardcoded user ID)
2. `_user_id_extractor` (function to extract from `RunAgentInput`)
3. `_default_user_extractor` (creates `thread_user_xxx`) ← **This is what's running!**

#### 3. **ADKAgent Constructor Parameters**
**File:** `adk_agent.py`
**Lines:** 59-61

```python
# User identification
user_id: Optional[str] = None,
user_id_extractor: Optional[Callable[[RunAgentInput], str]] = None,
```

#### 4. **The Missing Piece**

**Problem:** 
- Our backend sends `X-User-Id: 3` header
- But `ADKAgent` is initialized WITHOUT `user_id` or `user_id_extractor`
- So it falls back to `_default_user_extractor` → `thread_user_xxx`

**Why `user_id_extractor` doesn't work directly:**
- `user_id_extractor` only receives `RunAgentInput` (not `Request`)
- `RunAgentInput` doesn't have the HTTP headers
- Headers are on the `Request` object (FastAPI)

#### 5. **The Solution Path**

**File:** `endpoint.py`
**Lines:** 122-133

The endpoint CAN extract headers into `RunAgentInput.state`:

```python
@app.post(path)
async def adk_endpoint(input_data: RunAgentInput, request: Request):
    if extract_state_fn:
        extracted_state_dict = await extract_state_fn(request, input_data)
        if extracted_state_dict:
            existing_state = input_data.state if isinstance(input_data.state, dict) else {}
            merged_state = {**existing_state, **extracted_state_dict}
            input_data = input_data.model_copy(update={"state": merged_state})
```

---

## ✅ THE FIX

### Step 1: Extract Headers into State

When calling `add_adk_fastapi_endpoint()`, pass a function to extract the `X-User-Id` and `X-Session-Id` headers into the state:

```python
async def extract_user_and_session(request: Request, input_data: RunAgentInput) -> dict[str, Any]:
    """Extract X-User-Id and X-Session-Id headers into state."""
    state = {}
    
    user_id = request.headers.get("X-User-Id")
    session_id = request.headers.get("X-Session-Id")
    
    if user_id:
        state["_ag_ui_user_id"] = user_id
    if session_id:
        state["_ag_ui_session_id"] = session_id
    
    return state
```

### Step 2: Use `user_id_extractor` to Read from State

Create ADKAgent with a `user_id_extractor` that reads from the state:

```python
def extract_user_from_state(input: RunAgentInput) -> str:
    """Extract user ID from state (set by header extractor)."""
    if isinstance(input.state, dict):
        user_id = input.state.get("_ag_ui_user_id")
        if user_id:
            return str(user_id)
    # Fallback to thread_user if not found
    return f"thread_user_{input.thread_id}"

default_adk_agent = ADKAgent(
    adk_agent=agent,
    app_name=APP_NAME,
    user_id_extractor=extract_user_from_state,  # ← ADD THIS
    session_service=session_service,
    ...
)
```

### Step 3: Pass the Extractor to Endpoint

```python
add_adk_fastapi_endpoint(
    app, 
    default_adk_agent, 
    path="/ag-ui",
    extract_state_from_request=extract_user_and_session  # ← ADD THIS
)
```

---

## 📊 How It Works

### Flow Diagram

```
1. Frontend → /api/copilotkit (Next.js)
   ├─ Reads cookies: copilot_adk_user_id=3
   └─ Creates HttpAgent with headers: X-User-Id: 3

2. HttpAgent → /ag-ui (Backend FastAPI)
   ├─ FastAPI receives headers
   └─ Calls adk_endpoint(input_data, request)

3. adk_endpoint extracts headers
   ├─ Calls extract_user_and_session(request, input_data)
   ├─ Puts user_id in input_data.state["_ag_ui_user_id"] = "3"
   └─ Passes input_data to agent.run()

4. ADKAgent._get_user_id() is called
   ├─ Calls user_id_extractor(input_data)
   ├─ Reads input_data.state["_ag_ui_user_id"] = "3"
   └─ Returns "3" instead of "thread_user_xxx"

5. Database stores user_id = "3" ✅
```

---

## 🎯 Implementation Plan

### Phase 1: Update Backend (backend/main.py)

1. Create `extract_user_and_session()` function
2. Create `extract_user_from_state()` function  
3. Pass `user_id_extractor` to ADKAgent
4. Pass `extract_state_from_request` to add_adk_fastapi_endpoint

### Phase 2: Test

1. Restart backend
2. Send message from frontend
3. Check database: should show `user_id = 3` (not `thread_user_xxx`)

### Phase 3: Handle Session ID

Similarly extract and use `X-Session-Id` if needed for session management.

---

## 📝 Code Changes Required

**File:** `backend/main.py`

**Add these functions:**
```python
async def extract_user_and_session(request: Request, input_data: RunAgentInput) -> dict[str, Any]:
    """Extract X-User-Id and X-Session-Id from headers into state."""
    from fastapi import Request
    
    state = {}
    user_id = request.headers.get("X-User-Id")
    session_id = request.headers.get("X-Session-Id")
    
    if user_id:
        state["_ag_ui_user_id"] = user_id
    if session_id:
        state["_ag_ui_session_id"] = session_id
    
    return state

def extract_user_from_state(input: RunAgentInput) -> str:
    """Extract user ID from state set by header extractor."""
    if isinstance(input.state, dict):
        user_id = input.state.get("_ag_ui_user_id")
        if user_id:
            return str(user_id)
    return f"thread_user_{input.thread_id}"
```

**Update ADKAgent initialization:**
```python
default_adk_agent = ADKAgent(
    adk_agent=agent,
    app_name=APP_NAME,
    user_id_extractor=extract_user_from_state,  # ← ADD
    session_timeout_seconds=SESSION_TIMEOUT_SECONDS,
    use_in_memory_services=False,
    session_service=session_service,
)
```

**Update endpoint:**
```python
add_adk_fastapi_endpoint(
    app, 
    default_adk_agent, 
    path="/ag-ui",
    extract_state_from_request=extract_user_and_session  # ← ADD
)
```

---

## ✅ Expected Result

**Before:**
```
user_id: thread_user_54af7703-a550-4d35-b2a2-e85f59ee3d4d  ❌
```

**After:**
```
user_id: 3  ✅
```

---

## 🔗 Files Analyzed

1. `.venv/lib/python3.13/site-packages/ag_ui_adk/adk_agent.py` - User ID resolution logic
2. `.venv/lib/python3.13/site-packages/ag_ui_adk/endpoint.py` - FastAPI endpoint and header extraction
3. `backend/main.py` - Our backend implementation (needs updates)

---

## 🎉 Summary

**The ag-ui-adk library DOES support custom user IDs!**

We just need to:
1. Extract headers into `RunAgentInput.state` using `extract_state_from_request`
2. Use `user_id_extractor` to read from that state
3. Pass both to the ADKAgent and endpoint

This is the **official, supported way** to use custom user IDs with ag-ui-adk!
