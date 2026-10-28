from typing import Any

from pydantic import BaseModel, ConfigDict, Field

from app.db.models import User
from app.enums.events import EventType


class EventResponseData(BaseModel):
    """Response data model for event res
    ponses.

    Attributes:
        success (bool): Indicates if the event was successful.
        message (str): A message describing the result.
        data (Any): The data returned by the event.
    """
    should_display: bool | None = Field(True, description="Indicates if the message should be displayed to the user")
    success: bool
    message: str
    data: Any


class Event(BaseModel):
    """Event model for internal event processing.

    Attributes:
        event_type (EventType): The type of event being processed.
        payload (dict[str, Any]): Event data payload.
        response (dict[str, EventResponseData] | None): Response data from event handlers.
        user_id (int | None): ID of the user associated with the event.
        current_user (User | None): SQLAlchemy User model instance.
        parent_event_type (EventType | None): The parent event type if this is a sub-event.
            None indicates this is a main event triggered directly from an API.
    """

    model_config = ConfigDict(arbitrary_types_allowed=True)

    event_type: EventType
    payload: dict[str, Any]
    response: dict[str, EventResponseData] | None = {}
    user_id: int | None = None
    current_user: User | None = None
    parent_event_type: EventType | None = Field(
        default=None,
        description="Parent event type if this is a sub-event. None indicates a main event.",
    )
