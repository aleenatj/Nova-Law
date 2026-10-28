# Event-Driven Architecture Guide

## Overview

This guide explains how to use the event-driven architecture in the Nova Law AI application. The system uses a publish-subscribe pattern where events trigger handlers that can modify payloads and trigger additional events, allowing for complex workflows and loose coupling between components.

## Architecture Components

### 1. Event Types

Events are simple operations that can be triggered and may have subscribers. The current system uses a simplified approach where:

- **Events**: Represent specific operations or workflows
- **Subscribers**: Events that are automatically triggered after another event completes
- **Handlers**: Functions that process events and can modify payloads

### 2. Core Components

- **Enums** (`app/enums/events.py`): Define all event types
- **Config** (`app/config/events/events.py`): Map events to their subscribers
- **Handlers** (`app/events/subscribers/`): Implement business logic for events
- **Dispatcher** (`app/events/dispatcher.py`): Orchestrates event execution
- **Schemas** (`app/schemas/v1/event.py`): Define event data structures

## Setup Guide

### A. How to Setup Enums

#### Step 1: Add Event Types to Enum

Edit `backend/app/enums/events.py`:

```python
class EventType(str, Enum):
    """
    Enum representing event types in the Nova Law AI application.

    Each event corresponds to a specific system action or process.
    Events can be triggered directly or as part of an event chain.
    """

    PASSWORD_RESET_REQUESTED = "password_reset_requested"
    SEND_PASSWORD_RESET_EMAIL = "send_password_reset_email"
    USER_REGISTERED = "user_registered"
    SEND_WELCOME_EMAIL = "send_welcome_email"
    NOTIFY_ADMIN_NEW_USER = "notify_admin_new_user"
```

#### Step 2: Follow Naming Conventions

- Use descriptive, action-oriented names
- Use snake_case for consistency
- Make names clear about what the event does

### B. How to Setup Config

#### Step 1: Define Event Flow

Edit `backend/app/config/events/events.py`:

```python
EVENT_SUBSCRIPTIONS: dict[EventType, list[EventType]] = {
    # Password reset flow
    EventType.PASSWORD_RESET_REQUESTED: [
        EventType.SEND_PASSWORD_RESET_EMAIL,
    ],

    # User registration flow
    EventType.USER_REGISTERED: [
        EventType.SEND_WELCOME_EMAIL,
        EventType.NOTIFY_ADMIN_NEW_USER,
    ],
}
```

#### Step 2: Event Flow Patterns

- **Simple Chain**: One event triggers one or more subscribers
- **Recursive Chain**: Subscribers can trigger their own subscribers
- **Parallel Execution**: Multiple subscribers run concurrently

### C. Rules and Methods for Creating New Subscriber Functions

#### Step 1: Create Handler File

Create a new file in `backend/app/events/subscribers/` (group by entity):

```python
# backend/app/events/subscribers/user.py
"""
User-related event handlers.

This module contains event handlers for user-related events like registration,
password reset, profile updates, etc.
"""

import logging
from sqlalchemy.orm import Session

from app.core.email import email_service
from app.core.security import create_password_reset_token
from app.db.services.auth import get_user_by_email
from app.enums.events import EventType
from app.events.dispatcher import event
from app.schemas.v1.event import Event, EventResponseData
from app.utils.validators import validate_event_payload
from app.websocket.manager import WebSocketManager

logger = logging.getLogger(__name__)
```

#### Step 2: Create Event Handler

```python
@event(EventType.PASSWORD_RESET_REQUESTED)
async def handle_password_reset_requested(
    db: Session, event: Event, websocket_manager: WebSocketManager
) -> EventResponseData:
    """
    Handle password reset request: Generate token and reset link.

    This event handler processes the PASSWORD_RESET_REQUESTED event.
    It validates the request, generates a reset token, and prepares
    the payload for email sending.

    Args:
        db: Database session for queries
        event: The PASSWORD_RESET_REQUESTED event that triggered this handler
        websocket_manager: Manager for sending real-time notifications

    Returns:
        EventResponseData: Success/failure status with relevant data
    """
    try:
        payload = event.payload
        required_keys = [{"forgot_password_request": ["email"]}]
        validation = validate_event_payload(payload, required_keys)
        if not validation["status"]:
            logger.error(
                f"Payload validation failed for {event.event_type.value}: {validation}"
            )
            raise ValueError("Required keys not found in payload")

        # Check if user exists
        user = get_user_by_email(db, payload["forgot_password_request"].email)
        if not user:
            raise ValueError(
                f"User not found for email: {payload['forgot_password_request'].email}"
            )

        if user.status != "Active":
            raise ValueError(
                f"User is not active: {payload['forgot_password_request'].email}"
            )

        # Generate password reset token
        token = create_password_reset_token(data={"sub": str(user.id)})
        from app.core.config import settings
        reset_link = f"{settings.FRONTEND_URL}/reset-password?token={token}"

        # Modify event payload for subscribers
        event.payload["token"] = token
        event.payload["reset_link"] = reset_link
        event.payload["user_id"] = user.id
        event.payload["username"] = user.first_name + " " + user.last_name or "User"
        event.payload["email"] = user.email

        return EventResponseData(
            success=True,
            message="Password reset token generated successfully",
            data={"token": token, "reset_link": reset_link},
        )

    except Exception as e:
        logger.exception(f"Error in handle_password_reset_requested: {e}")
        raise
```

#### Step 3: Create Subscriber Event Handler

```python
@event(EventType.SEND_PASSWORD_RESET_EMAIL)
async def send_password_reset_email(
    db: Session, event: Event, websocket_manager: WebSocketManager
) -> EventResponseData:
    """
    Send password reset email to user with reset link.

    This event handler processes the SEND_PASSWORD_RESET_EMAIL event.
    It sends the actual email to the user using the payload prepared
    by the previous handler.

    Args:
        db: Database session for queries
        event: The SEND_PASSWORD_RESET_EMAIL event that triggered this handler
        websocket_manager: Manager for sending real-time notifications

    Returns:
        EventResponseData: Success/failure status
    """
    try:
        payload = event.payload
        required_keys = ["email", "reset_link"]
        validation = validate_event_payload(payload, required_keys)
        if not validation["status"]:
            raise ValueError("Email or reset link not found in payload")

        email = payload.get("email", "No email found")
        username = payload.get("username", "")
        reset_link = payload.get("reset_link", "No reset link found")

        # Send password reset email
        await email_service.send_email(
            to_email=email,
            template=email_service.EmailTemplate.PASSWORD_RESET,
            context={
                "username": username,
                "reset_link": reset_link,
                "header_subtitle": "Password Reset Request",
            },
        )

        return EventResponseData(
            success=True, message="Password reset email sent.", data={}
        )
    except Exception as e:
        logger.exception(f"Error in send_password_reset_email: {e}")
        raise
```

#### Step 4: Handler Rules and Best Practices

1. **Function Signature**: Always use this signature:
   ```python
   async def handler_name(db: Session, event: Event, websocket_manager: WebSocketManager) -> EventResponseData:
   ```

2. **Decorator**: Always use the `@event(EventType.EVENT_NAME)` decorator

3. **Error Handling**: Always wrap in try-catch and log errors:
   ```python
   try:
       # Your logic here
   except Exception as e:
       logger.exception(f"Error in handler_name: {e}")
       raise
   ```

4. **Logging**: Log important steps and errors

5. **Data Validation**: Always validate event payload data using `validate_event_payload`

6. **Payload Modification**: Handlers can modify `event.payload` to pass data to subscribers

7. **Return Values**: Always return `EventResponseData` with success status and relevant data

8. **WebSocket Integration**: Check if websocket_manager is available:
   ```python
   if websocket_manager:
       await websocket_manager.broadcast_to_role("admin", notification_data, db)
   else:
       logger.warning("WebSocket manager not available")
   ```

### D. Dispatch Events from APIs/Events

#### Method 1: Dispatch from API Endpoints

```python
# backend/app/api/v1/auth.py
from app.events.dispatcher import event_dispatcher
from app.schemas.v1.event import Event
from app.enums.events import EventType
from app.utils.helpers import extract_status_messages

@router.post("/forgot-password")
async def forgot_password(
    request: ForgotPasswordRequest, db: Session = Depends(get_db)
) -> dict:
    """Handle forgot password request."""

    # Validate user exists and is active
    user = db.query(User).filter(User.email == request.email).first()
    if not user or user.status != UserStatus.ACTIVE:
        raise HTTPException(
            status_code=400, detail="Email is not registered."
        )

    # Create event data
    event_data = Event(
        event_type=EventType.PASSWORD_RESET_REQUESTED,
        payload={
            "forgot_password_request": {
                "email": user.email,
            },
        },
        user_id=user.id,
    )

    # Dispatch the event
    await event_dispatcher.dispatch_event(db, event_data)

    # Extract status messages from event responses
    success, messages = extract_status_messages(event_data.response)
    if not success:
        raise HTTPException(status_code=400, detail=messages)

    return {
        "status": 200,
        "message": "Password reset link has been sent to your email.",
        "data": []
    }
```

#### Method 2: Dispatch Methods Available

The EventDispatcher provides three different dispatch methods, each optimized for different use cases:

##### `dispatch_event()` - **Fully Parallel Execution**

**Key Characteristics:**
- ✅ **Main event runs first**
- ✅ **All subscribers run in parallel** (using `asyncio.create_task()`)
- ✅ **Recursive subscribers also run in parallel**
- ✅ **Fastest execution time**
- ❌ **No guaranteed order**
- ❌ **All events run regardless of failures**

**Example Flow:**
```
EVENT_A (main)
├── EVENT_B (parallel with C)
│   ├── EVENT_D (parallel with E)
│   └── EVENT_E (parallel with D)
└── EVENT_C (parallel with B)
    ├── EVENT_F (parallel with G)
    └── EVENT_G (parallel with F)
```

**When to Use:**
- ✅ **Performance is critical**
- ✅ **Events are independent**
- ✅ **Order doesn't matter**
- ✅ **All events should run regardless of failures**

**Code Example:**
```python
# All notifications sent simultaneously
await event_dispatcher.dispatch_event(db, event_data)
# EVENT_B, EVENT_C, EVENT_D, EVENT_E all start at roughly the same time
# Total time: ~2 seconds (fastest)
```

##### `dispatch_event_sync()` - **Fully Sequential Execution**

**Key Characteristics:**
- ✅ **Main event runs first**
- ❌ **Subscribers run one by one** (sequential)
- ❌ **Recursive subscribers also run sequentially**
- ❌ **Slowest execution time**
- ✅ **Guaranteed order**
- ❌ **Stops on first failure**

**Example Flow:**
```
EVENT_A (main)
├── EVENT_B (runs first)
│   ├── EVENT_D (runs first)
│   └── EVENT_E (runs second)
└── EVENT_C (runs second)
    ├── EVENT_F (runs first)
    └── EVENT_G (runs second)
```

**When to Use:**
- ✅ **Order is critical**
- ✅ **Events depend on each other**
- ✅ **You need predictable execution**
- ❌ **Performance is not critical**

**Code Example:**
```python
# Notifications sent one by one
await event_dispatcher.dispatch_event_sync(db, event_data)
# EVENT_B → EVENT_D → EVENT_E → EVENT_C → EVENT_F → EVENT_G
# Total time: ~5 seconds (slowest)
```

##### `dispatch_event_ordered()` - **Sequential with Early Stopping**

**Key Characteristics:**
- ✅ **Main event runs first**
- ❌ **Subscribers run one by one** (sequential)
- ❌ **Recursive subscribers also run sequentially**
- ❌ **Slower execution time**
- ✅ **Guaranteed order**
- ✅ **Configurable early stopping on failure**

**Example Flow:**
```
EVENT_A (main)
├── EVENT_B (runs first)
│   ├── EVENT_D (runs first)
│   └── EVENT_E (runs second, if D succeeds)
└── EVENT_C (runs second, if B succeeds)
    ├── EVENT_F (runs first)
    └── EVENT_G (runs second, if F succeeds)
```

**When to Use:**
- ✅ **Order is critical**
- ✅ **You need early failure detection**
- ✅ **Some events depend on others**
- ✅ **You want safety with some performance**

**Code Example:**
```python
# Sequential with early stopping
await event_dispatcher.dispatch_event_ordered(db, event_data, stop_on_failure=True)
# If EVENT_B fails, EVENT_C, EVENT_D, EVENT_E never run
# Total time: ~3 seconds (with safety)
```

##### Performance Comparison Example

For a typical user registration flow:
```python
EVENT_A: User registers
├── EVENT_B: Send welcome email (2s)
├── EVENT_C: Send SMS verification (1s)
├── EVENT_D: Create user profile (1s)
└── EVENT_E: Send admin notification (1s)
```

**Timing Results:**
- `dispatch_event()`: ~2 seconds (all run in parallel)
- `dispatch_event_sync()`: ~5 seconds (sequential: 2 + 1 + 1 + 1)
- `dispatch_event_ordered()`: ~5 seconds (same as sync, but with safety)

**Real-World Use Cases:**

1. **Use `dispatch_event()` for:**
   - User registration notifications
   - Marketing email campaigns
   - Analytics data collection
   - Logging and monitoring events

2. **Use `dispatch_event_sync()` for:**
   - Payment processing workflows
   - Order fulfillment chains
   - Data validation sequences
   - Multi-step approval processes

3. **Use `dispatch_event_ordered()` for:**
   - Critical business workflows
   - Financial transactions
   - User authentication flows
   - Any process where early failure detection is important

#### Method 3: Processing Event Responses

After dispatching events, always process the responses using `extract_status_messages`:

```python
# Dispatch events
await event_dispatcher.dispatch_event(db, event_data)

# Process responses
success, messages = extract_status_messages(event_data.response)

# Handle based on success status
if success:
    # All events succeeded or at least one succeeded
    return {"status": 200, "message": messages, "data": []}
else:
    # All events failed
    raise HTTPException(status_code=400, detail=messages)
```

## Examples

### Example 1: Simple Event Chain

```python
# Enum
PASSWORD_RESET_REQUESTED = "password_reset_requested"
SEND_PASSWORD_RESET_EMAIL = "send_password_reset_email"

# Config
EventType.PASSWORD_RESET_REQUESTED: [
    EventType.SEND_PASSWORD_RESET_EMAIL,
],

# Handlers
@event(EventType.PASSWORD_RESET_REQUESTED)
async def handle_password_reset_requested(db: Session, event: Event, websocket_manager: WebSocketManager) -> EventResponseData:
    # Generate token and modify payload
    pass

@event(EventType.SEND_PASSWORD_RESET_EMAIL)
async def send_password_reset_email(db: Session, event: Event, websocket_manager: WebSocketManager) -> EventResponseData:
    # Send email using payload from previous handler
    pass
```

### Example 2: Multiple Subscribers

```python
# Enum
USER_REGISTERED = "user_registered"
SEND_WELCOME_EMAIL = "send_welcome_email"
NOTIFY_ADMIN_NEW_USER = "notify_admin_new_user"

# Config
EventType.USER_REGISTERED: [
    EventType.SEND_WELCOME_EMAIL,
    EventType.NOTIFY_ADMIN_NEW_USER,
],

# Handlers run in parallel
@event(EventType.SEND_WELCOME_EMAIL)
async def send_welcome_email(db: Session, event: Event, websocket_manager: WebSocketManager) -> EventResponseData:
    # Send welcome email
    pass

@event(EventType.NOTIFY_ADMIN_NEW_USER)
async def notify_admin_new_user(db: Session, event: Event, websocket_manager: WebSocketManager) -> EventResponseData:
    # Notify admin
    pass
```

### Example 3: Complex Workflow with Recursive Subscribers

```python
# Enum
USER_REGISTERED = "user_registered"
PROCESS_USER_REGISTRATION = "process_user_registration"
SEND_WELCOME_EMAIL = "send_welcome_email"
NOTIFY_ADMIN_NEW_USER = "notify_admin_new_user"
CREATE_USER_PROFILE = "create_user_profile"
SEND_VERIFICATION_EMAIL = "send_verification_email"

# Config
EVENT_SUBSCRIPTIONS = {
    EventType.USER_REGISTERED: [
        EventType.PROCESS_USER_REGISTRATION,
    ],
    EventType.PROCESS_USER_REGISTRATION: [
        EventType.SEND_WELCOME_EMAIL,
        EventType.NOTIFY_ADMIN_NEW_USER,
        EventType.CREATE_USER_PROFILE,
    ],
    EventType.CREATE_USER_PROFILE: [
        EventType.SEND_VERIFICATION_EMAIL,
    ],
}
```

## Event Data Structure

### Event Schema

```python
class Event(BaseModel):
    event_type: EventType
    payload: dict[str, Any]
    response: dict[str, EventResponseData] | None = {}
    user_id: int | None = None
```

### EventResponseData Schema

```python
class EventResponseData(BaseModel):
    success: bool
    message: str
    data: Any
```

### Processing Event Responses

After dispatching events, you need to process the responses to extract status messages and determine overall success. Use the `extract_status_messages` utility function:

```python
from app.utils.helpers import extract_status_messages

# After dispatching events
await event_dispatcher.dispatch_event(db, event_data)

# Extract status messages from event responses
success, messages = extract_status_messages(event_data.response)

# Check overall success
if not success:
    # Handle failure - messages contains list of error messages
    raise HTTPException(status_code=400, detail=messages)

# Handle success - messages contains list of success messages
return {"status": 200, "message": messages, "data": []}
```

The `extract_status_messages` function:
- Takes a dictionary of `EventResponseData` objects
- Returns a tuple of `(success: bool, messages: list[dict[str, str]])`
- `success` is `True` if any event succeeded, `False` if all failed
- `messages` contains a list of dictionaries with `{"success": bool, "message": str}` for each event

## Troubleshooting

### Common Issues

1. **Handler Not Found**: Ensure the `@event` decorator is used and the enum exists
2. **Event Not Triggered**: Check the config mapping is correct
3. **Missing Data**: Validate event payload in handlers
4. **WebSocket Errors**: Check if websocket_manager is available

### Debugging

1. **Check Logs**: All events and errors are logged
2. **Event Response**: Check `event.response` for handler results
3. **Payload Validation**: Use `validate_event_payload` for data validation
4. **Response Processing**: Use `extract_status_messages` to process event responses

## Best Practices

1. **Event Naming**: Use clear, descriptive names
2. **Handler Organization**: Group handlers by entity/domain
3. **Error Handling**: Always handle exceptions and log errors
4. **Data Validation**: Validate all event payload data
5. **Logging**: Log important steps and errors
6. **Testing**: Test event flows thoroughly
7. **Documentation**: Document complex event flows
8. **Payload Modification**: Use payload modification to pass data between handlers
9. **Response Data**: Always return meaningful `EventResponseData`
10. **Response Processing**: Always use `extract_status_messages` to process event responses

## Configuration Utilities

The event configuration module provides several utility functions:

```python
from app.config.events.events import (
    get_subscribers_for_event,
    get_events_for_subscriber,
    get_all_business_events,
    get_all_subscriber_events,
    validate_event_configuration,
)

# Get subscribers for an event
subscribers = get_subscribers_for_event(EventType.PASSWORD_RESET_REQUESTED)

# Get events that trigger a subscriber
triggers = get_events_for_subscriber(EventType.SEND_PASSWORD_RESET_EMAIL)

# Get all events that have subscribers
business_events = get_all_business_events()

# Get all events used as subscribers
subscriber_events = get_all_subscriber_events()

# Validate configuration
is_valid = validate_event_configuration()
```

This architecture provides a flexible, scalable, and maintainable event-driven system that can evolve with your application's needs.
