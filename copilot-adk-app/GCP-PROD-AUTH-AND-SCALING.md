# Production-Grade User Authentication and Scaling on GCP

This document describes how to implement production-grade user authentication and scaling for the Copilot ADK app when running on Google Cloud Platform. **No code changes are prescribed here**—treat this as a design and implementation guide.

---

## 1. Production-Grade Authentication: What It Means

### 1.1 Requirements Checklist

| Area | Requirement | Current App (Reference) |
|------|-------------|--------------------------|
| **Secrets** | JWT secret and DB credentials from a secret store, not env defaults | JWT_SECRET from env; default dev value in code |
| **Transport** | All auth and API traffic over HTTPS only | Document recommends HTTPS in prod |
| **Password storage** | Strong hashing (e.g. Argon2), no plaintext | Argon2 via passlib ✅ |
| **Token handling** | Short-lived access tokens; optional refresh tokens; secure storage | JWT only; frontend uses localStorage |
| **Identity source** | Prefer managed identity (e.g. Google, OIDC) or hardened custom auth | Custom username/password in app DB |
| **Trust boundaries** | No trust of client-supplied user id without verification | X-User-Id from proxy; JWT sub used for API |
| **Rate limiting** | Login/register protected against brute force and abuse | Not implemented |
| **Audit** | Logging of auth events (login success/failure, registration) | Minimal |
| **User identity** | Unique, stable user IDs; safe handling of duplicate registration | DB SERIAL + username UNIQUE; race on register can 500 |

### 1.2 Gaps to Address for Production

- **Secrets**: Move `JWT_SECRET` (and DB URL if desired) to **Secret Manager**; never commit or use default dev secret.
- **HTTPS**: Enforce TLS at load balancer / Cloud Run; redirect HTTP → HTTPS.
- **Token storage**: Prefer httpOnly, Secure, SameSite cookies for tokens where possible, or ensure XSS mitigation if using localStorage.
- **Refresh flow**: Optional but recommended: short-lived access token + refresh token stored server-side or in a signed cookie.
- **Rate limiting**: Apply to `/auth/login` and `/auth/register` (e.g. per IP and per username).
- **User ID uniqueness**: Rely on DB `SERIAL` for `user_id`; treat **username** as the user-chosen identifier. Handle DB unique constraint on username (e.g. catch and return 409) so concurrent duplicate registration does not result in 500.
- **Audit**: Log auth outcomes (success/failure, user id, IP, timestamp) to Cloud Logging or a dedicated audit sink.

---

## 2. GCP-Native Authentication Options

### 2.1 Keep Custom Auth (Current Model) and Harden It

- **Where**: Continue username/password in your Postgres `users` table; JWT issued by your backend.
- **GCP pieces**:
  - **Secret Manager**: Store `JWT_SECRET` and optionally `DATABASE_URL`. Backend reads secrets at startup or via a thin cache.
  - **Cloud SQL**: Postgres for users and ADK data; use IAM database auth or strong passwords stored in Secret Manager.
  - **Cloud Run**: Service stays stateless; no code change to auth model, only config and secret injection.
- **Pros**: Full control; no dependency on external IdP.  
- **Cons**: You own password policy, account recovery, and abuse prevention.

### 2.2 Firebase Authentication / Identity Platform

- **Where**: Replace (or complement) custom login with Firebase Auth or **Identity Platform** (GCP’s enterprise offering).
- **Flow**: Frontend signs in with Google, email/link, or other providers; receives an ID token or custom token. Backend verifies the token (Firebase Admin SDK or JWT verification using Google’s public keys) and maps Firebase UID to your app’s `user_id` (e.g. in a `users` table).
- **GCP**: Identity Platform in the same project; optional integration with Cloud IAM for workforce identity.
- **Pros**: No password storage; social/SSO; built-in rate limiting and abuse controls; scales automatically.  
- **Cons**: Frontend and backend changes; dependency on Google’s IdP.

### 2.3 Identity-Aware Proxy (IAP)

- **Where**: Put **Cloud IAP** in front of your app (e.g. in front of the load balancer or BackendConfig for Cloud Run). Users sign in with Google (or another IdP you configure); IAP validates identity and passes verified user identity to the app (e.g. via headers).
- **Flow**: User → IAP (login) → Your service. Your backend trusts headers set by IAP (e.g. `X-Goog-Authenticated-User-*`) and does not issue its own JWTs for end users.
- **Pros**: No auth code in app; Google handles sign-in and MFA.  
- **Cons**: Tied to Google (or configured IdP) identities; less suitable for arbitrary “username” end users unless combined with another mechanism.

### 2.4 Hybrid: IAP for Admin + Custom or Identity Platform for End Users

- Use **IAP** for internal or admin UIs (Google identity).
- Use **custom JWT** or **Identity Platform** for end-user chat/app access, with your backend issuing or validating tokens and mapping to `user_id`.

### 2.5 Summary: Choosing an Option

| Scenario | Suggested direction |
|----------|----------------------|
| Minimal change, keep current auth | Harden with Secret Manager, HTTPS, rate limiting, and unique-username handling (no code change beyond config and small fixes). |
| Want Google/social login, no passwords | Identity Platform or Firebase Auth; backend verifies IdP token and maps to `user_id`. |
| Internal/admin only | IAP in front of the service; backend trusts IAP headers. |
| Mixed (admin + end users) | IAP for admin paths; custom or Identity Platform for end-user auth. |

---

## 3. Storing Secrets and Config in GCP

### 3.1 Secret Manager

- Create secrets for:
  - `JWT_SECRET`: Long random string (e.g. 256-bit) for signing JWTs.
  - Optionally: `DATABASE_URL` or Cloud SQL credentials.
- **Access**: Grant the Cloud Run service account `roles/secretmanager.secretAccessor` on the secret(s). At startup, backend fetches secrets (e.g. via Secret Manager API or a bootstrap script that writes env vars).
- **Rotation**: Rotate `JWT_SECRET` with a new version; deploy with new secret version. Use short token expiry during rotation so old JWTs expire quickly.

### 3.2 Environment and CORS

- Set non-secret config (e.g. `CORS_ORIGINS`, `APP_NAME`, `JWT_EXPIRE_MINUTES`) via Cloud Run environment variables or a config file from Cloud Storage.
- Never put production secrets in image or env in plain text; use Secret Manager and reference them as env (e.g. Cloud Run “secret as env”) or read in code.

---

## 4. Scaling Considerations

### 4.1 Stateless Auth (Current Design)

- JWTs are stateless: any instance can validate a token with the same `JWT_SECRET` and algorithm. No in-memory session store is required.
- **Scaling**: Run multiple Cloud Run instances behind a load balancer; no sticky session needed for auth. Ensure all instances get the same `JWT_SECRET` from Secret Manager.

### 4.2 Database Scaling

- **Connection pooling**: Use a pool (e.g. asyncpg pool) with a small max size per instance (e.g. 5–10). Cloud SQL has a max connections limit; `max_connections = instances × pool_size` must stay under that.
- **Cloud SQL Proxy**: Run Cloud SQL Auth Proxy sidecar or use PSC; keep DB off public IP.
- **Read replicas**: For read-heavy workloads (e.g. session list, history), use a read replica for reads; keep writes on the primary. Requires splitting read/write in the app.

### 4.3 Session and ADK State

- ADK session/state is stored in Postgres (or your current backend). That scales with the DB; ensure indexes on `(app_name, user_id)` and any lookup keys.
- No in-memory session store for auth is required if you stay JWT-only; optional refresh tokens can be stored in DB or in a signed cookie.

### 4.4 Rate Limiting and Abuse

- **Login/register**: Apply rate limits per IP and per username (e.g. 5 failed logins per 15 minutes per username). Options:
  - **Cloud Armor**: WAF and rate limiting at the load balancer (by IP and optionally by path).
  - **In-app**: Use a store (e.g. Redis/Memorystore, or Postgres with a small “throttle” table) to count attempts and reject over limit.
- **API**: Optional global or per-user rate limits for `/api/*` and `/ag-ui` to protect backend and Gemini usage.

### 4.5 Horizontal Scaling (Cloud Run)

- Cloud Run scales by request concurrency and CPU/memory. Set:
  - **Max instances** to cap cost and DB connections.
  - **Min instances** to reduce cold starts if needed.
  - **Concurrency** so that `instances × concurrency` aligns with your DB pool and Gemini quotas.
- Ensure **health check** (`/health`) is fast and does not hit the DB if possible.

### 4.6 User ID and Username Uniqueness

- **User ID**: Generated by the database (`SERIAL`). No two users share the same `user_id`; it is unique and stable. No application logic is required to “create” a unique user ID beyond inserting a row.
- **Username**: User-chosen; must be unique. The app enforces this with a UNIQUE constraint and a pre-insert check. Under concurrency, two requests with the same username can both pass the check; the second INSERT will fail with a unique constraint violation. For production, handle that exception and return a deterministic 409 (or 400) “Username already taken” instead of a 500 so clients and operators see consistent behavior.

---

## 5. Recommended Implementation Order (No Code Here)

1. **Secrets**: Move `JWT_SECRET` to Secret Manager; wire backend to read it at startup (or via Cloud Run “secret as env”).
2. **HTTPS**: Ensure Cloud Run and load balancer serve only HTTPS; set strict transport and correct CORS.
3. **Username race**: Handle DB unique constraint on username at register and return a clear 409/400.
4. **Rate limiting**: Add Cloud Armor or in-app rate limiting for `/auth/login` and `/auth/register`.
5. **Logging**: Emit structured logs for login/register success and failure (user id, IP, result) to Cloud Logging.
6. **Optional**: Refresh tokens and cookie-based token delivery; or integrate Identity Platform for social/login-without-password.
7. **Scaling**: Tune Cloud Run (max/min instances, concurrency) and DB pool size; add read replica if needed.

---

## 6. References

- [Secret Manager](https://cloud.google.com/secret-manager/docs)
- [Identity Platform](https://cloud.google.com/identity-platform/docs)
- [Identity-Aware Proxy](https://cloud.google.com/iap/docs)
- [Cloud Run scaling](https://cloud.google.com/run/docs/about-concurrency)
- [Cloud SQL connection limits and pooling](https://cloud.google.com/sql/docs/postgres/connect-instance-cloud-run#connection_pool)
- [Cloud Armor rate limiting](https://cloud.google.com/armor/docs/configure-rate-limiting-rules)
