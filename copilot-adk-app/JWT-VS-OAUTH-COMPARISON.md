# JWT vs OAuth Authentication: Current Implementation vs OAuth for External Actions

This document provides an **apple-to-apple comparison** between the current JWT-based authentication system and how OAuth token-based authorization for external actions would be implemented in the ADK app.

---

## Executive Summary

**Current State**: The app uses **JWT-based authentication** for app-level access control (login, session management, API protection).

**Missing**: **OAuth token-based authorization** for external actions where:
- Agent requests OAuth tokens from frontend
- Tools use OAuth tokens when calling external APIs
- External systems authorize actions based on user's OAuth credentials

**Key Difference**: JWT authenticates users to **your app**; OAuth authorizes your app (on behalf of users) to access **external systems**.

---

## Part 1: Current JWT Authentication Implementation

### 1.1 Authentication Flow (What Exists)

```
┌─────────────┐     POST /auth/login        ┌─────────────┐
│   Frontend  │  { username, password }     │   Backend   │
│             │ ──────────────────────────► │  FastAPI    │
└─────────────┘                             └──────┬──────┘
       ▲                                           │
       │                                           │ 1. Verify password (Argon2)
       │                                           │ 2. Create JWT token
       │     { access_token: JWT,                 │    { sub: user_id, exp: ... }
       │       user_id, username }                 │
       │ ◄────────────────────────────────────────┘
       │
       │  Store in localStorage: copilot_adk_token
       │
       │  GET /api/sessions
       │  Authorization: Bearer <JWT>
       │ ─────────────────────────────────────────► Backend
       │                                            decode_access_token()
       │                                            return user's sessions
       │ ◄─────────────────────────────────────────
```

### 1.2 Backend Implementation (Current)

**File**: `backend/main.py`

**Login Endpoint**:
```python
@app.post("/auth/login", response_model=TokenResponse)
async def login(body: LoginRequest):
    username = (body.username or "").strip().lower()
    user = await get_user_by_username(username)
    if not user or not verify_password(body.password, user["password_hash"]):
        raise HTTPException(status_code=401, detail="Invalid username or password")
    user_id = str(user["id"])
    token = create_access_token(user_id)  # ← Creates JWT
    return TokenResponse(access_token=token, user_id=user_id, username=user["username"])
```

**JWT Creation** (`backend/auth.py`):
```python
def create_access_token(subject: str) -> str:
    expire = datetime.utcnow() + timedelta(minutes=JWT_EXPIRE_MINUTES)
    to_encode = {"sub": subject, "exp": expire}
    return jwt.encode(to_encode, JWT_SECRET, algorithm=JWT_ALGORITHM)
```

**Token Usage**:
```python
async def get_current_user_id(authorization: Optional[str] = Header(None), ...):
    token = authorization.split(" ", 1)[1]
    user_id = decode_access_token(token)  # ← Decodes JWT, returns user_id
    if not user_id:
        raise HTTPException(status_code=401, detail="Invalid or expired token")
    return user_id
```

### 1.3 Frontend Implementation (Current)

**File**: `frontend/app/login/page.tsx`

**Login Flow**:
```typescript
const res = await fetch(`${getApiUrl()}/auth/login`, {
  method: "POST",
  headers: { "Content-Type": "application/json" },
  body: JSON.stringify({ username, password }),
});
const data = await res.json();
login(data.access_token, { user_id: data.user_id, username: data.username });
```

**Token Storage** (`frontend/lib/auth.ts`):
```typescript
export function setToken(token: string): void {
  localStorage.setItem("copilot_adk_token", token);
}
```

**Token Usage in API Calls** (`frontend/lib/api.ts`):
```typescript
export async function listSessions(token: string): Promise<SessionItem[]> {
  const res = await fetch(`${getApiUrl()}/api/sessions`, {
    headers: {
      Authorization: `Bearer ${token}`,  // ← JWT sent in header
    },
  });
  // ...
}
```

### 1.4 Agent Request Flow (Current)

**File**: `frontend/app/api/copilotkit/route.ts`

```typescript
export async function POST(req: NextRequest) {
  const userId = req.cookies.get("copilot_adk_user_id")?.value || "default";
  const sessionId = req.cookies.get("copilot_adk_session_id")?.value || "default";

  const runtime = new CopilotRuntime({
    agents: {
      my_agent: new HttpAgent({
        url: `${backendUrl}/ag-ui`,
        headers: {
          "X-User-Id": userId,      // ← User ID from cookie
          "X-Session-Id": sessionId, // ← Session ID from cookie
        },
      }),
    },
  });
  // ...
}
```

**Backend Extraction** (`backend/main.py`):
```python
async def extract_user_and_session(request: Request, input_data: RunAgentInput):
    state = {}
    user_id = request.headers.get("X-User-Id")  # ← From CopilotKit proxy
    session_id = request.headers.get("X-Session-Id")
    if user_id:
        state["_ag_ui_user_id"] = user_id
    return state
```

### 1.5 Current Agent Implementation

**File**: `backend/agent.py`

```python
agent = LlmAgent(
    name="assistant",
    model=GEMINI_MODEL,
    instruction="You are a helpful, friendly assistant...",
    # ← NO TOOLS DEFINED
    # ← NO EXTERNAL API CALLS
    # ← NO OAUTH TOKEN USAGE
)
```

**Key Point**: The agent has **no tools** that make external API calls, and there's **no mechanism** for tools to request or use OAuth tokens.

---

## Part 2: OAuth Implementation (How It Would Work)

### 2.1 OAuth Flow for External Actions (Proposed)

```
┌─────────────┐                              ┌─────────────┐
│   User      │  "Send email via Gmail"      │   Agent     │
│             │ ──────────────────────────► │             │
└─────────────┘                              └──────┬──────┘
                                                     │
                                                     │ 1. Agent needs OAuth token
                                                     │    for Gmail API
                                                     │
                                                     ▼
┌─────────────┐                              ┌─────────────┐
│  Frontend   │  Request OAuth token         │   Backend   │
│             │ ◄─────────────────────────── │             │
└──────┬──────┘                               └─────────────┘
       │
       │ 2. Frontend initiates OAuth flow
       │    (redirects to OAuth provider)
       │
       ▼
┌─────────────┐                              ┌─────────────┐
│   Google    │  User authorizes app         │   Frontend  │
│  OAuth      │ ◄─────────────────────────── │             │
│  Provider   │  Returns authorization code  │             │
└──────┬──────┘                               └──────┬──────┘
       │                                             │
       │ 3. Authorization code                     │ 4. Exchange code for token
       │                                             │
       └────────────────────────────────────────────┘
                                                     │
                                                     ▼
┌─────────────┐                              ┌─────────────┐
│   Backend  │  Store token per user          │   Tool      │
│             │ ◄──────────────────────────── │             │
└──────┬──────┘                               └──────┬──────┘
       │                                             │
       │ 5. Token stored in DB                      │ 6. Tool uses token
       │    (user_id, provider, token)               │    for external API call
       │                                             │
       ▼                                             ▼
┌─────────────┐                              ┌─────────────┐
│  Database   │                              │  External   │
│             │                              │   API       │
│  oauth_tokens│                              │  (Gmail)    │
│  table      │                              │             │
└─────────────┘                              └─────────────┘
```

### 2.2 Backend Implementation (Proposed)

**New Database Table** (`backend/db.py` - would need to be added):
```python
# OAuth tokens storage
CREATE TABLE IF NOT EXISTS oauth_tokens (
    id SERIAL PRIMARY KEY,
    user_id INTEGER NOT NULL REFERENCES users(id),
    provider VARCHAR(50) NOT NULL,  -- 'google', 'github', 'slack', etc.
    access_token TEXT NOT NULL,
    refresh_token TEXT,
    expires_at TIMESTAMP,
    scope TEXT,  -- OAuth scopes granted
    created_at TIMESTAMP DEFAULT NOW(),
    UNIQUE(user_id, provider)
);
```

**OAuth Token Management** (`backend/oauth.py` - would need to be created):
```python
from google.adk.auth import OAuth2Auth, AuthConfig

# OAuth configuration for Google
GOOGLE_OAUTH_CONFIG = AuthConfig(
    client_id=os.getenv("GOOGLE_CLIENT_ID"),
    client_secret=os.getenv("GOOGLE_CLIENT_SECRET"),
    authorization_url="https://accounts.google.com/o/oauth2/v2/auth",
    token_url="https://oauth2.googleapis.com/token",
    redirect_uri="http://localhost:3000/auth/oauth/callback",
    scopes=["https://www.googleapis.com/auth/gmail.send", "email"]
)

async def get_oauth_token(user_id: str, provider: str) -> Optional[str]:
    """Retrieve stored OAuth token for user and provider."""
    # Query oauth_tokens table
    # Return access_token if valid, None if expired/missing
    pass

async def store_oauth_token(user_id: str, provider: str, access_token: str, refresh_token: str, expires_at: datetime):
    """Store OAuth token in database."""
    # Insert/update oauth_tokens table
    pass

async def refresh_oauth_token(user_id: str, provider: str) -> Optional[str]:
    """Refresh expired OAuth token using refresh_token."""
    # Use refresh_token to get new access_token
    # Update database
    pass
```

**OAuth Endpoints** (`backend/main.py` - would need to be added):
```python
@app.get("/auth/oauth/authorize/{provider}")
async def oauth_authorize(provider: str, user_id: str = Depends(get_current_user_id)):
    """Initiate OAuth flow - redirect to provider."""
    # Generate state parameter (CSRF protection)
    # Build authorization URL
    # Redirect user to OAuth provider
    pass

@app.get("/auth/oauth/callback/{provider}")
async def oauth_callback(provider: str, code: str, state: str, user_id: str = Depends(get_current_user_id)):
    """Handle OAuth callback - exchange code for token."""
    # Verify state parameter
    # Exchange authorization code for access_token
    # Store token in database
    # Return success to frontend
    pass

@app.get("/auth/oauth/tokens")
async def list_oauth_tokens(user_id: str = Depends(get_current_user_id)):
    """List OAuth tokens for current user."""
    # Query oauth_tokens table for user_id
    # Return list of providers and token status
    pass
```

**Agent Token Request Mechanism** (`backend/main.py` - would need to be added):
```python
async def extract_user_and_session(request: Request, input_data: RunAgentInput):
    state = {}
    user_id = request.headers.get("X-User-Id")
    session_id = request.headers.get("X-Session-Id")
    
    if user_id:
        state["_ag_ui_user_id"] = user_id
        # NEW: Add OAuth token retrieval capability
        # state["_oauth_token_retriever"] = lambda provider: get_oauth_token(user_id, provider)
    
    return state
```

### 2.3 Frontend Implementation (Proposed)

**OAuth Token Request Handler** (`frontend/app/api/oauth/route.ts` - would need to be created):
```typescript
export async function GET(req: NextRequest) {
  const { searchParams } = new URL(req.url);
  const provider = searchParams.get("provider");
  const userId = req.cookies.get("copilot_adk_user_id")?.value;

  // Check if token exists
  const tokenResponse = await fetch(`${getApiUrl()}/auth/oauth/tokens?provider=${provider}`, {
    headers: {
      Authorization: `Bearer ${getToken()}`,
    },
  });

  const tokens = await tokenResponse.json();
  const token = tokens.find((t: any) => t.provider === provider);

  if (!token || isExpired(token)) {
    // Redirect to OAuth authorization
    const authUrl = `${getApiUrl()}/auth/oauth/authorize/${provider}?user_id=${userId}`;
    return Response.redirect(authUrl);
  }

  return Response.json({ token: token.access_token });
}
```

**OAuth Callback Handler** (`frontend/app/auth/oauth/callback/page.tsx` - would need to be created):
```typescript
export default function OAuthCallbackPage() {
  useEffect(() => {
    const { searchParams } = new URL(window.location.href);
    const code = searchParams.get("code");
    const provider = searchParams.get("provider");

    // Exchange code for token
    fetch(`${getApiUrl()}/auth/oauth/callback/${provider}?code=${code}`, {
      headers: {
        Authorization: `Bearer ${getToken()}`,
      },
    })
      .then(() => {
        // Redirect back to chat
        router.push("/chat");
      });
  }, []);
}
```

**Agent OAuth Token Request** (`frontend/app/api/copilotkit/route.ts` - would need modification):
```typescript
export async function POST(req: NextRequest) {
  // ... existing code ...

  // NEW: Add OAuth token request capability
  const runtime = new CopilotRuntime({
    agents: {
      my_agent: new HttpAgent({
        url: `${backendUrl}/ag-ui`,
        headers: {
          "X-User-Id": userId,
          "X-Session-Id": sessionId,
        },
        // NEW: OAuth token request handler
        onOAuthTokenRequest: async (provider: string) => {
          const tokenRes = await fetch(`/api/oauth?provider=${provider}`);
          const { token } = await tokenRes.json();
          return token;
        },
      }),
    },
  });
}
```

### 2.4 Tool Implementation with OAuth (Proposed)

**Example Tool** (`backend/tools/gmail_tool.py` - would need to be created):
```python
from google.adk.tools import BaseTool
from typing import Optional

class GmailSendTool(BaseTool):
    def __init__(self, oauth_token_retriever):
        super().__init__(
            name="send_email",
            description="Send an email via Gmail"
        )
        self._get_token = oauth_token_retriever

    async def run_async(self, *, args: dict, tool_context):
        to = args.get("to")
        subject = args.get("subject")
        body = args.get("body")
        
        # NEW: Retrieve OAuth token for Gmail
        access_token = await self._get_token("google")
        if not access_token:
            return {
                "error": "OAuth token not available. Please authorize Gmail access."
            }
        
        # Use token to call Gmail API
        import httpx
        async with httpx.AsyncClient() as client:
            response = await client.post(
                "https://gmail.googleapis.com/gmail/v1/users/me/messages/send",
                headers={
                    "Authorization": f"Bearer {access_token}",  # ← OAuth token
                    "Content-Type": "application/json",
                },
                json={
                    "raw": base64.b64encode(f"To: {to}\nSubject: {subject}\n\n{body}").decode()
                }
            )
            return {"status": "sent", "message_id": response.json()["id"]}
```

**Agent with OAuth Tools** (`backend/agent.py` - would need modification):
```python
from tools.gmail_tool import GmailSendTool

# OAuth token retriever function
async def get_oauth_token_for_user(user_id: str, provider: str) -> Optional[str]:
    """Retrieve OAuth token from database for user."""
    return await get_oauth_token(user_id, provider)

# Create tool with OAuth token retriever
gmail_tool = GmailSendTool(
    oauth_token_retriever=lambda provider: get_oauth_token_for_user(user_id, provider)
)

agent = LlmAgent(
    name="assistant",
    model=GEMINI_MODEL,
    tools=[gmail_tool],  # ← Tool that uses OAuth
    instruction="You are a helpful assistant that can send emails..."
)
```

---

## Part 3: Apple-to-Apple Comparison

### 3.1 Authentication Purpose

| Aspect | Current (JWT) | OAuth (Proposed) |
|--------|---------------|------------------|
| **Purpose** | Authenticate user to **your app** | Authorize **your app** to access **external systems** on behalf of user |
| **Scope** | App-level access control | External API access (Gmail, GitHub, Slack, etc.) |
| **Token Type** | JWT (self-contained, signed by your app) | OAuth access token (issued by external provider) |
| **Token Lifetime** | 60 minutes (configurable) | Varies by provider (typically 1 hour, refreshable) |
| **Token Storage** | Frontend `localStorage` | Backend database (`oauth_tokens` table) |

### 3.2 Flow Comparison

| Step | Current (JWT) | OAuth (Proposed) |
|------|---------------|------------------|
| **1. User Login** | Username/password → Backend → JWT token | Username/password → Backend → JWT token (same) |
| **2. Token Storage** | Frontend `localStorage` | Frontend `localStorage` (JWT) + Backend DB (OAuth) |
| **3. API Requests** | `Authorization: Bearer <JWT>` | `Authorization: Bearer <JWT>` (app API) |
| **4. External API Calls** | ❌ **Not implemented** | `Authorization: Bearer <OAuth>` (external API) |
| **5. Token Refresh** | Re-login required | Automatic refresh using `refresh_token` |

### 3.3 Code Structure Comparison

| Component | Current (JWT) | OAuth (Proposed) |
|-----------|---------------|------------------|
| **Backend Auth** | `backend/auth.py` - JWT creation/validation | `backend/auth.py` (JWT) + `backend/oauth.py` (OAuth) |
| **Database** | `users` table only | `users` table + `oauth_tokens` table |
| **Frontend Auth** | `frontend/lib/auth.ts` - JWT storage | `frontend/lib/auth.ts` (JWT) + `frontend/lib/oauth.ts` (OAuth) |
| **Agent Tools** | ❌ No tools | Tools that use OAuth tokens |
| **Token Request** | ❌ Not needed | Agent → Frontend → OAuth provider → Token |

### 3.4 Request Flow Comparison

**Current JWT Flow**:
```
User → Frontend → POST /auth/login → Backend
Backend → JWT token → Frontend (localStorage)
Frontend → GET /api/sessions (Authorization: Bearer <JWT>) → Backend
Backend → decode JWT → return sessions
```

**OAuth Flow (Proposed)**:
```
User → Frontend → POST /auth/login → Backend (same as JWT)
Backend → JWT token → Frontend (localStorage)

[When agent needs external API access]
Agent → Frontend: "Need Gmail token"
Frontend → GET /auth/oauth/authorize/google → Backend
Backend → Redirect to Google OAuth
Google → User authorizes → Callback with code
Backend → Exchange code → Store OAuth token in DB
Agent → Tool uses OAuth token → Gmail API
```

---

## Part 4: Key Differences

### 4.1 Authentication vs Authorization

**JWT (Current)**:
- **Authentication**: "Who is this user?" → Verifies user identity
- **Authorization**: "Can this user access app resources?" → Controls app-level access
- **Token Scope**: Limited to your app's resources

**OAuth (Proposed)**:
- **Authentication**: "Who is this user?" → Same as JWT (user still logs in)
- **Authorization**: "Can the app access external systems on behalf of user?" → Controls external API access
- **Token Scope**: Limited to external provider's resources (Gmail, GitHub, etc.)

### 4.2 Token Lifecycle

**JWT (Current)**:
- Created: When user logs in
- Stored: Frontend `localStorage`
- Used: Every API request to your backend
- Expires: After 60 minutes (configurable)
- Refresh: User must re-login

**OAuth (Proposed)**:
- Created: When user authorizes external provider (one-time)
- Stored: Backend database (`oauth_tokens` table)
- Used: When tools call external APIs
- Expires: Varies by provider (typically 1 hour)
- Refresh: Automatic using `refresh_token` (no user interaction)

### 4.3 User Interaction

**JWT (Current)**:
- User logs in once → Gets JWT → Uses app
- No additional authorization steps

**OAuth (Proposed)**:
- User logs in once → Gets JWT → Uses app
- **First time** tool needs external API: User redirected to OAuth provider → Authorizes → Returns to app
- **Subsequent times**: Token retrieved from database (no user interaction)

### 4.4 Security Model

**JWT (Current)**:
- Token signed by your app's secret
- Token contains user ID
- Token validated on every request
- If token stolen: Attacker can impersonate user in your app

**OAuth (Proposed)**:
- Token issued by external provider (Google, GitHub, etc.)
- Token contains scopes (what app can do)
- Token validated by external API
- If token stolen: Attacker can access external system, but not your app (still needs JWT)

---

## Part 5: Implementation Outline (No Code Changes)

### 5.1 Database Changes

1. **Create `oauth_tokens` table**:
   - `user_id` (FK to `users.id`)
   - `provider` (e.g., 'google', 'github')
   - `access_token` (encrypted)
   - `refresh_token` (encrypted)
   - `expires_at` (timestamp)
   - `scope` (OAuth scopes granted)
   - Unique constraint on `(user_id, provider)`

### 5.2 Backend Changes

1. **New file**: `backend/oauth.py`
   - OAuth configuration (client ID, secret, URLs)
   - Token storage/retrieval functions
   - Token refresh logic

2. **Modify**: `backend/main.py`
   - Add OAuth authorization endpoint (`/auth/oauth/authorize/{provider}`)
   - Add OAuth callback endpoint (`/auth/oauth/callback/{provider}`)
   - Add token listing endpoint (`/auth/oauth/tokens`)
   - Modify `extract_user_and_session` to include OAuth token retriever in state

3. **New file**: `backend/tools/` directory
   - Create tools that use OAuth tokens (e.g., `gmail_tool.py`, `github_tool.py`)

4. **Modify**: `backend/agent.py`
   - Add tools that require OAuth tokens
   - Pass OAuth token retriever to tools

### 5.3 Frontend Changes

1. **New file**: `frontend/lib/oauth.ts`
   - OAuth token request functions
   - Token status checking

2. **New file**: `frontend/app/auth/oauth/callback/page.tsx`
   - Handle OAuth callback from provider
   - Exchange code for token

3. **Modify**: `frontend/app/api/copilotkit/route.ts`
   - Add OAuth token request handler
   - Pass token retriever to `HttpAgent`

4. **New file**: `frontend/app/api/oauth/route.ts`
   - API route to check/request OAuth tokens

### 5.4 ADK Integration

1. **Use ADK's OAuth support**:
   - Import `google.adk.auth.OAuth2Auth`
   - Use `AuthConfig` for OAuth configuration
   - Integrate with ADK's authentication framework

2. **Tool Context**:
   - Tools receive `tool_context` parameter
   - Add OAuth token retriever to context
   - Tools call `tool_context.get_oauth_token(provider)`

### 5.5 Configuration

1. **Environment Variables**:
   - `GOOGLE_CLIENT_ID`
   - `GOOGLE_CLIENT_SECRET`
   - `GITHUB_CLIENT_ID` (if supporting GitHub)
   - `GITHUB_CLIENT_SECRET`
   - OAuth redirect URIs

2. **OAuth Provider Setup**:
   - Register app with OAuth providers (Google Cloud Console, GitHub, etc.)
   - Configure redirect URIs
   - Get client ID and secret

---

## Part 6: Summary

### What Exists (JWT)

✅ User login with username/password  
✅ JWT token creation and validation  
✅ Token storage in frontend `localStorage`  
✅ Protected API routes using JWT  
✅ User identification via `X-User-Id` header  
✅ Session management  

### What's Missing (OAuth)

❌ OAuth token storage in database  
❌ OAuth authorization flow (redirect to provider)  
❌ OAuth callback handling  
❌ Token refresh mechanism  
❌ Tools that use OAuth tokens  
❌ Agent-to-frontend OAuth token request mechanism  
❌ Frontend OAuth token management  

### Key Takeaway

**Current authentication (JWT)** handles **"Who can access my app?"**  
**OAuth (proposed)** handles **"What external systems can my app access on behalf of users?"**

These are **complementary**, not replacements:
- **JWT**: User → Your App
- **OAuth**: Your App → External Systems (on behalf of user)

Both are needed for a complete system where agents can perform actions in external systems using the user's credentials.

---

## Related Files

| Purpose | Current File | OAuth File (Would Need) |
|---------|--------------|-------------------------|
| JWT creation/validation | `backend/auth.py` | Same (JWT still used) |
| OAuth token management | ❌ None | `backend/oauth.py` (new) |
| Database schema | `backend/db.py` (users table) | `backend/db.py` (+ oauth_tokens table) |
| Auth routes | `backend/main.py` | `backend/main.py` (+ OAuth routes) |
| Frontend token storage | `frontend/lib/auth.ts` | `frontend/lib/auth.ts` + `frontend/lib/oauth.ts` |
| Agent tools | `backend/agent.py` (no tools) | `backend/tools/*.py` (new tools with OAuth) |
| OAuth callback | ❌ None | `frontend/app/auth/oauth/callback/page.tsx` (new) |

---

**Note**: This document describes the architecture and implementation approach. No code changes have been made to the codebase.
