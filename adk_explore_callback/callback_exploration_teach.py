#!/usr/bin/env python3
"""
ADK Callback Exploration - Teaching Version

A copy of callback_exploration.py with:
- NO truncation - full context for learning
- Session, events, and state shown for every callback
- How tools are passed to the LLM (name + description/metadata from docstring)

The LLM receives tool metadata (name, description, parameters) - NOT just the name.
FunctionTool uses the function's docstring as the description so the model can
pick the right tool.

Usage:
  GEMINI_MODEL=gemini-2.5-flash uv run python callback_exploration_teach.py
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

APP_NAME = "callback_exploration_teach_app"
GEMINI_MODEL = os.getenv("GEMINI_MODEL", "gemini-2.5-flash")

# No truncation for teaching - use 0 or very large to show full content
NO_TRUNCATE = 0  # 0 = no limit


# ---------------------------------------------------------------------------
# Tool with docstring - the docstring becomes the tool DESCRIPTION sent to the LLM
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
# Formatting helpers - NO truncation
# ---------------------------------------------------------------------------

def _safe_repr(obj: Any, max_len: int = 0) -> str:
    try:
        s = repr(obj)
        if max_len and len(s) > max_len:
            return s[:max_len] + "... [truncated]"
        return s
    except Exception as e:
        return f"<repr error: {e}>"


def _format_session(session) -> Dict[str, Any]:
    """Full session with events and state."""
    if not session:
        return {}
    try:
        events = []
        for i, ev in enumerate(getattr(session, "events", []) or []):
            ev_data = {
                "index": i,
                "author": getattr(ev, "author", "?"),
                "invocation_id": getattr(ev, "invocation_id", "?"),
            }
            if hasattr(ev, "content") and ev.content and hasattr(ev.content, "parts"):
                parts_preview = []
                for p in ev.content.parts[:5]:
                    if hasattr(p, "text") and p.text:
                        parts_preview.append({"type": "text", "text": p.text})
                    elif hasattr(p, "function_call"):
                        fc = p.function_call
                        parts_preview.append({
                            "type": "function_call",
                            "name": getattr(fc, "name", "?"),
                            "args": getattr(fc, "args", {}),
                        })
                    elif hasattr(p, "function_response"):
                        fr = p.function_response
                        parts_preview.append({
                            "type": "function_response",
                            "name": getattr(fr, "name", "?"),
                            "response": getattr(fr, "response", {}),
                        })
                ev_data["content_parts"] = parts_preview
            events.append(ev_data)
        state = getattr(session, "state", None)
        state_dict = dict(state) if state and hasattr(state, "items") else {}
        return {
            "id": session.id,
            "events_count": len(events),
            "events": events,
            "state": state_dict,
        }
    except Exception as e:
        return {"error": str(e)}


def _format_callback_context_full(ctx: CallbackContext) -> Dict[str, Any]:
    """Full context with session, events, state."""
    try:
        session = getattr(ctx, "session", None)
        state = ctx.state
        state_dict = dict(state) if state and hasattr(state, "items") else {}
        return {
            "agent_name": getattr(ctx, "agent_name", "?"),
            "session_id": session.id if session else "?",
            "state_keys": list(state.keys()) if hasattr(state, "keys") and state else [],
            "state_full": state_dict,
            "session_full": _format_session(session),
        }
    except Exception as e:
        return {"error": str(e)}


def _extract_tools_metadata(llm_request: LlmRequest) -> list:
    """
    Extract how tools are passed to the LLM.
    Tools include: name, description (from function docstring), parameters schema.
    The LLM needs this metadata to understand WHEN and HOW to call each tool.
    """
    out = []
    try:
        cfg = getattr(llm_request, "config", None)
        if not cfg:
            return out
        tools = getattr(cfg, "tools", None) or []
        for t in tools:
            decls = getattr(t, "function_declarations", []) or []
            for fd in decls:
                item = {
                    "name": getattr(fd, "name", "?"),
                    "description": getattr(fd, "description", ""),
                    "parameters": getattr(fd, "parameters", None),
                }
                if hasattr(item["parameters"], "properties"):
                    item["parameters_schema"] = {
                        "properties": getattr(item["parameters"], "properties", {}),
                        "required": getattr(item["parameters"], "required", []),
                    }
                else:
                    item["parameters_schema"] = str(item["parameters"])
                out.append(item)
    except Exception as e:
        out = [{"error": str(e)}]
    return out


def _format_llm_request_full(req: LlmRequest) -> Dict[str, Any]:
    """Full LLM request - no truncation. Includes tools metadata."""
    try:
        out = {"tools_passed_to_llm": _extract_tools_metadata(req)}
        if hasattr(req, "contents") and req.contents:
            out["contents_count"] = len(req.contents)
            out["contents_full"] = []
            for i, c in enumerate(req.contents):
                role = getattr(c, "role", "?")
                parts = getattr(c, "parts", []) or []
                part_list = []
                for p in parts:
                    if hasattr(p, "text") and p.text:
                        part_list.append({"type": "text", "text": p.text})
                    elif hasattr(p, "function_call"):
                        fc = p.function_call
                        part_list.append({
                            "type": "function_call",
                            "name": getattr(fc, "name", "?"),
                            "args": getattr(fc, "args", {}),
                        })
                    elif hasattr(p, "function_response"):
                        fr = p.function_response
                        part_list.append({
                            "type": "function_response",
                            "name": getattr(fr, "name", "?"),
                            "response": getattr(fr, "response", {}),
                        })
                out["contents_full"].append({"role": role, "parts": part_list})
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
                out["system_instruction_full"] = txt
        return out
    except Exception as e:
        return {"error": str(e)}


def _format_llm_response_full(resp: LlmResponse) -> Dict[str, Any]:
    try:
        out = {}
        if hasattr(resp, "content") and resp.content:
            c = resp.content
            parts = getattr(c, "parts", []) or []
            part_list = []
            for p in parts:
                if hasattr(p, "text") and p.text:
                    part_list.append({"type": "text", "text": p.text})
                elif hasattr(p, "function_call"):
                    fc = p.function_call
                    part_list.append({
                        "type": "function_call",
                        "name": getattr(fc, "name", "?"),
                        "args": getattr(fc, "args", {}),
                    })
            out["content_role"] = getattr(c, "role", "?")
            out["content_parts_full"] = part_list
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


def _format_tool_full(tool) -> Dict[str, Any]:
    """Full tool metadata - how it's represented for the LLM."""
    try:
        return {
            "name": getattr(tool, "name", "?"),
            "description": getattr(tool, "description", ""),
            "parameters": str(getattr(tool, "parameters", None)),
        }
    except Exception as e:
        return {"error": str(e)}


# ---------------------------------------------------------------------------
# Callbacks - full output, no truncation, session/events/state + tools metadata
# ---------------------------------------------------------------------------

def before_agent_callback(callback_context: CallbackContext) -> Optional[types.Content]:
    sep = "=" * 80
    print(f"\n{sep}")
    print("CALLBACK: before_agent_callback")
    print(f"{sep}")
    print("\n[RAW] callback_context:", _safe_repr(callback_context, NO_TRUNCATE))
    print("\n[FORMATTED] callback_context (session, events, state):")
    print(json.dumps(_format_callback_context_full(callback_context), indent=2, default=str))
    print(f"{sep}\n")
    return None


def after_agent_callback(callback_context: CallbackContext) -> Optional[types.Content]:
    sep = "=" * 80
    print(f"\n{sep}")
    print("CALLBACK: after_agent_callback")
    print(f"{sep}")
    print("\n[RAW] callback_context:", _safe_repr(callback_context, NO_TRUNCATE))
    print("\n[FORMATTED] callback_context (session, events, state):")
    print(json.dumps(_format_callback_context_full(callback_context), indent=2, default=str))
    print(f"{sep}\n")
    return None


def before_model_callback(
    callback_context: CallbackContext, llm_request: LlmRequest
) -> Optional[LlmResponse]:
    sep = "=" * 80
    print(f"\n{sep}")
    print("CALLBACK: before_model_callback")
    print(f"{sep}")
    print("\n[RAW] callback_context:", _safe_repr(callback_context, NO_TRUNCATE))
    print("\n[RAW] llm_request:", _safe_repr(llm_request, NO_TRUNCATE))
    print("\n[FORMATTED] callback_context (session, events, state):")
    print(json.dumps(_format_callback_context_full(callback_context), indent=2, default=str))
    print("\n[FORMATTED] llm_request (includes tools metadata - name + description from docstring):")
    req_fmt = _format_llm_request_full(llm_request)
    print(json.dumps(req_fmt, indent=2, default=str))
    print("\n*** HOW TOOLS ARE PASSED TO LLM ***")
    print("The LLM receives tools as function_declarations with: name, description (from docstring), parameters.")
    print("This metadata lets the model pick the right tool. See 'tools_passed_to_llm' above.")
    print(f"{sep}\n")
    return None


def after_model_callback(
    callback_context: CallbackContext, llm_response: LlmResponse
) -> Optional[LlmResponse]:
    sep = "=" * 80
    print(f"\n{sep}")
    print("CALLBACK: after_model_callback")
    print(f"{sep}")
    print("\n[RAW] callback_context:", _safe_repr(callback_context, NO_TRUNCATE))
    print("\n[RAW] llm_response:", _safe_repr(llm_response, NO_TRUNCATE))
    print("\n[FORMATTED] callback_context (session, events, state):")
    print(json.dumps(_format_callback_context_full(callback_context), indent=2, default=str))
    print("\n[FORMATTED] llm_response:")
    print(json.dumps(_format_llm_response_full(llm_response), indent=2, default=str))
    print(f"{sep}\n")
    return None


def before_tool_callback(
    tool: Any, args: Dict[str, Any], tool_context: ToolContext
) -> Optional[Dict[str, Any]]:
    sep = "=" * 80
    print(f"\n{sep}")
    print("CALLBACK: before_tool_callback")
    print(f"{sep}")
    print("\n[RAW] tool:", _safe_repr(tool, NO_TRUNCATE))
    print("\n[RAW] args:", _safe_repr(args, NO_TRUNCATE))
    print("\n[RAW] tool_context:", _safe_repr(tool_context, NO_TRUNCATE))
    print("\n[FORMATTED] tool (metadata - name, description from docstring):")
    print(json.dumps(_format_tool_full(tool), indent=2, default=str))
    print("\n[FORMATTED] args:", json.dumps(args, indent=2, default=str))
    st = tool_context.state
    print("\n[FORMATTED] tool_context.state:", dict(st) if st and hasattr(st, "items") else {})
    print("\n[FORMATTED] session/events from tool_context:")
    inv_ctx = getattr(tool_context, "_invocation_context", None)
    if inv_ctx and hasattr(inv_ctx, "session"):
        print(json.dumps(_format_session(inv_ctx.session), indent=2, default=str))
    print(f"{sep}\n")
    return None


def after_tool_callback(
    tool: Any, args: Dict[str, Any], tool_context: ToolContext, tool_response: Dict[str, Any]
) -> Optional[Dict[str, Any]]:
    sep = "=" * 80
    print(f"\n{sep}")
    print("CALLBACK: after_tool_callback")
    print(f"{sep}")
    print("\n[RAW] tool:", _safe_repr(tool, NO_TRUNCATE))
    print("\n[RAW] args:", _safe_repr(args, NO_TRUNCATE))
    print("\n[RAW] tool_context:", _safe_repr(tool_context, NO_TRUNCATE))
    print("\n[RAW] tool_response:", _safe_repr(tool_response, NO_TRUNCATE))
    print("\n[FORMATTED] tool metadata:", json.dumps(_format_tool_full(tool), indent=2, default=str))
    print("\n[FORMATTED] tool_response:", json.dumps(tool_response, indent=2, default=str))
    st = tool_context.state
    print("\n[FORMATTED] tool_context.state:", dict(st) if st and hasattr(st, "items") else {})
    print(f"{sep}\n")
    return None


# ---------------------------------------------------------------------------
# Agent
# ---------------------------------------------------------------------------

root_agent = Agent(
    name="callback_exploration_teach_agent",
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
    output_file = script_dir / f"callback_exploration_teach_output_{timestamp}.txt"

    log_file_handle = open(output_file, "w", encoding="utf-8")
    original_stdout = sys.stdout
    original_stderr = sys.stderr
    tee = TeeOutput(log_file_handle, sys.stdout)
    sys.stdout = tee
    sys.stderr = tee

    try:
        print("=" * 80)
        print("ADK Callback Exploration - Teaching Version (no truncation)")
        print("=" * 80)
        print(f"Output file: {output_file}")
        print(f"Model: {GEMINI_MODEL}")
        print(f"Agent: {root_agent.name}")
        print("\nTool docstring (becomes LLM tool description):")
        print(f"  {get_current_time.__doc__.strip()}")
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
        session_id = f"callback_teach_{timestamp}"

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
        print("Running agent (full context, no truncation)...\n")

        async for event in runner.run_async(
            user_id=user_id,
            session_id=session_id,
            new_message=user_message,
        ):
            if hasattr(event, "content") and event.content and event.content.parts:
                for part in event.content.parts:
                    if hasattr(part, "text") and part.text:
                        print(f"\n[AGENT RESPONSE] {part.text}")

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
        print(f"\nDone. Output: {output_file}")


if __name__ == "__main__":
    asyncio.run(main())
