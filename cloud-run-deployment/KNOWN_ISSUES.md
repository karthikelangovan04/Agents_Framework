# Known Issues

## Issue: MCP Connection Async Context Error

### Status
🔴 **OPEN** - Workaround attempted, root cause identified

### Description
When deploying the ADK agent with MCP toolset to Cloud Run, the MCP connection fails with the following error:

```
ConnectionError: Failed to create MCP session: Failed to create MCP session: unhandled errors in a TaskGroup (1 sub-exception)
```

The underlying exception is:
```
RuntimeError: Attempted to exit cancel scope in a different task than it was entered in
```

### Root Cause
The MCP client library uses AnyIO's `TaskGroup` and `CancelScope` for async context management. When running in Cloud Run's request handling environment, the async context boundaries don't align properly, causing the cancel scope to be entered in one task but exited in another.

This is a known limitation with:
- Python 3.11 and earlier (partially fixed in Python 3.12)
- AnyIO's cancel scope management in certain async environments
- Cloud Run's request handling model

### Affected Components
- **MCPToolset** with `StreamableHTTPConnectionParams`
- Cloud Run deployment environment
- Python 3.11/3.12 (though 3.12 should help)

### Attempted Fixes

1. ✅ **Upgraded to Python 3.12**
   - Updated Dockerfile to use `python:3.12-slim`
   - Python 3.12 has improved task context management
   - **Result**: Error persists, but Python version confirmed correct

2. ✅ **Fixed Authentication Approach**
   - Changed from static headers to `header_provider` callback
   - Headers now generated dynamically when connection is established
   - **Result**: Authentication works correctly, but async context issue remains

3. ✅ **Fixed Runner Initialization**
   - Added `app_name` parameter to `Runner` initialization
   - **Result**: Runner initializes correctly

4. ✅ **Fixed Session Management**
   - Added session creation if it doesn't exist
   - **Result**: Sessions are created correctly

### Current State

**What Works:**
- ✅ ADK Agent deploys successfully to Cloud Run
- ✅ MCP Server deploys successfully
- ✅ IAM permissions configured correctly
- ✅ Vertex AI authentication working
- ✅ Service-to-service authentication headers generated correctly
- ✅ Agent initialization and session management working

**What Doesn't Work:**
- ❌ MCP connection establishment fails due to async context issue
- ❌ Agent cannot use MCP tools

### Error Details

**Full Stack Trace:**
```
ConnectionError: Failed to create MCP session: Failed to create MCP session: unhandled errors in a TaskGroup (1 sub-exception)
  File "/usr/local/lib/python3.12/site-packages/google/adk/tools/mcp_tool/mcp_session_manager.py", line 471, in create_session
    session = await asyncio.wait_for(
  File "/usr/local/lib/python3.12/asyncio/tasks.py", line 520, in wait_for
    return await fut
  File "/usr/local/lib/python3.12/contextlib.py", line 659, in enter_async_context
    result = await _enter(cm)
  File "/usr/local/lib/python3.12/site-packages/google/adk/tools/mcp_tool/session_context.py", line 144, in __aenter__
    return await self.start()
  File "/usr/local/lib/python3.12/site-packages/google/adk/tools/mcp_tool/session_context.py", line 112, in start
    raise ConnectionError(...)
RuntimeError: Attempted to exit cancel scope in a different task than it was entered in
```

**Location:**
- `mcp/client/streamable_http.py` line 647: `streamable_http_client`
- `anyio/_backends/_asyncio.py` line 789: `__aexit__`

### Potential Solutions

1. **Use SSE Connection Instead of StreamableHTTP**
   - Try `SseConnectionParams` instead of `StreamableHTTPConnectionParams`
   - May have different async context handling
   - **Status**: Not tested

2. **Report to ADK Team**
   - This appears to be a compatibility issue between MCP client library and Cloud Run
   - May require changes to `SessionContext` or `MCPSessionManager`
   - **Status**: Should be reported

3. **Use Local MCP Server**
   - Deploy MCP server as a sidecar or use stdio connection
   - May avoid HTTP async context issues
   - **Status**: Not tested

4. **Wait for Library Update**
   - AnyIO or MCP client library may fix this in future versions
   - **Status**: Monitor for updates

### Workaround

Currently, there is no working workaround. The deployment infrastructure is correct, but the MCP connection cannot be established due to the async context issue.

### Related Files

- `/cloud-run-deployment/adk-agent/agent.py` - MCP toolset configuration
- `/cloud-run-deployment/adk-agent/main.py` - FastAPI application
- `/cloud-run-deployment/adk-agent/Dockerfile` - Container configuration
- `/cloud-run-deployment/adk-agent/auth_helper.py` - Authentication helper

### References

- [AnyIO CancelScope Documentation](https://anyio.readthedocs.io/en/stable/cancellation.html)
- [Python 3.12 Task Context Improvements](https://docs.python.org/3.12/whatsnew/3.12.html#asyncio)
- [ADK MCP Tools Documentation](./adk/docs/15-MCP-Tools-Dynamic-Loading.md)

### Next Steps

1. Report this issue to the Google ADK team
2. Test with SSE connection parameters as alternative
3. Consider using local MCP server connection if available
4. Monitor ADK library updates for fixes

---

**Last Updated:** 2026-02-17
**Reported By:** Deployment troubleshooting session
**Severity:** High (blocks MCP functionality)
