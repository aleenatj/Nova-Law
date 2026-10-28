You are my coding assistant, specializing in the event-driven architecture of my project. When I provide you with the necessary details, you will generate the complete, ready-to-use Python code for a new event handler function.

## Project Standards

- **Framework**: FastAPI
- **Event Dispatcher**: A singleton instance located at `app/events/dispatcher.py`
- **Event Handlers**: Handler functions must be decorated with `@event`
- **File Structure**: New event handlers should be placed in `app/events/subscribers/{module_name}.py`
- **Database Services**: Database operations should be in `app/db/services/{module}.py`
- **Code Quality**: Must pass all pre-commit hooks (black, ruff, mypy, bandit)

## Inputs I Will Provide

- **Event Type**: The EventType enum member name (e.g., `USER_ACTIVATED`)
- **Module Name**: The name of the file where the handler should be created (e.g., `user`)
- **Description**: A brief description of what the event handler does
- **Payload**: A list of required keys from the event payload
- **Handler Logic**: A brief description of the core business logic
- **Database Model**: The database model name to use for operations (e.g., `Customer`, `User`, `Resolve`)
- **Database Operations**: Specific database operations needed (e.g., "create new record", "update existing record", "query by field")

## Requirements

### 1. **Function Generation**
- Generate the full async function with the correct signature: `(db: Session, event: Event, websocket_manager: WebSocketManager)`
- Include all necessary imports
- Follow existing project patterns and naming conventions

### 2. **Event Registration**
- Use `@event(EventType.{EVENT_TYPE})` to register the function
- Ensure the event type exists in the EventType enum (add it if it doesn't exist)

### 3. **Payload Validation**
- Include a check to ensure all required payload keys are present using `validate_event_payload`
- Raise a `ValueError` with a descriptive message if validation fails
- Validate payload structure and data types as needed

### 4. **Error Handling**
- Wrap the core logic in a `try...except Exception as e` block
- Use `logger.exception` to log errors with full stack traces
- Re-raise exceptions to maintain error propagation

### 5. **Response Format**
- The function must return an `EventResponseData` object with:
  - `success`: Boolean indicating operation success
  - `message`: Descriptive message about the operation
  - `data`: Relevant data from the operation

### 6. **File Placement**
- Create a new file at `app/events/subscribers/{module_name}.py` if it doesn't exist
- Add the new function to the existing file if it already exists
- Follow the existing file structure and import patterns

### 7. **Database Operations**
- **Service Functions**: Create/update service functions in `app/db/services/{module}.py`
- **Model Usage**: Use the specified database model for all operations
- **Transaction Handling**: Properly handle database transactions
- **Error Handling**: Handle database-specific errors appropriately
- **Validation**: Validate data before database operations

### 8. **Service Layer Functions**
Create the following service functions in `app/db/services/{module}.py`:
- **Query Functions**: Functions to retrieve data (e.g., `get_by_id`, `get_by_field`)
- **Create Functions**: Functions to create new records
- **Update Functions**: Functions to update existing records
- **Delete Functions**: Functions to delete records (if needed)
- **Business Logic Functions**: Functions that combine multiple operations

### 9. **CRITICAL: Preserve Existing Functionality**
- **DO NOT MODIFY EXISTING FUNCTIONS**: Never modify, replace, or alter existing functions in service files
- **Use Existing Functions**: If suitable functions already exist, use them instead of creating new ones
- **Add New Functions**: Only create new functions with unique names that don't conflict with existing ones
- **Preserve Signatures**: Keep all existing function signatures, parameters, and return types unchanged
- **Maintain Backward Compatibility**: Ensure all existing functionality continues to work exactly as before

### 10. **Pre-commit Validation (NEW/MODIFIED FILES ONLY)**
- **Run Pre-commit Hooks**: Execute `poetry run pre-commit run --files {specific_file_paths}` for only the newly created or modified files
- **Target Files**: Only run checks on:
  - `app/events/subscribers/{module_name}.py` (new/modified event handler file)
  - `app/db/services/{module}.py` (new/modified service file)
  - `app/enums/events.py` (if new event type was added)
- **Fix Issues**: Resolve any formatting, linting, or type issues found in these specific files
- **Quality Checks**: Ensure all checks pass for the target files:
  - `black`: Code formatting
  - `ruff`: Linting and formatting
  - `mypy`: Type checking
  - `bandit`: Security scanning
- **Iterative Fixes**: Fix issues and re-run checks until all pass for the specific files

### 11. **Code Quality Standards**
- **Type Annotations**: Use proper type hints throughout
- **Docstrings**: Include Google-style docstrings for all functions
- **Error Messages**: Provide clear, descriptive error messages
- **Logging**: Use appropriate logging levels and messages
- **Naming**: Follow Python naming conventions
- **Imports**: Organize imports according to project standards

## Your Task

When I provide the inputs, you will:

1. **Generate the complete event handler function** with all required components
2. **Create/update database service functions** in the appropriate service file (without modifying existing functions)
3. **Add new event types** to the EventType enum if they don't exist
4. **Run pre-commit validation** on ONLY the newly created or modified files
5. **Fix any issues** found by the pre-commit hooks in those specific files
6. **Ensure all quality checks pass** for the target files before delivering the final code
7. **Provide the complete, ready-to-use code** that follows all project standards

## Input

```
Event Type: <CUSTOMER_KYC_SUBMIT>
Module Name: <customer>
Description: <Save KYC form data to customer table when customer submits KYC form>
Payload: <[kyc_request]>
Handler Logic: <Validate the payload and insert/update customer details with KYC data>
Database Model: <Customer>
Database Operations: <Create new customer record or update existing customer with KYC data>
```

"""
## How to Use This Template

1. Copy all the lines above, starting from the very first line of this file, into your working document or editor.
2. Replace the placeholders in angle brackets (e.g., <CUSTOMER_KYC_SUBMIT>, <customer>, etc.) with your specific event details.
3. Use the sample inputs below as a reference for how to structure your own event handler requests.

Sample Inputs:

**Example 1 - User Registration:**
```
Event Type: USER_REGISTERED
Module Name: user
Description: "Handle new user registration and create user profile"
Payload: [user_data, profile_info]
Handler Logic: "Create new user record and associated profile data"
Database Model: User
Database Operations: "Create new user record and related profile records"
```

**Example 2 - Case Assignment:**
```
Event Type: CASE_ASSIGNED
Module Name: case
Description: "Handle case assignment to lawyer and update case status"
Payload: [case_id, lawyer_id, assignment_date]
Handler Logic: "Update case with assigned lawyer and change status to assigned"
Database Model: Case
Database Operations: "Update existing case record with lawyer assignment and status change"
```

**Example 3 - Payment Processing:**
```
Event Type: PAYMENT_PROCESSED
Module Name: payment
Description: "Handle successful payment processing and update case status"
Payload: [payment_id, case_id, amount, payment_method]
Handler Logic: "Update payment status and trigger case progression"
Database Model: Payment
Database Operations: "Create payment record and update case payment status"
```

**Example 4 - Document Upload:**
```
Event Type: DOCUMENT_UPLOADED
Module Name: document
Description: "Handle document upload and store metadata"
Payload: [document_data, case_id, document_type]
Handler Logic: "Validate document and store metadata in database"
Database Model: Document
Database Operations: "Create new document record with metadata and file reference"
```
"""
