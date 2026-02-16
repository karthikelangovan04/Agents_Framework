#!/usr/bin/env python3
"""
ADK Multi-Agent Demo: Plugin (Runner-scope) + Agent (Agent-scope) Callbacks

Demonstrates:
- PLUGIN callbacks: Runner-scope, apply to EVERY agent, model, and tool
  - FullDemoPlugin: sensitive data check, logging
  - CachePlugin: SQLite LLM cache
- AGENT callbacks: Local to each agent instance
  - time_agent, echo_agent, root (SequentialAgent) each have their own callbacks

Architecture:
- One Runner with plugins (global)
- SequentialAgent root with sub_agents = [time_agent, echo_agent]
- Plugin hooks run first; agent callbacks run after (per agent)

Usage:
  GEMINI_MODEL=gemini-2.5-flash uv run python callback_plugin_multi_agent_full_demo.py
"""

from __future__ import annotations

import asyncio
import hashlib
import json
import os
import re
import sqlite3
import sys
from datetime import datetime
from pathlib import Path
from typing import Any, Dict, Optional

from dotenv import load_dotenv
from google.adk.agents import Agent, BaseAgent
from google.adk.agents.callback_context import CallbackContext
from google.adk.agents.sequential_agent import SequentialAgent
from google.adk.memory import InMemoryMemoryService
from google.adk.models import LlmRequest, LlmResponse
from google.adk.plugins.base_plugin import BasePlugin
from google.adk.runners import Runner
from google.adk.sessions import InMemorySessionService
from google.adk.tools import BaseTool, FunctionTool, ToolContext
from google.genai import types

load_dotenv()

APP_NAME = "callback_plugin_multi_agent_full_demo"
GEMINI_MODEL = os.getenv("GEMINI_MODEL", "gemini-2.5-flash")
SCRIPT_DIR = Path(__file__).parent
DB_PATH = SCRIPT_DIR / "llm_cache_multi_agent.db"

NPI_PATTERN = re.compile(r"\b(\d{10})\b")
PCI_PATTERN = re.compile(r"\b(\d{4}[\s\-]?\d{4}[\s\-]?\d{4}[\s\-]?\d{4}(?:[\s\-]?\d{1,4})?)\b")


def _has_sensitive_data(text: str) -> bool:
    if not text:
        return False
    if NPI_PATTERN.search(text):
        return True
    for m in PCI_PATTERN.finditer(text):
        if 13 <= len(re.sub(r"\D", "", m.group(1))) <= 19:
            return True
    return False


def _get_text_from_content(c) -> str:
    parts = getattr(c, "parts", []) or []
    return " ".join(getattr(p, "text", "") or "" for p in parts if hasattr(p, "text"))


def _make_cache_key(llm_request: LlmRequest) -> str:
    """Hash request contents for cache key."""
    parts = []
    for c in getattr(llm_request, "contents", []) or []:
        parts.append(f"{getattr(c, 'role', '')}:{_get_text_from_content(c)}")
    return hashlib.sha256(json.dumps(parts).encode()).hexdigest()[:32]


def _extract_text_from_response(llm_response: LlmResponse) -> str:
    c = getattr(llm_response, "content", None)
    if not c:
        return ""
    return _get_text_from_content(c)


def _build_cached_response(text: str) -> LlmResponse:
    return LlmResponse(
        content=types.Content(role="model", parts=[types.Part(text=text)]),
    )


# ---------------------------------------------------------------------------
# SQLite cache init
# ---------------------------------------------------------------------------

def init_cache_db():
    conn = sqlite3.connect(DB_PATH)
    conn.execute("""
        CREATE TABLE IF NOT EXISTS llm_cache (
            cache_key TEXT PRIMARY KEY,
            response_text TEXT NOT NULL,
            created_at TIMESTAMP DEFAULT CURRENT_TIMESTAMP
        )
    """)
    conn.commit()
    conn.close()


# ---------------------------------------------------------------------------
# Full Plugin: All hooks (Runner-scope, apply to every agent)
# ---------------------------------------------------------------------------

class FullDemoPlugin(BasePlugin):
    def __init__(self):
        super().__init__(name="full_demo_plugin")
        self.call_log: list = []

    def _log(self, hook: str, msg: str = ""):
        entry = f"[Plugin:{hook}] {msg}".strip()
        self.call_log.append(entry)
        print(entry)

    async def on_user_message_callback(
        self, *, invocation_context, user_message: types.Content
    ) -> Optional[types.Content]:
        self._log("on_user_message", "User message received")
        text = _get_text_from_content(user_message)
        if _has_sensitive_data(text):
            self._log("on_user_message", "*** SENSITIVE DATA DETECTED (NPI/PCI) - Will skip agent ***")
            invocation_context.session.state["sensitive_data_detected"] = True
        return None

    async def before_run_callback(self, *, invocation_context) -> Optional[types.Content]:
        self._log("before_run", "Runner starting")
        return None

    async def after_run_callback(self, *, invocation_context) -> None:
        self._log("after_run", "Runner finished")

    async def before_agent_callback(
        self, *, agent: BaseAgent, callback_context: CallbackContext
    ) -> Optional[types.Content]:
        self._log("before_agent", f"Agent '{agent.name}' about to run")
        if callback_context.state.get("sensitive_data_detected"):
            self._log("before_agent", "Skipping agent - sensitive data in user message")
            return types.Content(
                role="model",
                parts=[
                    types.Part(
                        text="Your message contains sensitive data (NPI or credit card detected). "
                        "Please rephrase without sharing such information."
                    )
                ],
            )
        return None

    async def after_agent_callback(
        self, *, agent: BaseAgent, callback_context: CallbackContext
    ) -> Optional[types.Content]:
        self._log("after_agent", f"Agent '{agent.name}' finished")
        return None

    async def before_model_callback(
        self, *, callback_context: CallbackContext, llm_request: LlmRequest
    ) -> Optional[LlmResponse]:
        self._log("before_model", "Before LLM call")
        return None

    async def after_model_callback(
        self, *, callback_context: CallbackContext, llm_response: LlmResponse
    ) -> Optional[LlmResponse]:
        self._log("after_model", "After LLM call")
        return None

    async def on_model_error_callback(
        self, *, callback_context: CallbackContext, llm_request: LlmRequest, error: Exception
    ) -> Optional[LlmResponse]:
        self._log("on_model_error", f"Model error: {error}")
        return _build_cached_response(f"[Fallback] Model error: {error}. Please try again.")

    async def before_tool_callback(
        self, *, tool: BaseTool, tool_args: dict, tool_context: ToolContext
    ) -> Optional[dict]:
        self._log("before_tool", f"Tool '{tool.name}' about to run, args={tool_args}")
        return None

    async def after_tool_callback(
        self, *, tool: BaseTool, tool_args: dict, tool_context: ToolContext, result: dict
    ) -> Optional[dict]:
        self._log("after_tool", f"Tool '{tool.name}' finished, result={result}")
        return None

    async def on_tool_error_callback(
        self, *, tool: BaseTool, tool_args: dict, tool_context: ToolContext, error: Exception
    ) -> Optional[dict]:
        self._log("on_tool_error", f"Tool '{tool.name}' error: {error}")
        return {"error": str(error), "fallback": True}

    async def on_event_callback(self, *, invocation_context, event) -> Optional[Any]:
        self._log("on_event", f"Event from {getattr(event, 'author', '?')}")
        return None


# ---------------------------------------------------------------------------
# Cache plugin
# ---------------------------------------------------------------------------

_cache_key_by_session: Dict[str, str] = {}


class CachePlugin(BasePlugin):
    """Handles LLM response caching in SQLite."""

    def __init__(self):
        super().__init__(name="cache_plugin")

    async def before_model_callback(
        self, *, callback_context: CallbackContext, llm_request: LlmRequest
    ) -> Optional[LlmResponse]:
        cache_key = _make_cache_key(llm_request)
        sid = callback_context.session.id if callback_context.session else "default"
        _cache_key_by_session[sid] = cache_key
        conn = sqlite3.connect(DB_PATH)
        try:
            row = conn.execute(
                "SELECT response_text FROM llm_cache WHERE cache_key = ?", (cache_key,)
            ).fetchone()
            if row:
                print(f"[CachePlugin] CACHE HIT for key {cache_key[:8]}...")
                return _build_cached_response(row[0])
        finally:
            conn.close()
        return None

    async def after_model_callback(
        self, *, callback_context: CallbackContext, llm_response: LlmResponse
    ) -> Optional[LlmResponse]:
        sid = callback_context.session.id if callback_context.session else "default"
        cache_key = _cache_key_by_session.pop(sid, None)
        if cache_key:
            text = _extract_text_from_response(llm_response)
            has_fn_call = False
            if hasattr(llm_response, "content") and llm_response.content:
                for p in llm_response.content.parts or []:
                    if getattr(p, "function_call", None):
                        has_fn_call = True
                        break
            if text and not has_fn_call:
                conn = sqlite3.connect(DB_PATH)
                try:
                    conn.execute(
                        "INSERT OR REPLACE INTO llm_cache (cache_key, response_text) VALUES (?, ?)",
                        (cache_key, text),
                    )
                    conn.commit()
                    print(f"[CachePlugin] CACHE STORED for key {cache_key[:8]}...")
                finally:
                    conn.close()
        return None


# ---------------------------------------------------------------------------
# Tools
# ---------------------------------------------------------------------------

def get_current_time(tool_context: ToolContext) -> Dict[str, str]:
    """Returns current date and time. Call when user asks about time or date."""
    now = datetime.now()
    return {
        "current_time": now.strftime("%H:%M:%S"),
        "current_date": now.strftime("%Y-%m-%d"),
        "timezone": "local",
    }


def echo_message(tool_context: ToolContext, message: str = "") -> Dict[str, str]:
    """Echoes the given message. Use when user wants to repeat or confirm something."""
    return {"echoed": message or "(empty)", "length": len(message or "")}


get_current_time_tool = FunctionTool(get_current_time)
echo_message_tool = FunctionTool(echo_message)


# ---------------------------------------------------------------------------
# Agent callback factories (agent-scope, local to each agent)
# ---------------------------------------------------------------------------

def make_llm_agent_callbacks(agent_name: str):
    """Create all callbacks for LlmAgent (model + tool hooks supported)."""
    def before_agent(callback_context: CallbackContext) -> Optional[types.Content]:
        print(f"[Agent:{agent_name}] before_agent_callback")
        return None

    def after_agent(callback_context: CallbackContext) -> Optional[types.Content]:
        print(f"[Agent:{agent_name}] after_agent_callback")
        return None

    def before_model(
        callback_context: CallbackContext, llm_request: LlmRequest
    ) -> Optional[LlmResponse]:
        print(f"[Agent:{agent_name}] before_model_callback")
        return None

    def after_model(
        callback_context: CallbackContext, llm_response: LlmResponse
    ) -> Optional[LlmResponse]:
        print(f"[Agent:{agent_name}] after_model_callback")
        return None

    def before_tool(tool, args: dict, tool_context: ToolContext) -> Optional[dict]:
        print(f"[Agent:{agent_name}] before_tool_callback: {getattr(tool, 'name', '?')}")
        return None

    def after_tool(
        tool, args: dict, tool_context: ToolContext, tool_response: dict
    ) -> Optional[dict]:
        print(f"[Agent:{agent_name}] after_tool_callback: {getattr(tool, 'name', '?')}")
        return None

    return {
        "before_agent_callback": before_agent,
        "after_agent_callback": after_agent,
        "before_model_callback": before_model,
        "after_model_callback": after_model,
        "before_tool_callback": before_tool,
        "after_tool_callback": after_tool,
    }


def make_base_agent_callbacks(agent_name: str):
    """Create callbacks for BaseAgent (SequentialAgent etc. - only agent hooks)."""
    def before_agent(callback_context: CallbackContext) -> Optional[types.Content]:
        print(f"[Agent:{agent_name}] before_agent_callback")
        return None

    def after_agent(callback_context: CallbackContext) -> Optional[types.Content]:
        print(f"[Agent:{agent_name}] after_agent_callback")
        return None

    return {
        "before_agent_callback": before_agent,
        "after_agent_callback": after_agent,
    }


# ---------------------------------------------------------------------------
# Sub-agents and root SequentialAgent
# ---------------------------------------------------------------------------

time_agent = Agent(
    name="time_agent",
    model=GEMINI_MODEL,
    description="Tells current time and date.",
    instruction="Use get_current_time when asked about time or date. Be concise.",
    tools=[get_current_time_tool],
    **make_llm_agent_callbacks("time_agent"),
)

echo_agent = Agent(
    name="echo_agent",
    model=GEMINI_MODEL,
    description="Echoes user messages.",
    instruction="Use echo_message to repeat what the user said. Be brief.",
    tools=[echo_message_tool],
    **make_llm_agent_callbacks("echo_agent"),
)

root_agent = SequentialAgent(
    name="root_sequential",
    sub_agents=[time_agent, echo_agent],
    **make_base_agent_callbacks("root_sequential"),
)


# ---------------------------------------------------------------------------
# Main
# ---------------------------------------------------------------------------

class TeeOutput:
    def __init__(self, fh, stream):
        self.terminal = stream
        self.log_file = fh

    def write(self, msg):
        self.terminal.write(msg)
        self.log_file.write(msg)
        self.log_file.flush()

    def flush(self):
        self.terminal.flush()
        self.log_file.flush()


async def main():
    init_cache_db()

    timestamp = datetime.now().strftime("%Y%m%d_%H%M%S")
    output_file = SCRIPT_DIR / f"callback_plugin_multi_agent_output_{timestamp}.txt"

    fh = open(output_file, "w", encoding="utf-8")
    orig_stdout, orig_stderr = sys.stdout, sys.stderr
    tee = TeeOutput(fh, sys.stdout)
    sys.stdout = sys.stderr = tee

    try:
        print("=" * 80)
        print("ADK Multi-Agent Demo: Plugin (Runner) + Agent (Local) Callbacks")
        print("=" * 80)
        print(f"Output: {output_file}")
        print(f"Cache DB: {DB_PATH}")
        print("Root: SequentialAgent with sub_agents=[time_agent, echo_agent]")
        print("Plugin callbacks: global (every agent). Agent callbacks: local (per agent).")
        print("=" * 80)

        full_plugin = FullDemoPlugin()
        cache_plugin = CachePlugin()

        runner = Runner(
            agent=root_agent,
            app_name=APP_NAME,
            session_service=InMemorySessionService(),
            memory_service=InMemoryMemoryService(),
            plugins=[full_plugin, cache_plugin],
        )

        user_id = "user_001"
        session_id = f"multi_agent_{timestamp}"
        await runner.session_service.create_session(
            app_name=APP_NAME, user_id=user_id, session_id=session_id
        )

        # Test 1: What time is it? (time_agent runs first in sequence)
        print("\n--- Test 1: What time is it? ---")
        msg1 = types.Content(
            parts=[types.Part(text="What time is it right now?")],
            role="user",
        )
        async for event in runner.run_async(
            user_id=user_id, session_id=session_id, new_message=msg1
        ):
            if hasattr(event, "content") and event.content and event.content.parts:
                for p in event.content.parts:
                    if hasattr(p, "text") and p.text:
                        print(f"\n[RESPONSE] {p.text}")

        # Test 2: Same question in NEW session - cache hit
        session_id_2 = f"multi_agent_cache_{timestamp}"
        await runner.session_service.create_session(
            app_name=APP_NAME, user_id=user_id, session_id=session_id_2
        )
        print("\n--- Test 2: Same question in fresh session (expect CACHE HIT) ---")
        async for event in runner.run_async(
            user_id=user_id, session_id=session_id_2, new_message=msg1
        ):
            if hasattr(event, "content") and event.content and event.content.parts:
                for p in event.content.parts:
                    if hasattr(p, "text") and p.text:
                        print(f"\n[RESPONSE] {p.text}")

        # Test 3: Sensitive data - should skip agent
        print("\n--- Test 3: Sensitive data (expect skip) ---")
        msg3 = types.Content(
            parts=[
                types.Part(
                    text="My NPI is 1234567890 and my card is 4111 1111 1111 1111. Help me."
                )
            ],
            role="user",
        )
        async for event in runner.run_async(
            user_id=user_id, session_id=session_id, new_message=msg3
        ):
            if hasattr(event, "content") and event.content and event.content.parts:
                for p in event.content.parts:
                    if hasattr(p, "text") and p.text:
                        print(f"\n[RESPONSE] {p.text}")

        # Test 4: Echo request (echo_agent in sequence)
        print("\n--- Test 4: Echo (echo_agent) ---")
        msg4 = types.Content(
            parts=[types.Part(text="Echo back: Hello World")],
            role="user",
        )
        async for event in runner.run_async(
            user_id=user_id, session_id=session_id, new_message=msg4
        ):
            if hasattr(event, "content") and event.content and event.content.parts:
                for p in event.content.parts:
                    if hasattr(p, "text") and p.text:
                        print(f"\n[RESPONSE] {p.text}")

        print("\n" + "=" * 80)
        print("Demo complete.")
        print("=" * 80)

    except Exception as e:
        import traceback

        print(f"\nERROR: {e}")
        traceback.print_exc()
    finally:
        sys.stdout, sys.stderr = orig_stdout, orig_stderr
        fh.close()
        print(f"\nDone. Output: {output_file}")


if __name__ == "__main__":
    asyncio.run(main())
