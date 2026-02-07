"""
FastAPI app: two AG-UI endpoints (deal_builder, knowledge_qa) with Postgres session storage.
Wiring aligned with reference copilot-adk-app: X-User-Id / X-Session-Id -> state (_ag_ui_*),
user_id_extractor, DatabaseSessionService. Auth skipped; no session create API.
Run from backend/: uvicorn main:app --host 0.0.0.0 --port 8000
"""
from typing import Any

from fastapi import FastAPI, Request
from fastapi.middleware.cors import CORSMiddleware

from config import APP_NAME, CORS_ORIGINS, PORT, SESSION_TIMEOUT_SECONDS
from session_service import session_service
from agents.deal_builder import deal_builder_agent
from agents.knowledge_qa import knowledge_qa_agent

try:
    from ag_ui_adk import ADKAgent, add_adk_fastapi_endpoint
    from ag_ui.core import RunAgentInput
    HAS_AG_UI = True
except ImportError as e:
    HAS_AG_UI = False
    RunAgentInput = None  # type: ignore
    print(f"⚠️ ag_ui_adk not loaded: {e}. POST /ag-ui/* will not work.")

app = FastAPI(title="ADK CopilotKit Backend", version="0.1.0")
app.add_middleware(
    CORSMiddleware,
    allow_origins=CORS_ORIGINS,
    allow_credentials=True,
    allow_methods=["*"],
    allow_headers=["*"],
)


async def extract_user_and_session(request: Request, input_data: RunAgentInput) -> dict[str, Any]:
    """Extract X-User-Id and X-Session-Id from headers into state (same as reference).
    AG-UI/ADK uses these to resolve user_id and load session from DatabaseSessionService.
    """
    state = {}
    user_id = request.headers.get("X-User-Id")
    session_id = request.headers.get("X-Session-Id")
    if user_id:
        state["_ag_ui_user_id"] = user_id
    if session_id:
        state["_ag_ui_session_id"] = session_id
        state["_ag_ui_thread_id"] = session_id  # thread_id = session_id per reference
    state["_ag_ui_app_name"] = APP_NAME
    return state


def extract_user_from_state(input: RunAgentInput) -> str:
    """Resolve user ID from state (called by ADKAgent._get_user_id()). Same as reference."""
    if isinstance(getattr(input, "state", None), dict):
        uid = input.state.get("_ag_ui_user_id")
        if uid:
            return str(uid)
    return f"thread_user_{getattr(input, 'thread_id', 'default')}"


@app.on_event("shutdown")
async def shutdown():
    """Close session service connection pool (reference does this)."""
    try:
        if hasattr(session_service, "close"):
            await session_service.close()
    except Exception:
        pass


@app.middleware("http")
async def log_ag_ui_headers(request: Request, call_next):
    """Log AG-UI requests for debugging (reference pattern)."""
    if request.url.path.startswith("/ag-ui/"):
        user_id = request.headers.get("X-User-Id", "NOT_SET")
        session_id = request.headers.get("X-Session-Id", "NOT_SET")
        seg = session_id[:8] if session_id != "NOT_SET" and len(session_id) >= 8 else session_id
        print(f"🔍 Backend {request.url.path}: X-User-Id={user_id}, X-Session-Id={seg}...")
    return await call_next(request)


if HAS_AG_UI:
    try:
        adk_deal_builder = ADKAgent(
            adk_agent=deal_builder_agent,
            app_name=APP_NAME,
            user_id_extractor=extract_user_from_state,
            session_timeout_seconds=SESSION_TIMEOUT_SECONDS,
            use_in_memory_services=False,
            session_service=session_service,
        )
        adk_knowledge_qa = ADKAgent(
            adk_agent=knowledge_qa_agent,
            app_name=APP_NAME,
            user_id_extractor=extract_user_from_state,
            session_timeout_seconds=SESSION_TIMEOUT_SECONDS,
            use_in_memory_services=False,
            session_service=session_service,
        )
        print("✅ ADKAgent(s) initialized with Postgres session service + user_id_extractor")
    except TypeError as e:
        print(f"⚠️ ADKAgent fallback to in-memory services: {e}")
        adk_deal_builder = ADKAgent(
            adk_agent=deal_builder_agent,
            app_name=APP_NAME,
            user_id_extractor=extract_user_from_state,
            session_timeout_seconds=SESSION_TIMEOUT_SECONDS,
            use_in_memory_services=True,
        )
        adk_knowledge_qa = ADKAgent(
            adk_agent=knowledge_qa_agent,
            app_name=APP_NAME,
            user_id_extractor=extract_user_from_state,
            session_timeout_seconds=SESSION_TIMEOUT_SECONDS,
            use_in_memory_services=True,
        )
    add_adk_fastapi_endpoint(
        app,
        adk_deal_builder,
        path="/ag-ui/deal_builder",
        extract_state_from_request=extract_user_and_session,
    )
    add_adk_fastapi_endpoint(
        app,
        adk_knowledge_qa,
        path="/ag-ui/knowledge_qa",
        extract_state_from_request=extract_user_and_session,
    )
else:
    # Placeholder when ag-ui-adk is not installed. Use exact paths so we return 501, not 405.
    @app.api_route("/ag-ui", methods=["GET", "POST"])
    @app.api_route("/ag-ui/deal_builder", methods=["GET", "POST"])
    @app.api_route("/ag-ui/knowledge_qa", methods=["GET", "POST"])
    async def ag_ui_placeholder():
        from fastapi import HTTPException
        raise HTTPException(status_code=501, detail="Install ag-ui-adk: pip install ag-ui-adk")


@app.get("/health")
async def health():
    return {"status": "ok"}


@app.get("/routes")
async def list_routes():
    """Debug: list registered routes and methods (remove in production)."""
    return [
        {"path": r.path, "methods": list(r.methods)}
        for r in app.routes
        if hasattr(r, "path") and hasattr(r, "methods")
    ]


if __name__ == "__main__":
    import sys
    import uvicorn
    from config import HOST, PORT
    from port_check import is_port_in_use
    if is_port_in_use(PORT):
        print(f"❌ Port {PORT} is already in use (e.g. by reference copilot-adk-app on 8000).")
        print(f"   Set PORT in .env to a free port, e.g. PORT=8001")
        sys.exit(1)
    uvicorn.run(app, host=HOST, port=PORT)
