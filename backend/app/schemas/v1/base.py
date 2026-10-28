from typing import Any, Generic, TypeVar

from pydantic import BaseModel, Field, model_validator

from app.core.error_handling import raise_bad_request
from app.enums.base import SortDirection
from app.utils.encryption import decrypt_id, encrypt_id

DataT = TypeVar("DataT")


def is_id_field(field: str) -> bool:
    return field == "id" or field.endswith("_id")


class EncryptedResponse(BaseModel):
    @model_validator(mode="before")
    @classmethod
    def encrypt_fields(cls, values: Any) -> Any:
        if isinstance(values, dict):
            salt_name = getattr(cls, "encryption_salt", None)
            for field in values:
                if is_id_field(field) and values[field] is not None and (isinstance(values[field], int) or values[field].isdigit()):
                    values[field] = encrypt_id(str(values[field]), salt_name)
        return values    
class DecryptedRequest(BaseModel):
    @model_validator(mode="before")
    @classmethod
    def decrypt_fields(cls, values: Any) -> Any:
        if isinstance(values, dict):
            salt_name = getattr(cls, "encryption_salt", None)
            for field in values:
                if is_id_field(field) and values[field] is not None and isinstance(values[field], str):
                    # If the value is a string that is just integer digits, skip decryption
                    if not values[field].isdigit():
                        decrypted_id = decrypt_id(str(values[field]), salt_name)
                        if not decrypted_id:
                            raise_bad_request(message=f"Invalid {field} : {values[field]}")
                        values[field] = decrypted_id
        return values


class ResponseMessage(BaseModel):
    success: bool = Field(..., description="Indicates if the operation was successful")
    message: str = Field(..., description="Descriptive message about the operation")


class BaseResponse(BaseModel, Generic[DataT]):
    """Response model."""

    success: bool = Field(..., description="Indicates if the operation was successful")
    message: list[ResponseMessage] = Field(
        description="A single message or a list of detailed messages",
        examples=[
            "Success message",
            [
                {"success": True, "message": "Token generated"},
                {"success": False, "message": "Email not delivered"},
            ],
        ],
    )
    data: DataT = Field(..., description="Response data")


class BaseRequest(BaseModel):
    page: int = Field(default=1, ge=1, description="Page number", examples=[1])
    limit: int = Field(default=10, ge=10, le=50, description="Limit", examples=[10])
    order_dir: str = Field(
        default=SortDirection.DESC, description="Direction", examples=["desc", "asc"]
    )
    order_by: str = Field(default="id", description="Order by", examples=["id"])
