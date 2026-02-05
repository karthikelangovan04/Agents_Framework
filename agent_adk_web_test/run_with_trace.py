#!/usr/bin/env python3
"""
Runnable script for the adk_web_testing agent that captures and prints
telemetry traces (invocation, invoke_agent, call_llm, execute_tool, etc.).

Uses the venv at:  ../adk/.venv  (or ADK_VENV env var).

Run from this directory (agent_adk_web_test):
  ../adk/.venv/bin/python run_with_trace.py
  # or with a question:
  ../adk/.venv/bin/python run_with_trace.py "What time is it in Paris?"

Or set ADK_VENV and run from repo root:
  ADK_VENV=adk/.venv adk/.venv/bin/python agent_adk_web_test/run_with_trace.py "What time is it in Tokyo?"

Requires GOOGLE_API_KEY (or Vertex) for real model calls. Loads env from
agent_adk_web_test/adk_web_testing/.env if present. Telemetry trace is printed
even if the run fails (e.g. missing API key), so you can confirm spans are captured.
"""

from __future__ import annotations

import asyncio
import os
import sys
from typing import Any

# Path to .env (agent_adk_web_test/adk_web_testing/.env)
_SCRIPT_DIR = os.path.dirname(os.path.abspath(__file__))
_ENV_PATH = os.path.join(_SCRIPT_DIR, "adk_web_testing", ".env")


def _load_env() -> None:
    """Load .env from adk_web_testing/.env into os.environ."""
    if not os.path.isfile(_ENV_PATH):
        return
    try:
        from dotenv import load_dotenv
        load_dotenv(_ENV_PATH)
        return
    except ImportError:
        pass
    # Fallback: simple KEY=value parser (strip optional surrounding quotes)
    with open(_ENV_PATH, encoding="utf-8") as f:
        for line in f:
            line = line.strip()
            if not line or line.startswith("#"):
                continue
            if "=" in line:
                key, _, value = line.partition("=")
                key = key.strip()
                value = value.strip().strip("'\"").strip()
                if key:
                    os.environ.setdefault(key, value)

# --- 1. OpenTelemetry: configure BEFORE importing google.adk so ADK uses our tracer ---
_tracer_provider: Any = None


def _setup_telemetry_capture():
    global _tracer_provider
    try:
        from opentelemetry import trace
        from opentelemetry.sdk.trace import TracerProvider
        from opentelemetry.sdk.trace.export import SpanExporter, SpanExportResult, SimpleSpanProcessor
    except ImportError as e:
        print("OpenTelemetry not in venv. Install: pip install opentelemetry-api opentelemetry-sdk", file=sys.stderr)
        raise SystemExit(1) from e

    captured_spans: list[dict[str, Any]] = []

    class InMemoryCaptureExporter(SpanExporter):
        def export(self, spans: Any) -> SpanExportResult:
            for span in spans:
                name = getattr(span, "name", None)
                if name is None:
                    continue
                start = getattr(span, "start_time", None)
                end = getattr(span, "end_time", None)
                duration_ms = None
                if end is not None and start is not None:
                    duration_ms = (end - start) / 1e9 * 1000  # nanoseconds -> ms
                attrs = getattr(span, "attributes", None)
                captured_spans.append({
                    "name": name,
                    "duration_ms": duration_ms,
                    "start_time": start,
                    "end_time": end,
                    "attributes": dict(attrs) if attrs is not None else {},
                    "parent_span_id": getattr(span, "parent", None) or getattr(span, "parent_span_id", None),
                })
            return SpanExportResult.SUCCESS

        def shutdown(self) -> None:
            pass

        def force_flush(self, timeout_millis: int = 30000) -> bool:
            return True

    exporter = InMemoryCaptureExporter()
    _tracer_provider = TracerProvider()
    _tracer_provider.add_span_processor(SimpleSpanProcessor(exporter))
    trace.set_tracer_provider(_tracer_provider)
    return captured_spans


def _print_trace(spans: list[dict[str, Any]]) -> None:
    if not spans:
        print("\n[Trace] No spans captured (OTel may not be instrumenting this run).")
        return
    # Sort by start_time so root/outer spans appear first (invocation → invoke_agent → call_llm → execute_tool)
    start = lambda s: s.get("start_time") or 0
    sorted_spans = sorted(spans, key=start)
    print("\n" + "=" * 60 + "\n[Telemetry trace]\n" + "=" * 60)
    for s in sorted_spans:
        name = s.get("name", "?")
        dur = s.get("duration_ms")
        dur_str = f" {dur:.2f}ms" if dur is not None else ""
        print(f"  {name}{dur_str}")
    print("=" * 60)


async def main() -> None:
    # Load .env first (adk_web_testing/.env) so GOOGLE_API_KEY etc. are set
    _load_env()

    # Ensure we're in the right directory for imports
    script_dir = _SCRIPT_DIR
    if script_dir not in sys.path:
        sys.path.insert(0, script_dir)

    # Capture list will be populated by the exporter
    captured_spans = _setup_telemetry_capture()

    # Now import ADK and our agent (they will use the global tracer we just set)
    from google.adk.runners import InMemoryRunner
    from google.genai import types

    from adk_web_testing.agent import root_agent

    user_id = "run_with_trace_user"
    session_id = "trace_session_1"

    runner = InMemoryRunner(agent=root_agent)
    app_name = getattr(runner, "app_name", None) or "adk_web_testing"
    await runner.session_service.create_session(
        app_name=app_name,
        user_id=user_id,
        session_id=session_id,
    )

    question = "What time is it in London?"
    if len(sys.argv) > 1:
        question = " ".join(sys.argv[1:])

    print(f"You: {question}\nAgent: ", end="", flush=True)

    try:
        async for event in runner.run_async(
            user_id=user_id,
            session_id=session_id,
            new_message=types.Content(role="user", parts=[types.Part(text=question)]),
        ):
            if getattr(event, "content", None) and getattr(event.content, "parts", None):
                for part in event.content.parts:
                    if getattr(part, "text", None):
                        print(part.text, end="", flush=True)
        print()
    except Exception as e:
        print(f"\n[Run error: {e}]")
    finally:
        # Flush and show trace even if the run failed (e.g. missing API key)
        try:
            if _tracer_provider is not None and hasattr(_tracer_provider, "force_flush"):
                _tracer_provider.force_flush()
        except Exception:
            pass
        _print_trace(captured_spans)


if __name__ == "__main__":
    asyncio.run(main())
