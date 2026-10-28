from sqlalchemy import Column, Integer, String
from sqlalchemy.orm import relationship

from app.db.database import Base


class TimelineType(Base):
    __tablename__ = "timeline_type"

    id = Column(Integer, primary_key=True, index=True, autoincrement=True, unique=True)
    type_name = Column(String(150), nullable=False)
    version = Column(Integer, nullable=False)
    role_code = Column(String(25), nullable=False)

    # Relationships
    timeline_events = relationship("TimelineEvent", back_populates="timeline_type")
