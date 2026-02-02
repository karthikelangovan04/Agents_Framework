# Python A2A (Agent-to-Agent) Setup and Installation Guide

**File Path**: `A2A/docs/00-Setup-and-Installation.md`

## Overview

Python A2A is a comprehensive Python library for implementing Google's Agent-to-Agent (A2A) protocol. The A2A protocol enables AI agents to communicate, securely exchange information, and coordinate actions regardless of their underlying technologies or vendors.

## Prerequisites

- Python 3.9 or higher
- UV package manager installed
- API keys for AI providers (OpenAI, Anthropic, etc.) - optional depending on use case

## Step 1: Install UV

If you don't have UV installed, install it using one of these methods:

### macOS/Linux
```bash
curl -LsSf https://astral.sh/uv/install.sh | sh
```

### Windows
```powershell
powershell -ExecutionPolicy ByPass -c "irm https://astral.sh/uv/install.ps1 | iex"
```

### Verify Installation
```bash
uv --version
```

## Step 2: Create Virtual Environment with UV

Navigate to your project directory and create a virtual environment named `A2A`:

```bash
cd /path/to/your/project
uv venv A2A
```

This creates an `A2A` directory in your project.

## Step 3: Activate Virtual Environment

### macOS/Linux
```bash
source A2A/bin/activate
```

### Windows
```powershell
A2A\Scripts\activate
```

## Step 4: Install Python A2A

With your virtual environment activated, install Python A2A:

### Basic Installation
```bash
uv pip install python-a2a
```

### With Optional Integrations

For OpenAI integration:
```bash
uv pip install "python-a2a[openai]"
```

For Anthropic Claude integration:
```bash
uv pip install "python-a2a[anthropic]"
```

For all optional dependencies:
```bash
uv pip install "python-a2a[all]"
```

This will install Python A2A and all its dependencies, including:
- `fastapi` - For web server functionality
- `pydantic` - For data validation
- `httpx` - For HTTP client functionality
- `langchain` - For LangChain integration (optional)
- And many other dependencies

## Step 5: Verify Installation

Verify that Python A2A is installed correctly:

```bash
python -c "from python_a2a import __version__; print(__version__)"
```

You should see the version number printed (e.g., `0.5.10`).

## Step 6: Set Up Authentication (Optional)

Depending on which AI providers you want to use, you may need to set up API keys:

### OpenAI
```bash
export OPENAI_API_KEY=your_openai_api_key_here
```

Or create a `.env` file:
```bash
OPENAI_API_KEY=your_openai_api_key_here
```

### Anthropic
```bash
export ANTHROPIC_API_KEY=your_anthropic_api_key_here
```

Or add to `.env`:
```bash
ANTHROPIC_API_KEY=your_anthropic_api_key_here
```

## Project Structure

After setup, your project structure should look like:

```
your-project/
├── A2A/                    # Virtual environment
│   ├── bin/               # Python executables
│   ├── lib/               # Installed packages
│   └── .gitignore         # Git ignore file
├── A2A/docs/              # Documentation
├── A2A/examples/          # Example code
├── .env                   # Environment variables (API keys)
└── requirements.txt       # Dependencies (optional)
```

## Quick Test

Create a simple test file `test_a2a_setup.py`:

```python
from python_a2a import A2AServer, Message, TextContent, MessageRole

# Create a simple A2A server
server = A2AServer(
    agent_card={
        "name": "test_agent",
        "description": "A test A2A agent"
    }
)

print("✅ Python A2A is set up correctly!")
print(f"Server created: {server}")
```

Run it:
```bash
python test_a2a_setup.py
```

## Troubleshooting

### Issue: `uv: command not found`
- Make sure UV is installed and in your PATH
- Try restarting your terminal

### Issue: `ModuleNotFoundError: No module named 'python_a2a'`
- Ensure virtual environment is activated
- Reinstall: `uv pip install --upgrade python-a2a`

### Issue: Import errors for optional features
- Install the specific integration: `uv pip install "python-a2a[openai]"` or `uv pip install "python-a2a[anthropic]"`
- Or install all: `uv pip install "python-a2a[all]"`

### Issue: Authentication errors
- Verify your API keys are set correctly in environment variables or `.env` file
- Check that your API keys are valid and have necessary permissions

## Next Steps

- Read the [Core Concepts Guide](01-Core-Concepts.md) to understand A2A fundamentals
- Check out [Examples](examples/) for working code samples
- Explore [Server Implementation](02-Server-Implementation.md) for building A2A servers
- Learn about [Client Implementation](03-Client-Implementation.md) for consuming A2A agents

## References

- [A2A Protocol Documentation](https://a2aprotocol.ai/)
- [Python A2A PyPI Package](https://pypi.org/project/python-a2a/)
- [A2A Protocol Specification](https://a2aprotocol.org/)
