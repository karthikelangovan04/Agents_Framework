# A2A-SDK Package Structure

**File Path**: `docs-a2a-sdk/01-Package-Structure.md`  
**Package**: `a2a-sdk` (version 0.3.22)

## Overview

This document provides a comprehensive overview of the A2A-SDK package structure, including all modules, classes, and their organization.

---

## Package Statistics

- **Total Modules**: 83
- **Total Classes**: 166
- **Total Functions**: 36
- **Total Methods**: 2,896
- **Type Classes**: 96 (protobuf-generated)

---

## Main Package Structure

```
a2a/
├── __init__.py              # Package initialization
├── _base.py                 # Base model classes
├── auth/                    # Authentication
│   └── user.py             # User types
├── client/                  # Client implementation
│   ├── auth/               # Client authentication
│   ├── transports/         # Transport protocols
│   ├── middleware/         # Client middleware
│   └── ...
├── server/                  # Server implementation
│   ├── apps/               # Application frameworks
│   ├── request_handlers/   # Request handlers
│   ├── agent_execution/    # Agent execution
│   ├── tasks/              # Task management
│   └── events/             # Event system
├── types/                   # Type definitions (96 classes)
├── utils/                   # Utility functions
├── grpc/                    # gRPC support (optional)
└── extensions/              # Extensions
```

---

## Core Modules

### 1. `a2a._base`

**Purpose**: Base classes for all A2A data models.

**Key Classes**:
- `A2ABaseModel` - Base Pydantic model with camelCase alias support

**Location**: `a2a/_base.py`

---

### 2. `a2a.auth`

**Purpose**: Authentication infrastructure.

**Submodules**:
- `a2a.auth.user` - User types (`User`, `UnauthenticatedUser`)

**Key Classes**:
- `User` - Authenticated user
- `UnauthenticatedUser` - Unauthenticated user

---

### 3. `a2a.client`

**Purpose**: Client implementation for A2A protocol.

**Submodules**:
- `a2a.client.auth` - Client authentication
- `a2a.client.transports` - Transport protocols
- `a2a.client.middleware` - Client middleware
- `a2a.client.base_client` - Base client
- `a2a.client.client` - Main client implementation
- `a2a.client.client_task_manager` - Task management
- `a2a.client.card_resolver` - Agent card resolution
- `a2a.client.errors` - Error classes
- `a2a.client.helpers` - Helper functions
- `a2a.client.legacy` - Legacy client support

**Key Classes**:
- `Client` - Main client (11 methods)
- `BaseClient` - Abstract base client (12 methods)
- `ClientConfig` - Client configuration (3 methods)
- `ClientTaskManager` - Task orchestration (6 methods)
- `ClientCallContext` - Call context (27 methods)
- `A2ACardResolver` - Card resolution (2 methods)

**Transports**:
- `JsonRpcTransport` - JSON-RPC transport (10 methods)
- `RestTransport` - REST transport (10 methods)
- `GrpcTransport` - gRPC transport (requires `[grpc]`)

---

### 4. `a2a.server`

**Purpose**: Server implementation for A2A agents.

**Submodules**:
- `a2a.server.apps` - Application frameworks
  - `a2a.server.apps.jsonrpc` - JSON-RPC apps
  - `a2a.server.apps.rest` - REST apps
- `a2a.server.request_handlers` - Request handlers
- `a2a.server.agent_execution` - Agent execution
- `a2a.server.tasks` - Task management
- `a2a.server.events` - Event system
- `a2a.server.context` - Server context
- `a2a.server.id_generator` - ID generation

**Key Classes**:
- `RequestHandler` - Base request handler (9 methods)
- `JSONRPCHandler` - JSON-RPC handler (11 methods)
- `RESTHandler` - REST handler (10 methods)
- `AgentExecutor` - Agent execution (2 methods)
- `RequestContext` - Request context (4 methods)
- `ServerCallContext` - Server context (27 methods)
- `TaskManager` - Task orchestration (6 methods)
- `TaskStore` - Task storage interface (3 methods)
- `InMemoryTaskStore` - In-memory storage (4 methods)
- `DatabaseTaskStore` - Database storage (requires `[sql]`)

**Application Frameworks**:
- `A2AFastAPI` - FastAPI integration (1 method)
- `A2AStarletteApplication` - Starlette integration (4 methods)
- `A2ARESTFastAPIApplication` - FastAPI REST adapter (2 methods)

---

### 5. `a2a.types`

**Purpose**: Type definitions (protobuf-generated).

**Statistics**: 96 classes

**Key Types**:
- `Message` - Message type
- `Task` - Task type
- `AgentCard` - Agent card type
- `A2ARequest` - Request type
- `A2AError` - Error type
- `AgentCapabilities` - Agent capabilities
- Plus 90 more types

**Note**: All types inherit from `A2ABaseModel` and provide 27 methods each (inherited from base model).

---

### 6. `a2a.utils`

**Purpose**: Utility functions and helpers.

**Submodules**:
- `a2a.utils.message` - Message utilities (3 functions)
- `a2a.utils.artifact` - Artifact handling (4 functions)
- `a2a.utils.proto_utils` - Protocol buffer conversion
  - `FromProto` - Protocol buffer conversion (33 methods)
  - `ToProto` - Protocol buffer conversion (30 methods)
- `a2a.utils.errors` - Error classes
  - `A2AServerError` - Base server error
  - `MethodNotImplementedError` - Method not implemented
  - `ServerError` - General server error (3 methods)
- `a2a.utils.helpers` - Helper functions (7 functions)
- `a2a.utils.task` - Task utilities (3 functions)
- `a2a.utils.telemetry` - Telemetry (2 functions)
- `a2a.utils.signing` - Signing utilities (requires `[signing]`)
- `a2a.utils.parts` - Message parts utilities (3 functions)
- `a2a.utils.error_handlers` - Error handlers (2 functions)

---

### 7. `a2a.grpc`

**Purpose**: gRPC support (optional, requires `[grpc]`).

**Submodules**:
- `a2a.grpc.a2a_pb2` - Protocol buffer definitions
- `a2a.grpc.a2a_pb2_grpc` - gRPC service definitions

---

### 8. `a2a.extensions`

**Purpose**: Extension system.

**Submodules**:
- `a2a.extensions.common` - Common extension utilities (3 functions)

---

## Module Breakdown by Category

### Client Modules (20+ modules)

```
a2a.client
├── base_client.py
├── client.py
├── client_config.py
├── client_factory.py
├── client_task_manager.py
├── card_resolver.py
├── errors.py
├── helpers.py
├── legacy.py
├── middleware.py
├── optionals.py
├── auth/
│   ├── credentials.py
│   └── interceptor.py
└── transports/
    ├── base.py
    ├── jsonrpc.py
    ├── rest.py
    └── grpc.py (optional)
```

### Server Modules (30+ modules)

```
a2a.server
├── context.py
├── id_generator.py
├── apps/
│   ├── jsonrpc/
│   │   ├── fastapi_app.py
│   │   ├── jsonrpc_app.py
│   │   └── starlette_app.py
│   └── rest/
│       ├── fastapi_app.py
│       └── rest_adapter.py
├── request_handlers/
│   ├── request_handler.py
│   ├── jsonrpc_handler.py
│   ├── rest_handler.py
│   ├── grpc_handler.py (optional)
│   ├── default_request_handler.py
│   └── response_helpers.py
├── agent_execution/
│   ├── agent_executor.py
│   ├── context.py
│   ├── request_context_builder.py
│   └── simple_request_context_builder.py
├── tasks/
│   ├── task_manager.py
│   ├── task_store.py
│   ├── inmemory_task_store.py
│   ├── database_task_store.py (optional)
│   ├── task_updater.py
│   ├── result_aggregator.py
│   ├── push_notification_sender.py
│   ├── base_push_notification_sender.py
│   ├── push_notification_config_store.py
│   ├── inmemory_push_notification_config_store.py
│   └── database_push_notification_config_store.py (optional)
└── events/
    ├── event_queue.py
    ├── event_consumer.py
    ├── queue_manager.py
    └── in_memory_queue_manager.py
```

### Utility Modules (10+ modules)

```
a2a.utils
├── message.py
├── artifact.py
├── proto_utils.py
├── errors.py
├── helpers.py
├── task.py
├── telemetry.py
├── signing.py (optional)
├── parts.py
├── error_handlers.py
└── constants.py
```

---

## Optional Dependencies

### Modules Requiring Extras

| Module | Extra Required | Purpose |
|--------|----------------|---------|
| `a2a.client.transports.grpc` | `[grpc]` | gRPC transport |
| `a2a.grpc.a2a_pb2_grpc` | `[grpc]` | gRPC services |
| `a2a.server.request_handlers.grpc_handler` | `[grpc]` | gRPC handler |
| `a2a.server.models` | `[sql]` | Database models |
| `a2a.server.tasks.database_task_store` | `[sql]` | Database task storage |
| `a2a.server.tasks.database_push_notification_config_store` | `[sql]` | Database push config |
| `a2a.utils.signing` | `[signing]` | JWT signing |

---

## Key Architectural Patterns

### 1. Transport Abstraction

- `ClientTransport` base class
- Multiple implementations: JSON-RPC, REST, gRPC
- Allows switching protocols without changing client code

### 2. Context Pattern

- `ClientCallContext` - Client-side context
- `ServerCallContext` - Server-side context
- `RequestContext` - Agent execution context

### 3. Factory Pattern

- `ClientFactory` - Creates clients
- `RequestContextBuilder` - Creates request contexts

### 4. Store Pattern

- `TaskStore` - Task storage interface
- `PushNotificationConfigStore` - Push config storage
- Multiple implementations: InMemory, Database

### 5. Handler Pattern

- `RequestHandler` - Base handler
- Protocol-specific handlers: JSON-RPC, REST, gRPC

---

## Import Examples

### Client Imports

```python
# Main client
from a2a.client import Client, ClientConfig

# Transports
from a2a.client.transports.rest import RestTransport
from a2a.client.transports.jsonrpc import JsonRpcTransport

# Context
from a2a.client.middleware import ClientCallContext

# Task management
from a2a.client.client_task_manager import ClientTaskManager
```

### Server Imports

```python
# Request handlers
from a2a.server.request_handlers.jsonrpc_handler import JSONRPCHandler
from a2a.server.request_handlers.rest_handler import RESTHandler

# Applications
from a2a.server.apps.jsonrpc.fastapi_app import A2AFastAPI

# Agent execution
from a2a.server.agent_execution.agent_executor import AgentExecutor
from a2a.server.agent_execution.context import RequestContext

# Task management
from a2a.server.tasks.task_manager import TaskManager
from a2a.server.tasks.inmemory_task_store import InMemoryTaskStore
```

### Type Imports

```python
# Core types
from a2a.types import Message, Task, AgentCard

# Request/response types
from a2a.types import A2ARequest, SendMessageRequest
```

---

## Comparison with ADK Package Structure

| Aspect | ADK | A2A SDK |
|--------|-----|---------|
| **Package Name** | `google.adk` | `a2a` |
| **Main Modules** | ~25 packages | 8 main areas |
| **Client/Server** | Unified (Agent) | Separate (Client/Server) |
| **Transport** | Built-in | Abstracted (multiple protocols) |
| **Types** | Runtime types | Protobuf-generated (96 types) |
| **State Management** | Session-based | Context-based + Task-based |

---

## Next Steps

1. **Client Development**: [02-Client-Package.md](02-Client-Package.md)
2. **Server Development**: [03-Server-Package.md](03-Server-Package.md)
3. **Context Management**: [04-Context-and-Memory.md](04-Context-and-Memory.md)
4. **Type Definitions**: [05-Types-Package.md](05-Types-Package.md)

---

**Last Updated:** February 2, 2026  
**A2A-SDK Version:** 0.3.22
