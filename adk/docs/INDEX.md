# Google ADK Documentation Index

**File Path**: `docs/INDEX.md`

Welcome to the comprehensive documentation for Google Agent Development Kit (ADK). This index provides an overview of all available documentation and guides you to the right resources for your needs.

## 📚 Documentation Overview

This documentation set covers all major packages and features of Google ADK, with detailed examples, runnable code samples, and best practices.

## 🚀 Getting Started

**New to Google ADK?** Start here:

1. **[Setup and Installation Guide](00-Setup-and-Installation.md)** (`docs/00-Setup-and-Installation.md`)
   - Setting up virtual environment with UV
   - Installing Google ADK
   - Authentication setup
   - Quick start guide

2. **[Complete Package Listing](03-Package-Listing.md)** (`docs/03-Package-Listing.md`)
   - Complete inventory of all 25 Google ADK packages
   - File paths for all documentation
   - Package structure and subpackages

## 📦 Core Packages

### 1. [Agents Package](01-Agents-Package.md) (`docs/01-Agents-Package.md`)
The foundation of Google ADK - learn how to create and configure agents.

**Topics Covered:**
- Creating simple agents
- Multi-agent systems
- Agent configuration
- Sub-agents and routing
- Callbacks and hooks
- Input/output schemas

**Key Examples:**
- Simple agent
- Agent with tools
- Multi-agent system
- Agent with callbacks
- Structured input/output

### 2. [Tools Package](02-Tools-Package.md) (`docs/02-Tools-Package.md`)
Extend agent capabilities with tools - functions, APIs, and integrations.

**Topics Covered:**
- Function tools
- Custom tools
- Built-in tool sets
- Google Search integration
- Agent tools
- Transfer to agent

**Key Examples:**
- Simple function tool
- Multiple tools
- Custom BaseTool
- Google Search tool
- Agent tool
- Long-running tools

### 3. [A2A (Agent-to-Agent) Package](04-A2A-Package.md) (`docs/04-A2A-Package.md`)
Enable agents to communicate with each other over networks.

**Topics Covered:**
- Remote agent servers
- Consuming remote agents
- Agent cards
- A2A protocol
- Distributed agent systems

**Key Examples:**
- Remote agent server
- Remote agent client
- Agent card configuration
- Multiple remote agents

### 4. [Apps Package](05-Apps-Package.md) (`docs/05-Apps-Package.md`)
Create web applications and APIs with agents.

**Topics Covered:**
- Web app creation
- API endpoints
- Resumability
- Multi-agent apps
- FastAPI integration

**Key Examples:**
- Simple web app
- App with resumability
- Multi-agent app
- Custom API integration

### 5. [Code Executors Package](06-Code-Executors-Package.md) (`docs/06-Code-Executors-Package.md`)
Enable agents to write and execute code safely.

**Topics Covered:**
- Code execution
- Built-in executors
- Custom executors
- Safety considerations
- Data analysis agents

**Key Examples:**
- Agent with code execution
- Custom code executor
- Data analysis agent

### 6. [Sessions Package](07-Sessions-Package.md) (`docs/07-Sessions-Package.md`)
Manage conversation sessions and maintain context.

**Topics Covered:**
- Session management
- Session services
- State management
- Multiple sessions
- Persistent sessions

**Key Examples:**
- Basic session usage
- Vertex AI session service
- Session state management
- Multiple sessions

### 7. [Memory Package](08-Memory-Package.md) (`docs/08-Memory-Package.md`)
Enable agents to store and retrieve information.

**Topics Covered:**
- Memory services
- Memory storage
- Memory retrieval
- RAG memory
- Memory search

**Key Examples:**
- Basic memory usage
- Vertex AI Memory Bank
- RAG memory service
- Memory search

### 8. [Runners Package](10-Runners-Package.md) (`docs/10-Runners-Package.md`)
The execution engine for agents - understand how agents are actually run.

**Topics Covered:**
- Runner vs Agent distinction
- Agent execution lifecycle
- Session management
- Event processing
- Service coordination
- Resumability
- Live mode execution

**Key Examples:**
- Basic runner usage
- Runner with services
- Resumable invocations
- Event processing

### 9. [State Management](11-State-Management.md) (`docs/11-State-Management.md`)
Manage application, user, and session-level state with automatic scoping and delta tracking.

**Topics Covered:**
- State scopes (app, user, session, temp)
- State prefixes and naming
- State delta updates
- State persistence
- State extraction utilities

**Key Examples:**
- Application-level state
- User-level state
- Session-level state
- Temporary state
- State delta updates

### 10. [ADK Web Interface Analysis](14-ADK-Web-Interface-Analysis.md) (`docs/14-ADK-Web-Interface-Analysis.md`)
Detailed analysis of the ADK web interface: `adk web`, Dev UI, API endpoints, agent discovery, Runner/services, and library structure.

### 11. [MCP Tools Dynamic Loading](15-MCP-Tools-Dynamic-Loading.md) (`docs/15-MCP-Tools-Dynamic-Loading.md`)
Comprehensive guide to MCP (Model Context Protocol) tools in Google ADK, including dynamic loading mechanisms, comparison with other applications (Claude/ChatGPT), and implementation patterns.

**Topics Covered:**
- MCP tool architecture
- Dynamic loading mechanism
- Comparison with Claude/ChatGPT approach
- Implementation patterns for dynamic tools
- Best practices and advanced patterns

### 12. [Other Packages](09-Other-Packages.md) (`docs/09-Other-Packages.md`)
Additional packages providing supporting functionality.

**Topics Covered:**
- Models package
- Auth package
- Examples package
- Planners package
- Flows package
- Plugins package
- Artifacts package
- Events package
- Telemetry package
- Evaluation package

### 13. [Safety and Security for AI Agents](24-Safety-and-Security.md) (`docs/24-Safety-and-Security.md`)
Multi-layered safety and security guidance for building trustworthy agents with Vertex AI and ADK.

**Topics Covered:**
- Identity and authorization (agent-auth, user auth)
- Guardrails: in-tool guardrails, Gemini safety features, callbacks and plugins
- Sandboxed code execution
- Evaluation and tracing
- VPC-SC and network controls
- Risk assessment and best practices

## 🔧 Specialized Topics

### [MCP Tools Dynamic Loading](15-MCP-Tools-Dynamic-Loading.md) (`docs/15-MCP-Tools-Dynamic-Loading.md`)
Deep dive into how Google ADK handles MCP tools, including:
- How dynamic loading works (lazy loading via `get_tools()`)
- Comparison with Claude Desktop and ChatGPT approaches
- Patterns for implementing dynamic tool configuration
- Session-scoped and context-aware tool filtering
- Best practices for production deployments

### [MCP Dynamic Configuration and Server Management](16-MCP-Dynamic-Configuration-and-Server-Management.md) (`docs/16-MCP-Dynamic-Configuration-and-Server-Management.md`)
Comprehensive guide to implementing Claude/Cursor-like dynamic MCP configuration:
- How local stdio servers are automatically started
- How remote SSE/HTTP servers work
- Dynamic configuration system with JSON files
- MCP marketplace integration
- Complete working examples

### [Per-User MCP Tool Management](17-Per-User-MCP-Tool-Management.md) (`docs/17-Per-User-MCP-Tool-Management.md`)
Complete guide to implementing per-user MCP tool management like Claude/Cursor:
- How each user can have their own MCP tools
- Frontend-to-backend flow for tool configuration
- User-level vs session-level tool management
- Required Google ADK packages (Sessions, State Management)
- Complete working examples with multiple users

## 🎯 Quick Reference Guide

### I want to...

**Create a simple agent:**
→ [Agents Package - Example 1](01-Agents-Package.md#example-1-simple-agent)

**Add tools to my agent:**
→ [Tools Package - Example 1](02-Tools-Package.md#example-1-simple-function-tool)

**Create a web app:**
→ [Apps Package - Example 1](05-Apps-Package.md#example-1-simple-web-app)

**Use the ADK web interface (adk web) for development:**
→ [ADK Web Interface Analysis](14-ADK-Web-Interface-Analysis.md)

**Enable code execution:**
→ [Code Executors Package - Example 1](06-Code-Executors-Package.md#example-1-agent-with-code-execution)

**Add session management:**
→ [Sessions Package - Example 1](07-Sessions-Package.md#example-1-basic-session-usage)

**Add memory capabilities:**
→ [Memory Package - Example 1](08-Memory-Package.md#example-1-basic-memory-usage)

**Understand how agents execute:**
→ [Runners Package - Example 1](10-Runners-Package.md#example-1-basic-runner-usage)

**Use MCP tools dynamically:**
→ [MCP Tools Dynamic Loading](15-MCP-Tools-Dynamic-Loading.md)

**Configure MCP servers like Claude/Cursor:**
→ [MCP Dynamic Configuration and Server Management](16-MCP-Dynamic-Configuration-and-Server-Management.md)

**Implement per-user MCP tools:**
→ [Per-User MCP Tool Management](17-Per-User-MCP-Tool-Management.md)

**Manage state across scopes:**
→ [State Management - Example 1](11-State-Management.md#example-1-application-level-state)

**Harden agent safety and security:**
→ [Safety and Security for AI Agents](24-Safety-and-Security.md)

**Create remote agents:**
→ [A2A Package - Example 1](04-A2A-Package.md#example-1-creating-a-remote-agent-server)

**Set up authentication:**
→ [Setup Guide - Step 6](00-Setup-and-Installation.md#step-6-set-up-authentication)

## 📁 Example Files

All runnable examples are located in the `examples/` directory:

- `simple_agent.py` - Basic agent example
- `tool_agent.py` - Agent with tools
- `multi_agent.py` - Multi-agent system
- `weather_tool.py` - Weather tool example
- `multi_tool_agent.py` - Multiple tools
- `code_executor_agent.py` - Code execution
- `session_agent.py` - Session management
- `memory_agent.py` - Memory capabilities
- `web_app.py` - Web application
- `remote_agent_server.py` - Remote agent server
- `remote_agent_client.py` - Remote agent client

## 🔗 Package Dependencies

Understanding how packages relate:

```
Setup & Installation
    ↓
Agents (Core)
    ├── Tools
    ├── Code Executors
    ├── Sessions
    ├── Memory
    ├── A2A
    └── Apps
```

## 📖 Documentation Structure

Each package documentation follows this structure:

1. **Overview** - What the package does
2. **Key Classes** - Main components
3. **Examples** - Runnable code samples
4. **Best Practices** - Recommended approaches
5. **Troubleshooting** - Common issues and solutions
6. **Related Documentation** - Links to related docs

## 🛠️ Development Workflow

1. **Setup** - Follow [Setup Guide](00-Setup-and-Installation.md)
2. **Learn Core** - Read [Agents Package](01-Agents-Package.md)
3. **Add Tools** - Explore [Tools Package](02-Tools-Package.md)
4. **Build App** - Create with [Apps Package](05-Apps-Package.md)
5. **Enhance** - Add [Sessions](07-Sessions-Package.md) and [Memory](08-Memory-Package.md)
6. **Scale** - Use [A2A Package](04-A2A-Package.md) for distributed systems

## 📚 Additional Resources

- [Google ADK Official Documentation](https://google.github.io/adk-docs/)
- [Google AI Studio](https://makersuite.google.com/)
- [Vertex AI Documentation](https://cloud.google.com/vertex-ai/docs)
- [UV Package Manager](https://github.com/astral-sh/uv)

## 🛡️ Safety and Security

- **Risk assessment and guardrails** → [Safety and Security for AI Agents](24-Safety-and-Security.md)
- **Identity, tool guardrails, callbacks/plugins** → [24-Safety-and-Security.md](24-Safety-and-Security.md#guardrails-to-screen-inputs-and-outputs)
- **Sandboxed code execution** → [24-Safety-and-Security.md](24-Safety-and-Security.md#sandboxed-code-execution)

## 🐛 Troubleshooting

Common issues and where to find solutions:

- **Installation issues** → [Setup Guide - Troubleshooting](00-Setup-and-Installation.md#troubleshooting)
- **Agent not responding** → [Agents Package - Troubleshooting](01-Agents-Package.md#troubleshooting)
- **Tool not being called** → [Tools Package - Troubleshooting](02-Tools-Package.md#troubleshooting)
- **Session issues** → [Sessions Package - Troubleshooting](07-Sessions-Package.md#troubleshooting)
- **Memory issues** → [Memory Package - Troubleshooting](08-Memory-Package.md#troubleshooting)

## 📝 Contributing

Found an issue or want to improve the documentation? Contributions are welcome!

## 📄 License

This documentation is provided as-is for educational and reference purposes.

---

**Last Updated:** 2025-01-27

**Google ADK Version:** 1.22.1

**Python Version:** 3.10+
