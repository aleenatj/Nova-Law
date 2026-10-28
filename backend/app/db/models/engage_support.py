"""Engage support model. Option columns store integer keys; see app.enums.engage_support for labels."""

from sqlalchemy import Column, DateTime, Integer, String, Text
from sqlalchemy.sql import func

from app.db.database import Base


class EngageSupport(Base):
    """Engage support form submission. Option fields store integer keys (see enums.engage_support)."""

    __tablename__ = "engage_support"

    id = Column(Integer, primary_key=True, index=True, autoincrement=True)

    name = Column(String(255), nullable=True)
    phone = Column(String(50), nullable=True)
    email = Column(String(255), nullable=True)
    how_can_help = Column(Integer, nullable=True)
    trouble_with_any = Column(Integer, nullable=True)
    trouble_navigating_engage = Column(Integer, nullable=True)
    section_stuck_on = Column(Integer, nullable=True)
    issues_listed = Column(Integer, nullable=True)
    new_lawfirm = Column(String(255), nullable=True)
    helped_resolve_issue = Column(Integer, nullable=True)
    support_query_message = Column(Text, nullable=True)

    created_at = Column(
        DateTime(timezone=True),
        server_default=func.now(),
        nullable=False,
    )
    updated_at = Column(
        DateTime(timezone=True),
        server_default=func.now(),
        onupdate=func.now(),
        nullable=False,
    )
