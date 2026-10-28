# API Endpoint Generation Template

You are my coding assistant. I want you to generate all required files for a new API model in my project.

## Project Standards

- **Framework**: FastAPI
- **API Version**: v1
- **File Structure**:
  - API Handler: `app/api/v1/{module}.py`
  - Business Logic: `app/db/services/{module}.py`
  - Schemas: `app/schemas/v1/{model}.py`
  - Permissions: `app/config/permissions/role_permission.py`
  - Router Registration: update `app/api/v1/__init__.py` (or `main.py`) to include new router

## Inputs I Will Provide

- Model name (PascalCase, e.g., `LawFirm`)
- Module name (snake_case, e.g., `law_firm`)
- Allowed roles (e.g., `Navigator`)
- Methods to generate (list: `["POST","PUT","GET","GET/{id}","DELETE/{id}"]`)
- Optional description of the endpoint (for docs only; do **not** create ROUTE_METADATA)
- **Event type** (optional, e.g., `{MODEL}_CREATED`) - If provided, add event dispatch to POST endpoint

## Requirements

### 1. Endpoints

- Generate **only** the specified methods.
- Paths follow:
  - `POST` → `/api/v1/{model_name}`
  - `PUT` → `/api/v1/{model_name}`
  - `GET` → `/api/v1/{model_name}`
  - `GET/{id}` → `/api/v1/{model_name}/{id}`
  - `DELETE/{id}` → `/api/v1/{model_name}/{id}`
- Requires Auth (`get_current_active_user`).
- Do **not** use `@has_permission`; permission checks are enforced via `get_current_active_user` and `PERMISSIONS`.
- **Event Dispatch**: If event type is provided, add event dispatch to POST endpoint before return.

### 2. Allowed Roles

- Define **only** in `app/config/permissions/role_permission.py`
- Example:

```
PERMISSIONS = {
    "Navigator": {
        "/api/v1/{model_name}": {"POST", "PUT", "GET"},
        "/api/v1/{model_name}/{id}": {"GET", "DELETE"},
    }
}
```

❌ Do **not** create `ROUTE_METADATA` or any extra metadata entries.

### 3. Schemas (in `app/schemas/v1/{model}.py`)

- `{Model}CreateRequest`
- `{Model}UpdateRequest`
- `{Model}SearchRequest` (inherits from `DecryptedRequest`)
  - Must include:
    ```
    page: int = 1
    limit: int = 20
    order_by: str = "created_at"
    order_dir: str = "desc"
    ```
- `{Model}Response`
- `{Model}ListResponse`
- `{Model}CreateResponse`
- `{Model}UpdateResponse`
- `DeleteResponse`
- All responses must inherit from `EncryptedResponse` where applicable.
- Use `Field(..., description=..., example=...)` on all request/response fields.

### 4. Business Logic (in `app/db/services/{module}.py`)

- Implement full DB logic using SQLAlchemy ORM (no DB access in API layer).
- Implement:
  - `create_{model}_service`
  - `update_{model}_service` (update by decrypted ID from payload)
  - `search_{model}_service` (filters + pagination + ordering)
  - `get_{model}_by_id_service` (decrypt ID and fetch)
  - `delete_{model}_service` (decrypt and soft delete if applicable)
- Use existing encryption/decryption utilities (do **not** implement manual crypto).
- On invalid inputs, raise `HTTPException` with structured detail (see Error Conventions).

### 5. API Handlers (in `app/api/v1/{module}.py`)

- Use dependency-injected signatures:

```
async def create_{model}_endpoint(
    request_data: {Model}CreateRequest,
    current_user: User = Depends(get_current_active_user),
    db: Session = Depends(get_db),
) -> BaseResponse[{Model}CreateResponse]
```

- Response format must always be:

```
return BaseResponse(
    success=True,
    message=[ResponseMessage(success=True, message="...")],
    data=...,
)
```

- For list/search:

```
return BaseResponse(
    success=True,
    message=[ResponseMessage(success=True, message="Records fetched")],
    data={
        "total_count": total_count,
        "records_in_page": len(items),
        "items": items,
    },
)
```

- **Event Dispatch** (if event type provided): Add imports at top of file and dispatch code in POST endpoint before return:

**Top of file imports:**
```
from app.events.dispatcher import event_dispatcher
from app.schemas.v1.event import Event
from app.enums.events import EventType
from app.utils.helpers import extract_status_messages
```

**POST endpoint dispatch code:**
```
# Create event data
event_data = Event(
    event_type=EventType.{EVENT_TYPE},
    payload={
        "{model}_data": {
            "id": created_{model}.id,
            "name": created_{model}.name,
            # Add other relevant fields
        },
        "user_id": current_user.id,
    },
    user_id=current_user.id,
)

# Dispatch the event (wait for completion)
await event_dispatcher.dispatch_event(db, event_data)

# Extract status messages from event responses
success, messages = extract_status_messages(event_data.response)
if not success:
    # Log event failures but don't fail the API call
    logger.warning(f"Event dispatch failed: {messages}")
```

- Log only exceptions; do not log successful calls.

### 6. Router Include

- Update `app/api/v1/__init__.py` (or `app/main.py`) with:

```
from . import {module}
router.include_router({module}.router)
```

- Ensure the router mounts at `/api/v1/{module}` with an appropriate tag.

### 7. Additional Conditions

- Run `black`, `ruff`, `ruff format`, `mypy`, `bandit` only on newly created/modified files.
- Maintain a unified response structure across all endpoints.
- `SearchRequest` inherits from `DecryptedRequest` so no custom decrypt helper is needed in API.
- **Event Integration**: If event type provided, ensure proper imports and error handling.

### 8. Error Conventions (very important)

- When raising HTTP errors, always structure `detail` as a dict:

```
from fastapi import HTTPException, status
raise HTTPException(
    status_code=status.HTTP_400_BAD_REQUEST,
    detail={"success": False, "message": "Invalid {model} ID format"},
)
```

- Do **not** use plain string for `detail`.
- The global exception handlers will convert this into the final wire format:

```json
{
  "success": false,
  "message": [{ "success": false, "message": "Invalid {model} ID format" }],
  "data": []
}
```

### 9. Unit Tests

- Create `app/tests/test_{module}.py`.
- Use `pytest` and `TestClient` from existing `conftest.py`:
  - Import and use `client` and `db` fixtures from `conftest.py` (do **not** redefine engine/session/client).
- Cover all specified endpoints (success + failure paths).
- Use emails like `user@unit-test.com` to avoid collisions.
- For error assertions, check unified structure (message list):

```
assert resp.status_code == 400
body = resp.json()
assert body["success"] is False
assert body["message"][0]["message"] == "Invalid {model} ID format"
```

## Your Task

When I give you:

- Model = `{Model}`
- Module = `{module}`
- Roles = `{roles}`
- Methods = `[{methods}]`
- Description = `{description}`
- **Event type** = `{event_type}` (optional)

Generate:
- API handler with only specified endpoints
- Schemas
- Service layer with DB implementation
- Permission entries (PERMISSIONS only; no ROUTE_METADATA)
- Router registration in main
- Unit tests under `app/tests/test_{module}.py` aligned with `conftest.py` and the structured error detail convention
- **Event dispatch code** (if event type provided) - Add event dispatch to POST endpoint

## Example Usage

**Input:**
- Model = <`LawFirm`>
- Module = <`law_firm`>
- Roles = <`Navigator`>
- Methods = <`["POST", "PUT", "GET", "GET/{id}", "DELETE/{id}"]`>
- Description = <`Manage law firm records`>
- Event type = <`LAW_FIRM_CREATED`>

**Output:**
- API handler with only specified endpoints
- Schemas
- Service layer with DB implementation
- Permission entries (PERMISSIONS only; no ROUTE_METADATA)
- Router registration in main
- Unit tests under `app/tests/test_law_firm.py` aligned with `conftest.py` and the structured error detail convention
