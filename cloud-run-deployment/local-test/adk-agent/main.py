"""
FastAPI app for ADK Agent - Local Test (No auth)
"""

import logging
import os
from contextlib import asynccontextmanager

from dotenv import load_dotenv
from fastapi import FastAPI, HTTPException
from google.adk.runners import Runner
from google.adk.sessions import InMemorySessionService
from google.genai import types

from agent import root_agent

load_dotenv()

logger = logging.getLogger(__name__)
logging.basicConfig(format="[%(levelname)s]: %(message)s", level=logging.INFO)

session_service = InMemorySessionService()
runner = Runner(
    app_name="currency_agent_app",
    agent=root_agent,
    session_service=session_service,
)


@asynccontextmanager
async def lifespan(app: FastAPI):
    logger.info("🚀 ADK Agent (local) starting...")
    yield
    logger.info("🛑 ADK Agent shutting down...")


app = FastAPI(title="Currency Agent (Local)", version="1.0.0", lifespan=lifespan)


@app.get("/")
async def root():
    return {"status": "healthy", "service": "currency_agent"}


@app.post("/chat")
async def chat(message: dict):
    user_message = message.get("message", "")
    session_id = message.get("session_id", "default_session")
    user_id = message.get("user_id", "default_user")

    if not user_message:
        raise HTTPException(status_code=400, detail="Message required")

    app_name = "currency_agent_app"
    existing = await session_service.get_session(app_name=app_name, user_id=user_id, session_id=session_id)
    if not existing:
        await session_service.create_session(app_name=app_name, user_id=user_id, session_id=session_id)

    user_content = types.Content(role='user', parts=[types.Part(text=user_message)])
    response_parts = []

    async for event in runner.run_async(
        user_id=user_id, session_id=session_id, new_message=user_content
    ):
        if hasattr(event, 'content') and event.content and hasattr(event.content, 'parts'):
            for part in event.content.parts:
                if hasattr(part, 'text') and part.text:
                    response_parts.append(part.text)

    return {"response": "".join(response_parts), "session_id": session_id}


if __name__ == "__main__":
    import uvicorn
    port = int(os.getenv("PORT", 8081))
    uvicorn.run(app, host="0.0.0.0", port=port)
