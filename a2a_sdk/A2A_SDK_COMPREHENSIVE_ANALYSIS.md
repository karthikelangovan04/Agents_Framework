# A2A-SDK Comprehensive Analysis

**Generated:** February 2, 2026  
**Package:** a2a-sdk  
**Version:** 0.3.22 (latest from PyPI)  
**Analysis Method:** Comprehensive introspection of all modules, classes, and methods

---

## Executive Summary

The **a2a-sdk** (Agent-to-Agent SDK) is a comprehensive Python SDK for building A2A protocol-compliant agents. This analysis reveals:

- **83 modules** across 8 main package areas
- **166 classes** providing core functionality
- **36 standalone functions** for utilities and helpers
- **2,896 methods** across all classes
- **96 type classes** in `a2a.types` module (protobuf-generated)

### Key Differences from Local A2A Directory

The local `A2A/` directory appears to be a virtual environment with documentation and examples, but **does not contain the actual a2a-sdk source code**. The installed `a2a-sdk` package (version 0.3.22) is significantly more comprehensive than what's documented in the local examples.

---

## Package Structure

### Core Modules

#### 1. **a2a._base**
- **A2ABaseModel**: Base class for all A2A data models
  - Extends Pydantic's `BaseModel`
  - Provides camelCase alias support with deprecation warnings
  - 27 methods including serialization, validation, and model utilities

#### 2. **a2a.auth** & **a2a.auth.user**
- **User**: Base user class
- **UnauthenticatedUser**: Unauthenticated user representation
- Authentication infrastructure for A2A agents

#### 3. **a2a.client** - Client Implementation
The client package provides comprehensive client functionality:

**Core Client Classes:**
- **BaseClient**: Abstract base client (12 methods)
- **Client**: Main client implementation (11 methods)
- **ClientConfig**: Client configuration (3 methods)
- **A2AClient**: Legacy client (9 methods)
- **A2AGrpcClient**: gRPC client (requires `a2a-sdk[grpc]`)

**Client Components:**
- **ClientFactory**: Factory for creating clients (4 methods)
- **ClientTaskManager**: Task management (6 methods)
- **A2ACardResolver**: Agent card resolution (2 methods)
- **ClientCallContext**: Call context with 27 methods
- **ClientCallInterceptor**: Interceptor pattern

**Transports:**
- **ClientTransport**: Base transport (9 methods)
- **JsonRpcTransport**: JSON-RPC transport (10 methods)
- **RestTransport**: REST transport (10 methods)
- **GrpcTransport**: gRPC transport (requires `a2a-sdk[grpc]`)

**Authentication:**
- **CredentialService**: Credential management
- **InMemoryContextCredentialStore**: In-memory credential storage
- **AuthInterceptor**: Authentication interceptor

**Error Handling:**
- **A2AClientError**: Base client error
- **A2AClientHTTPError**: HTTP-specific errors
- **A2AClientInvalidArgsError**: Invalid argument errors
- **A2AClientInvalidStateError**: Invalid state errors
- **A2AClientJSONError**: JSON parsing errors
- Plus 2 more error classes

#### 4. **a2a.server** - Server Implementation
Comprehensive server implementation with multiple protocol support:

**Application Frameworks:**
- **A2AFastAPI**: FastAPI integration for JSON-RPC (1 method)
- **A2AFastAPIApplication**: FastAPI application wrapper (3 methods)
- **A2AStarletteApplication**: Starlette application (4 methods)
- **A2ARESTFastAPIApplication**: FastAPI REST adapter (2 methods)
- **JSONRPCApplication**: JSON-RPC application (2 methods)
- **RESTAdapter**: REST protocol adapter (4 methods)

**Request Handling:**
- **RequestHandler**: Base request handler (9 methods)
- **DefaultRequestHandler**: Default implementation (10 methods)
- **JSONRPCHandler**: JSON-RPC handler (11 methods)
- **RESTHandler**: REST handler (10 methods)
- **GrpcHandler**: gRPC handler (requires `a2a-sdk[grpc]`)

**Agent Execution:**
- **AgentExecutor**: Executes agent logic (2 methods)
- **RequestContext**: Request context (4 methods)
- **RequestContextBuilder**: Context builder interface
- **SimpleRequestContextBuilder**: Simple implementation (2 methods)

**Server Context:**
- **ServerCallContext**: Server call context (27 methods)

**Task Management:**
- **TaskManager**: Task orchestration (6 methods)
- **TaskStore**: Task storage interface (3 methods)
- **InMemoryTaskStore**: In-memory storage (4 methods)
- **DatabaseTaskStore**: Database storage (requires SQL extras)
- **TaskUpdater**: Task updates (12 methods)
- **ResultAggregator**: Result aggregation (4 methods)

**Push Notifications:**
- **PushNotificationSender**: Push notification interface
- **BasePushNotificationSender**: Base implementation (2 methods)
- **PushNotificationConfigStore**: Config storage interface (3 methods)
- **InMemoryPushNotificationConfigStore**: In-memory config (4 methods)
- **DatabasePushNotificationConfigStore**: Database config (requires SQL extras)

**Event System:**
- **EventQueue**: Event queue (8 methods)
- **EventConsumer**: Event consumer (4 methods)
- **QueueManager**: Queue management (5 methods)
- **InMemoryQueueManager**: In-memory queue manager (6 methods)
- **NoTaskQueue**: Exception class
- **TaskQueueExists**: Exception class

**ID Generation:**
- **IDGenerator**: ID generation interface
- **UUIDGenerator**: UUID-based generator
- **IDGeneratorContext**: Context for ID generation (27 methods)

#### 5. **a2a.types** - Type Definitions
**96 classes** - Protobuf-generated type definitions including:

- **A2A**: Main protocol type (27 methods)
- **A2ARequest**: Request type
- **A2AError**: Error type
- **AgentCapabilities**: Agent capabilities
- **APIKeySecurityScheme**: Security scheme
- Plus 91 more type classes

All type classes inherit from `A2ABaseModel` and provide 27 methods each (inherited from base model).

#### 6. **a2a.utils** - Utility Functions
Comprehensive utility modules:

**a2a.utils.artifact** (4 functions):
- Artifact handling utilities

**a2a.utils.error_handlers** (2 functions):
- Error handling utilities

**a2a.utils.helpers** (7 functions):
- General helper functions

**a2a.utils.message** (3 functions):
- Message handling utilities

**a2a.utils.parts** (3 functions):
- Message parts utilities

**a2a.utils.proto_utils**:
- **FromProto**: Protocol buffer conversion (33 methods)
- **ToProto**: Protocol buffer conversion (30 methods)
- 4 utility functions

**a2a.utils.task** (3 functions):
- Task utilities

**a2a.utils.telemetry** (2 functions):
- Telemetry utilities

**a2a.utils.errors**:
- **A2AServerError**: Base server error
- **MethodNotImplementedError**: Method not implemented error
- **ServerError**: General server error (3 methods)

**a2a.utils.signing**:
- Signing utilities (requires `a2a-sdk[signing]`)

#### 7. **a2a.grpc** - gRPC Support
- **a2a_pb2**: Protocol buffer definitions
- **a2a_pb2_grpc**: gRPC service definitions (requires `a2a-sdk[grpc]`)

#### 8. **a2a.extensions** - Extensions
- **a2a.extensions.common**: Common extension utilities (3 functions)

---

## Optional Dependencies

The SDK supports several optional extras:

### Required Extras for Specific Features:

1. **`a2a-sdk[grpc]`**: gRPC support
   - Required for: `a2a.client.transports.grpc`, `a2a.grpc.a2a_pb2_grpc`, `a2a.server.request_handlers.grpc_handler`

2. **`a2a-sdk[signing]`**: JWT signing support
   - Required for: `a2a.utils.signing`

3. **`a2a-sdk[sql]` / `a2a-sdk[postgresql]` / `a2a-sdk[mysql]` / `a2a-sdk[sqlite]`**: Database support
   - Required for: `a2a.server.models`, `a2a.server.tasks.database_task_store`, `a2a.server.tasks.database_push_notification_config_store`

---

## Key Classes and Their Methods

### Client Classes

#### `Client` (a2a.client.client)
Main client class with 11 methods:
- Client initialization and configuration
- Message sending
- Conversation management
- Agent discovery

#### `BaseClient` (a2a.client.base_client)
Abstract base with 12 methods:
- Transport management
- Authentication handling
- Request/response processing
- Error handling

### Server Classes

#### `RequestHandler` (a2a.server.request_handlers.request_handler)
Base request handler with 9 methods:
- Request processing
- Response generation
- Error handling
- Context management

#### `TaskManager` (a2a.server.tasks.task_manager)
Task orchestration with 6 methods:
- Task creation
- Task status tracking
- Result aggregation
- Task lifecycle management

### Type Classes

All 96 type classes in `a2a.types` inherit from `A2ABaseModel` and provide:
- Pydantic model validation
- JSON serialization/deserialization
- CamelCase alias support
- Model copying and construction
- Field access and manipulation

---

## Comparison with explore_a2a.py

The `explore_a2a.py` script was designed for `python_a2a` package, which appears to be a different package structure. The actual `a2a-sdk` package:

1. **Uses `a2a` as the package name**, not `python_a2a`
2. **Has a more comprehensive structure** with 83 modules vs. the expected modules in explore_a2a.py
3. **Includes protocol-specific implementations** (JSON-RPC, REST, gRPC)
4. **Has extensive server-side functionality** not visible in client-only usage
5. **Includes task management and event systems** for complex agent workflows

---

## Architecture Patterns

### 1. **Transport Abstraction**
The SDK uses a transport abstraction layer:
- `ClientTransport` base class
- Multiple implementations: JSON-RPC, REST, gRPC
- Allows switching protocols without changing client code

### 2. **Context Pattern**
Extensive use of context objects:
- `ClientCallContext` (27 methods)
- `ServerCallContext` (27 methods)
- `IDGeneratorContext` (27 methods)
- `RequestContext` for agent execution

### 3. **Factory Pattern**
- `ClientFactory` for creating clients
- `RequestContextBuilder` for context creation

### 4. **Interceptor Pattern**
- `ClientCallInterceptor` for client-side interceptors
- `AuthInterceptor` for authentication

### 5. **Store Pattern**
Multiple store interfaces:
- `TaskStore` with in-memory and database implementations
- `PushNotificationConfigStore` with multiple implementations
- `CredentialStore` for authentication

---

## Usage Recommendations

### For Client Development:
```python
from a2a.client import Client, ClientConfig
from a2a.client.transports.rest import RestTransport

# Create client
config = ClientConfig(transport=RestTransport(...))
client = Client(config)
```

### For Server Development:
```python
from a2a.server.apps.jsonrpc.fastapi_app import A2AFastAPI
from a2a.server.request_handlers.jsonrpc_handler import JSONRPCHandler

# Create FastAPI app
app = A2AFastAPI(handler=JSONRPCHandler(...))
```

### For Type Definitions:
```python
from a2a.types import A2A, A2ARequest, AgentCapabilities

# Use type-safe models
request = A2ARequest(...)
```

---

## Statistics Summary

| Category | Count |
|----------|-------|
| Total Modules | 83 |
| Total Classes | 166 |
| Total Functions | 36 |
| Total Methods | 2,896 |
| Type Classes | 96 |
| Client Classes | ~20 |
| Server Classes | ~30 |
| Utility Functions | ~25 |

---

## Files Generated

1. **`a2a_sdk_comprehensive_analysis.json`**: Complete JSON analysis (22,532 lines)
   - Contains full details of all classes, methods, signatures, and documentation
   - Suitable for programmatic analysis and tooling

2. **`analyze_a2a_sdk.py`**: Analysis script
   - Reusable script for future analysis
   - Can be adapted for other packages

---

## Next Steps

1. **Install Optional Extras**: For full functionality, install:
   ```bash
   uv pip install "a2a-sdk[grpc,signing,postgresql]"
   ```

2. **Explore Examples**: Review the examples in `A2A/examples/` directory

3. **Read Documentation**: Check the official A2A protocol documentation

4. **Build Agents**: Use the comprehensive API to build production-ready A2A agents

---

## Conclusion

The **a2a-sdk** package is a production-ready, comprehensive SDK for building A2A protocol-compliant agents. It provides:

- ✅ Complete client and server implementations
- ✅ Multiple transport protocols (JSON-RPC, REST, gRPC)
- ✅ Type-safe models with Pydantic
- ✅ Task management and event systems
- ✅ Authentication and security support
- ✅ Extensible architecture with clear patterns
- ✅ Framework integrations (FastAPI, Starlette)

The SDK is significantly more comprehensive than what's visible in basic usage, with extensive server-side functionality, task orchestration, and event systems for building complex multi-agent systems.

---

**Analysis completed:** February 2, 2026  
**Analysis tool:** `analyze_a2a_sdk.py`  
**Environment:** UV venv with a2a-sdk 0.3.22
