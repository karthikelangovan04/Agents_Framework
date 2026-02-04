# Authentication Flow

This document describes how authentication works in the Copilot ADK app: login with username and password, JWT token issuance, and how the token is used for protected API calls. **Passwords are shown as `****` in all examples.**

---

## Overview

1. **Login**: User sends username + password to `POST /auth/login`.
2. **Backend**: Verifies password (Argon2), creates a JWT with user id as subject, returns token + user info.
3. **Frontend**: Stores token in `localStorage` and sends `Authorization: Bearer <token>` on every API request.
4. **Protected routes**: Backend decodes the JWT and uses the `sub` (user id) to authorize requests.

---

## 1. Login Request (curl example)

The agent or any client can log in by sending a POST request with JSON body:

```bash
curl -s -X POST http://localhost:8000/auth/login \
  -H "Content-Type: application/json" \
  -d '{"username":"karthikelangovanpadma","password":"****"}'
```

**Important**: Use your real password in the `"password":"****"` field; this document masks it as `****` for security.

---

## 2. Login Response

On success, the backend returns JSON like:

```json
{
  "access_token": "eyJhbGciOiJIUzI1NiIsInR5cCI6IkpXVCJ9...",
  "token_type": "bearer",
  "user_id": "4",
  "username": "karthikelangovanpadma"
}
```

- **access_token**: JWT string. Use this for all subsequent authenticated requests.
- **token_type**: Always `"bearer"`.
- **user_id**: Numeric user id (string in JSON).
- **username**: The username that was used to log in.

On failure (wrong username or password), the backend returns `401` with body like:

```json
{ "detail": "Invalid username or password" }
```

---

## 3. Using the Token for API Calls

After login, the client must send the token in the `Authorization` header for protected endpoints.

**Example: list sessions**

```bash
TOKEN="<paste access_token from login response here>"

curl -s http://localhost:8000/api/sessions \
  -H "Authorization: Bearer $TOKEN"
```

**Example: one-liner (login + use token)**

```bash
TOKEN=$(curl -s -X POST http://localhost:8000/auth/login \
  -H "Content-Type: application/json" \
  -d '{"username":"karthikelangovanpadma","password":"****"}' | jq -r '.access_token')

curl -s http://localhost:8000/api/sessions \
  -H "Authorization: Bearer $TOKEN"
```

If the token is missing, invalid, or expired, the backend returns `401` with `"Not authenticated"` or `"Invalid or expired token"`.

---

## 4. Backend Implementation

### 4.1 Login endpoint

- **Route**: `POST /auth/login`
- **Body**: `{ "username": string, "password": string }`
- **Flow**:
  1. Normalize username (strip, lowercase).
  2. Look up user by username in the database (`get_user_by_username`).
  3. Verify password with `verify_password(plain, user["password_hash"])` (Argon2).
  4. If valid: create JWT with `create_access_token(user_id)`, return `TokenResponse`.
  5. If invalid: return `401`, detail `"Invalid username or password"`.

### 4.2 JWT creation and validation

- **Config** (from `config.py`): `JWT_SECRET`, `JWT_ALGORITHM` (default `HS256`), `JWT_EXPIRE_MINUTES` (default `60`).
- **create_access_token(subject)** (in `auth.py`): Encodes payload `{ "sub": subject, "exp": expire }` with `jose.jwt.encode`.
- **decode_access_token(token)**: Decodes with `jose.jwt.decode`, returns `payload["sub"]` (user id) or `None` if invalid/expired.

### 4.3 Password hashing

- **Library**: `passlib` with **Argon2** (`CryptContext(schemes=["argon2"])`).
- **hash_password(plain)**: Used at registration; store the returned hash in the database.
- **verify_password(plain, hashed)**: Used at login to check the submitted password against the stored hash.

### 4.4 Protected routes and dependency

- **Dependency**: `get_current_user_id(authorization, x_user_id)`.
  - If `X-User-Id` header is present (e.g. from CopilotKit proxy), it returns that value (for agent requests).
  - Otherwise it expects `Authorization: Bearer <token>`, extracts the token, decodes it via `decode_access_token`, and returns the user id. If missing or invalid, raises `401`.
- **Usage**: Endpoints like `GET /api/sessions` and `POST /api/sessions` use `user_id: str = Depends(get_current_user_id)` so only authenticated users (or requests with valid `X-User-Id`) can access them.

---

## 5. Frontend Implementation

### 5.1 Login (browser)

- **Page**: `frontend/app/login/page.tsx`
- **Action**: On form submit, `POST` to `getApiUrl() + "/auth/login"` with `{ username, password }`.
- **On success**: Calls `login(data.access_token, { user_id: data.user_id, username: data.username })` from `AuthContext`, then redirects to `/chat`.

### 5.2 Storing token and user

- **Storage**: `frontend/lib/auth.ts`
  - Token: `localStorage` key `copilot_adk_token`.
  - User: `localStorage` key `copilot_adk_user` (JSON: `{ user_id, username }`).
- **AuthContext** (`frontend/contexts/AuthContext.tsx`):
  - On load: reads token and user from `auth.getToken()` / `auth.getUser()` and sets state.
  - On login: calls `auth.setToken(t)` and `auth.setUser(u)`, and sets `copilot_adk_user_id` cookie for the AG-UI/CopilotKit proxy.
  - On logout: clears localStorage, calls `/api/session` to clear cookies, and clears `copilot_adk_*` cookies.

### 5.3 Sending the token on API calls

- **API client**: `frontend/lib/api.ts`
- **Pattern**: For `listSessions(token)` and `createSession(token)`, the frontend passes the stored token and sets:
  - `Authorization: Bearer ${token}`
- The token comes from `AuthContext` (e.g. `token` from `useAuth()`), which in turn reads it from `localStorage` on load and after login.

---

## 6. Summary Diagram

```
┌─────────────┐     POST /auth/login        ┌─────────────┐
│   Client    │  { username, password: **** }│   Backend    │
│ (curl/UI)   │ ──────────────────────────► │   FastAPI   │
└─────────────┘                             └──────┬──────┘
       ▲                                           │
       │                                           │ verify_password()
       │                                           │ create_access_token(user_id)
       │     { access_token, user_id, username }    │
       │ ◄────────────────────────────────────────┘
       │
       │  Store token (e.g. localStorage / $TOKEN)
       │
       │  GET /api/sessions
       │  Authorization: Bearer <access_token>
       │ ─────────────────────────────────────────► Backend
       │                                            decode_access_token()
       │                                            return user's sessions
       │ ◄─────────────────────────────────────────
```

---

## 7. Security Notes

- **Never commit real passwords.** This document uses `****` in examples.
- **JWT_SECRET**: Must be set in production (e.g. via `backend/.env`); do not use the default dev secret.
- **HTTPS**: Use HTTPS in production for login and all API traffic.
- **Cookie**: The frontend sets `copilot_adk_user_id` for the CopilotKit → backend proxy; the actual auth for REST API calls is the Bearer token.

---

## 8. Related Files

| Purpose                | File |
|------------------------|------|
| Login/register routes  | `backend/main.py` |
| JWT + password hashing | `backend/auth.py` |
| JWT/password config    | `backend/config.py` |
| Client token/user storage | `frontend/lib/auth.ts` |
| Login UI + call to backend | `frontend/app/login/page.tsx` |
| Auth state + login/logout | `frontend/contexts/AuthContext.tsx` |
| API calls with Bearer token | `frontend/lib/api.ts` |
