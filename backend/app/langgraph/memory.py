from datetime import datetime, timezone
from typing import Any

from langchain_core.messages import AIMessage, BaseMessage, HumanMessage
from pydantic import BaseModel, Field


class ChatMemory(BaseModel):
    """Memory state for LangGraph chat workflows."""

    messages: list[BaseMessage] = Field(default_factory=list)
    session_id: str | None = None
    user_id: str | None = None
    metadata: dict[str, Any] = Field(default_factory=dict)
    next_agent: str | None = None
    created_at: datetime = Field(default_factory=datetime.now(timezone.utc))
    updated_at: datetime = Field(default_factory=datetime.now(timezone.utc))

    def add_message(self, message: BaseMessage) -> None:
        """Add a message to the memory."""
        self.messages.append(message)
        self.updated_at = datetime.now(timezone.utc)

    def get_recent_messages(self, count: int = 5) -> list[BaseMessage]:
        """Get the most recent messages."""
        return self.messages[-count:] if self.messages else []

    def get_conversation_summary(self) -> str:
        """Get a summary of the conversation."""
        if not self.messages:
            return "No conversation history."

        summary_parts = []
        for msg in self.messages[-10:]:  # Last 10 messages
            if isinstance(msg, HumanMessage):
                summary_parts.append(f"User: {msg.content[:100]}...")
            elif isinstance(msg, AIMessage):
                summary_parts.append(f"Assistant: {msg.content[:100]}...")

        return " | ".join(summary_parts)

    def clear_messages(self) -> None:
        """Clear all messages."""
        self.messages = []
        self.updated_at = datetime.now(timezone.utc)

    def to_dict(self) -> dict[str, Any]:
        """Convert memory to dictionary."""
        return {
            "session_id": self.session_id,
            "user_id": self.user_id,
            "messages": [
                {
                    "type": "human" if isinstance(msg, HumanMessage) else "ai",
                    "content": msg.content,
                }
                for msg in self.messages
            ],
            "metadata": self.metadata,
            "next_agent": self.next_agent,
            "created_at": self.created_at.isoformat(),
            "updated_at": self.updated_at.isoformat(),
        }

    @classmethod
    def from_dict(cls, data: dict[str, Any]) -> "ChatMemory":
        """Create memory from dictionary."""
        messages: list[BaseMessage] = []
        for msg_data in data.get("messages", []):
            if msg_data["type"] == "human":
                messages.append(HumanMessage(content=msg_data["content"]))
            else:
                messages.append(AIMessage(content=msg_data["content"]))

        return cls(
            messages=messages,
            session_id=data.get("session_id"),
            user_id=data.get("user_id"),
            metadata=data.get("metadata", {}),
            next_agent=data.get("next_agent"),
            created_at=datetime.fromisoformat(
                data.get("created_at", datetime.now(timezone.utc).isoformat()),
            ),
            updated_at=datetime.fromisoformat(
                data.get("updated_at", datetime.now(timezone.utc).isoformat()),
            ),
        )
