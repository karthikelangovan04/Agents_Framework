"""
FastAPI app: auth, session APIs, and AG-UI endpoint for CopilotKit.
Parameterized for dev and Cloud Run via config.
"""
import uuid
from typing import List, Optional

from fastapi import FastAPI, Depends, HTTPException, Request, Header
from fastapi.middleware.cors import CORSMiddleware
from pydantic import BaseModel

from config import APP_NAME, CORS_ORIGINS, SESSION_TIMEOUT_SECONDS
from agent import agent, session_service
from auth import hash_password, verify_password, create_access_token, decode_access_token
from db import init_db, close_db, get_pool, get_user_by_username, create_user

# Optional: ag-ui-adk for CopilotKit; fallback if not installed
try:
    from ag_ui_adk import ADKAgent, add_adk_fastapi_endpoint
    HAS_AG_UI = True
except ImportError:
    HAS_AG_UI = False

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
    """Create a new chat session (new conversation)."""
    session_id = str(uuid.uuid4())
    try:
        session = await session_service.create_session(
            app_name=APP_NAME,
            user_id=user_id,
            session_id=session_id,
        )
        return SessionItem(
            id=session.id,
            create_time=str(session.create_time) if getattr(session, "create_time", None) else None,
            update_time=str(session.update_time) if getattr(session, "update_time", None) else None,
        )
    except Exception as e:
        raise HTTPException(status_code=500, detail=str(e))


# --- AG-UI endpoint for CopilotKit ---
# CopilotKit frontend sends X-User-Id and X-Session-Id so each request uses the right user/session.
# We create an ADKAgent per request with those values when possible; otherwise use defaults.
if HAS_AG_UI:
    # ADKAgent with Postgres session service
    # Note: user_id/session_id are handled per-request by the AG-UI protocol, not at init
    try:
        default_adk_agent = ADKAgent(
            adk_agent=agent,
            app_name=APP_NAME,
            session_timeout_seconds=SESSION_TIMEOUT_SECONDS,
            use_in_memory_services=False,
            session_service=session_service,
        )
    except TypeError:
        # Fallback if session_service not supported
        default_adk_agent = ADKAgent(
            adk_agent=agent,
            app_name=APP_NAME,
            session_timeout_seconds=SESSION_TIMEOUT_SECONDS,
            use_in_memory_services=True,
        )
    add_adk_fastapi_endpoint(app, default_adk_agent, path="/ag-ui")
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
