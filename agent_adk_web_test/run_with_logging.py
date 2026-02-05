#!/usr/bin/env python3
"""
Run the adk_web_testing agent with:
  - A log file (timestamped) for run output and telemetry trace
  - A separate raw-response file with each ADK event as sent (JSON)

Uses the same venv and .env as run_with_trace.py. Does not modify run_with_trace.py.

Run from agent_adk_web_test:
  ../adk/.venv/bin/python run_with_logging.py "What time is it in Paris?"
  ./run_with_logging.sh "What time is it in Tokyo?"
"""

from __future__ import annotations

import asyncio
import json
import logging
import os
import sys
from datetime import datetime
from typing import Any

# Path to .env (agent_adk_web_test/adk_web_testing/.env)
_SCRIPT_DIR = os.path.dirname(os.path.abspath(__file__))
_ENV_PATH = os.path.join(_SCRIPT_DIR, "adk_web_testing", ".env")
_LOGS_DIR = os.path.join(_SCRIPT_DIR, "logs")

_tracer_provider: Any = None


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


def _setup_telemetry_capture():
    global _tracer_provider
    try:
        from opentelemetry import trace
        from opentelemetry.sdk.trace import TracerProvider
        from opentelemetry.sdk.trace.export import SpanExporter, SpanExportResult, SimpleSpanProcessor
    except ImportError as e:
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
                duration_ms = (end - start) / 1e9 * 1000 if (end is not None and start is not None) else None
                attrs = getattr(span, "attributes", None)
                captured_spans.append({
                    "name": name,
                    "duration_ms": duration_ms,
                    "start_time": start,
                    "end_time": end,
                    "attributes": dict(attrs) if attrs is not None else {},
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


def _event_to_dict(event: Any) -> dict[str, Any]:
    """Serialize an ADK Event to a JSON-serializable dict."""
    try:
        if hasattr(event, "model_dump"):
            try:
                return event.model_dump(mode="json")
            except TypeError:
                return event.model_dump()
        if hasattr(event, "dict"):
            return event.dict()
    except Exception:
        pass
    out: dict[str, Any] = {}
    for attr in ("id", "invocation_id", "author", "content", "actions", "branch", "timestamp", "usage_metadata"):
        if hasattr(event, attr):
            v = getattr(event, attr)
            if v is None:
                out[attr] = None
            elif hasattr(v, "model_dump"):
                try:
                    out[attr] = v.model_dump(mode="json")
                except Exception:
                    try:
                        out[attr] = v.model_dump()
                    except Exception:
                        out[attr] = str(v)
            elif hasattr(v, "dict"):
                try:
                    out[attr] = v.dict()
                except Exception:
                    out[attr] = str(v)
            else:
                out[attr] = v
    return out


def _json_default(obj: Any) -> Any:
    if hasattr(obj, "isoformat"):
        return obj.isoformat()
    raise TypeError(f"Object of type {type(obj).__name__} is not JSON serializable")


async def main() -> None:
    _load_env()

    script_dir = _SCRIPT_DIR
    if script_dir not in sys.path:
        sys.path.insert(0, script_dir)

    # Timestamp for this run
    ts = datetime.now().strftime("%Y%m%d_%H%M%S")
    os.makedirs(_LOGS_DIR, exist_ok=True)
    log_path = os.path.join(_LOGS_DIR, f"run_{ts}.log")
    raw_path = os.path.join(_LOGS_DIR, f"raw_{ts}.jsonl")

    # Log file: both file and console
    file_handler = logging.FileHandler(log_path, encoding="utf-8")
    file_handler.setLevel(logging.DEBUG)
    file_handler.setFormatter(logging.Formatter("%(asctime)s [%(levelname)s] %(message)s"))
    console_handler = logging.StreamHandler(sys.stdout)
    console_handler.setLevel(logging.INFO)
    console_handler.setFormatter(logging.Formatter("%(message)s"))
    root = logging.getLogger()
    root.setLevel(logging.DEBUG)
    root.handlers.clear()
    root.addHandler(file_handler)
    root.addHandler(console_handler)
    log = logging.getLogger(__name__)

    log.info("Log file: %s", log_path)
    log.info("Raw response file: %s", raw_path)

    captured_spans = _setup_telemetry_capture()

    from google.adk.runners import InMemoryRunner
    from google.genai import types

    from adk_web_testing.agent import root_agent

    user_id = "run_with_logging_user"
    session_id = "logging_session_1"

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

    log.info("You: %s", question)
    print(f"You: {question}\nAgent: ", end="", flush=True)

    agent_text: list[str] = []
    raw_file = open(raw_path, "w", encoding="utf-8")
    try:
        async for event in runner.run_async(
            user_id=user_id,
            session_id=session_id,
            new_message=types.Content(role="user", parts=[types.Part(text=question)]),
        ):
            # Write raw event to JSONL file (one JSON object per line)
            try:
                d = _event_to_dict(event)
                raw_file.write(json.dumps(d, default=_json_default) + "\n")
                raw_file.flush()
            except Exception as e:
                log.debug("Raw serialize event: %s", e)
            # Console output and collect agent text for log file
            if getattr(event, "content", None) and getattr(event.content, "parts", None):
                for part in event.content.parts:
                    if getattr(part, "text", None):
                        t = part.text
                        print(t, end="", flush=True)
                        agent_text.append(t)
        print()
        if agent_text:
            log.info("Agent: %s", "".join(agent_text))
    except Exception as e:
        log.exception("Run error: %s", e)
        print(f"\n[Run error: {e}]")
    finally:
        raw_file.close()
        try:
            if _tracer_provider is not None and hasattr(_tracer_provider, "force_flush"):
                _tracer_provider.force_flush()
        except Exception:
            pass

        # Trace to log and console
        if not captured_spans:
            log.info("[Trace] No spans captured.")
            print("\n[Trace] No spans captured.")
        else:
            sorted_spans = sorted(captured_spans, key=lambda s: s.get("start_time") or 0)
            log.info("=== Telemetry trace ===")
            print("\n" + "=" * 60 + "\n[Telemetry trace]\n" + "=" * 60)
            for s in sorted_spans:
                name = s.get("name", "?")
                dur = s.get("duration_ms")
                dur_str = f" {dur:.2f}ms" if dur is not None else ""
                line = f"  {name}{dur_str}"
                log.info(line)
                print(line)
            log.info("======================")
            print("=" * 60)
        log.info("Done. Log: %s  Raw: %s", log_path, raw_path)


if __name__ == "__main__":
    asyncio.run(main())
