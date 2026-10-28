from typing import Any
from pydantic import BaseModel, Field, EmailStr
from .base import BaseResponse


class ContactUsRequest(BaseModel):
    """Schema for contact us request."""

    first_name: str = Field(..., min_length=1, max_length=100, description="First Name")
    last_name: str = Field(..., min_length=1, max_length=100, description="Last Name")
    phone: str = Field(..., max_length=20, description="Phone")
    email: EmailStr = Field(..., max_length=255, description="Email")
    message: str = Field(..., min_length=1, max_length=500, description="Message")

class ContactUsResponse(BaseResponse):
    """Schema for contact us response."""
    pass