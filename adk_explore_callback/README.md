# ADK Callback Exploration

Explore ADK callbacks (before/after Agent, Model, Tool) with detailed logging of what is passed in each invocation.

## Quick Start

```bash
GEMINI_MODEL=gemini-2.5-flash uv run python callback_exploration.py
```

Output is saved to `callback_exploration_output_<timestamp>.txt`.

## What's Included

- **callback_exploration.py** – Agent with all 6 callbacks that print RAW and FORMATTED input
- **docs/callbacks/** – ADK callback documentation (extracted from adk-docs)
- **docs/CALLBACK-SIGNATURES-REFERENCE.md** – Quick reference for callback parameters and return types
- **docs/EXTRACTION-GUIDE.md** – How raw docs were fetched from the adk-docs repo

## Callbacks Demonstrated

| Callback | When | What You Get |
|----------|------|--------------|
| before_agent | Before agent's main logic | CallbackContext |
| after_agent | After agent finishes | CallbackContext |
| before_model | Before LLM call | CallbackContext, LlmRequest |
| after_model | After LLM returns | CallbackContext, LlmResponse |
| before_tool | Before tool runs | tool, args, ToolContext |
| after_tool | After tool returns | tool, args, ToolContext, tool_response |

## Requirements

- `GOOGLE_API_KEY` or equivalent in `.env`
- `GEMINI_MODEL` (default: gemini-2.5-flash)
