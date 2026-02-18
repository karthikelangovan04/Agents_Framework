"""
FastAPI application for ADK Agent on Cloud Run

This creates a FastAPI server that exposes the ADK agent as an HTTP service.
"""

import logging
import os
from contextlib import asynccontextmanager

from dotenv import load_dotenv
from fastapi import FastAPI, HTTPException
from fastapi.responses import JSONResponse
from google.adk.runners import Runner
from google.adk.sessions import InMemorySessionService
from google.genai import types

from agent import root_agent

# Load environment variables
load_dotenv()

logger = logging.getLogger(__name__)
logging.basicConfig(
    format="[%(levelname)s]: %(message)s",
    level=logging.INFO
)

# Initialize session service
session_service = InMemorySessionService()

# Create runner (requires app_name when using agent parameter)
runner = Runner(
    app_name="currency_agent_app",
    agent=root_agent,
    session_service=session_service
)


@asynccontextmanager
async def lifespan(app: FastAPI):
    """Lifespan context manager for startup/shutdown."""
    logger.info("🚀 ADK Agent service starting up...")
    yield
    logger.info("🛑 ADK Agent service shutting down...")


# Create FastAPI app
app = FastAPI(
    title="Currency Agent API",
    description="ADK Agent with remote MCP server connection",
    version="1.0.0",
    lifespan=lifespan,
)


@app.get("/")
async def root():
    """Health check endpoint."""
    return {
        "status": "healthy",
        "service": "currency_agent",
        "version": "1.0.0"
    }


@app.post("/chat")
async def chat(message: dict):
    """
    Chat endpoint for interacting with the agent.
    
    Expected payload:
    {
        "message": "What is 100 USD in EUR?",
        "session_id": "optional-session-id",
        "user_id": "optional-user-id"
    }
    """
    try:
        user_message = message.get("message", "")
        session_id = message.get("session_id", "default_session")
        
        if not user_message:
            raise HTTPException(
                status_code=400,
                detail="Message is required"
            )
        
        logger.info(f"📨 Received message: {user_message}")
        
        # Create Content object for the message
        user_content = types.Content(
            role='user',
            parts=[types.Part(text=user_message)]
        )
        
        # Get or create session
        user_id = message.get("user_id", "default_user")
        app_name = "currency_agent_app"
        
        # Check if session exists, create if not
        existing_session = await session_service.get_session(
            app_name=app_name,
            user_id=user_id,
            session_id=session_id
        )
        
        if not existing_session:
            logger.info(f"📝 Creating new session: {session_id} for user: {user_id}")
            await session_service.create_session(
                app_name=app_name,
                user_id=user_id,
                session_id=session_id
            )
        
        # Run the agent
        response_parts = []
        async for event in runner.run_async(
            user_id=user_id,
            session_id=session_id,
            new_message=user_content
        ):
            if hasattr(event, 'content') and event.content:
                if hasattr(event.content, 'parts'):
                    for part in event.content.parts:
                        if hasattr(part, 'text') and part.text:
                            response_parts.append(part.text)
                elif isinstance(event.content, str):
                    response_parts.append(event.content)
        
        response_text = "".join(response_parts)
        logger.info(f"✅ Agent response: {response_text[:100]}...")
        
        return {
            "response": response_text,
            "session_id": session_id
        }
        
    except Exception as e:
        logger.error(f"❌ Error processing request: {e}", exc_info=True)
        raise HTTPException(
            status_code=500,
            detail=f"Internal server error: {str(e)}"
        )


@app.get("/health")
async def health():
    """Health check endpoint."""
    import sys
    return {
        "status": "healthy",
        "python_version": sys.version,
        "mcp_server_url": os.getenv("MCP_SERVER_URL", "not set")
    }


if __name__ == "__main__":
    import uvicorn
    port = int(os.getenv("PORT", 8080))
    uvicorn.run(
        app,
        host="0.0.0.0",
        port=port
    )
