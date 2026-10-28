Help me generate a new card event handler in the project.

Event Details:
- Event Type: <EVENT_TYPE>         # Replace <EVENT_TYPE> with the event type name (e.g., CASE_OPEN_CUS_CARD), then remove this comment
- Description: <WHAT THIS EVENT DOES>   # Replace <WHAT THIS EVENT DOES> with a short description of the event's purpose, then remove this comment
- Payload Keys: <LIST_OF_KEYS>     # Replace <LIST_OF_KEYS> with a comma-separated list of required payload keys (e.g., email, username, deactivation_reason), then remove this comment
- Module: <MODULE_NAME>            # Replace <MODULE_NAME> with the relevant module name (e.g., user), then remove this comment
- User Type: <USER_TYPE>            # Replace <USER_TYPE> with the relevant user type (e.g., customer, lawyer, navigator), then remove this comment
- Component: Component name is defined in ComponentEnum and mapped to event_type, use <EVENT_TYPE>.value from ComponentEnum.
- Template Json : <JSON>        #Provide the JSON template you want to create. and remove this comment and example JSON
e.g.,
{
    "1":{"status": "{status}",
        "case_number": "{case_number}",
        "timestamp": "{timestamp}"
    }
}

Please do the following:

1. Create the event handler if not exists
- Place the handler in: `app/events/subscribers/<MODULE_NAME>.py`
- Use the decorator: `@event(EventType.<EVENT_TYPE>)`
- Use the standard function signature:
  ```python
  async def <meaningful_function_name>(
      db: Session, event: Event, websocket_manager: WebSocketManager
  ) -> EventResponseData:
In the docstring:
- Include a brief description of what the handler does.
- Add a required payload block like:
{
  "case_id": "1",
  "case_number": "CASE-001",
}

2. Inside the handler
- Validate required payload keys using the existing validate_event_payload(...) helper.
- Extract payload values.
- Generate the card using the existing replace_placeholders(...) helper.
- Save the card in timeline_event table using the existing save_timeline_event(...) helper.

Avoid unnecessary logs (no success logs). Only log exceptions.
For response, return in the following consistent format:

return EventResponseData(
    success=True,
    message="Card generated and saved to timeline successfully.",
    data=card_data
)

3. Create a new card template if not exists
- Create a <COMPONENT_NAME>.json file in app/config/components/<MODULE_NAME>/<USER_TYPE>/<COMPONENT_NAME>/
- Json data : <TEMPLATE_JSON>

4. Standards and Quality Checks
- Follow the coding standards and patterns used in existing event handlers like case_open_cus_card.

Ensure code:
- Passes ruff, ruff format, black, mypy, and bandit checks
- Is compliant with all pre-commit hooks enabled in the project

Avoid:
- Inline hardcoded values unless derived from inputs
- Unused variables, unnecessary logs, or vague error messages

Notes:
- Do not modify `EventType` or `config\event.py` — these are predefined.
- Do not update the `__init__.py` file in the `subscribers` module.
- Let Cursor infer template names, enum keys, and subject formats from the event type and payload keys.