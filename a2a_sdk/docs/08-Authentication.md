# A2A-SDK Authentication Package Documentation

**File Path**: `docs-a2a-sdk/08-Authentication.md`  
**Package**: `a2a.auth`, `a2a.client.auth`

## Overview

The A2A SDK provides comprehensive authentication and credential management for securing agent communications.

## Key Classes

### User

Represents an authenticated user.

**Location**: `a2a.auth.user`

**Usage**:
```python
from a2a.auth.user import User

user = User(user_id="user_123")
```

### UnauthenticatedUser

Represents an unauthenticated user.

**Location**: `a2a.auth.user`

**Usage**:
```python
from a2a.auth.user import UnauthenticatedUser

user = UnauthenticatedUser()
```

### CredentialService

Manages credentials for client authentication.

**Location**: `a2a.client.auth.credentials`

**Usage**:
```python
from a2a.client.auth.credentials import CredentialService, InMemoryContextCredentialStore

credential_store = InMemoryContextCredentialStore()
credential_service = CredentialService(credential_store)
```

### InMemoryContextCredentialStore

In-memory credential storage.

**Location**: `a2a.client.auth.credentials`

**Key Methods**:
- `get_credential()` - Retrieve credential
- `store_credential()` - Store credential

### AuthInterceptor

Intercepts requests to add authentication.

**Location**: `a2a.client.auth.interceptor`

**Usage**:
```python
from a2a.client.auth.interceptor import AuthInterceptor

interceptor = AuthInterceptor(credential_service)
```

## Example 1: Basic Authentication

```python
#!/usr/bin/env python3
"""Basic authentication example."""

from a2a.client import Client, ClientConfig
from a2a.client.transports.rest import RestTransport
from a2a.client.auth.credentials import CredentialService, InMemoryContextCredentialStore
from a2a.client.middleware import ClientCallContext
from a2a.types import Message

# Create credential store
credential_store = InMemoryContextCredentialStore()

# Store credentials
credential_store.store_credential(
    session_id="session_123",
    security_scheme_name="api_key",
    credential="your-api-key-here"
)

# Create credential service
credential_service = CredentialService(credential_store)

# Create client with authentication
config = ClientConfig(
    transport=RestTransport(base_url="http://localhost:8000"),
    credential_service=credential_service
)
client = Client(config)

# Create context with session ID
context = ClientCallContext(session_id="session_123")

# Send authenticated message
message = Message(role="user", content=[{"text": "Hello"}])
async for event in client.send_message(message, context=context):
    print(event)
```

## Example 2: Multiple Security Schemes

```python
#!/usr/bin/env python3
"""Multiple security schemes example."""

from a2a.client.auth.credentials import InMemoryContextCredentialStore

credential_store = InMemoryContextCredentialStore()

# Store multiple credentials
credential_store.store_credential(
    session_id="session_123",
    security_scheme_name="api_key",
    credential="api-key-123"
)

credential_store.store_credential(
    session_id="session_123",
    security_scheme_name="bearer_token",
    credential="bearer-token-456"
)

# Retrieve credentials
api_key = credential_store.get_credential(
    security_scheme_name="api_key",
    context=ClientCallContext(session_id="session_123")
)

bearer_token = credential_store.get_credential(
    security_scheme_name="bearer_token",
    context=ClientCallContext(session_id="session_123")
)
```

## Example 3: Server-Side Authentication

```python
#!/usr/bin/env python3
"""Server-side authentication example."""

from a2a.server.context import ServerCallContext
from a2a.auth.user import User, UnauthenticatedUser

# Create authenticated context
authenticated_context = ServerCallContext(
    user=User(user_id="user_123"),
    state={"authenticated": True}
)

# Create unauthenticated context
unauthenticated_context = ServerCallContext(
    user=UnauthenticatedUser(),
    state={"authenticated": False}
)

# Check authentication
if authenticated_context.user and not isinstance(authenticated_context.user, UnauthenticatedUser):
    print("User is authenticated")
    print(f"User ID: {authenticated_context.user.user_id}")
```

## Example 4: Custom Credential Store

```python
#!/usr/bin/env python3
"""Custom credential store example."""

from a2a.client.auth.credentials import CredentialService
from a2a.client.middleware import ClientCallContext
import os

class EnvironmentCredentialStore:
    """Credential store using environment variables."""
    
    def get_credential(self, security_scheme_name: str, context: ClientCallContext = None) -> str:
        """Get credential from environment."""
        env_key = f"A2A_{security_scheme_name.upper()}"
        return os.getenv(env_key)
    
    def store_credential(self, session_id: str, security_scheme_name: str, credential: str):
        """Store credential in environment (read-only in practice)."""
        # In practice, this would be read-only
        pass

# Use custom credential store
credential_store = EnvironmentCredentialStore()
credential_service = CredentialService(credential_store)

# Get credential from environment
credential = credential_store.get_credential(
    security_scheme_name="api_key",
    context=ClientCallContext()
)
```

## Security Schemes

### API Key

```python
credential_store.store_credential(
    session_id="session_123",
    security_scheme_name="api_key",
    credential="your-api-key"
)
```

### Bearer Token

```python
credential_store.store_credential(
    session_id="session_123",
    security_scheme_name="bearer_token",
    credential="your-bearer-token"
)
```

## Best Practices

1. **Store Credentials Securely**
   ```python
   # ✅ GOOD: Use secure storage
   credential_store = DatabaseCredentialStore(...)  # Encrypted
   
   # ❌ BAD: Hardcode credentials
   credential = "hardcoded-key"  # Never do this
   ```

2. **Use Session-Based Credentials**
   ```python
   # ✅ GOOD: Store per session
   credential_store.store_credential(
       session_id="session_123",
       security_scheme_name="api_key",
       credential="key"
   )
   ```

3. **Validate Authentication**
   ```python
   # ✅ GOOD: Check authentication
   if context.user and not isinstance(context.user, UnauthenticatedUser):
       # Process authenticated request
       pass
   ```

## Comparison with ADK

| Feature | ADK | A2A SDK Auth |
|--------|-----|--------------|
| **User Types** | Built-in | `User`, `UnauthenticatedUser` |
| **Credential Storage** | Built-in | `CredentialStore` interface |
| **Authentication** | Built-in | `CredentialService` |
| **Interceptors** | Built-in | `AuthInterceptor` |

## Related Documentation

- [Client Package](02-Client-Package.md) - Client usage
- [Server Package](03-Server-Package.md) - Server implementation
- [Context and Memory](04-Context-and-Memory.md) - Context management

---

**Last Updated:** February 2, 2026  
**A2A-SDK Version:** 0.3.22
