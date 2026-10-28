from pydantic import BaseModel, ConfigDict, Field

from .base import EncryptedResponse


class LawyerLawFirmCreate(BaseModel):
    """Schema for creating a new lawyer-law firm relationship."""

    lawyer_id: int = Field(..., description="Lawyer ID")
    lawfirm_id: int = Field(..., description="Law firm ID")


class LawyerLawFirmResponse(EncryptedResponse):
    """Schema for lawyer-law firm response."""

    lawyer_id: int = Field(..., description="Lawyer ID")
    lawfirm_id: int = Field(..., description="Law firm ID")

    model_config = ConfigDict(from_attributes=True)


class LawyerLawFirmListResponse(EncryptedResponse):
    """Schema for lawyer-law firm list response."""

    lawyer_id: int = Field(..., description="Lawyer ID")
    lawfirm_id: int = Field(..., description="Law firm ID")

    model_config = ConfigDict(from_attributes=True)
