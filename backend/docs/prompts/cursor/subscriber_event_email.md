Help me generate a new email event handler in the project.

Event Details:
- Event Type: <EVENT_TYPE>         # Replace <EVENT_TYPE> with the event type name (e.g., USER_DEACTIVATED_EMAIL), then remove this comment
- Description: <WHAT THIS EVENT DOES>   # Replace <WHAT THIS EVENT DOES> with a short description of the event's purpose, then remove this comment
- Payload Keys: <LIST_OF_KEYS>     # Replace <LIST_OF_KEYS> with a comma-separated list of required payload keys (e.g., email, username, deactivation_reason), then remove this comment
- Module: <MODULE_NAME>            # Replace <MODULE_NAME> with the relevant module name (e.g., user), then remove this comment

Please do the following:

1. Create the event handler
- Place the handler in: `app/events/subscribers/<MODULE_NAME>.py`
- Use the decorator: `@event(EventType.<EVENT_TYPE>)`
- Use the standard function signature:
  ```python
  async def <meaningful_function_name>(
      db: Session, event: Event, websocket_manager: WebSocketManager
  ) -> EventResponseData:
In the docstring:
- Include a brief description of what the handler does.
- Add an example payload block like:
{
  "email": "user@example.com",
  "username": "JohnDoe",
  "deactivation_reason": "Violation of terms"
}

2. Inside the handler
- Validate required payload keys using the existing validate_event_payload(...) helper.
- Extract payload values.
- Send the email using:

await email_service.send_email(
    to_email=<payload_email>,
    template=email_service.EmailTemplate.<TEMPLATE_ENUM>,
    context={
        <key>: <payload[key]>  # for each key
    },
)
Avoid unnecessary logs (no success logs). Only log exceptions.
For response, return in the following consistent format:

return EventResponseData(
    success=True,
    message="Email sent successfully.",
    data={
        "email": email,
        "username": username,
        "message_id": response.message_id  # if available
    }
)
3. Update email template configuration
- Add a new entry in the EmailTemplate enum:

<TEMPLATE_ENUM> = "<template_name>"  # e.g., USER_DEACTIVATED_EMAIL = "user_deactivated_email"
Add a subject line in EMAIL_SUBJECTS:
"<template_name>": "<subject_line_using_context>"
# e.g., "user_deactivated_email": "Your account has been deactivated, {{ username }}"
4. Generate the HTML email template
- File path: app/config/templates/email/html/<template_name>.html

The template should:
- Extend from base.html
- Include the standard header and footer partials
- Use the context variables from the payload
- Display the necessary information in a user-friendly format

5. Standards and Quality Checks
- Follow the coding standards and patterns used in existing event handlers like send_password_reset_email.

Ensure code:
- Passes ruff, ruff format, black, mypy, and bandit checks
- Is compliant with all pre-commit hooks enabled in the project

Avoid:
- Inline hardcoded values unless derived from inputs
- Unused variables, unnecessary logs, or vague error messages
- Do not use inline styles in the new template. Instead, apply only existing classes from base.html. If new styling is absolutely required, define a class in base.html and reference it from the template. Always prefer reusing existing classes over creating new ones.

Notes:
- Do not modify `EventType` or `config\event.py` — these are predefined.
- Do not update the `__init__.py` file in the `subscribers` module.
- Let Cursor infer template names, enum keys, and subject formats from the event type and payload keys.
