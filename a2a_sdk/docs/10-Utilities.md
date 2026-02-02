# A2A-SDK Utilities Package Documentation

**File Path**: `docs-a2a-sdk/10-Utilities.md`  
**Package**: `a2a.utils`

## Overview

The `a2a.utils` package provides utility functions and helpers for common operations in A2A SDK.

## Key Modules

### Message Utilities

**Location**: `a2a.utils.message`

**Functions**: 3 functions

**Usage**:
```python
from a2a.utils.message import (
    # Message utility functions
)
```

### Artifact Utilities

**Location**: `a2a.utils.artifact`

**Functions**: 4 functions

**Usage**:
```python
from a2a.utils.artifact import (
    # Artifact utility functions
)
```

### Protocol Buffer Utilities

**Location**: `a2a.utils.proto_utils`

**Key Classes**:
- `FromProto` - Convert from protocol buffers (33 methods)
- `ToProto` - Convert to protocol buffers (30 methods)

**Functions**: 4 functions

**Usage**:
```python
from a2a.utils.proto_utils import FromProto, ToProto

# Convert from proto
from_proto = FromProto()
result = from_proto.convert(proto_message)

# Convert to proto
to_proto = ToProto()
proto_message = to_proto.convert(python_object)
```

### Error Utilities

**Location**: `a2a.utils.errors`

**Key Classes**:
- `A2AServerError` - Base server error
- `MethodNotImplementedError` - Method not implemented
- `ServerError` - General server error (3 methods)

**Usage**:
```python
from a2a.utils.errors import A2AServerError, MethodNotImplementedError

try:
    # Code that may raise errors
    pass
except MethodNotImplementedError as e:
    print(f"Method not implemented: {e}")
except A2AServerError as e:
    print(f"Server error: {e}")
```

### Helper Functions

**Location**: `a2a.utils.helpers`

**Functions**: 7 functions

**Usage**:
```python
from a2a.utils.helpers import (
    # Helper functions
)
```

### Task Utilities

**Location**: `a2a.utils.task`

**Functions**: 3 functions

**Usage**:
```python
from a2a.utils.task import (
    # Task utility functions
)
```

### Telemetry Utilities

**Location**: `a2a.utils.telemetry`

**Functions**: 2 functions

**Usage**:
```python
from a2a.utils.telemetry import (
    # Telemetry functions
)
```

### Message Parts Utilities

**Location**: `a2a.utils.parts`

**Functions**: 3 functions

**Usage**:
```python
from a2a.utils.parts import (
    # Message parts utilities
)
```

### Error Handlers

**Location**: `a2a.utils.error_handlers`

**Functions**: 2 functions

**Usage**:
```python
from a2a.utils.error_handlers import (
    # Error handler functions
)
```

### Signing Utilities (Optional)

**Location**: `a2a.utils.signing`

**Requires**: `pip install "a2a-sdk[signing]"`

**Usage**:
```python
from a2a.utils.signing import (
    # Signing utilities (JWT)
)
```

## Example: Using Utilities

```python
#!/usr/bin/env python3
"""Using A2A SDK utilities."""

from a2a.utils.errors import A2AServerError, MethodNotImplementedError
from a2a.utils.proto_utils import FromProto, ToProto

# Error handling
try:
    # Some operation
    raise MethodNotImplementedError("This method is not implemented")
except MethodNotImplementedError as e:
    print(f"Error: {e}")

# Protocol buffer conversion
from_proto = FromProto()
to_proto = ToProto()

# Convert from proto
# python_obj = from_proto.convert(proto_message)

# Convert to proto
# proto_msg = to_proto.convert(python_obj)
```

## Best Practices

1. **Use Error Utilities**
   ```python
   # ✅ GOOD: Use specific error types
   raise MethodNotImplementedError("Method not implemented")
   ```

2. **Use Protocol Buffer Utilities**
   ```python
   # ✅ GOOD: Use conversion utilities
   from_proto = FromProto()
   result = from_proto.convert(proto_message)
   ```

## Related Documentation

- [Package Structure](01-Package-Structure.md) - Package overview
- [Server Package](03-Server-Package.md) - Server implementation

---

**Last Updated:** February 2, 2026  
**A2A-SDK Version:** 0.3.22
