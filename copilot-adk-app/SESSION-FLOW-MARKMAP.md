---
title: Session Flow - Frontend to Backend (Copilot ADK App)
markmap:
  colorFreezeLevel: 2
---

# User Session Flow: Frontend → Backend

## 1. Login and token storage (frontend)

### 1.1 Login page submits credentials

- **File**: `frontend/app/login/page.tsx`
- **What it does**: User enters username/password; form POSTs to backend `/auth/login`; on success calls `login(access_token, { user_id, username })` from AuthContext and redirects to `/chat`.
- **Snippet** (handleSubmit):

```ts
const res = await fetch(`${getApiUrl()}/auth/login`, {
  method: "POST",
  headers: { "Content-Type": "application/json" },
  body: JSON.stringify({ username, password }),
});
const data = await res.json().catch(() => ({}));
if (!res.ok) throw new Error(data.detail || "Login failed");
login(data.access_token, { user_id: data.user_id, username: data.username });
router.replace("/chat");
```

### 1.2 AuthContext stores token and user

- **File**: `frontend/contexts/AuthContext.tsx`
- **What it does**: `login(t, u)` calls `auth.setToken(t)` and `auth.setUser(u)`, then sets cookie `copilot_adk_user_id=<user_id>` so the CopilotKit API route can send it to the backend.
- **Snippet** (login):

```ts
const login = (t: string, u: UserInfo) => {
  auth.setToken(t);
  auth.setUser(u);
  setToken(t);
  setUser(u);
  if (typeof document !== "undefined") {
    document.cookie = `copilot_adk_user_id=${u.user_id}; path=/; max-age=${60 * 60 * 24 * 7}; samesite=lax`;
  }
};
```

### 1.3 Persistence in localStorage

- **File**: `frontend/lib/auth.ts`
- **What it does**: Token stored under `copilot_adk_token`, user under `copilot_adk_user` (JSON: `user_id`, `username`). Used for initial load and for REST API calls (Bearer token).
- **Keys**: `TOKEN_KEY = "copilot_adk_token"`, `USER_KEY = "copilot_adk_user"`.

---

## 2. Session list and create (REST API with JWT)

### 2.1 Chat page loads sessions

- **File**: `frontend/app/chat/page.tsx`
- **What it does**: On mount (when user/token exist), calls `listSessions(token)`. If no sessions, calls `createSession(token)` and sets first session as current. Updates `copilot_adk_session_id` cookie and optionally calls `setUserAndSessionCookies(user_id, session_id)`.
- **Snippet** (initSessions):

```ts
let list = await listSessions(token);
if (list.length === 0) {
  const newSession = await createSession(token);
  list = [newSession];
}
setSessions(list);
if (list.length > 0) {
  const first = list[0];
  setCurrentSessionId(first.id);
  document.cookie = `copilot_adk_session_id=${first.id}; path=/; ...`;
  await setUserAndSessionCookies(user.user_id, first.id).catch(() => {});
}
```

### 2.2 listSessions and createSession (frontend API client)

- **File**: `frontend/lib/api.ts`
- **What it does**: Sends `Authorization: Bearer <token>` to backend. `listSessions` → `GET /api/sessions`; `createSession` → `POST /api/sessions`. Backend resolves user from JWT and returns sessions for that user.
- **Snippet** (listSessions):

```ts
const res = await fetch(`${getApiUrl()}/api/sessions`, {
  headers: { Authorization: `Bearer ${token}` },
});
const data = await res.json();
return (data.sessions || []).map((s) => ({ id: s.id, ... }));
```

### 2.3 Backend: get current user from JWT and list/create sessions

- **File**: `backend/main.py`
- **What it does**: `get_current_user_id` reads `Authorization: Bearer <token>`, decodes JWT, returns `sub` as user_id. `GET /api/sessions` and `POST /api/sessions` use this; they call `session_service.list_sessions(app_name, user_id)` and `session_service.create_session(app_name, user_id, session_id, state)`.
- **Snippet** (get_current_user_id):

```py
async def get_current_user_id(authorization, x_user_id):
    if x_user_id:
        return x_user_id
    token = authorization.split(" ", 1)[1]
    user_id = decode_access_token(token)
    if not user_id:
        raise HTTPException(status_code=401, detail="Invalid or expired token")
    return user_id
```

- **Snippet** (create_session initial state for AG-UI):

```py
initial_state = {
    "_ag_ui_user_id": user_id,
    "_ag_ui_app_name": APP_NAME,
    "_ag_ui_thread_id": session_id,
    "_ag_ui_session_id": session_id,
}
session = await session_service.create_session(
    app_name=APP_NAME, user_id=user_id, session_id=session_id, state=initial_state
)
```

---

## 3. Cookies for AG-UI (user_id and session_id)

### 3.1 Where cookies are set

- **User cookie**: Set in `AuthContext` on login and on restore; and in `chat/page.tsx` when `user` is available. Name: `copilot_adk_user_id`, value: numeric user id.
- **Session cookie**: Set in `chat/page.tsx` whenever `currentSessionId` changes (initial load, new chat, or selecting another session). Name: `copilot_adk_session_id`, value: UUID session id.

### 3.2 Next.js API route that can set cookies (optional backup)

- **File**: `frontend/app/api/session/route.ts`
- **What it does**: `POST /api/session` with body `{ user_id, session_id }` sets `copilot_adk_user_id` and `copilot_adk_session_id` on the response. Used by `setUserAndSessionCookies()` so cookies are set even when the client calls the API (same-origin).
- **Snippet**:

```ts
if (userId) {
  res.cookies.set("copilot_adk_user_id", String(userId), { path: "/", maxAge: 60 * 60 * 24 * 7, sameSite: "lax" });
}
if (sessionId) {
  res.cookies.set("copilot_adk_session_id", sessionId, { path: "/", maxAge: 60 * 60 * 24 * 7, sameSite: "lax" });
}
```

### 3.3 setUserAndSessionCookies (frontend)

- **File**: `frontend/lib/api.ts`
- **What it does**: Calls `POST /api/session` with `{ user_id: userId, session_id: sessionId }` so the server response sets the cookies. Used after loading/creating/selecting a session so the next CopilotKit request sends the right cookies.
- **Snippet**:

```ts
export async function setUserAndSessionCookies(userId: number, sessionId: string): Promise<void> {
  await fetch("/api/session", {
    method: "POST",
    headers: { "Content-Type": "application/json" },
    body: JSON.stringify({ user_id: userId, session_id: sessionId }),
  });
}
```

---

## 4. CopilotKit → Next.js proxy → Backend /ag-ui

### 4.1 CopilotKit component (chat page)

- **File**: `frontend/app/chat/page.tsx`
- **What it does**: Wraps the chat UI in `<CopilotKit runtimeUrl="/api/copilotkit" agent="my_agent" threadId={currentSessionId}>`. All agent requests go to Next.js `POST /api/copilotkit`; `threadId` is the current session UUID so AG-UI treats it as the conversation thread.
- **Snippet**:

```tsx
<CopilotKit
  key={currentSessionId}
  threadId={currentSessionId || undefined}
  runtimeUrl="/api/copilotkit"
  agent="my_agent"
>
```

### 4.2 Next.js CopilotKit API route (proxy)

- **File**: `frontend/app/api/copilotkit/route.ts`
- **What it does**: Reads cookies `copilot_adk_user_id` and `copilot_adk_session_id` from the incoming request, then creates an `HttpAgent` that calls the backend `POST /ag-ui` with headers `X-User-Id` and `X-Session-Id`. Every CopilotKit message is forwarded to the backend with these headers.
- **Snippet**:

```ts
const userId = req.cookies.get("copilot_adk_user_id")?.value || "default";
const sessionId = req.cookies.get("copilot_adk_session_id")?.value || "default";

const runtime = new CopilotRuntime({
  agents: {
    my_agent: new HttpAgent({
      url: `${backendUrl}/ag-ui`,
      headers: {
        "X-User-Id": userId,
        "X-Session-Id": sessionId,
      },
    }),
  },
});
```

---

## 5. AG-UI protocol on the backend (deep dive)

### 5.1 Request hits /ag-ui with headers

- **File**: `backend/main.py`
- **What it does**: Middleware logs `X-User-Id` and `X-Session-Id` for `/ag-ui`. The `ag-ui-adk` library handles the POST body (AG-UI protocol); before running the agent it calls `extract_state_from_request(request, input_data)` to merge request context into the run state.
- **Flow**: Incoming request has headers set by Next.js from cookies → AG-UI handler runs → state extractor runs first.

### 5.2 extract_state_from_request (header → state)

- **File**: `backend/main.py` — function `extract_user_and_session`
- **What it does**: Reads `X-User-Id` and `X-Session-Id` from the request and puts them into a state dict as `_ag_ui_user_id` and `_ag_ui_session_id`. This state is merged into the run input so the agent and session service use the correct user and session.
- **Snippet**:

```py
async def extract_user_and_session(request: Request, input_data: RunAgentInput) -> dict[str, Any]:
    state = {}
    user_id = request.headers.get("X-User-Id")
    session_id = request.headers.get("X-Session-Id")
    if user_id:
        state["_ag_ui_user_id"] = user_id
    if session_id:
        state["_ag_ui_session_id"] = session_id
    return state
```

### 5.3 user_id_extractor (state → ADK user id)

- **File**: `backend/main.py` — function `extract_user_from_state`
- **What it does**: AG-UI/ADKAgent calls this to resolve the “user id” for the run. It reads `input.state["_ag_ui_user_id"]` (set above). If missing, falls back to `thread_user_<thread_id>`. Returned value is used by the session service to scope sessions per user.
- **Snippet**:

```py
def extract_user_from_state(input: RunAgentInput) -> str:
    if isinstance(input.state, dict):
        user_id = input.state.get("_ag_ui_user_id")
        if user_id:
            return str(user_id)
    return f"thread_user_{input.thread_id}"
```

### 5.4 ADKAgent and session service

- **File**: `backend/main.py` (ADKAgent setup), `backend/agent.py` (session_service)
- **What it does**: `ADKAgent` is created with `user_id_extractor=extract_user_from_state` and `session_service=session_service`. So for each request, user id comes from state (from headers), and session/thread lookup uses `(app_name, user_id, session_id/thread_id)`. Session state is stored in Postgres via `DatabaseSessionService`.
- **File** `backend/agent.py`:

```py
session_service = DatabaseSessionService(db_url=DATABASE_URL)
agent = LlmAgent(name="assistant", model=GEMINI_MODEL, ...)
```

### 5.5 How AG-UI protocol uses session_id and thread_id

- **thread_id**: In CopilotKit, `threadId` is set to `currentSessionId` (the UUID). The AG-UI client sends this in the protocol; the backend uses it to load/save the correct conversation.
- **session_id**: Same UUID is sent as `X-Session-Id` and stored in state as `_ag_ui_session_id`. The ADK session service keys storage by (app_name, user_id, session_id). So thread_id and session_id are the same value in this app.
- **Session lifecycle**: (1) Frontend creates session via `POST /api/sessions` → backend creates row in Postgres with initial state including `_ag_ui_user_id`, `_ag_ui_thread_id`, `_ag_ui_session_id`. (2) User sends message → CopilotKit calls `/api/copilotkit` with cookies → Next.js adds `X-User-Id`, `X-Session-Id` → backend merges into state → user_id_extractor returns authenticated user id → session service loads/updates session for that (user_id, session_id). So one session = one thread = one conversation in the DB.

---

## 6. Session history (loading previous messages)

### 6.1 Frontend: getSessionHistory

- **File**: `frontend/lib/api.ts`
- **What it does**: When user selects or opens a session, chat page calls `getSessionHistory(sessionId, user.user_id)`. It POSTs to backend `POST /agents/state` with `{ threadId: sessionId, appName, userId }`. Backend (ag-ui-adk) returns thread state and messages; frontend displays them in the main content area.
- **Snippet**:

```ts
const res = await fetch(`${getApiUrl()}/agents/state`, {
  method: "POST",
  headers: { "Content-Type": "application/json" },
  body: JSON.stringify({
    threadId: sessionId,
    appName: "copilot_adk_app",
    userId: String(userId),
  }),
});
// data.threadExists, data.messages, data.state
```

### 6.2 Backend /agents/state

- **Provided by**: `ag-ui-adk` when you use `add_adk_fastapi_endpoint`. Not defined in app code.
- **What it does**: Accepts AG-UI state request (threadId, appName, userId), uses the same `session_service` to load the session from Postgres, returns existing state and message history so the frontend can show “previous conversation” and the agent can continue in the same thread.

---

## 7. End-to-end flow summary

- **Login**: `login/page.tsx` → POST `/auth/login` → backend returns JWT + user_id → `AuthContext.login()` → localStorage (token, user) + cookie `copilot_adk_user_id`.
- **Sessions**: `chat/page.tsx` → `listSessions(token)` / `createSession(token)` → backend JWT → `session_service` → cookie `copilot_adk_session_id` (+ optional `POST /api/session`).
- **Chat message**: User types → CopilotKit → POST `/api/copilotkit` (cookies sent) → Next.js reads cookies → HttpAgent POST `/ag-ui` with `X-User-Id`, `X-Session-Id` → backend `extract_user_and_session` → state `_ag_ui_user_id`, `_ag_ui_session_id` → `user_id_extractor` → ADKAgent + session_service load/update session by (user_id, session_id) → response back to UI.
- **History**: On session select, `getSessionHistory(sessionId, user_id)` → POST `/agents/state` (threadId = sessionId) → ag-ui-adk + session_service return state/messages → frontend renders previous messages.

---

## 8. File reference (paths)

| Role | App path |
|------|----------|
| Login form | `frontend/app/login/page.tsx` |
| Auth state + cookie on login | `frontend/contexts/AuthContext.tsx` |
| Token/user localStorage | `frontend/lib/auth.ts` |
| Session list/create API client | `frontend/lib/api.ts` |
| Chat UI + CopilotKit + cookies | `frontend/app/chat/page.tsx` |
| Set cookies via API | `frontend/app/api/session/route.ts` |
| CopilotKit → backend proxy | `frontend/app/api/copilotkit/route.ts` |
| Auth + session REST + AG-UI | `backend/main.py` |
| Session service (Postgres) | `backend/agent.py` |
