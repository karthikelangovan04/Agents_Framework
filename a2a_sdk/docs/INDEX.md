# A2A-SDK Documentation Index

**File Path**: `docs-a2a-sdk/INDEX.md`  
**Package**: `a2a-sdk` (version 0.3.22)

Welcome to the comprehensive documentation for A2A-SDK (Agent-to-Agent SDK). This index provides an overview of all available documentation and guides you to the right resources for your needs.

## 📚 Documentation Overview

This documentation set covers all major packages and features of A2A-SDK, with detailed examples, runnable code samples, and comparisons with Google ADK framework.

## 🚀 Getting Started

**New to A2A-SDK?** Start here:

1. **[Setup and Installation Guide](00-Setup-and-Installation.md)** (`docs-a2a-sdk/00-Setup-and-Installation.md`)
   - Setting up virtual environment with UV
   - Installing a2a-sdk
   - Optional extras installation
   - Quick start guide

2. **[Package Structure Overview](01-Package-Structure.md)** (`docs-a2a-sdk/01-Package-Structure.md`)
   - Complete module breakdown
   - Package organization
   - Key components overview

## 📦 Core Packages

### 1. [Client Package](02-Client-Package.md) (`docs-a2a-sdk/02-Client-Package.md`)
The client implementation for A2A protocol - learn how to create and use A2A clients.

**Topics Covered:**
- Creating A2A clients
- Client configuration
- Transport protocols (JSON-RPC, REST, gRPC)
- Authentication and credentials
- Task management
- Message sending and streaming

**Key Classes:**
- `Client` - Main client implementation
- `BaseClient` - Abstract base client
- `ClientConfig` - Client configuration
- `ClientTaskManager` - Task orchestration
- `ClientCallContext` - Call context management

### 2. [Server Package](03-Server-Package.md) (`docs-a2a-sdk/03-Server-Package.md`)
Server implementation for building A2A agent servers.

**Topics Covered:**
- Creating A2A servers
- Request handling
- Agent execution
- Framework integrations (FastAPI, Starlette)
- Task management
- Event system
- Push notifications

**Key Classes:**
- `RequestHandler` - Base request handler
- `JSONRPCHandler` - JSON-RPC handler
- `RESTHandler` - REST handler
- `AgentExecutor` - Agent execution
- `TaskManager` - Task orchestration
- `ServerCallContext` - Server context

### 3. [Context and Memory Management](04-Context-and-Memory.md) (`docs-a2a-sdk/04-Context-and-Memory.md`)
Understanding how A2A SDK manages context and memory (short-term and long-term).

**Topics Covered:**
- Short-term context (ClientCallContext, ServerCallContext)
- Long-term memory (conversation storage)
- Context retention strategies
- Comparison with ADK framework
- Best practices for context management

**Key Concepts:**
- Client-side context retention
- Server-side context management
- Conversation persistence
- Task-based context tracking

### 4. [Types Package](05-Types-Package.md) (`docs-a2a-sdk/05-Types-Package.md`)
Type definitions and data models for A2A protocol.

**Topics Covered:**
- Message types
- Task types
- Agent card types
- Request/response types
- Protocol buffer types

**Key Classes:**
- `Message` - Message type
- `Task` - Task type
- `AgentCard` - Agent card type
- `A2ARequest` - Request type
- Plus 96 protobuf-generated types

### 5. [Transports Package](06-Transports-Package.md) (`docs-a2a-sdk/06-Transports-Package.md`)
Transport layer implementations for different protocols.

**Topics Covered:**
- JSON-RPC transport
- REST transport
- gRPC transport (optional)
- Transport abstraction
- Protocol selection

**Key Classes:**
- `ClientTransport` - Base transport
- `JsonRpcTransport` - JSON-RPC implementation
- `RestTransport` - REST implementation
- `GrpcTransport` - gRPC implementation

### 6. [Task Management](07-Task-Management.md) (`docs-a2a-sdk/07-Task-Management.md`)
Task orchestration and lifecycle management.

**Topics Covered:**
- Task creation and tracking
- Task stores (in-memory, database)
- Task updates and status
- Result aggregation
- Push notifications

**Key Classes:**
- `TaskManager` - Task orchestration
- `TaskStore` - Task storage interface
- `InMemoryTaskStore` - In-memory storage
- `DatabaseTaskStore` - Database storage
- `TaskUpdater` - Task updates
- `ResultAggregator` - Result aggregation

### 7. [Authentication Package](08-Authentication.md) (`docs-a2a-sdk/08-Authentication.md`)
Authentication and credential management.

**Topics Covered:**
- Credential services
- Credential stores
- Authentication interceptors
- Security schemes
- User management

**Key Classes:**
- `CredentialService` - Credential management
- `InMemoryContextCredentialStore` - In-memory credentials
- `AuthInterceptor` - Authentication interceptor
- `User` / `UnauthenticatedUser` - User types

### 8. [Event System](09-Event-System.md) (`docs-a2a-sdk/09-Event-System.md`)
Event queues and consumers for asynchronous processing.

**Topics Covered:**
- Event queues
- Event consumers
- Queue managers
- In-memory queues
- Event processing

**Key Classes:**
- `EventQueue` - Event queue
- `EventConsumer` - Event consumer
- `QueueManager` - Queue management
- `InMemoryQueueManager` - In-memory queues

### 9. [Utilities Package](10-Utilities.md) (`docs-a2a-sdk/10-Utilities.md`)
Utility functions and helpers.

**Topics Covered:**
- Message utilities
- Artifact handling
- Protocol buffer utilities
- Error handling
- Telemetry
- Task utilities

**Key Modules:**
- `a2a.utils.message` - Message utilities
- `a2a.utils.artifact` - Artifact handling
- `a2a.utils.proto_utils` - Protocol buffer conversion
- `a2a.utils.errors` - Error classes
- `a2a.utils.telemetry` - Telemetry

## 🔧 Specialized Topics

### [Context Retention: A2A SDK vs ADK](04-Context-and-Memory.md) (`docs-a2a-sdk/04-Context-and-Memory.md`)
Deep dive into how A2A SDK manages context compared to Google ADK:

- **Short-term context**: ClientCallContext, ServerCallContext, RequestContext
- **Long-term memory**: Conversation storage, task persistence
- **Context flow**: How context flows in multi-agent systems
- **Comparison**: Side-by-side comparison with ADK's session/memory system
- **Best practices**: Context retention strategies

### [A2A Multi-Agent Orchestration](11-Multi-Agent-Orchestration.md) (`docs-a2a-sdk/11-Multi-Agent-Orchestration.md`)
How to build multi-agent systems with A2A SDK:

- Orchestrator patterns
- Context passing between agents
- Task coordination
- State management across agents

## 🎯 Quick Reference Guide

### I want to...

**Create an A2A client:**
→ [Client Package - Example 1](02-Client-Package.md#example-1-basic-client)

**Create an A2A server:**
→ [Server Package - Example 1](03-Server-Package.md#example-1-basic-server)

**Understand context retention:**
→ [Context and Memory Management](04-Context-and-Memory.md)

**Use JSON-RPC transport:**
→ [Transports Package - JSON-RPC](06-Transports-Package.md#json-rpc-transport)

**Manage tasks:**
→ [Task Management - Example 1](07-Task-Management.md#example-1-basic-task-management)

**Add authentication:**
→ [Authentication Package - Example 1](08-Authentication.md#example-1-basic-authentication)

**Handle events:**
→ [Event System - Example 1](09-Event-System.md#example-1-basic-event-queue)

## 📊 Comparison with Google ADK

| Feature | A2A SDK | Google ADK |
|---------|---------|------------|
| **Context Management** | ClientCallContext, ServerCallContext | Session, InvocationContext |
| **Long-term Memory** | Conversation storage, Task persistence | MemoryService, MemoryBank |
| **Short-term Context** | RequestContext, CallContext | Session.events, Session.state |
| **State Management** | Task-based state | Hierarchical state (app/user/session) |
| **Session Management** | Conversation-based | SessionService |
| **Multi-agent** | Task orchestration | RemoteA2aAgent |

## 📁 Example Files

All runnable examples are located in the `A2A/examples/` directory:

- `simple_client.py` - Basic client example
- `simple_server.py` - Basic server example
- `multi_agent_chat.py` - Multi-agent system
- `conversation_storage.py` - Conversation persistence
- `calculator_agent.py` - Agent with function calling

## 🔗 Package Dependencies

Understanding how packages relate:

```
Setup & Installation
    ↓
Types (Core Models)
    ├── Client
    │   ├── Transports
    │   ├── Authentication
    │   └── Task Management
    ├── Server
    │   ├── Request Handlers
    │   ├── Agent Execution
    │   ├── Task Management
    │   └── Event System
    └── Utilities
```

## 📖 Documentation Structure

Each package documentation follows this structure:

1. **Overview** - What the package does
2. **Key Classes** - Main components
3. **Architecture** - How it works
4. **Examples** - Runnable code samples
5. **Best Practices** - Recommended approaches
6. **Comparison with ADK** - How it differs from Google ADK
7. **Troubleshooting** - Common issues and solutions
8. **Related Documentation** - Links to related docs

## 🛠️ Development Workflow

1. **Setup** - Follow [Setup Guide](00-Setup-and-Installation.md)
2. **Learn Core** - Read [Package Structure](01-Package-Structure.md)
3. **Build Client** - Explore [Client Package](02-Client-Package.md)
4. **Build Server** - Create with [Server Package](03-Server-Package.md)
5. **Understand Context** - Study [Context and Memory](04-Context-and-Memory.md)
6. **Scale** - Use [Multi-Agent Orchestration](11-Multi-Agent-Orchestration.md)

## 📚 Additional Resources

- [A2A Protocol Documentation](https://a2aprotocol.org/)
- [A2A SDK PyPI Package](https://pypi.org/project/a2a-sdk/)
- [A2A Protocol Specification](https://a2aprotocol.org/latest/)
- [Google ADK Documentation](../docs/INDEX.md)

## 🐛 Troubleshooting

Common issues and where to find solutions:

- **Installation issues** → [Setup Guide - Troubleshooting](00-Setup-and-Installation.md#troubleshooting)
- **Client connection issues** → [Client Package - Troubleshooting](02-Client-Package.md#troubleshooting)
- **Server startup issues** → [Server Package - Troubleshooting](03-Server-Package.md#troubleshooting)
- **Context retention issues** → [Context and Memory - Troubleshooting](04-Context-and-Memory.md#troubleshooting)

## 📝 Contributing

Found an issue or want to improve the documentation? Contributions are welcome!

## 📄 License

This documentation is provided as-is for educational and reference purposes.

---

**Last Updated:** February 2, 2026

**A2A-SDK Version:** 0.3.22

**Python Version:** 3.10+
