#!/usr/bin/env python3
"""
ADK Callback Exploration Script

Demonstrates all 6 callbacks (before/after Agent, Model, Tool) with detailed
logging of what is passed in each invocation - both RAW and FORMATTED.

Reference: test_google_search_postgres_with_tokens_simple.py
Docs: adk_explore_callback/docs/callbacks/

Usage:
  GEMINI_MODEL=gemini-2.5-flash uv run python callback_exploration.py
"""

from __future__ import annotations

import asyncio
import json
import os
import sys
from datetime import datetime
from pathlib import Path
from typing import Any, Dict, Optional

from dotenv import load_dotenv
from google.adk.agents import Agent
from google.adk.agents.callback_context import CallbackContext
from google.adk.memory import InMemoryMemoryService
from google.adk.models import LlmRequest, LlmResponse
from google.adk.runners import Runner
from google.adk.sessions import InMemorySessionService
from google.adk.tools import FunctionTool, ToolContext
from google.genai import types

load_dotenv()

APP_NAME = "callback_exploration_app"
GEMINI_MODEL = os.getenv("GEMINI_MODEL", "gemini-2.5-flash")


# ---------------------------------------------------------------------------
# Simple tool for the agent (no external APIs)
# ---------------------------------------------------------------------------

def get_current_time(tool_context: ToolContext) -> Dict[str, str]:
    """Returns current date and time. Call this when the user asks about time or date."""
    now = datetime.now()
    return {
        "current_time": now.strftime("%H:%M:%S"),
        "current_date": now.strftime("%Y-%m-%d"),
        "timezone": "local",
    }


get_current_time_tool = FunctionTool(get_current_time)


# ---------------------------------------------------------------------------
# Formatting helpers for callback output
# ---------------------------------------------------------------------------

def _safe_repr(obj: Any, max_len: int = 2000) -> str:
    """Raw representation - safe for complex objects."""
    try:
        s = repr(obj)
        return s[:max_len] + "..." if len(s) > max_len else s
    except Exception as e:
        return f"<repr error: {e}>"


def _format_for_display(obj: Any) -> str:
    """Formatted display - human-readable."""
    if obj is None:
        return "None"
    if isinstance(obj, dict):
        try:
            return json.dumps(obj, indent=2, default=str)[:1500]
        except Exception:
            return _safe_repr(obj, 500)
    if hasattr(obj, "model_dump"):
        try:
            return json.dumps(obj.model_dump(), indent=2, default=str)[:1500]
        except Exception:
            pass
    if hasattr(obj, "__dict__"):
        try:
            d = {k: v for k, v in obj.__dict__.items() if not k.startswith("_")}
            return json.dumps(d, indent=2, default=str)[:1500]
        except Exception:
            pass
    return _safe_repr(obj, 500)


def _format_callback_context(ctx: CallbackContext) -> Dict[str, Any]:
    """Extract key fields from CallbackContext for display."""
    try:
        state = ctx.state
        state_keys = list(state.keys()) if hasattr(state, "keys") and state else []
        state_preview = dict(state) if state and hasattr(state, "items") else {}
        return {
            "agent_name": getattr(ctx, "agent_name", "?"),
            "session_id": ctx.session.id if ctx.session else "?",
            "state_keys": state_keys,
            "state_preview": state_preview,
        }
    except Exception as e:
        return {"error": str(e)}


def _format_llm_request(req: LlmRequest) -> Dict[str, Any]:
    """Extract key fields from LlmRequest."""
    try:
        out = {}
        if hasattr(req, "contents") and req.contents:
            out["contents_count"] = len(req.contents)
            out["contents_preview"] = []
            for c in req.contents[:3]:
                role = getattr(c, "role", "?")
                parts = getattr(c, "parts", []) or []
                texts = []
                for p in parts[:2]:
                    if hasattr(p, "text") and p.text:
                        texts.append(p.text[:80])
                    elif hasattr(p, "function_call"):
                        texts.append(f"<function_call: {getattr(p.function_call, 'name', '?')}>")
                    elif hasattr(p, "function_response"):
                        texts.append("<function_response>")
                out["contents_preview"].append({"role": role, "texts": texts or ["(no text)"]})
        if hasattr(req, "config") and req.config:
            cfg = req.config
            if hasattr(cfg, "system_instruction") and cfg.system_instruction:
                si = cfg.system_instruction
                if isinstance(si, str):
                    txt = si
                elif hasattr(si, "parts") and si.parts:
                    txt = getattr(si.parts[0], "text", "") or str(si)
                else:
                    txt = str(si)
                out["system_instruction_preview"] = (txt or "")[:200]
        return out
    except Exception as e:
        return {"error": str(e)}


def _format_llm_response(resp: LlmResponse) -> Dict[str, Any]:
    """Extract key fields from LlmResponse."""
    try:
        out = {}
        if hasattr(resp, "content") and resp.content:
            c = resp.content
            role = getattr(c, "role", "?")
            parts = getattr(c, "parts", []) or []
            texts = []
            for p in parts[:3]:
                if hasattr(p, "text") and p.text:
                    texts.append(p.text[:150])
                elif hasattr(p, "function_call"):
                    texts.append(f"<function_call: {getattr(p.function_call, 'name', '?')}>")
            out["content_role"] = role
            out["content_texts"] = texts or ["(function_call or other)"]
        if hasattr(resp, "usage_metadata") and resp.usage_metadata:
            um = resp.usage_metadata
            out["usage"] = {
                "prompt_tokens": getattr(um, "prompt_token_count", None),
                "output_tokens": getattr(um, "candidates_token_count", None),
                "total_tokens": getattr(um, "total_token_count", None),
            }
        return out
    except Exception as e:
        return {"error": str(e)}


# ---------------------------------------------------------------------------
# Callbacks - each logs RAW and FORMATTED input
# ---------------------------------------------------------------------------

def before_agent_callback(callback_context: CallbackContext) -> Optional[types.Content]:
    """Before agent: runs before agent's main logic."""
    sep = "=" * 80
    print(f"\n{sep}")
    print("CALLBACK: before_agent_callback")
    print(f"{sep}")
    print("\n[RAW] callback_context:", _safe_repr(callback_context, 800))
    print("\n[FORMATTED] callback_context:")
    print(json.dumps(_format_callback_context(callback_context), indent=2, default=str))
    print(f"{sep}\n")
    return None


def after_agent_callback(callback_context: CallbackContext) -> Optional[types.Content]:
    """After agent: runs after agent's main logic completes."""
    sep = "=" * 80
    print(f"\n{sep}")
    print("CALLBACK: after_agent_callback")
    print(f"{sep}")
    print("\n[RAW] callback_context:", _safe_repr(callback_context, 800))
    print("\n[FORMATTED] callback_context:")
    print(json.dumps(_format_callback_context(callback_context), indent=2, default=str))
    print(f"{sep}\n")
    return None


def before_model_callback(
    callback_context: CallbackContext, llm_request: LlmRequest
) -> Optional[LlmResponse]:
    """Before model: runs before LLM call."""
    sep = "=" * 80
    print(f"\n{sep}")
    print("CALLBACK: before_model_callback")
    print(f"{sep}")
    print("\n[RAW] callback_context:", _safe_repr(callback_context, 600))
    print("\n[RAW] llm_request:", _safe_repr(llm_request, 1000))
    print("\n[FORMATTED] callback_context:")
    print(json.dumps(_format_callback_context(callback_context), indent=2, default=str))
    print("\n[FORMATTED] llm_request:")
    print(json.dumps(_format_llm_request(llm_request), indent=2, default=str))
    print(f"{sep}\n")
    return None


def after_model_callback(
    callback_context: CallbackContext, llm_response: LlmResponse
) -> Optional[LlmResponse]:
    """After model: runs after LLM returns."""
    sep = "=" * 80
    print(f"\n{sep}")
    print("CALLBACK: after_model_callback")
    print(f"{sep}")
    print("\n[RAW] callback_context:", _safe_repr(callback_context, 600))
    print("\n[RAW] llm_response:", _safe_repr(llm_response, 1000))
    print("\n[FORMATTED] callback_context:")
    print(json.dumps(_format_callback_context(callback_context), indent=2, default=str))
    print("\n[FORMATTED] llm_response:")
    print(json.dumps(_format_llm_response(llm_response), indent=2, default=str))
    print(f"{sep}\n")
    return None


def before_tool_callback(
    tool: Any, args: Dict[str, Any], tool_context: ToolContext
) -> Optional[Dict[str, Any]]:
    """Before tool: runs before tool execution. Args: (tool, args, tool_context)."""
    sep = "=" * 80
    print(f"\n{sep}")
    print("CALLBACK: before_tool_callback")
    print(f"{sep}")
    print("\n[RAW] tool:", _safe_repr(tool, 400))
    print("\n[RAW] args:", _safe_repr(args, 600))
    print("\n[RAW] tool_context:", _safe_repr(tool_context, 600))
    print("\n[FORMATTED] tool name:", getattr(tool, "name", str(tool)))
    print("\n[FORMATTED] args:")
    print(json.dumps(args, indent=2, default=str))
    st = tool_context.state
    print("\n[FORMATTED] tool_context.state keys:", list(st.keys()) if st and hasattr(st, "keys") else [])
    print(f"{sep}\n")
    return None


def after_tool_callback(
    tool: Any, args: Dict[str, Any], tool_context: ToolContext, tool_response: Dict[str, Any]
) -> Optional[Dict[str, Any]]:
    """After tool: runs after tool execution. Args: (tool, args, tool_context, tool_response)."""
    sep = "=" * 80
    print(f"\n{sep}")
    print("CALLBACK: after_tool_callback")
    print(f"{sep}")
    print("\n[RAW] tool:", _safe_repr(tool, 400))
    print("\n[RAW] args:", _safe_repr(args, 400))
    print("\n[RAW] tool_context:", _safe_repr(tool_context, 400))
    print("\n[RAW] tool_response:", _safe_repr(tool_response, 600))
    print("\n[FORMATTED] tool name:", getattr(tool, "name", str(tool)))
    print("\n[FORMATTED] tool_response:")
    print(json.dumps(tool_response, indent=2, default=str))
    print(f"{sep}\n")
    return None


# ---------------------------------------------------------------------------
# Agent with all callbacks
# ---------------------------------------------------------------------------

root_agent = Agent(
    name="callback_exploration_agent",
    model=GEMINI_MODEL,
    description="Agent to demonstrate callbacks - answers questions and can tell the time.",
    instruction=(
        "You are a helpful assistant. You can tell the user the current time when they ask. "
        "Be concise and friendly."
    ),
    tools=[get_current_time_tool],
    before_agent_callback=before_agent_callback,
    after_agent_callback=after_agent_callback,
    before_model_callback=before_model_callback,
    after_model_callback=after_model_callback,
    before_tool_callback=before_tool_callback,
    after_tool_callback=after_tool_callback,
)


# ---------------------------------------------------------------------------
# Main
# ---------------------------------------------------------------------------

class TeeOutput:
    """Write to both console and file."""

    def __init__(self, file_handle, stream):
        self.terminal = stream
        self.log_file = file_handle

    def write(self, message):
        self.terminal.write(message)
        self.log_file.write(message)
        self.log_file.flush()

    def flush(self):
        self.terminal.flush()
        self.log_file.flush()


async def main():
    script_dir = Path(__file__).parent
    timestamp = datetime.now().strftime("%Y%m%d_%H%M%S")
    output_file = script_dir / f"callback_exploration_output_{timestamp}.txt"

    log_file_handle = open(output_file, "w", encoding="utf-8")
    original_stdout = sys.stdout
    original_stderr = sys.stderr
    tee = TeeOutput(log_file_handle, sys.stdout)
    sys.stdout = tee
    sys.stderr = tee

    try:
        print("=" * 80)
        print("ADK Callback Exploration")
        print("=" * 80)
        print(f"Output file: {output_file}")
        print(f"Model: {GEMINI_MODEL}")
        print(f"Agent: {root_agent.name}")
        print("=" * 80)

        session_service = InMemorySessionService()
        memory_service = InMemoryMemoryService()

        runner = Runner(
            agent=root_agent,
            app_name=APP_NAME,
            session_service=session_service,
            memory_service=memory_service,
        )

        user_id = "user_001"
        session_id = f"callback_test_{timestamp}"

        session = await session_service.create_session(
            app_name=APP_NAME,
            user_id=user_id,
            session_id=session_id,
        )
        print(f"\nSession created: {session.id}\n")

        user_message = types.Content(
            parts=[types.Part(text="What time is it right now?")],
            role="user",
        )
        print(f"User message: {user_message.parts[0].text}\n")
        print("Running agent (observe callbacks below)...\n")

        response_text = None
        async for event in runner.run_async(
            user_id=user_id,
            session_id=session_id,
            new_message=user_message,
        ):
            if hasattr(event, "content") and event.content and event.content.parts:
                for part in event.content.parts:
                    if hasattr(part, "text") and part.text:
                        response_text = part.text
                        print(f"\n[AGENT RESPONSE] {response_text}")

        print("\n" + "=" * 80)
        print("Exploration complete.")
        print(f"Output saved to: {output_file}")
        print("=" * 80)

    except Exception as e:
        import traceback

        print(f"\nERROR: {e}")
        traceback.print_exc()
    finally:
        sys.stdout = original_stdout
        sys.stderr = original_stderr
        log_file_handle.close()
        print(f"\nDone. Output saved to: {output_file}")


if __name__ == "__main__":
    asyncio.run(main())
