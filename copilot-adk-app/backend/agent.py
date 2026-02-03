"""
ADK LlmAgent and DatabaseSessionService (Postgres).
Shared agent and session service; user_id and session_id are provided per request by the client (AG-UI protocol).
"""
import os
from google.adk.agents import LlmAgent
from google.adk.memory import InMemoryMemoryService
from google.adk.sessions import DatabaseSessionService

from config import APP_NAME, DATABASE_URL, GEMINI_MODEL, SESSION_TIMEOUT_SECONDS

# Postgres session storage (same DB can be used for app users table)
session_service = DatabaseSessionService(db_url=DATABASE_URL)
memory_service = InMemoryMemoryService()

# Single shared agent; ADK Runner uses session_service so context is per (user_id, session_id)
agent = LlmAgent(
    name="assistant",
    model=GEMINI_MODEL,
    instruction=(
        "You are a helpful, friendly assistant. "
        "Remember context from earlier in the conversation. "
        "Be concise but thorough when asked questions."
    ),
)
