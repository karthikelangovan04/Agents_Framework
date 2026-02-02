# Google ADK & A2A Exploration Project

This repository contains comprehensive exploration and documentation for:
1. **Google ADK** (Agent Development Kit)
2. **Python A2A** (Python A2A library)
3. **A2A SDK** (Official A2A SDK from PyPI)

## Project Structure

```
Google-ADK-A2A-Explore/
├── adk/                    # Google ADK
│   ├── docs/              # ADK documentation
│   ├── examples/          # ADK examples
│   ├── .venv/            # ADK virtual environment
│   ├── explore_packages.py      # Package exploration script
│   ├── get_package_details.py   # Package details script
│   ├── get_package_details_output.json
│   └── FILE-PATHS.md     # File path reference
│
├── python_a2a/            # Python A2A Library
│   ├── A2A/              # Python A2A virtual environment and docs
│   ├── explore_a2a.py    # Exploration script
│   └── ...
│
├── a2a_sdk/              # A2A SDK (Official)
│   ├── docs/             # A2A SDK documentation
│   ├── venv/             # A2A SDK virtual environment
│   ├── analyze_a2a_sdk.py
│   └── ...
│
└── [root files]
```

## Quick Start

### Google ADK

```bash
cd adk
source .venv/bin/activate
# See docs/INDEX.md for documentation
# Run utility scripts:
python explore_packages.py
python get_package_details.py <package_name>
```

### Python A2A

```bash
cd python_a2a
python explore_a2a.py
# See A2A/docs/ for documentation
```

### A2A SDK

```bash
cd a2a_sdk
source venv/bin/activate
python analyze_a2a_sdk.py
# See docs/INDEX.md for documentation
```

## Documentation

### Google ADK
- **Location**: `adk/docs/`
- **Index**: [adk/docs/INDEX.md](adk/docs/INDEX.md)
- **Topics**: Agents, Tools, Sessions, Memory, A2A, Apps, etc.

### Python A2A
- **Location**: `python_a2a/A2A/docs/`
- **Topics**: Core concepts, server/client implementation, workflows

### A2A SDK
- **Location**: `a2a_sdk/docs/`
- **Index**: [a2a_sdk/docs/INDEX.md](a2a_sdk/docs/INDEX.md)
- **Topics**: Client/Server, Context & Memory, Transports, Tasks, etc.

## Key Comparisons

| Feature | Google ADK | Python A2A | A2A SDK |
|---------|------------|-------------|---------|
| **Package** | `google-adk` | `python_a2a` | `a2a-sdk` |
| **Import** | `google.adk` | `python_a2a` | `a2a` |
| **Context** | Session-based | Conversation-based | Context-based + Task-based |
| **Memory** | MemoryService | Conversation storage | Task persistence |
| **Protocol** | Built-in A2A | A2A protocol | JSON-RPC, REST, gRPC |

## Analysis Results

### A2A SDK Comprehensive Analysis
- **83 modules** analyzed
- **166 classes** documented
- **2,896 methods** catalogued
- **96 protobuf-generated types**

See: `a2a_sdk/A2A_SDK_COMPREHENSIVE_ANALYSIS.md`

## Context Retention Analysis

Detailed analysis of how each framework manages context:
- **ADK**: See `adk/docs/ADK-Memory-and-Session-Runtime-Trace.md`
- **A2A SDK**: See `a2a_sdk/docs/04-Context-and-Memory.md`

## Contributing

Each directory is self-contained with its own documentation and examples.

---

**Last Updated:** February 2, 2026
