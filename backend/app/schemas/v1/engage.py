from typing import Any
from pydantic import BaseModel, Field, RootModel, model_serializer
from .base import BaseResponse, DecryptedRequest
from app.enums.engage import ActionEnum


class GetKycRequest(DecryptedRequest):
    """Schema for getting kyc request."""

    case_id: str = Field(..., description="Case ID", examples=["4eZ1ASaLikWyWGVqiGmuNg==a4ayc_80"])


class RuleItem(BaseModel):
    identifier: str = Field(..., description="Question identifier", examples=["1", "2", "3"])
    operator: str = Field(..., description="Rule operator", examples=["is", "in"])
    value: Any = Field(..., description="Rule value", examples=["tom", "jerry"])
    source: str | None = Field(
        default=None,
        description="Answer source for this rule (kyc or triage). Present only when the question defines it.",
        examples=["kyc", "triage"],
    )

    @model_serializer(mode="wrap")
    def _omit_empty_source(self, serializer: Any) -> dict[str, Any]:
        data = serializer(self)
        if data.get("source") is None:
            data.pop("source", None)
        return data


class Answer(BaseModel):
    value: str = Field(..., description="Answer value")


class QuestionData(BaseModel):
    question_type: str = Field(..., description="Question type", examples=["conditional", "non-conditional"])
    variant: str = Field(..., description="Question variant", examples=["parent", "child"])
    title: str = Field(..., description="Question title")
    description: str = Field(..., description="Question description")
    placeholder: str | None = Field(None, description="Question placeholder")
    question: str = Field(..., description="Question", examples=["First name"])
    indexed: bool | None = Field(None, description="Question indexed", examples=[True, False])
    options: list | None = Field(None, description="Question options")
    default: str | None = Field(None, description="Question default", examples=["option value"])
    required: bool = Field(..., description="Question required", examples=[True, False])
    input_type: str = Field(..., description="Question input type", examples=["radio","text"])
    min_length: int | None = Field(None, description="Answer min length", examples=[1, 2])
    max_length: int | None = Field(None, description="Answer max length", examples=[250,500])
    rules: list[RuleItem] | None = Field(None, description="Question rules")
    question_order: int = Field(..., description="Question order", examples=[1, 2, 3])
    answer_type: str = Field(..., description="Question answer type", examples=["selected_options", "text"])
    answer: list[Answer] | None = Field(None, description="Question answer")
    question_status: str | None = Field(None, description="Question status", examples=["Active", "Inactive"])
    version: str | None = Field(None, description="Question version", examples=["1", "2"])
    form_fields: dict | None = Field(None, description="Form fields")


class FullQuestionModel(RootModel[dict[str, QuestionData]]):
    pass


class GetKycResponse(BaseResponse):
    """Schema for getting kyc response."""
    data: FullQuestionModel | None = Field(None, description="Engage questios")


class SubmitAnswer(BaseModel):
    question_identifier: str = Field(..., description="Question ID", examples=["1", "2", "3"])
    answer: Answer | list[Answer] = Field(..., description="Answer", examples=[{"value": "John Doe"}])


class SubmitKycRequest(DecryptedRequest):
    """Schema for submitting kyc request."""
    case_id: str = Field(..., description="Case ID", examples=["4eZ1ASaLikWyWGVqiGmuNg==a4ayc_80"])
    action: ActionEnum = Field(..., description="Action", examples=["push", "hold"])
    answers: list[SubmitAnswer] = Field(..., description="Answers")


class SubmitKycResponse(BaseResponse):
    """Schema for submitting kyc response."""
    data: FullQuestionModel | None = Field(None, description="Engage questions")


class EngageCompleteEventRequest(BaseModel):
    """Schema for marking onboarding completed request."""
    case_id: int = Field(..., description="Case ID")


class EngageCompleteRequest(DecryptedRequest):
    """Schema for engaging complete request."""
    x_api_key: str = Field(..., description="X API key")
    client_code: str = Field(..., description="Client code")
    email: str = Field(..., description="Email")


class EngageCompleteResponse(BaseResponse):
    """Schema for engaging complete response."""
    pass


class UpdateKycRequest(DecryptedRequest):
    """Schema for patching kyc request."""
    case_id: str = Field(..., description="Case ID", examples=["4eZ1ASaLikWyWGVqiGmuNg==a4ayc_80"])
    answers: list[SubmitAnswer] = Field(..., description="Answers")


class UpdateKycResponse(BaseResponse):
    """Schema for patching kyc response."""
    pass