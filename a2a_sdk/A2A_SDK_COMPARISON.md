# A2A-SDK Comparison: Expected vs. Actual

## Overview

This document compares what was expected from `explore_a2a.py` (designed for `python_a2a`) with what we actually found in the installed `a2a-sdk` package.

---

## Key Findings

### 1. Package Name Mismatch

| Expected (explore_a2a.py) | Actual (a2a-sdk) |
|---------------------------|------------------|
| `python_a2a` | `a2a` |
| Module structure: `python_a2a.*` | Module structure: `a2a.*` |

**Conclusion:** The `explore_a2a.py` script was designed for a different package (`python_a2a`) than what's actually installed (`a2a-sdk` with package name `a2a`).

---

### 2. Expected Modules (from explore_a2a.py)

The script expected these modules:
```python
modules_to_explore = [
    'python_a2a',
    'python_a2a.server',
    'python_a2a.client',
    'python_a2a.models',
    'python_a2a.workflow',
    'python_a2a.mcp',
    'python_a2a.langchain',
    'python_a2a.discovery',
]
```

### 3. Actual Modules (from a2a-sdk)

The actual `a2a-sdk` package has **83 modules** organized as:

```
a2a/
├── _base                    # Base model classes
├── auth/                    # Authentication
│   └── user/
├── client/                  # Client implementation
│   ├── auth/
│   │   ├── credentials/
│   │   └── interceptor/
│   ├── transports/
│   │   ├── base/
│   │   ├── grpc/           # Optional: requires [grpc]
│   │   ├── jsonrpc/
│   │   └── rest/
│   ├── legacy/
│   └── middleware/
├── extensions/              # Extensions
│   └── common/
├── grpc/                    # gRPC support (optional)
│   ├── a2a_pb2
│   └── a2a_pb2_grpc
├── server/                  # Server implementation
│   ├── agent_execution/
│   │   ├── agent_executor/
│   │   ├── context/
│   │   ├── request_context_builder/
│   │   └── simple_request_context_builder/
│   ├── apps/
│   │   ├── jsonrpc/
│   │   │   ├── fastapi_app/
│   │   │   ├── jsonrpc_app/
│   │   │   └── starlette_app/
│   │   └── rest/
│   │       ├── fastapi_app/
│   │       └── rest_adapter/
│   ├── events/
│   │   ├── event_consumer/
│   │   ├── event_queue/
│   │   ├── in_memory_queue_manager/
│   │   └── queue_manager/
│   ├── id_generator/
│   ├── models/              # Optional: requires [sql]
│   ├── request_handlers/
│   │   ├── default_request_handler/
│   │   ├── grpc_handler/    # Optional: requires [grpc]
│   │   ├── jsonrpc_handler/
│   │   ├── request_handler/
│   │   ├── response_helpers/
│   │   └── rest_handler/
│   └── tasks/
│       ├── base_push_notification_sender/
│       ├── database_push_notification_config_store/  # Optional
│       ├── database_task_store/                      # Optional
│       ├── inmemory_push_notification_config_store/
│       ├── inmemory_task_store/
│       ├── push_notification_config_store/
│       ├── push_notification_sender/
│       ├── result_aggregator/
│       ├── task_manager/
│       ├── task_store/
│       └── task_updater/
├── types/                   # 96 protobuf-generated type classes
└── utils/                   # Utility functions
    ├── artifact/
    ├── constants/
    ├── error_handlers/
    ├── errors/
    ├── helpers/
    ├── message/
    ├── parts/
    ├── proto_utils/
    ├── signing/             # Optional: requires [signing]
    ├── task/
    └── telemetry/
```

---

## Module Comparison

### Expected Modules → Actual Equivalent

| Expected Module | Actual Module(s) | Notes |
|----------------|------------------|-------|
| `python_a2a.server` | `a2a.server.*` | Much more comprehensive with submodules |
| `python_a2a.client` | `a2a.client.*` | More comprehensive with transports, auth, etc. |
| `python_a2a.models` | `a2a.types` | 96 type classes (protobuf-generated) |
| `python_a2a.workflow` | `a2a.server.tasks.*` | Task management system |
| `python_a2a.mcp` | ❌ Not found | May be in extensions or not present |
| `python_a2a.langchain` | ❌ Not found | May be in extensions or not present |
| `python_a2a.discovery` | `a2a.client.card_resolver` | Agent card resolution |

---

## Expected Classes (from explore_a2a.py)

The script expected these key classes:
```python
key_classes = [
    'A2AServer', 
    'A2AClient', 
    'Message', 
    'Conversation', 
    'AgentCard', 
    'Flow', 
    'OpenAIA2AServer', 
    'AnthropicA2AServer'
]
```

### Actual Classes Found

| Expected Class | Actual Equivalent | Location |
|---------------|-------------------|----------|
| `A2AServer` | `A2AFastAPI`, `A2AStarletteApplication`, `A2ARESTFastAPIApplication` | `a2a.server.apps.*` |
| `A2AClient` | `Client`, `BaseClient`, `A2AClient` (legacy) | `a2a.client.*` |
| `Message` | Types in `a2a.types` | `a2a.types` |
| `Conversation` | Types in `a2a.types` | `a2a.types` |
| `AgentCard` | Types in `a2a.types` | `a2a.types` |
| `Flow` | `TaskManager`, `TaskStore` | `a2a.server.tasks.*` |
| `OpenAIA2AServer` | ❌ Not found | May be in extensions |
| `AnthropicA2AServer` | ❌ Not found | May be in extensions |

---

## Architecture Differences

### Expected Architecture (from explore_a2a.py)
- Simple client/server model
- Direct class imports
- Workflow support
- MCP integration
- LangChain integration

### Actual Architecture (a2a-sdk)
- **Transport Abstraction**: Multiple transport protocols (JSON-RPC, REST, gRPC)
- **Framework Integration**: FastAPI, Starlette support
- **Task Management**: Comprehensive task orchestration system
- **Event System**: Event queues and consumers
- **Authentication**: Credential management and interceptors
- **Type Safety**: 96 protobuf-generated type classes
- **Extensibility**: Extension system for custom functionality

---

## What's Missing (Expected but Not Found)

1. **`python_a2a.mcp`**: MCP (Model Context Protocol) integration
   - May be in `a2a.extensions` or not included in base package
   - May require optional extras

2. **`python_a2a.langchain`**: LangChain integration
   - May be in `a2a.extensions` or not included in base package
   - May require optional extras

3. **`OpenAIA2AServer` / `AnthropicA2AServer`**: Provider-specific servers
   - May be in extensions or examples
   - May require separate packages

4. **`Flow` class**: Workflow class
   - Replaced by `TaskManager` and `TaskStore` system

---

## What's Additional (Not Expected but Found)

1. **Transport Layer**: Complete abstraction for multiple protocols
2. **Framework Integrations**: FastAPI and Starlette support
3. **Task Management**: Comprehensive task orchestration
4. **Event System**: Event queues and consumers
5. **Push Notifications**: Push notification system
6. **ID Generation**: Configurable ID generation
7. **Request Context Builders**: Flexible context creation
8. **Middleware System**: Client-side middleware/interceptors
9. **Error Handling**: Comprehensive error classes
10. **Telemetry**: Built-in telemetry support

---

## Conclusion

The `a2a-sdk` package is **significantly more comprehensive** than what was expected from `explore_a2a.py`. The differences include:

1. **Different package name**: `a2a` vs `python_a2a`
2. **More modular structure**: 83 modules vs. expected 8
3. **More comprehensive**: 166 classes vs. expected ~8 key classes
4. **More protocols**: JSON-RPC, REST, gRPC vs. expected single protocol
5. **More features**: Task management, events, push notifications, etc.

The local `A2A/` directory contains documentation and examples but **not the actual SDK source code**. The actual SDK is installed via `pip install a2a-sdk` and provides a much richer API than what's visible in basic usage.

---

## Recommendations

1. **Update `explore_a2a.py`**: Modify to work with `a2a` package instead of `python_a2a`
2. **Use `analyze_a2a_sdk.py`**: This script correctly analyzes the `a2a-sdk` package
3. **Review Optional Extras**: Install `[grpc]`, `[signing]`, `[sql]` extras for full functionality
4. **Check Extensions**: Look in `a2a.extensions` for MCP and LangChain integrations
5. **Review Examples**: Check `A2A/examples/` for usage patterns

---

**Comparison Date:** February 2, 2026  
**a2a-sdk Version:** 0.3.22
