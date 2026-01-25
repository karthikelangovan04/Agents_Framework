# Google ADK Setup and Installation Guide

**File Path**: `docs/00-Setup-and-Installation.md`

## Overview

The Google Agent Development Kit (ADK) is a comprehensive framework for building AI agents using Google's Gemini models and Vertex AI. This guide will help you set up your development environment using UV (a fast Python package manager) and get started with Google ADK.

## Prerequisites

- Python 3.10 or higher
- UV package manager installed
- Google Cloud account (for Vertex AI features) or Google API key (for Gemini API)

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

Navigate to your project directory and create a virtual environment:

```bash
cd /path/to/your/project
uv venv
```

This creates a `.venv` directory in your project.

## Step 3: Activate Virtual Environment

### macOS/Linux
```bash
source .venv/bin/activate
```

### Windows
```powershell
.venv\Scripts\activate
```

## Step 4: Install Google ADK

With your virtual environment activated, install Google ADK:

```bash
uv pip install google-adk
```

This will install Google ADK and all its dependencies, including:
- `google-genai` - Google's Generative AI SDK
- `google-cloud-aiplatform` - Vertex AI platform SDK
- `fastapi` - For web server functionality
- And many other dependencies

## Step 5: Verify Installation

Verify that Google ADK is installed correctly:

```bash
python -c "import google.adk; print(google.adk.__version__)"
```

You should see the version number printed.

## Step 6: Set Up Authentication

Google ADK requires authentication to use Google's AI services. You have two options:

### Option A: Google API Key (Simpler, for Gemini API)

1. Get your API key from [Google AI Studio](https://makersuite.google.com/app/apikey)
2. Create a `.env` file in your project root:

```bash
GOOGLE_API_KEY=your_api_key_here
```

### Option B: Google Cloud Credentials (For Vertex AI)

1. Install Google Cloud SDK: `gcloud init`
2. Authenticate: `gcloud auth application-default login`
3. Set your project: `gcloud config set project YOUR_PROJECT_ID`

Or set environment variables:
```bash
export GOOGLE_CLOUD_PROJECT=your-project-id
export GOOGLE_APPLICATION_CREDENTIALS=/path/to/service-account-key.json
```

## Step 7: Install Additional Dependencies (Optional)

For specific features, you may need additional packages:

```bash
# For code execution
uv pip install google-adk[code-executor]

# For all optional dependencies
uv pip install google-adk[all]
```

## Project Structure

After setup, your project structure should look like:

```
your-project/
├── .venv/              # Virtual environment
├── .env                # Environment variables (API keys)
├── docs/               # Documentation
├── examples/           # Example agents
└── requirements.txt    # Dependencies (optional)
```

## Quick Test

Create a simple test file `test_setup.py`:

```python
from google.adk import Agent

# Create a simple agent
agent = Agent(
    name="test_agent",
    description="A test agent",
    model="gemini-1.5-flash"
)

print("✅ Google ADK is set up correctly!")
print(f"Agent created: {agent.name}")
```

Run it:
```bash
python test_setup.py
```

## Troubleshooting

### Issue: `uv: command not found`
- Make sure UV is installed and in your PATH
- Try restarting your terminal

### Issue: `ModuleNotFoundError: No module named 'google.adk'`
- Ensure virtual environment is activated
- Reinstall: `uv pip install --upgrade google-adk`

### Issue: Authentication errors
- Verify your API key is correct in `.env`
- For Vertex AI, ensure `gcloud auth application-default login` is run
- Check that your project has the necessary APIs enabled

### Issue: Permission errors with UV cache
- UV may need write access to cache directories
- Try running with appropriate permissions or use `--no-cache` flag

## Next Steps

Now that you have Google ADK installed, you can:

1. Read the [Agents Package Documentation](01-Agents-Package.md)
2. Explore [Tools Package](02-Tools-Package.md)
3. Check out example agents in the `examples/` directory
4. Read the [Index](INDEX.md) for all available documentation

## Additional Resources

- [Google ADK Official Documentation](https://google.github.io/adk-docs/)
- [UV Documentation](https://github.com/astral-sh/uv)
- [Google AI Studio](https://makersuite.google.com/)
- [Vertex AI Documentation](https://cloud.google.com/vertex-ai/docs)
