from sqlalchemy import Column, ForeignKey, Integer, UniqueConstraint
from sqlalchemy.orm import relationship

from app.db.database import Base


class LawyerLawFirm(Base):
    """LawyerLawFirm model for many-to-many relationship between lawyers and law firms."""

    __tablename__ = "lawyer_law_firm"

    lawyer_id = Column(Integer, ForeignKey("lawyer.id"), primary_key=True)
    lawfirm_id = Column(Integer, ForeignKey("law_firm.id"), primary_key=True)

    # Relationships
    lawyer = relationship("Lawyer", back_populates="lawyer_law_firms")
    law_firm = relationship("LawFirm", back_populates="lawyer_law_firms")

    # Unique constraint to prevent duplicate lawyer-lawfirm combinations
    __table_args__ = (
        UniqueConstraint("lawyer_id", "lawfirm_id", name="uq_lawyer_lawfirm"),
    )
