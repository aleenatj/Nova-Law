"""
WebSocket Connection Model

This model represents persistent WebSocket connection information stored in the database.
It tracks user connections with their connection IDs.
"""

from sqlalchemy import Column, DateTime, Integer, String, ForeignKey
from sqlalchemy.orm import relationship
from sqlalchemy.sql import func

from app.db.database import Base


class WebSocketConnection(Base):
    """Model for storing WebSocket connection information."""

    __tablename__ = "websocket_connections"

    user_id = Column(Integer, ForeignKey("user.id", ondelete="CASCADE"), primary_key=True)
    role_code = Column(String(30), nullable=False)
    connection_id = Column(String(100), primary_key=True, nullable=False)
    connected_at = Column(
        DateTime(timezone=True),
        server_default=func.now(),
        nullable=False,
    )
    disconnected_at = Column(DateTime(timezone=True), nullable=True)
    created_at = Column(
        DateTime(timezone=True), 
        server_default=func.now(), 
        nullable=False
    )
    updated_at = Column(
        DateTime(timezone=True),
        server_default=func.now(),
        onupdate=func.now(),
        nullable=False
    )

    # Relationships
    user = relationship("User", back_populates="websocket_connections")

    def __repr__(self) -> str:
        return f"<WebSocketConnection(user_id={self.user_id}, connection_id={self.connection_id})>"
