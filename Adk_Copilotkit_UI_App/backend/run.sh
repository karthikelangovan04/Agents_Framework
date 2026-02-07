#!/usr/bin/env bash
# Run backend on port from .env (default 8001). Use this so you don't conflict with reference on 8000.
cd "$(dirname "$0")"
. .venv/bin/activate
python main.py
