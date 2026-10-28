from datetime import datetime

from pydantic import BaseModel, ConfigDict, Field

from app.schemas.v1.base import EncryptedResponse


class QuestionAnswersBase(BaseModel):
    """Base question answers schema."""
    question: str = Field(..., description="Question text")
    version: str | None = Field(None, description="Question version")
    answer: str | None = Field(None, description="Answer text")
    question_identifier: str = Field(..., description="Question identifier")
    question_order: int = Field(..., description="Question order")


class QuestionAnswersCreate(QuestionAnswersBase):
    """Schema for creating a new question answer."""
    pass


class QuestionAnswersUpdate(BaseModel):
    """Schema for updating a question answer."""
    question: str | None = Field(None, description="Question text")
    version: str | None = Field(None, description="Question version")
    answer: str | None = Field(None, description="Answer text")
    question_identifier: str | None = Field(None, description="Question identifier")
    question_order: int | None = Field(None, description="Question order")


class QuestionAnswersResponse(EncryptedResponse):
    """Schema for question answers response."""
    id: int = Field(..., description="Question answer ID")
    question: str = Field(..., description="Question text")
    version: str | None = Field(None, description="Question version")
    answer: str | None = Field(None, description="Answer text")
    question_identifier: str = Field(..., description="Question identifier")
    question_order: int = Field(..., description="Question order")
    created_at: datetime = Field(..., description="Creation timestamp")
    updated_at: datetime | None = Field(None, description="Last update timestamp")

    model_config = ConfigDict(from_attributes=True)


class QuestionAnswersListResponse(EncryptedResponse):
    """Schema for question answers list response."""
    id: int = Field(..., description="Question answer ID")
    question: str = Field(..., description="Question text")
    version: str | None = Field(None, description="Question version")
    answer: str | None = Field(None, description="Answer text")
    question_identifier: str = Field(..., description="Question identifier")
    question_order: int = Field(..., description="Question order")
    created_at: datetime = Field(..., description="Creation timestamp")

    model_config = ConfigDict(from_attributes=True)
