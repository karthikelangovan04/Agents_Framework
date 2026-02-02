# A2A-SDK Setup and Installation

**File Path**: `docs-a2a-sdk/00-Setup-and-Installation.md`  
**Package**: `a2a-sdk`

## Overview

This guide will help you set up A2A-SDK in your development environment using UV package manager (recommended) or pip.

---

## Prerequisites

- **Python**: 3.10 or higher
- **Package Manager**: UV (recommended) or pip
- **Operating System**: macOS, Linux, or Windows

---

## Step 1: Install UV (Recommended)

UV is a fast Python package installer and resolver written in Rust.

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

---

## Step 2: Create Virtual Environment

### Using UV (Recommended)

```bash
# Create virtual environment
uv venv a2a-sdk-venv

# Activate virtual environment
# macOS/Linux:
source a2a-sdk-venv/bin/activate

# Windows:
a2a-sdk-venv\Scripts\activate
```

### Using Python venv

```bash
# Create virtual environment
python3 -m venv a2a-sdk-venv

# Activate virtual environment
# macOS/Linux:
source a2a-sdk-venv/bin/activate

# Windows:
a2a-sdk-venv\Scripts\activate
```

---

## Step 3: Install A2A-SDK

### Basic Installation

```bash
# Using UV (recommended)
uv pip install a2a-sdk

# Using pip
pip install a2a-sdk
```

### Installation with Optional Extras

A2A-SDK supports optional extras for additional functionality:

#### gRPC Support
```bash
uv pip install "a2a-sdk[grpc]"
# or
pip install "a2a-sdk[grpc]"
```

#### Signing Support (JWT)
```bash
uv pip install "a2a-sdk[signing]"
# or
pip install "a2a-sdk[signing]"
```

#### Database Support

**PostgreSQL**:
```bash
uv pip install "a2a-sdk[postgresql]"
```

**MySQL**:
```bash
uv pip install "a2a-sdk[mysql]"
```

**SQLite**:
```bash
uv pip install "a2a-sdk[sqlite]"
```

**All SQL databases**:
```bash
uv pip install "a2a-sdk[sql]"
```

#### Multiple Extras
```bash
uv pip install "a2a-sdk[grpc,signing,postgresql]"
```

---

## Step 4: Verify Installation

```python
import a2a
print(f"A2A SDK installed successfully!")
print(f"Package location: {a2a.__file__}")

# Check available modules
import pkgutil
modules = [name for _, name, _ in pkgutil.iter_modules(a2a.__path__)]
print(f"Available modules: {modules}")
```

**Expected Output**:
```
A2A SDK installed successfully!
Package location: /path/to/a2a-sdk-venv/lib/python3.13/site-packages/a2a/__init__.py
Available modules: ['_base', 'auth', 'client', 'extensions', 'grpc', 'server', 'types', 'utils']
```

---

## Step 5: Quick Start Example

### Simple Client Example

Create `examples/simple_client_test.py`:

```python
#!/usr/bin/env python3
"""Simple A2A client test."""

from a2a.client import Client, ClientConfig
from a2a.client.transports.rest import RestTransport
from a2a.types import Message

async def main():
    # Create client configuration
    config = ClientConfig(
        transport=RestTransport(
            base_url="http://localhost:8000"
        )
    )
    
    # Create client
    client = Client(config)
    
    # Create message
    message = Message(
        role="user",
        content=[{"text": "Hello, A2A!"}]
    )
    
    # Send message
    async for event in client.send_message(message):
        print(f"Received: {event}")

if __name__ == "__main__":
    import asyncio
    asyncio.run(main())
```

### Simple Server Example

Create `examples/simple_server_test.py`:

```python
#!/usr/bin/env python3
"""Simple A2A server test."""

from a2a.server.apps.jsonrpc.fastapi_app import A2AFastAPI
from a2a.server.request_handlers.jsonrpc_handler import JSONRPCHandler
from a2a.types import Message, AgentCard
import uvicorn

# Create agent card
agent_card = AgentCard(
    name="test_agent",
    description="A simple test agent"
)

# Create request handler
handler = JSONRPCHandler(
    agent_card=agent_card,
    # Add your agent logic here
)

# Create FastAPI app
app = A2AFastAPI(handler=handler)

if __name__ == "__main__":
    uvicorn.run(app, host="0.0.0.0", port=8000)
```

---

## Step 6: Check Installed Version

```bash
# Using pip
pip show a2a-sdk

# Using Python
python3 -c "import a2a; print(getattr(a2a, '__version__', 'unknown'))"
```

---

## Troubleshooting

### Issue: ModuleNotFoundError: No module named 'a2a'

**Solution**:
1. Ensure virtual environment is activated
2. Verify installation: `pip list | grep a2a-sdk`
3. Reinstall: `uv pip install a2a-sdk`

### Issue: ImportError for grpc modules

**Solution**:
Install gRPC extras:
```bash
uv pip install "a2a-sdk[grpc]"
```

### Issue: ImportError for database modules

**Solution**:
Install database extras:
```bash
uv pip install "a2a-sdk[postgresql]"  # or mysql, sqlite, sql
```

### Issue: ImportError for signing modules

**Solution**:
Install signing extras:
```bash
uv pip install "a2a-sdk[signing]"
```

---

## Next Steps

1. **Read Package Structure**: [01-Package-Structure.md](01-Package-Structure.md)
2. **Learn Client Usage**: [02-Client-Package.md](02-Client-Package.md)
3. **Learn Server Usage**: [03-Server-Package.md](03-Server-Package.md)
4. **Understand Context**: [04-Context-and-Memory.md](04-Context-and-Memory.md)

---

## Comparison with ADK Setup

| Aspect | ADK | A2A SDK |
|--------|-----|---------|
| **Package Name** | `google-adk` | `a2a-sdk` |
| **Import Name** | `google.adk` | `a2a` |
| **Python Version** | 3.10+ | 3.10+ |
| **Optional Extras** | Limited | Extensive (grpc, signing, sql) |
| **Installation** | `pip install google-adk` | `pip install a2a-sdk` |

---

**Last Updated:** February 2, 2026  
**A2A-SDK Version:** 0.3.22
