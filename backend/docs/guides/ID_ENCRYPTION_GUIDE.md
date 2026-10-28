# ID Encryption System Guide

This project implements automatic ID encryption/decryption for all primary key IDs to enhance security.

## Overview

- **Encryption**: All IDs are automatically encrypted when sent in API responses
- **Decryption**: All encrypted IDs are automatically decrypted when received in API requests
- **Error Handling**: Invalid IDs return `None` instead of raising exceptions

## Environment Setup

Add the encryption key to your environment variables:

```bash
export ENCRYPTION_SECRET_KEY="your-secure-encryption-key-here"
```

For production, use a strong, randomly generated key.

## How It Works

### 1. Response Models

All response models inherit from `EncryptedResponse` which automatically encrypts:
- `id` fields
- Any field ending with `_id` (e.g., `user_id`, `session_id`)

```python
from app.schemas.user import UserResponse

# The ID will be automatically encrypted in the response
response = UserResponse(
    id="user-uuid-123",  # This becomes encrypted in the response
    email="user@example.com",
    full_name="John Doe"
)
```

### 2. API Route Parameters

Use dependency functions to automatically decrypt IDs in route parameters:

```python
from app.utils.dependencies import get_decrypted_user_id, get_decrypted_session_id

@router.get("/users/{user_id}")
async def get_user(user_id: str = Depends(get_decrypted_user_id)):
    # user_id is already decrypted here
    pass

@router.get("/chat/sessions/{session_id}/messages")
async def get_messages(session_id: str = Depends(get_decrypted_session_id)):
    # session_id is already decrypted here
    pass
```

### 3. Request Body IDs

For request bodies, use the `__init__` method in request schemas:

```python
class ChatRequest(BaseModel):
    message: str
    session_id: Optional[str] = None

    def __init__(self, **data):
        super().__init__(**data)
        if self.session_id:
            from app.utils.encryption import decrypt_id
            decrypted_id = decrypt_id(self.session_id)
            if decrypted_id is None:
                raise ValueError("Invalid session ID")
            self.session_id = decrypted_id
```

### 4. Manual Encryption/Decryption

For custom cases, use the utility functions directly:

```python
from app.utils.encryption import encrypt_id, decrypt_id

# Encrypt an ID
encrypted = encrypt_id("user-uuid-123")

# Decrypt an ID
decrypted = decrypt_id(encrypted)  # Returns "user-uuid-123" or None if invalid
```

## Available Dependency Functions

- `get_decrypted_user_id()` - For user IDs
- `get_decrypted_session_id()` - For session IDs
- `get_decrypted_message_id()` - For message IDs

## Error Handling

- Invalid encrypted IDs return `None` from `decrypt_id()`
- Dependency functions raise `HTTPException(400)` for invalid IDs
- Request schema validation raises `ValueError` for invalid IDs

## Security Notes

- Never log or expose raw database IDs
- Always use encrypted IDs in URLs and responses
- The encryption key should be kept secure and rotated regularly
- IDs are encrypted using Fernet (symmetric encryption)

## Testing

Test the encryption system:

```python
from app.utils.encryption import encrypt_id, decrypt_id

test_id = "test-uuid-123"
encrypted = encrypt_id(test_id)
decrypted = decrypt_id(encrypted)
assert test_id == decrypted  # Should be True
```
