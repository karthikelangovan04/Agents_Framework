# A2A SDK (Official)

This directory contains comprehensive documentation and analysis of the official A2A SDK package (`a2a-sdk` from PyPI).

## Structure

```
a2a_sdk/
├── docs/                              # A2A SDK documentation
│   ├── INDEX.md                      # Main documentation index
│   ├── 00-Setup-and-Installation.md
│   ├── 01-Package-Structure.md
│   ├── 02-Client-Package.md
│   ├── 03-Server-Package.md
│   ├── 04-Context-and-Memory.md      # Context retention analysis
│   └── ...
├── venv/                             # A2A SDK virtual environment
├── analyze_a2a_sdk.py               # Comprehensive analysis script
├── a2a_sdk_comprehensive_analysis.json # Full analysis results
├── A2A_SDK_COMPREHENSIVE_ANALYSIS.md  # Analysis summary
└── A2A_SDK_COMPARISON.md              # Comparison with ADK
```

## Documentation

All A2A SDK documentation is in the `docs/` directory. Start with:
- [INDEX.md](docs/INDEX.md) - Main documentation index
- [04-Context-and-Memory.md](docs/04-Context-and-Memory.md) - Context retention analysis

## Virtual Environment

The A2A SDK virtual environment is located at `venv/`.

To activate:
```bash
source venv/bin/activate  # macOS/Linux
# or
venv\Scripts\activate    # Windows
```

## Analysis

The comprehensive analysis includes:
- **83 modules** analyzed
- **166 classes** documented
- **2,896 methods** catalogued
- **96 protobuf-generated types**

Run the analysis script:
```bash
cd a2a_sdk
source venv/bin/activate
python analyze_a2a_sdk.py
```

## Key Findings

- **Package**: `a2a-sdk` (version 0.3.22)
- **Import**: `import a2a`
- **Context Management**: `ClientCallContext`, `ServerCallContext`
- **Long-term Memory**: Task-based persistence
- **Comparison**: See [A2A_SDK_COMPARISON.md](A2A_SDK_COMPARISON.md)

## Related Directories

- `../adk/` - Google ADK documentation and examples
- `../python_a2a/` - Python A2A library exploration

---

**Last Updated:** February 2, 2026  
**A2A-SDK Version:** 0.3.22
