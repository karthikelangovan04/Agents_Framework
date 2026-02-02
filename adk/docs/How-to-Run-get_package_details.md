# How to Run `get_package_details.py`

**File Path**: `get_package_details.py`

## Overview

The `get_package_details.py` script is a utility tool that extracts detailed information about Google ADK packages. It uses Python's `inspect` module to analyze package structure, including classes, methods, functions, signatures, and documentation.

## What It Does

The script:
- Imports a specified Google ADK package
- Extracts all classes and their methods
- Captures function signatures and documentation
- Outputs structured JSON data with complete package information

## Prerequisites

1. **Python 3.10 or higher** installed
2. **Google ADK installed** in your Python environment:
   ```bash
   pip install google-adk
   # or
   uv pip install google-adk
   ```
3. **Access to the script**: The script should be in your project directory

## Basic Usage

### Command Syntax

```bash
python3 get_package_details.py <package_name>
```

### Arguments

- **`package_name`** (required): The name of the Google ADK package to analyze
  - Examples: `agents`, `tools`, `a2a`, `apps`, `sessions`, etc.
  - The script will import `google.adk.<package_name>`

### Example: Analyzing the Agents Package

```bash
python3 get_package_details.py agents
```

This will output JSON data to the console containing all information about the `google.adk.agents` package.

## Output Format

The script outputs JSON with the following structure:

```json
{
  "name": "package_name",
  "doc": "Package documentation string",
  "classes": [
    {
      "name": "ClassName",
      "doc": "Class documentation",
      "methods": [
        {
          "name": "method_name",
          "signature": "(self, param1: type, param2: type) -> return_type",
          "doc": "Method documentation"
        }
      ],
      "signature": "Constructor signature"
    }
  ],
  "functions": [
    {
      "name": "function_name",
      "signature": "(param1: type) -> return_type",
      "doc": "Function documentation"
    }
  ],
  "constants": []
}
```

## Saving Output to a File

To save the output to a file instead of displaying it:

### Using Output Redirection

```bash
python3 get_package_details.py agents > output.json
```

### Example with Error Handling

```bash
python3 get_package_details.py agents > get_package_details_output.json 2>&1
```

This saves both standard output and errors to the file.

## Common Package Examples

### 1. Agents Package

```bash
python3 get_package_details.py agents
```

**What you'll get:**
- Classes: `Agent`, `BaseAgent`, `LlmAgent`, `SequentialAgent`, `ParallelAgent`, `LoopAgent`, etc.
- Methods for each class with signatures and documentation

### 2. Tools Package

```bash
python3 get_package_details.py tools
```

**What you'll get:**
- Classes: `BaseTool`, `FunctionTool`, `AgentTool`, `TransferToAgentTool`, etc.
- Tool-related methods and signatures

### 3. A2A Package (Agent-to-Agent)

```bash
python3 get_package_details.py a2a
```

**What you'll get:**
- A2A-specific classes and methods
- Remote agent communication utilities

### 4. Apps Package

```bash
python3 get_package_details.py apps
```

**What you'll get:**
- `App` class and related configuration classes
- Application management methods

### 5. Sessions Package

```bash
python3 get_package_details.py sessions
```

**What you'll get:**
- Session management classes
- State handling methods

### 6. Code Executors Package

```bash
python3 get_package_details.py code_executors
```

**What you'll get:**
- Code execution classes
- Executor configuration methods

## Advanced Usage

### Pretty-Printing JSON Output

If you want formatted, readable JSON output:

```bash
python3 get_package_details.py agents | python3 -m json.tool
```

Or save formatted output:

```bash
python3 get_package_details.py agents | python3 -m json.tool > formatted_output.json
```

### Analyzing Multiple Packages

You can create a simple bash script to analyze multiple packages:

```bash
#!/bin/bash
packages=("agents" "tools" "a2a" "apps" "sessions")

for package in "${packages[@]}"; do
    echo "Analyzing $package..."
    python3 get_package_details.py "$package" > "${package}_details.json"
done
```

### Extracting Specific Information

You can use `jq` (if installed) to extract specific parts of the output:

```bash
# Get only class names
python3 get_package_details.py agents | jq '.classes[].name'

# Get all method names from Agent class
python3 get_package_details.py agents | jq '.classes[] | select(.name=="Agent") | .methods[].name'

# Count total methods
python3 get_package_details.py agents | jq '[.classes[].methods[]] | length'
```

## Understanding the Output

### Package Information

- **`name`**: The package name you specified
- **`doc`**: Module-level documentation (if available)

### Class Information

Each class entry contains:
- **`name`**: Class name
- **`doc`**: Class documentation string
- **`signature`**: Constructor signature (from `__init__`)
- **`methods`**: Array of all public methods

### Method Information

Each method entry contains:
- **`name`**: Method name
- **`signature`**: Full method signature with parameter types and return type
- **`doc`**: Method documentation string

### Function Information

Standalone functions (not part of classes) are listed in the `functions` array with:
- **`name`**: Function name
- **`signature`**: Function signature
- **`doc`**: Function documentation

## Troubleshooting

### Error: "No module named 'google.adk'"

**Problem**: Google ADK is not installed or not in your Python path.

**Solution**:
```bash
# Install Google ADK
pip install google-adk

# Or with UV
uv pip install google-adk

# Verify installation
python3 -c "import google.adk; print('OK')"
```

### Error: "No module named 'google.adk.<package_name>'"

**Problem**: The package name you specified doesn't exist in Google ADK.

**Solution**:
- Check available packages in the [Package Listing documentation](03-Package-Listing.md)
- Verify the package name spelling
- Some packages may have different names (e.g., `code_executors` not `codeexecutors`)

### Error: "Usage: python get_package_details.py <package_name>"

**Problem**: You didn't provide a package name argument.

**Solution**: Always provide a package name:
```bash
python3 get_package_details.py <package_name>
```

### Empty Output or Missing Classes

**Possible Causes**:
1. The package might not export classes at the top level
2. Classes might be in submodules
3. The package might only contain functions

**Solution**: Check the package structure manually:
```python
import google.adk.<package_name> as pkg
import inspect
print(inspect.getmembers(pkg))
```

### Permission Errors

**Problem**: Cannot write output file.

**Solution**: Check file permissions:
```bash
chmod +w output.json
# Or specify a different output location
python3 get_package_details.py agents > ~/output.json
```

## Example Workflow

### Complete Analysis Workflow

1. **Analyze a package**:
   ```bash
   python3 get_package_details.py agents > agents_details.json
   ```

2. **View the structure**:
   ```bash
   python3 -c "import json; data=json.load(open('agents_details.json')); print(f'Classes: {len(data[\"classes\"])}'); [print(f'  - {c[\"name\"]}') for c in data['classes']]"
   ```

3. **Extract specific information**:
   ```bash
   # View Agent class methods
   python3 -c "import json; data=json.load(open('agents_details.json')); agent=[c for c in data['classes'] if c['name']=='Agent'][0]; [print(f'{m[\"name\"]}{m[\"signature\"]}') for m in agent['methods']]"
   ```

## Integration with Documentation

This script is useful for:
- **Generating API documentation** automatically
- **Understanding package structure** before writing code
- **Creating reference guides** for specific packages
- **Comparing package versions** over time
- **Discovering available methods** and their signatures

## Related Documentation

- [Package Listing](03-Package-Listing.md) - Complete list of all Google ADK packages
- [Agents Package](01-Agents-Package.md) - Detailed agents documentation
- [Tools Package](02-Tools-Package.md) - Tools package documentation
- [Setup and Installation](00-Setup-and-Installation.md) - Installation guide

## Script Source Code

The script is located at: `get_package_details.py`

You can view or modify it to:
- Add filtering options
- Change output format
- Add support for submodules
- Include additional metadata

## Tips

1. **Save outputs**: Always save outputs to files for later reference
2. **Use JSON tools**: Use `jq` or Python's `json.tool` for better readability
3. **Compare packages**: Save outputs from different packages to compare structures
4. **Version control**: Consider versioning the output files to track API changes
5. **Automate**: Create scripts to analyze all packages at once

## Quick Reference

```bash
# Basic usage
python3 get_package_details.py <package_name>

# Save to file
python3 get_package_details.py agents > output.json

# Pretty print
python3 get_package_details.py agents | python3 -m json.tool

# With error handling
python3 get_package_details.py agents > output.json 2>&1

# Extract class names
python3 get_package_details.py agents | python3 -c "import json, sys; data=json.load(sys.stdin); [print(c['name']) for c in data['classes']]"
```

---

**Last Updated**: Based on Google ADK version 1.22.1
