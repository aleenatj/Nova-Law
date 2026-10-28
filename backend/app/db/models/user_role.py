from sqlalchemy import Column, ForeignKey, Integer, UniqueConstraint
from sqlalchemy.orm import relationship

from app.db.database import Base


class UserRole(Base):
    """UserRole model for user roles."""

    __tablename__ = "user_role"

    user_id = Column(Integer, ForeignKey("user.id"), primary_key=True)
    role_id = Column(
        Integer, primary_key=True
    )  # 1=nova_navigator, 2=lawyer, 3=customer

    # Relationships
    user = relationship("User", back_populates="user_roles")

    # Unique constraint to prevent duplicate user-role combinations
    __table_args__ = (UniqueConstraint("user_id", "role_id", name="uq_user_role"),)
