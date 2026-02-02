# Google ADK (Agent Development Kit)

This directory contains all Google ADK related files, documentation, examples, and virtual environment.

## Structure

```
adk/
├── docs/              # ADK documentation
├── examples/          # ADK example code
├── .venv/            # ADK virtual environment
├── explore_packages.py      # Package exploration script
├── get_package_details.py   # Package details script
├── get_package_details_output.json  # Package details output
└── FILE-PATHS.md     # Complete file path reference
```

## Documentation

All ADK documentation is in the `docs/` directory. Start with:
- [INDEX.md](docs/INDEX.md) - Main documentation index

## Examples

All runnable examples are in the `examples/` directory.

## Utility Scripts

- `explore_packages.py` - Explore all ADK packages and generate structure
- `get_package_details.py` - Get detailed information about a specific package

Usage:
```bash
cd adk
source .venv/bin/activate
python explore_packages.py
python get_package_details.py <package_name>
```

## File Path Reference

See [FILE-PATHS.md](FILE-PATHS.md) for a complete reference of all documentation files and their locations.

## Virtual Environment

The ADK virtual environment is located at `.venv/`.

To activate:
```bash
source .venv/bin/activate  # macOS/Linux
# or
.venv\Scripts\activate     # Windows
```

## Related Directories

- `../python_a2a/` - Python A2A library exploration
- `../a2a_sdk/` - A2A SDK documentation and analysis

---

**Last Updated:** February 2, 2026
