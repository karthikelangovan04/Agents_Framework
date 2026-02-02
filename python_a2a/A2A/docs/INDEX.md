# Python A2A Documentation Index

**File Path**: `A2A/docs/INDEX.md`

Welcome to the comprehensive documentation for Python A2A (Agent-to-Agent Protocol). This index provides an overview of all available documentation and guides you to the right resources for your needs.

## 📚 Documentation Overview

This documentation set covers all major features and capabilities of Python A2A, with detailed examples, runnable code samples, and best practices.

## 🚀 Getting Started

**New to Python A2A?** Start here:

1. **[Setup and Installation Guide](00-Setup-and-Installation.md)** (`A2A/docs/00-Setup-and-Installation.md`)
   - Setting up virtual environment with UV
   - Installing Python A2A
   - Authentication setup
   - Quick start guide

2. **[Core Concepts](01-Core-Concepts.md)** (`A2A/docs/01-Core-Concepts.md`)
   - Understanding Agent Cards
   - Messages and Conversations
   - Content Types
   - Protocol Flow

## 📦 Core Documentation

### 1. [Server Implementation](02-Server-Implementation.md) (`A2A/docs/02-Server-Implementation.md`)
Learn how to create and deploy A2A servers.

**Topics Covered:**
- Basic A2A servers
- FastAPI integration
- Function calling
- Streaming responses
- LLM-powered servers (OpenAI, Anthropic)
- Error handling

**Key Examples:**
- Simple echo server
- Calculator agent
- Conversation handling
- Streaming server

### 2. [Client Implementation](03-Client-Implementation.md) (`A2A/docs/03-Client-Implementation.md`)
Learn how to create A2A clients to communicate with servers.

**Topics Covered:**
- Basic client setup
- Sending messages
- Handling responses
- Streaming
- Function calling
- Error handling

**Key Examples:**
- Simple client
- Multi-agent client
- Streaming client

### 3. [Workflows](04-Workflows.md) (`A2A/docs/04-Workflows.md`)
Orchestrate complex agent interactions.

**Topics Covered:**
- Basic workflows
- Conditional branching
- Parallel execution
- Auto-routing
- Workflow context

**Key Examples:**
- Multi-step workflows
- Conditional routing
- Parallel agent execution

### 4. [Advanced Features](05-Advanced-Features.md) (`A2A/docs/05-Advanced-Features.md`)
Explore advanced capabilities.

**Topics Covered:**
- MCP (Model Context Protocol) integration
- LangChain integration
- Agent discovery
- Agent networks
- Custom content types
- Task management

### 5. [Conversation Storage](06-Conversation-Storage.md) (`A2A/docs/06-Conversation-Storage.md`)
Store A2A conversations in databases (similar to ADK DatabaseSessionService).

**Topics Covered:**
- Conversation serialization (`to_json()`, `from_json()`)
- SQLite storage implementation
- PostgreSQL storage (like ADK DatabaseSessionService)
- SQLAlchemy integration
- Using a2a-session-manager library
- Integration with A2A servers

**Key Examples:**
- SQLite conversation storage
- PostgreSQL conversation storage
- Conversation persistence in servers

## 💻 Examples

All runnable example files are located in the `A2A/examples/` directory:

| Example | File Path | Description |
|---------|-----------|-------------|
| Simple Server | `A2A/examples/simple_server.py` | Basic A2A server |
| Simple Client | `A2A/examples/simple_client.py` | Basic A2A client |
| Calculator Agent | `A2A/examples/calculator_agent.py` | Agent with function calling |
| Multi-Agent Chat | `A2A/examples/multi_agent_chat.py` | Multiple agents interaction |
| Conversation Storage | `A2A/examples/conversation_storage.py` | Database storage for conversations |

## 🎯 Quick Start Examples

### Run a Simple Server

```bash
cd A2A
source bin/activate  # or A2A\Scripts\activate on Windows
python examples/simple_server.py
```

### Run a Simple Client

```bash
# In another terminal
cd A2A
source bin/activate
python examples/simple_client.py
```

## 📖 Key Features Documented

- ✅ Agent Card creation and discovery
- ✅ Message and conversation handling
- ✅ Function calling
- ✅ Streaming responses
- ✅ Multi-agent systems
- ✅ Workflow orchestration
- ✅ MCP integration
- ✅ LangChain integration
- ✅ Error handling
- ✅ Best practices

## 🔧 Project Structure

```
A2A/
├── docs/                    # Documentation files
│   ├── INDEX.md            # This file
│   ├── 00-Setup-and-Installation.md
│   ├── 01-Core-Concepts.md
│   ├── 02-Server-Implementation.md
│   ├── 03-Client-Implementation.md
│   ├── 04-Workflows.md
│   └── 05-Advanced-Features.md
├── examples/                # Runnable examples
│   ├── simple_server.py
│   ├── simple_client.py
│   ├── calculator_agent.py
│   └── multi_agent_chat.py
├── bin/                     # Virtual environment (Python executables)
├── lib/                     # Virtual environment (installed packages)
└── .gitignore              # Git ignore file
```

## 🛠️ Technologies Used

- **Python A2A**: Core library (version 0.5.10)
- **FastAPI**: Web framework for servers
- **Pydantic**: Data validation
- **HTTPX**: HTTP client
- **UV**: Package manager

## 📚 Additional Resources

- [A2A Protocol Documentation](https://a2aprotocol.ai/)
- [Python A2A PyPI Package](https://pypi.org/project/python-a2a/)
- [A2A Protocol Specification](https://a2aprotocol.org/)
- [Google's A2A Announcement](https://developers.googleblog.com/en/a2a-a-new-era-of-agent-interoperability)

## 🤝 Contributing

This documentation is part of the Google ADK A2A Explore project. For issues or improvements, please refer to the main project repository.

## 📝 License

This documentation follows the same license as Python A2A (MIT License).

---

**Last Updated**: January 2026  
**Python A2A Version**: 0.5.10
