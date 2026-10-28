from pydantic import BaseModel, ConfigDict, Field

from .base import EncryptedResponse


class UserRoleCreate(BaseModel):
    """Schema for creating a new user role."""

    user_id: int = Field(..., description="User ID")
    role_id: int = Field(
        ..., description="Role ID (1=customer, 2=lawyer, 3=nova_navigator)"
    )


class UserRoleResponse(EncryptedResponse):
    """Schema for user role response."""

    user_id: int = Field(..., description="User ID")
    role_id: int = Field(..., description="Role ID")

    model_config = ConfigDict(from_attributes=True)


class UserRoleListResponse(EncryptedResponse):
    """Schema for user role list response."""

    user_id: int = Field(..., description="User ID")
    role_id: int = Field(..., description="Role ID")

    model_config = ConfigDict(from_attributes=True)
