from pydantic import BaseModel
class WebSocketMessage(BaseModel):
    """WebSocket message schema for timeline events."""

    case_id: int
    timeline_event_id: int
    role_code: str
    component_type: str
    component_path: str
    action_user_id: int | None = None
    notify_user_id: int | None = None
    is_disable_event: bool = False