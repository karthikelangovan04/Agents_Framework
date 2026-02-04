"""
FastAPI app: auth, session APIs, and AG-UI endpoint for CopilotKit.
Parameterized for dev and Cloud Run via config.
"""
import uuid
from typing import List, Optional, Any

from fastapi import FastAPI, Depends, HTTPException, Request, Header
from typing import Any
from ag_ui.core import RunAgentInput
from fastapi.middleware.cors import CORSMiddleware
from pydantic import BaseModel

from config import APP_NAME, CORS_ORIGINS, SESSION_TIMEOUT_SECONDS
from agent import agent, session_service
from auth import hash_password, verify_password, create_access_token, decode_access_token
from db import init_db, close_db, get_pool, get_user_by_username, create_user

# Optional: ag-ui-adk for CopilotKit; fallback if not installed
try:
    from ag_ui_adk import ADKAgent, add_adk_fastapi_endpoint
    from ag_ui.core import RunAgentInput
    HAS_AG_UI = True
except ImportError:
    HAS_AG_UI = False
    RunAgentInput = None  # type: ignore

app = FastAPI(title="Copilot ADK API", version="0.1.0")
app.add_middleware(
    CORSMiddleware,
    allow_origins=CORS_ORIGINS,
    allow_credentials=True,
    allow_methods=["*"],
    allow_headers=["*"],
)


# --- Pydantic models ---
class RegisterRequest(BaseModel):
    username: str
    password: str


class LoginRequest(BaseModel):
    username: str
    password: str


class TokenResponse(BaseModel):
    access_token: str
    token_type: str = "bearer"
    user_id: str
    username: str


class SessionItem(BaseModel):
    id: str
    create_time: Optional[str] = None
    update_time: Optional[str] = None


class SessionListResponse(BaseModel):
    sessions: List[SessionItem]


# --- Auth dependency ---
async def get_current_user_id(
    authorization: Optional[str] = Header(None),
    x_user_id: Optional[str] = Header(None),
) -> str:
    """Resolve user id from JWT (Authorization: Bearer <token>) or X-User-Id header (for agent)."""
    if x_user_id:
        return x_user_id
    if not authorization or not authorization.startswith("Bearer "):
        raise HTTPException(status_code=401, detail="Not authenticated")
    token = authorization.split(" ", 1)[1]
    user_id = decode_access_token(token)
    if not user_id:
        raise HTTPException(status_code=401, detail="Invalid or expired token")
    return user_id


# --- Startup: init DB ---
@app.on_event("startup")
async def startup():
    await init_db()


@app.on_event("shutdown")
async def shutdown():
    await close_db()
    try:
        await session_service.close()
    except Exception:
        pass


# --- Auth routes ---
@app.post("/auth/register", response_model=TokenResponse)
async def register(body: RegisterRequest):
    username = (body.username or "").strip().lower()
    if not username or len(body.password) < 6:
        raise HTTPException(status_code=400, detail="Username required and password at least 6 characters")
    existing = await get_user_by_username(username)
    if existing:
        raise HTTPException(status_code=400, detail="Username already taken")
    user = await create_user(username, hash_password(body.password))
    user_id = str(user["id"])
    token = create_access_token(user_id)
    return TokenResponse(access_token=token, user_id=user_id, username=user["username"])


@app.post("/auth/login", response_model=TokenResponse)
async def login(body: LoginRequest):
    username = (body.username or "").strip().lower()
    if not username:
        raise HTTPException(status_code=400, detail="Username required")
    user = await get_user_by_username(username)
    if not user or not verify_password(body.password, user["password_hash"]):
        raise HTTPException(status_code=401, detail="Invalid username or password")
    user_id = str(user["id"])
    token = create_access_token(user_id)
    return TokenResponse(access_token=token, user_id=user_id, username=user["username"])


# --- Session API (list/create for ChatGPT-like UI) ---
@app.get("/api/sessions", response_model=SessionListResponse)
async def list_sessions(user_id: str = Depends(get_current_user_id)):
    """List ADK sessions for the current user."""
    try:
        list_fn = getattr(session_service, "list_sessions", None)
        if not list_fn:
            return SessionListResponse(sessions=[])
        resp = await list_fn(app_name=APP_NAME, user_id=user_id)
        sessions = [
            SessionItem(
                id=s.id,
                create_time=str(s.create_time) if getattr(s, "create_time", None) else None,
                update_time=str(s.update_time) if getattr(s, "update_time", None) else None,
            )
            for s in (getattr(resp, "sessions", None) or [])
        ]
        return SessionListResponse(sessions=sessions)
    except Exception as e:
        raise HTTPException(status_code=500, detail=str(e))


@app.post("/api/sessions", response_model=SessionItem)
async def create_session(user_id: str = Depends(get_current_user_id)):
    """Create a new chat session (new conversation) with proper AG-UI state."""
    session_id = str(uuid.uuid4())
    try:
        # Create session with initial AG-UI state
        # This ensures ADK SessionManager can find it when user sends first message
        initial_state = {
            "_ag_ui_user_id": user_id,
            "_ag_ui_app_name": APP_NAME,
            "_ag_ui_thread_id": session_id,  # thread_id = session_id
            "_ag_ui_session_id": session_id,
        }
        
        session = await session_service.create_session(
            app_name=APP_NAME,
            user_id=user_id,
            session_id=session_id,
            state=initial_state,  # Initialize with AG-UI metadata
        )
        
        print(f"✅ Created session {session_id[:8]}... with initial state for user {user_id}")
        
        return SessionItem(
            id=session.id,
            create_time=str(session.create_time) if getattr(session, "create_time", None) else None,
            update_time=str(session.update_time) if getattr(session, "update_time", None) else None,
        )
    except Exception as e:
        print(f"❌ Failed to create session: {e}")
        raise HTTPException(status_code=500, detail=str(e))


# --- AG-UI Header Extraction Functions ---

async def extract_user_and_session(request: Request, input_data: RunAgentInput) -> dict[str, Any]:
    """Extract X-User-Id and X-Session-Id from headers into state.
    
    This allows ADKAgent to access user_id via user_id_extractor.
    """
    state = {}
    user_id = request.headers.get("X-User-Id")
    session_id = request.headers.get("X-Session-Id")
    
    print(f"🔍 Extracting headers: X-User-Id={user_id}, X-Session-Id={session_id[:8] if session_id else 'None'}...")
    
    if user_id:
        state["_ag_ui_user_id"] = user_id
        print(f"✅ Set state._ag_ui_user_id = {user_id}")
    if session_id:
        state["_ag_ui_session_id"] = session_id
        print(f"✅ Set state._ag_ui_session_id = {session_id[:8]}...")
    
    return state


def extract_user_from_state(input: RunAgentInput) -> str:
    """Extract user ID from state (set by extract_user_and_session).
    
    This is called by ADKAgent._get_user_id() to resolve the user ID.
    """
    if isinstance(input.state, dict):
        user_id = input.state.get("_ag_ui_user_id")
        if user_id:
            print(f"✅ user_id_extractor: Found user_id={user_id} in state")
            return str(user_id)
    
    # Fallback to thread_user
    fallback = f"thread_user_{input.thread_id}"
    print(f"⚠️ user_id_extractor: No user_id in state, falling back to {fallback}")
    return fallback


# Add middleware to log headers
@app.middleware("http")
async def log_ag_ui_headers(request, call_next):
    if request.url.path == "/ag-ui":
        user_id = request.headers.get("X-User-Id", "NOT_SET")
        session_id = request.headers.get("X-Session-Id", "NOT_SET")
        print(f"🔍 Backend /ag-ui: X-User-Id={user_id}, X-Session-Id={session_id[:8] if session_id != 'NOT_SET' else 'NOT_SET'}...")
    response = await call_next(request)
    return response

# --- AG-UI endpoint for CopilotKit ---
if HAS_AG_UI:
    # ADKAgent with Postgres session service
    # Note: user_id/session_id are handled per-request by the AG-UI protocol, not at init
    try:
        default_adk_agent = ADKAgent(
            adk_agent=agent,
            app_name=APP_NAME,
            user_id_extractor=extract_user_from_state,  # ← Extract user from state
            session_timeout_seconds=SESSION_TIMEOUT_SECONDS,
            use_in_memory_services=False,
            session_service=session_service,
        )
        print("✅ ADKAgent initialized with Postgres session service + user_id_extractor")
    except TypeError as e:
        # Fallback if session_service not supported
        print(f"⚠️ ADKAgent fallback to in-memory services: {e}")
        default_adk_agent = ADKAgent(
            adk_agent=agent,
            app_name=APP_NAME,
            user_id_extractor=extract_user_from_state,  # ← Extract user from state
            session_timeout_seconds=SESSION_TIMEOUT_SECONDS,
            use_in_memory_services=True,
        )
    add_adk_fastapi_endpoint(
        app, 
        default_adk_agent, 
        path="/ag-ui",
        extract_state_from_request=extract_user_and_session  # ← Extract headers into state
    )
else:
    @app.get("/ag-ui")
    async def ag_ui_placeholder():
        raise HTTPException(
            status_code=501,
            detail="Install ag-ui-adk: pip install ag-ui-adk",
        )


@app.get("/health")
async def health():
    return {"status": "ok"}


if __name__ == "__main__":
    import uvicorn
    from config import HOST, PORT
    uvicorn.run(app, host=HOST, port=PORT)
