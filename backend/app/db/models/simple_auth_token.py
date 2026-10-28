"""SimpleAuthToken model for storing customer simple auth tokens."""

from sqlalchemy import Column, DateTime, ForeignKey, Integer, String, func
from sqlalchemy.orm import relationship

from app.db.database import Base


class SimpleAuthToken(Base):
    """SimpleAuthToken model for simplified login flow."""

    __tablename__ = "simple_auth_tokens"

    id = Column(Integer, primary_key=True, autoincrement=True)
    token = Column(String(1000), unique=True, nullable=False)
    user_id = Column(
        Integer,
        ForeignKey("user.id", ondelete="CASCADE"),
        nullable=False,
        index=True,
    )
    created_at = Column(
        DateTime(timezone=True), server_default=func.now(), nullable=False
    )
    updated_at = Column(
        DateTime(timezone=True),
        server_default=func.now(),
        onupdate=func.now(),
        nullable=False,
    )

    user = relationship("User", back_populates="simple_auth_tokens")

