#!/bin/bash
# Run the adk_web_testing agent with telemetry trace capture.
# Uses the venv at ../adk/.venv (or ADK_VENV if set).

set -e
SCRIPT_DIR="$(cd "$(dirname "${BASH_SOURCE[0]}")" && pwd)"
REPO_ROOT="$(cd "$SCRIPT_DIR/.." && pwd)"
ADK_VENV="${ADK_VENV:-$REPO_ROOT/adk/.venv}"
PYTHON="${ADK_VENV}/bin/python"

if [[ ! -x "$PYTHON" ]]; then
  echo "Venv not found or no python: $PYTHON" >&2
  echo "Create it with: cd $REPO_ROOT/adk && python3 -m venv .venv && .venv/bin/pip install google-adk opentelemetry-api opentelemetry-sdk" >&2
  exit 1
fi

cd "$SCRIPT_DIR"
exec "$PYTHON" run_with_trace.py "$@"
