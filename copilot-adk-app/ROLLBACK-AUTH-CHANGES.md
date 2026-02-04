# Rollback: Authentication / Register Changes

This document describes the code changes that were made and how to roll them back.

---

## Changes That Were Made

### 1. `backend/main.py`

**Import added**

- **Line 9**: `import asyncpg` was added so the register endpoint can catch `asyncpg.UniqueViolationError`.

**Register endpoint updated**

- **Lines 107–114** (approx.): The register flow was changed from a direct call to `create_user` to a try/except that catches unique constraint violations and returns HTTP 409.

**Before (original):**

```python
    existing = await get_user_by_username(username)
    if existing:
        raise HTTPException(status_code=400, detail="Username already taken")
    user = await create_user(username, hash_password(body.password))
    user_id = str(user["id"])
```

**After (current):**

```python
    existing = await get_user_by_username(username)
    if existing:
        raise HTTPException(status_code=400, detail="Username already taken")
    try:
        user = await create_user(username, hash_password(body.password))
    except asyncpg.UniqueViolationError:
        # Race: another request created this username between check and insert
        raise HTTPException(status_code=409, detail="Username already taken")
    user_id = str(user["id"])
```

No other files were modified (e.g. no changes to `AUTHENTICATION.md` or `db.py`).

---

## Rollback Steps

To revert to the state before these changes:

### Step 1: Revert the register endpoint in `backend/main.py`

Replace the current register block (with the try/except) with the original version:

- Remove the `try:` before `create_user(...)`.
- Remove the `except asyncpg.UniqueViolationError: ...` block (the 4 lines that raise 409).
- Leave a single direct call: `user = await create_user(username, hash_password(body.password))`.

So the register endpoint should again look like:

```python
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
```

### Step 2: Remove the asyncpg import from `backend/main.py`

- Delete the line: `import asyncpg` (line 9).
- Keep all other imports unchanged.

---

## After Rollback

- Duplicate username registration will again be enforced only by the “check then insert” and the DB unique constraint. Under concurrent requests with the same username, one may get a 500 (unhandled `UniqueViolationError`) instead of 409.
- No other behavior or docs were changed; rollback is limited to `backend/main.py` as above.

---

## Optional: Rollback via Git

If this work was committed:

```bash
cd copilot-adk-app
git log --oneline -5 backend/main.py   # find the commit that made the change
git checkout <previous-commit> -- backend/main.py
```

Or to revert the specific commit that introduced the auth/register change:

```bash
git revert <commit-hash> --no-edit
```
