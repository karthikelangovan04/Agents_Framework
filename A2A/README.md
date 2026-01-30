# Python A2A (Agent-to-Agent Protocol) Exploration

A comprehensive exploration and documentation project for Python A2A, featuring detailed documentation for all features with runnable examples.

## 📋 Project Overview

This project provides:
- Complete documentation for Python A2A library
- Runnable example agents demonstrating various features
- Setup guides and best practices
- Index page for easy navigation

## 🚀 Quick Start

### Prerequisites

- Python 3.9 or higher
- UV package manager
- API keys for AI providers (optional, depending on use case)

### Setup

1. **Virtual environment is already created** (named `A2A`)

2. **Activate virtual environment:**
```bash
source A2A/bin/activate  # On macOS/Linux
# or
A2A\Scripts\activate      # On Windows
```

3. **Python A2A is already installed** in this venv

4. **Verify installation:**
```bash
python -c "from python_a2a import __version__; print(__version__)"
```

5. **Set up authentication (optional):**
Create a `.env` file if using LLM providers:
```bash
OPENAI_API_KEY=your_openai_api_key_here
ANTHROPIC_API_KEY=your_anthropic_api_key_here
```

## 📚 Documentation

All documentation is located in the `A2A/docs/` directory:

- **[INDEX.md](docs/INDEX.md)** - Start here! Complete index of all documentation
- **[00-Setup-and-Installation.md](docs/00-Setup-and-Installation.md)** - Setup guide
- **[01-Core-Concepts.md](docs/01-Core-Concepts.md)** - Core concepts and fundamentals
- **[02-Server-Implementation.md](docs/02-Server-Implementation.md)** - Building A2A servers
- **[03-Client-Implementation.md](docs/03-Client-Implementation.md)** - Creating A2A clients
- **[04-Workflows.md](docs/04-Workflows.md)** - Workflow orchestration
- **[05-Advanced-Features.md](docs/05-Advanced-Features.md)** - Advanced features

## 💻 Examples

All runnable examples are in the `A2A/examples/` directory:

### Simple Server
```bash
python examples/simple_server.py
```
Starts an A2A server on http://localhost:8000

### Simple Client
```bash
# Make sure server is running first
python examples/simple_client.py
```
Connects to the server and sends a message

### Calculator Agent
```bash
python examples/calculator_agent.py
```
An agent that performs mathematical calculations via function calls

### Multi-Agent Chat
```bash
# Start multiple agents first, then:
python examples/multi_agent_chat.py
```
Demonstrates interaction with multiple agents

## 📁 Project Structure

```
A2A/
├── docs/                    # Documentation files
│   ├── INDEX.md
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
├── bin/                     # Virtual environment executables
├── lib/                     # Installed packages
├── .gitignore              # Git ignore file
└── README.md               # This file
```

## 🎯 Key Features

- ✅ Agent Card creation and discovery
- ✅ Message and conversation handling
- ✅ Function calling
- ✅ Streaming responses
- ✅ Multi-agent systems
- ✅ Workflow orchestration
- ✅ MCP (Model Context Protocol) integration
- ✅ LangChain integration
- ✅ Error handling
- ✅ Best practices

## 🔧 Development

### Exploring the Library

Use the exploration script:
```bash
python explore_a2a.py
```

This generates `a2a_exploration.json` with detailed library structure.

## 📖 Additional Resources

- [A2A Protocol Documentation](https://a2aprotocol.ai/)
- [Python A2A PyPI Package](https://pypi.org/project/python-a2a/)
- [A2A Protocol Specification](https://a2aprotocol.org/)
- [Google's A2A Announcement](https://developers.googleblog.com/en/a2a-a-new-era-of-agent-interoperability)

## 📝 Notes

- This virtual environment (`A2A`) is separate from the main project's `.venv`
- The `.gitignore` file ensures the venv contents are not committed to git
- Documentation follows the same structure as the main ADK documentation

## 🤝 Contributing

This is part of the Google ADK A2A Explore project. For issues or improvements, please refer to the main project repository.

---

**Python A2A Version**: 0.5.10  
**Last Updated**: January 2026
