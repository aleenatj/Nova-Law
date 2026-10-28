# Enum Organization Guide

## Overview

This guide outlines the best practices for organizing enums in the Nova Law AI application. Proper enum organization improves code maintainability, readability, and scalability.

## Current Implementation

We have organized enums by **domain/feature** rather than putting all enums in one file. This approach provides better separation of concerns and makes the codebase more maintainable.

## Directory Structure

```
backend/app/enums/
├── __init__.py          # Main exports and organization
├── auth.py              # Authentication and authorization enums
├── chat.py              # Chat and messaging enums
├── agents.py            # AI agent related enums
├── errors.py            # Error and logging enums
└── system.py            # System and API enums
```

## Best Practices

### 1. **Domain-Specific Organization (Recommended)**

**Why this approach:**
- ✅ **Better separation of concerns** - Related enums are grouped together
- ✅ **Easier to find and maintain** - Developers know where to look for specific enums
- ✅ **Reduced merge conflicts** - Changes to different domains don't conflict
- ✅ **Better scalability** - Easy to add new domains without cluttering existing files
- ✅ **Clear dependencies** - Import only what you need
- ✅ **Type safety** - Better IDE support and type checking

**Example structure:**
```python
# backend/app/enums/auth.py
class UserRole(str, Enum):
    ADMIN = "admin"
    LAWYER = "lawyer"
    CLIENT = "client"

class Permission(str, Enum):
    USER_READ = "user:read"
    USER_CREATE = "user:create"
    # ... more permissions
```

### 2. **Import Strategy**

**Centralized imports through `__init__.py`:**
```python
# backend/app/enums/__init__.py
from .auth import UserRole, Permission
from .chat import ChatStatus, MessageType
from .agents import AgentType
from .errors import ErrorCode, ErrorSeverity, ErrorCategory
from .system import APIVersion

__all__ = [
    "UserRole", "Permission",
    "ChatStatus", "MessageType",
    "AgentType",
    "ErrorCode", "ErrorSeverity", "ErrorCategory",
    "APIVersion",
]
```

**Usage in other files:**
```python
# Clean, organized imports
from app.enums import UserRole, ChatStatus, AgentType
```

### 3. **Enum Design Guidelines**

**Use `str` enums for API responses:**
```python
class UserRole(str, Enum):
    ADMIN = "admin"
    LAWYER = "lawyer"
    CLIENT = "client"
```

**Add comprehensive docstrings:**
```python
class ChatStatus(str, Enum):
    """Chat session statuses for tracking conversation state."""

    ACTIVE = "active"      # Session is currently active
    CLOSED = "closed"      # Session has been closed by user
    ARCHIVED = "archived"  # Session archived for long-term storage
    PENDING = "pending"    # Session waiting for user input
```

**Group related values with comments:**
```python
class ErrorCode(str, Enum):
    """Application error codes for consistent error handling."""

    # Authentication errors
    INVALID_CREDENTIALS = "INVALID_CREDENTIALS"
    TOKEN_EXPIRED = "TOKEN_EXPIRED"

    # Validation errors
    INVALID_INPUT = "INVALID_INPUT"
    MISSING_REQUIRED_FIELD = "MISSING_REQUIRED_FIELD"

    # Resource errors
    RESOURCE_NOT_FOUND = "RESOURCE_NOT_FOUND"
    RESOURCE_ALREADY_EXISTS = "RESOURCE_ALREADY_EXISTS"
```

### 4. **Alternative Approaches (Not Recommended)**

#### ❌ **Single File Approach**
```python
# backend/app/enums.py - NOT RECOMMENDED
class UserRole(str, Enum): ...
class ChatStatus(str, Enum): ...
class AgentType(str, Enum): ...
class ErrorCode(str, Enum): ...
# ... 20+ enums in one file
```

**Problems:**
- 🚫 **Hard to maintain** - Large files become unwieldy
- 🚫 **Merge conflicts** - Multiple developers editing same file
- 🚫 **Poor discoverability** - Hard to find specific enums
- 🚫 **Violates single responsibility principle**

#### ❌ **Scattered Approach**
```python
# Enums scattered across different modules
# backend/app/models/user.py
class UserRole(str, Enum): ...

# backend/app/models/chat.py
class ChatStatus(str, Enum): ...

# backend/app/utils/constants.py
class ErrorCode(str, Enum): ...
```

**Problems:**
- 🚫 **Inconsistent organization** - No clear pattern
- 🚫 **Import complexity** - Need to know which file has which enum
- 🚫 **Circular imports** - Risk of import cycles
- 🚫 **Poor reusability** - Enums tied to specific modules

### 5. **Migration Strategy**

When migrating existing enums:

1. **Create the new structure:**
   ```bash
   mkdir -p backend/app/enums
   touch backend/app/enums/__init__.py
   ```

2. **Move enums by domain:**
   ```python
   # Move UserRole, Permission to auth.py
   # Move ChatStatus, MessageType to chat.py
   # etc.
   ```

3. **Update imports gradually:**
   ```python
   # Old
   from app.utils.constants import UserRole

   # New
   from app.enums import UserRole
   ```

4. **Remove old enum definitions** after all imports are updated

### 6. **Testing Strategy**

**Test enum values:**
```python
def test_user_role_values():
    """Test that UserRole enum has expected values."""
    assert UserRole.ADMIN == "admin"
    assert UserRole.LAWYER == "lawyer"
    assert UserRole.CLIENT == "client"
    assert UserRole.ASSISTANT == "assistant"

def test_user_role_membership():
    """Test enum membership validation."""
    assert "admin" in [role.value for role in UserRole]
    assert "invalid_role" not in [role.value for role in UserRole]
```

**Test enum imports:**
```python
def test_enum_imports():
    """Test that all enums can be imported correctly."""
    from app.enums import (
        UserRole, ChatStatus, MessageType,
        AgentType, ErrorCode, APIVersion
    )
    assert all([UserRole, ChatStatus, MessageType, AgentType, ErrorCode, APIVersion])
```

### 7. **Performance Considerations**

**Enum lookup performance:**
- ✅ **Fast** - O(1) lookup time
- ✅ **Memory efficient** - Single instance per value
- ✅ **Type safe** - Compile-time validation

**Import performance:**
- ✅ **Lazy loading** - Only import what you use
- ✅ **No circular dependencies** - Clean import structure

### 8. **Future Considerations**

**Adding new enums:**
1. Determine the appropriate domain file
2. Add the enum with proper documentation
3. Update `__init__.py` exports
4. Add tests for the new enum

**Example adding a new enum:**
```python
# backend/app/enums/chat.py
class MessagePriority(str, Enum):
    """Message priority levels for chat system."""

    LOW = "low"
    NORMAL = "normal"
    HIGH = "high"
    URGENT = "urgent"
```

**Update exports:**
```python
# backend/app/enums/__init__.py
from .chat import ChatStatus, MessageType, MessagePriority

__all__ = [
    # ... existing exports
    "MessagePriority",
]
```

## Summary

The **domain-specific organization** approach is the recommended best practice because it:

- ✅ **Improves maintainability** - Related enums are grouped together
- ✅ **Enhances discoverability** - Easy to find specific enums
- ✅ **Reduces conflicts** - Different domains can be developed independently
- ✅ **Scales well** - Easy to add new domains without affecting existing code
- ✅ **Follows Python best practices** - Clean imports and proper separation of concerns

This approach aligns with the existing project architecture and provides a solid foundation for future growth.
