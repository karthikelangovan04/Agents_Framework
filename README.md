# Google ADK A2A Explore

A comprehensive exploration and documentation project for Google Agent Development Kit (ADK), featuring detailed documentation for each package with runnable examples.

## 📋 Project Overview

This project provides:
- Complete documentation for all Google ADK packages
- Runnable example agents demonstrating various features
- Setup guides and best practices
- Index page for easy navigation

## 🚀 Quick Start

### Prerequisites

- Python 3.10 or higher
- UV package manager
- Google API key or Google Cloud credentials

### Setup

1. **Create virtual environment:**
```bash
uv venv
source .venv/bin/activate  # On Windows: .venv\Scripts\activate
```

2. **Install Google ADK:**
```bash
uv pip install google-adk
```

3. **Set up authentication:**
Create a `.env` file:
```bash
GOOGLE_API_KEY=your_api_key_here
```

4. **Run an example:**
```bash
python examples/simple_agent.py
```

## 📚 Documentation

All documentation is located in the `docs/` directory:

- **[INDEX.md](docs/INDEX.md)** - Start here! Complete index of all documentation
- **[00-Setup-and-Installation.md](docs/00-Setup-and-Installation.md)** - Setup guide
- **[01-Agents-Package.md](docs/01-Agents-Package.md)** - Agents documentation
- **[02-Tools-Package.md](docs/02-Tools-Package.md)** - Tools documentation
- **[04-A2A-Package.md](docs/04-A2A-Package.md)** - Agent-to-Agent documentation
- **[05-Apps-Package.md](docs/05-Apps-Package.md)** - Apps documentation
- **[06-Code-Executors-Package.md](docs/06-Code-Executors-Package.md)** - Code executors
- **[07-Sessions-Package.md](docs/07-Sessions-Package.md)** - Session management
- **[08-Memory-Package.md](docs/08-Memory-Package.md)** - Memory services
- **[09-Other-Packages.md](docs/09-Other-Packages.md)** - Other packages

## 📁 Project Structure

```
.
├── docs/                    # Documentation files
│   ├── INDEX.md            # Documentation index
│   ├── 00-Setup-and-Installation.md
│   ├── 01-Agents-Package.md
│   ├── 02-Tools-Package.md
│   ├── 04-A2A-Package.md
│   ├── 05-Apps-Package.md
│   ├── 06-Code-Executors-Package.md
│   ├── 07-Sessions-Package.md
│   ├── 08-Memory-Package.md
│   └── 09-Other-Packages.md
├── examples/                # Runnable example agents
│   ├── simple_agent.py
│   ├── tool_agent.py
│   ├── multi_agent.py
│   ├── weather_tool.py
│   ├── multi_tool_agent.py
│   ├── code_executor_agent.py
│   ├── session_agent.py
│   ├── memory_agent.py
│   ├── web_app.py
│   ├── remote_agent_server.py
│   └── remote_agent_client.py
├── .venv/                   # Virtual environment (created by uv)
├── .env                     # Environment variables (create this)
├── explore_packages.py      # Package exploration script
├── get_package_details.py   # Package details script
└── README.md                # This file
```

## 🎯 Examples

### Simple Agent
```bash
python examples/simple_agent.py
```

### Agent with Tools
```bash
python examples/tool_agent.py
```

### Multi-Agent System
```bash
python examples/multi_agent.py
```

### Web Application
```bash
python examples/web_app.py
# Then visit http://localhost:8000/docs
```

### Remote Agent Server
```bash
# Terminal 1: Start server
python examples/remote_agent_server.py

# Terminal 2: Start client
python examples/remote_agent_client.py
```

## 🔧 Development Tools

### Explore Packages
```bash
python explore_packages.py
```

### Get Package Details
```bash
python get_package_details.py agents
```

## 📖 Key Features Documented

- ✅ Agent creation and configuration
- ✅ Tool integration and custom tools
- ✅ Multi-agent systems
- ✅ Agent-to-Agent (A2A) communication
- ✅ Web applications with agents
- ✅ Code execution capabilities
- ✅ Session management
- ✅ Memory services
- ✅ Authentication setup
- ✅ Best practices and patterns

## 🛠️ Technologies Used

- **Google ADK** - Agent Development Kit
- **UV** - Fast Python package manager
- **Python 3.10+** - Programming language
- **FastAPI** - Web framework (via ADK Apps)
- **Pydantic** - Data validation

## 📝 Notes

- All examples are designed to be runnable and educational
- Documentation includes troubleshooting sections
- Each package has multiple examples demonstrating different use cases
- Examples use `gemini-1.5-flash` by default (fast and cost-effective)

## 🔗 Useful Links

- [Google ADK Official Docs](https://google.github.io/adk-docs/)
- [Google AI Studio](https://makersuite.google.com/)
- [UV Documentation](https://github.com/astral-sh/uv)

## 📄 License

This project is for educational and documentation purposes.

---

**Happy Coding with Google ADK! 🚀**
