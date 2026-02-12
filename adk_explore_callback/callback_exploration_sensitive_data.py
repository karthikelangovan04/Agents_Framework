#!/usr/bin/env python3
"""
ADK Callback: Sensitive Data Protection Demo

Demonstrates protecting NPI (National Provider Identifier) and PCI (credit card)
data before it reaches the LLM. Sensitive values are replaced with hashed tokens,
stored in SQLite, then restored in the response after the LLM call.

Usage:
  GEMINI_MODEL=gemini-2.5-flash uv run python callback_exploration_sensitive_data.py
"""

from __future__ import annotations

import asyncio
import hashlib
import re
import sqlite3
import os
import sys
from datetime import datetime
from pathlib import Path
import json
from typing import Any, Dict, List, Optional

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

APP_NAME = "callback_sensitive_data_app"
GEMINI_MODEL = os.getenv("GEMINI_MODEL", "gemini-2.5-flash")

# SQLite DB for hash -> original mapping (scoped per session)
SCRIPT_DIR = Path(__file__).parent
DB_PATH = SCRIPT_DIR / "sensitive_data_mapping.db"

# Token prefixes so we can detect them in LLM response
NPI_TOKEN_PREFIX = "NPI_TOKEN_"
PCI_TOKEN_PREFIX = "PCI_TOKEN_"


# ---------------------------------------------------------------------------
# Formatting helpers (like original callback_exploration.py)
# ---------------------------------------------------------------------------

def _safe_repr(obj: Any, max_len: int = 2000) -> str:
    try:
        s = repr(obj)
        return s[:max_len] + "..." if len(s) > max_len else s
    except Exception as e:
        return f"<repr error: {e}>"


def _format_callback_context(ctx: CallbackContext) -> Dict[str, Any]:
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
    try:
        out = {}
        if hasattr(req, "contents") and req.contents:
            out["contents_count"] = len(req.contents)
            out["contents_preview"] = []
            for c in req.contents[:5]:
                role = getattr(c, "role", "?")
                parts = getattr(c, "parts", []) or []
                texts = []
                for p in parts[:3]:
                    if hasattr(p, "text") and p.text:
                        texts.append(p.text[:200])
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
                out["system_instruction_preview"] = (txt or "")[:300]
        return out
    except Exception as e:
        return {"error": str(e)}


def _format_llm_response(resp: LlmResponse) -> Dict[str, Any]:
    try:
        out = {}
        if hasattr(resp, "content") and resp.content:
            c = resp.content
            role = getattr(c, "role", "?")
            parts = getattr(c, "parts", []) or []
            texts = []
            for p in parts[:3]:
                if hasattr(p, "text") and p.text:
                    texts.append(p.text[:300])
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
# Sensitive data patterns
# ---------------------------------------------------------------------------

# NPI: 10-digit number (National Provider Identifier)
NPI_PATTERN = re.compile(r"\b(\d{10})\b")

# PCI: Credit card - 13-19 digits, optional spaces/dashes between groups
# Matches: 4111111111111111, 4111 1111 1111 1111, 4111-1111-1111-1111
PCI_PATTERN = re.compile(
    r"\b(\d{4}[\s\-]?\d{4}[\s\-]?\d{4}[\s\-]?\d{4}(?:[\s\-]?\d{1,4})?)\b"
)


def _make_hash(value: str, prefix: str) -> str:
    """Create a short hash for the token."""
    h = hashlib.sha256(value.encode()).hexdigest()[:12]
    return f"{prefix}{h}"


def _detect_and_replace_sensitive(text: str, session_id: str, conn: sqlite3.Connection) -> str:
    """
    Replace sensitive values with hashed tokens. Returns modified text.
    Stores mapping in SQLite.
    """
    if not text:
        return text
    result = text

    # NPI
    for m in NPI_PATTERN.finditer(text):
        orig = m.group(1)
        token = _make_hash(orig, NPI_TOKEN_PREFIX)
        conn.execute(
            "INSERT OR REPLACE INTO mapping (session_id, token, original_value, kind) VALUES (?, ?, ?, ?)",
            (session_id, token, orig, "NPI"),
        )
        result = result.replace(orig, token, 1)

    # PCI (credit card)
    for m in PCI_PATTERN.finditer(text):
        orig = m.group(1)
        # Normalize for storage (digits only for matching)
        digits_only = re.sub(r"\D", "", orig)
        if 13 <= len(digits_only) <= 19:  # Valid card length
            token = _make_hash(orig, PCI_TOKEN_PREFIX)
            conn.execute(
                "INSERT OR REPLACE INTO mapping (session_id, token, original_value, kind) VALUES (?, ?, ?, ?)",
                (session_id, token, orig, "PCI"),
            )
            result = result.replace(orig, token, 1)

    return result


def _restore_sensitive(text: str, session_id: str, conn: sqlite3.Connection) -> str:
    """
    Replace hashed tokens with original values. Returns modified text.
    """
    if not text:
        return text
    result = text

    for prefix in (NPI_TOKEN_PREFIX, PCI_TOKEN_PREFIX):
        pattern = re.compile(re.escape(prefix) + r"[a-f0-9]{12}")
        for m in pattern.finditer(text):
            token = m.group(0)
            row = conn.execute(
                "SELECT original_value FROM mapping WHERE session_id = ? AND token = ?",
                (session_id, token),
            ).fetchone()
            if row:
                result = result.replace(token, row[0], 1)

    return result


# ---------------------------------------------------------------------------
# SQLite setup
# ---------------------------------------------------------------------------

def init_db():
    """Create SQLite table for hash mappings."""
    conn = sqlite3.connect(DB_PATH)
    conn.execute("""
        CREATE TABLE IF NOT EXISTS mapping (
            session_id TEXT NOT NULL,
            token TEXT NOT NULL,
            original_value TEXT NOT NULL,
            kind TEXT NOT NULL,
            created_at TIMESTAMP DEFAULT CURRENT_TIMESTAMP,
            PRIMARY KEY (session_id, token)
        )
    """)
    conn.commit()
    conn.close()


# ---------------------------------------------------------------------------
# Tool
# ---------------------------------------------------------------------------

def get_current_time(tool_context: ToolContext) -> Dict[str, str]:
    """Returns current date and time."""
    now = datetime.now()
    return {
        "current_time": now.strftime("%H:%M:%S"),
        "current_date": now.strftime("%Y-%m-%d"),
        "timezone": "local",
    }


get_current_time_tool = FunctionTool(get_current_time)


# ---------------------------------------------------------------------------
# Callbacks: before_model hashes sensitive data, after_model restores it
# ---------------------------------------------------------------------------

def before_model_callback(
    callback_context: CallbackContext, llm_request: LlmRequest
) -> Optional[LlmResponse]:
    """
    Before LLM: replace NPI and PCI values with hashed tokens.
    Sensitive data never reaches the model.
    """
    sep = "=" * 80
    print(f"\n{sep}")
    print("CALLBACK: before_model_callback (SENSITIVE DATA PROTECTION)")
    print(f"{sep}")

    # Raw and formatted BEFORE redaction
    print("\n[RAW] callback_context:", _safe_repr(callback_context, 600))
    print("\n[RAW] llm_request (BEFORE redaction):", _safe_repr(llm_request, 1200))
    print("\n[FORMATTED] callback_context:")
    print(json.dumps(_format_callback_context(callback_context), indent=2, default=str))
    print("\n[FORMATTED] llm_request (BEFORE redaction):")
    print(json.dumps(_format_llm_request(llm_request), indent=2, default=str))

    session_id = callback_context.session.id if callback_context.session else "default"
    conn = sqlite3.connect(DB_PATH)

    try:
        contents = getattr(llm_request, "contents", None) or []
        for i, c in enumerate(contents):
            parts = getattr(c, "parts", []) or []
            for j, p in enumerate(parts):
                if hasattr(p, "text") and p.text:
                    original = p.text
                    redacted = _detect_and_replace_sensitive(original, session_id, conn)
                    if redacted != original:
                        print(f"\n[PROTECTION] Redacted sensitive data")
                        print(f"  Session: {session_id}")
                        print(f"  Original: ...{original[:60]}...")
                        print(f"  Redacted: ...{redacted[:80]}...")
                    p.text = redacted
        conn.commit()

        # Raw and formatted AFTER redaction (what goes to LLM)
        print("\n[FORMATTED] llm_request (AFTER redaction - sent to LLM):")
        print(json.dumps(_format_llm_request(llm_request), indent=2, default=str))
    finally:
        conn.close()

    print(f"{sep}\n")
    return None


def after_model_callback(
    callback_context: CallbackContext, llm_response: LlmResponse
) -> Optional[LlmResponse]:
    """
    After LLM: replace hashed tokens in the response with original values.
    User sees real values; LLM only ever saw tokens.
    """
    sep = "=" * 80
    print(f"\n{sep}")
    print("CALLBACK: after_model_callback (SENSITIVE DATA RESTORATION)")
    print(f"{sep}")

    # Raw and formatted BEFORE restoration (what LLM returned)
    print("\n[RAW] callback_context:", _safe_repr(callback_context, 600))
    print("\n[RAW] llm_response (BEFORE restoration):", _safe_repr(llm_response, 1200))
    print("\n[FORMATTED] callback_context:")
    print(json.dumps(_format_callback_context(callback_context), indent=2, default=str))
    print("\n[FORMATTED] llm_response (BEFORE restoration - from LLM):")
    print(json.dumps(_format_llm_response(llm_response), indent=2, default=str))

    session_id = callback_context.session.id if callback_context.session else "default"
    conn = sqlite3.connect(DB_PATH)

    try:
        content = getattr(llm_response, "content", None)
        if content and hasattr(content, "parts"):
            for p in content.parts or []:
                if hasattr(p, "text") and p.text:
                    original = p.text
                    restored = _restore_sensitive(original, session_id, conn)
                    if restored != original:
                        print(f"\n[PROTECTION] Restored original values")
                        print(f"  Session: {session_id}")
                        print(f"  Before: ...{original[:80]}...")
                        print(f"  After:  ...{restored[:80]}...")
                    p.text = restored

        # Raw and formatted AFTER restoration (what user sees)
        print("\n[FORMATTED] llm_response (AFTER restoration - to user):")
        print(json.dumps(_format_llm_response(llm_response), indent=2, default=str))
    finally:
        conn.close()

    print(f"{sep}\n")
    return None


# ---------------------------------------------------------------------------
# Agent
# ---------------------------------------------------------------------------

root_agent = Agent(
    name="sensitive_data_agent",
    model=GEMINI_MODEL,
    description="Agent that handles NPI and PCI data safely - values are protected before LLM calls.",
    instruction=(
        "You are a helpful assistant. When users mention NPI numbers or credit card numbers, "
        "you may see tokenized placeholders instead. Still help them - for example, "
        "if they ask to verify an NPI or card, acknowledge you received it and can help. "
        "Be concise and friendly."
    ),
    tools=[get_current_time_tool],
    before_model_callback=before_model_callback,
    after_model_callback=after_model_callback,
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
    init_db()

    timestamp = datetime.now().strftime("%Y%m%d_%H%M%S")
    output_file = SCRIPT_DIR / f"callback_sensitive_data_output_{timestamp}.txt"

    log_file_handle = open(output_file, "w", encoding="utf-8")
    original_stdout = sys.stdout
    original_stderr = sys.stderr
    tee = TeeOutput(log_file_handle, sys.stdout)
    sys.stdout = tee
    sys.stderr = tee

    try:
        print("=" * 80)
        print("ADK Sensitive Data Protection Demo")
        print("=" * 80)
        print(f"Output file: {output_file}")
        print(f"SQLite DB: {DB_PATH}")
        print(f"Model: {GEMINI_MODEL}")
        print("=" * 80)
        print("\nSensitive patterns:")
        print("  - NPI: 10-digit number (e.g. 1234567890)")
        print("  - PCI: Credit card (e.g. 4111 1111 1111 1111)")
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
        session_id = f"sensitive_test_{timestamp}"

        session = await session_service.create_session(
            app_name=APP_NAME,
            user_id=user_id,
            session_id=session_id,
        )
        print(f"\nSession: {session.id}\n")

        # Demo message with NPI and PCI
        user_message = types.Content(
            parts=[
                types.Part(
                    text=(
                        "My NPI is 1234567890 and my card is 4111 1111 1111 1111. "
                        "Can you confirm you have these on file and tell me the current time?"
                    )
                )
            ],
            role="user",
        )
        print(f"User message (contains NPI + PCI): {user_message.parts[0].text}\n")
        print("Running agent (sensitive data is hashed before LLM, restored after)...\n")

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
        print("Demo complete. Sensitive columns were protected before LLM calls.")
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
