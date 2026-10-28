"""RefreshToken model for managing user refresh tokens across multiple devices."""

from sqlalchemy import Column, DateTime, ForeignKey, Integer, String, func
from sqlalchemy.orm import relationship

from app.db.database import Base


class RefreshToken(Base):
    """RefreshToken model for managing user authentication across multiple devices."""

    __tablename__ = "refresh_tokens"

    id = Column(Integer, primary_key=True, index=True)
    refresh_token = Column(String(1000), unique=True, nullable=False)
    user_id = Column(Integer, ForeignKey("user.id", ondelete="CASCADE"), nullable=False, index=True)
    expiry_at = Column(DateTime(timezone=True), nullable=False)
    created_at = Column(
        DateTime(timezone=True), server_default=func.now(), nullable=False
    )
    updated_at = Column(
        DateTime(timezone=True),
        server_default=func.now(),
        onupdate=func.now(),
        nullable=False,
    )

    # Relationships
    user = relationship("User", back_populates="refresh_tokens")

    def __repr__(self) -> str:
        """Return string representation of RefreshToken."""
        return f"<RefreshToken(id={self.id}, user_id={self.user_id})>"

