from datetime import date, datetime
from typing import Any

from pydantic import BaseModel, ConfigDict, Field, RootModel, model_validator
from fastapi.exceptions import RequestValidationError
from app.enums.resolve import ResolveListStatusEnum
from app.schemas.v1.base import (
    BaseRequest,
    BaseResponse,
    DecryptedRequest,
    EncryptedResponse,
)
from app.schemas.v1.timeline_event import LawyerData


class ResolveBase(BaseModel):
    """Base resolve schema."""
    resolve_date: date | None = Field(None, description="Date of resolution")
    title: str | None = Field(None, description="Resolve title")
    questions_answered: int | None = Field(None, description="Number of questions answered")
    user_id: int | None = Field(None, description="User ID")
    result_reference_id: str | None = Field(None, description="Result reference ID")
    customer_id: int | None = Field(None, description="Customer ID")
    status: str | None = Field("In progress", description="Resolution status")


class ResolveCreate(ResolveBase):
    """Schema for creating a new resolve."""
    pass


class ResolveUpdate(BaseModel):
    """Schema for updating a resolve."""
    resolve_date: date | None = Field(None, description="Date of resolution")
    user_id: int | None = Field(None, description="User ID")
    result_reference_id: str | None = Field(None, description="Result reference ID")
    status: str | None = Field(None, description="Resolution status")


class ResolveResponse(EncryptedResponse):
    """Schema for resolve response."""
    id: int = Field(..., description="Resolve ID")
    title: str | None = Field(None, description="Resolve title")
    questions_answered: int | None = Field(None, description="Number of questions answered")
    resolve_date: date | None = Field(None, description="Date of resolution")
    user_id: int | None = Field(None, description="User ID")
    result_reference_id: str | None = Field(None, description="Result reference ID")
    status: str | None = Field(None, description="Resolution status")
    created_at: datetime = Field(..., description="Creation timestamp")
    updated_at: datetime | None = Field(None, description="Last update timestamp")

    model_config = ConfigDict(from_attributes=True)


class CreateSessionResponseData(EncryptedResponse):
    """Schema for response data with encrypted ID"""
    id: str | None = Field(None, description="Resolve ID")


class CreateSessionResponse(BaseResponse):
    """Schema for create session response."""
    data: CreateSessionResponseData = Field(..., description="Encrypted resolve id")

    model_config = ConfigDict(from_attributes=True)


class GetResolveQuestionsRequest(DecryptedRequest):
    """Schema for get resolve questions request."""
    resolve_id: str | None = Field(None, description="Resolve ID")


class OptionValue(BaseModel):
    value: str = Field(..., description="Option value", examples=["option value"])
    tooltip: str | None = Field(None, description="Option tooltip", examples=["option tooltip"])
    additional_title: str | None = Field(None, description="Option additional title", examples=["option additional title"])
    additional_description: str | None = Field(None, description="Option additional description", examples=["option additional description"])


class RuleItem(BaseModel):
    identifier: str = Field(..., description="Question identifier", examples=["1", "2", "3"])
    operator: str = Field(..., description="Rule operator", examples=["is", "in"])
    value: Any = Field(..., description="Rule value", examples=["tom", "jerry"])


class Answer(BaseModel):
    value: str = Field(..., description="Answer value")


class QuestionData(BaseModel):
    question_type: str = Field(..., description="Question type", examples=["conditional", "non-conditional"])
    variant: str = Field(..., description="Question variant", examples=["parent", "child"])
    title: str = Field(..., description="Question title")
    description: str = Field(..., description="Question description")
    placeholder: str | None = Field(None, description="Question placeholder")
    question: str = Field(..., description="Question", examples=["First name"])
    options: list[dict[str, OptionValue]] | None = Field(None, description="Question options")
    required: bool = Field(..., description="Question required", examples=[True, False])
    input_type: str = Field(..., description="Question input type", examples=["radio","text"])
    max_length: int | None = Field(None, description="Question max length", examples=[50, 100, 255])
    rules: list[RuleItem] | None = Field(None, description="Question rules")
    question_order: int = Field(..., description="Question order", examples=[1, 2, 3])
    answer_type: str = Field(..., description="Question answer type", examples=["selected_options", "text"])
    answer: list[Answer] | None = Field(None, description="Question answer")
    question_status: str | None = Field(None, description="Question status", examples=["Active", "Inactive"])
    version: str | None = Field(None, description="Question version", examples=["1", "2"])


class FullQuestionModel(RootModel[dict[str, QuestionData]]):
    pass


class ResultData(BaseModel):
    result_type: str = Field(..., description="Result type", examples=["court"])
    title: str = Field(..., description="Result title", examples=["Court"])
    summary: str = Field(..., description="Result summary", examples=["A summary .."])
    version: str = Field(..., description="Result version", examples=["1"])
    recommendations: dict[str, str] | None = Field(None, description="Result recommendations")
    affordability: str | None = Field(None, description="Result afforadability")
    tags: list[str] | None = Field(None, description="Result tags")

EXAMPLE_QUESTION_DATA = {
    "1": {
        "question_type": "conditional",
        "variant": "parent",
        "title": "First name",
        "description": "First name",
        "placeholder": "First name",
        "question": "First name",
        "options": [
            {"value": "option value", "tooltip": "option tooltip", "additional_description": "option additional description"}
        ],
        "required": True,
        "input_type": "text",
        "max_length": 100,
        "rules": [
            {"identifier": "1", "operator": "is", "value": "tom"}
        ],
        "question_order": 1,
        "answer_type": "text",
        "answer": [{"value": "tom"}],
        "question_status": "Active",
        "version": "1"
    }
}

class CaseInfo(EncryptedResponse):
    id: str = Field(..., description="Case ID", examples=["Z0FBQUFBQm9rRHN4UU1UMVp"])
    case_no: str = Field(..., description="Case number", examples=["1234567890"])
    type: str = Field(..., description="Case type", examples=["Family Law"])
    status: str = Field(..., description="Case status", examples=["Open"])
    is_kyc_completed: bool | None = Field(None, description="Is KYC completed", examples=[True, False])

class ResolveData(EncryptedResponse):
    resolve_id: str = Field(..., description="Resolve ID", examples=["Z0FBQUFBQm9rRHN4UU1UMVp"])
    title: str | None = Field(None, description="Resolve title")
    questions_answered: int | None = Field(None, description="Number of questions answered")
    resolve_status: str = Field(..., description="Resolve status", examples=["Completed"])
    result: ResultData | None = Field(None, description="Result")
    info: str | None = Field(None, description="Additional information")
    created_at: datetime = Field(..., description="Creation timestamp", examples=["2024-01-15T10:30:00Z"])
    updated_at: datetime = Field(..., description="Last update timestamp", examples=["2024-01-15T10:30:00Z"])
    question_data: FullQuestionModel = Field(..., description="Question data", examples=[EXAMPLE_QUESTION_DATA])
    case: CaseInfo | None = Field(None, description="Case information")
    lawyers: list[LawyerData] | None = Field(None, description="List of lawyers associated with the case")


class ResolveQuestionResponse(BaseResponse):
    """Schema for resolve question answers response."""
    data: ResolveData | None = Field(None, description="Resolve questios")

    model_config = ConfigDict(from_attributes=True)


class ResolveAnswersRequest(BaseModel):
    """Schema for resolve answers request."""
    resolve_id: str | None = Field(None, description="Resolve ID")


class ResolveSubmitAnswerData(BaseModel):
    question_identifier: str = Field(..., description="Question identifier")
    version: str = Field(..., description="Version")
    answer: list[Answer] = Field(..., description="Answer")


class AnswerQuestionRequest(DecryptedRequest):
    """Schema for answering a question request."""
    resolve_id: str = Field(..., description="Resolve ID", examples=["Z0FBQUFBQm9rRHN4UU1UMVp"])
    answers: list[ResolveSubmitAnswerData] = Field(..., description="Answers", examples=[[{"question_identifier": 1, "version": "1", "answer": [{"value": "tom"}]}]])

    @model_validator(mode='after')
    @classmethod
    def validate_answers(cls, values: Any) -> Any:
        if not values.answers:
            raise RequestValidationError("answers field cannot be empty")
        return values


class ResolveAnswers(BaseModel):
    """Schema for resolve answers."""
    id: str = Field(..., description="Resolve ID")
    question_identifier: str = Field(..., description="Question identifier")
    question: str = Field(..., description="Question")
    version: int = Field(..., description="Version")
    answer: str = Field(..., description="Answer")
    score: int = Field(..., description="Score")
    question_order: int = Field(..., description="Question order")
    created_at: datetime = Field(..., description="Creation timestamp")
    updated_at: datetime | None = Field(None, description="Last update timestamp")


class ResolveAnswersResponse(BaseResponse):
    """Schema for resolve answers response."""
    data: ResolveAnswers | None = Field(None, description="Resolve answers")

    model_config = ConfigDict(from_attributes=True)


class AnswerQuestionResponseData(EncryptedResponse):
    """Schema for answer question response data."""
    resolve_id: str = Field(..., description="Resolve ID")
    error_list: list[str] | None = Field(None, description="Errors")

class AnswerQuestionResponse(BaseResponse):
    """Schema for answer question response."""
    data: AnswerQuestionResponseData = Field(..., description="Answer question response data")

    model_config = ConfigDict(from_attributes=True)


class ResolveSubmitRequest(DecryptedRequest):
    """Schema for resolve submit request."""
    resolve_id: str = Field(..., description="Resolve ID", examples=["Z0FBQUFBQm9rRHN4UU1UMVp"])
    answers: list[ResolveSubmitAnswerData] | None = Field(None, description="Answers", examples=[[{"question_identifier": 1, "version": "1", "answer": [{"value": "tom"}]}]] )


class ResultVersion(RootModel[dict[str, ResultData]]):
    pass


class ResolveResult(RootModel[dict[str, ResultVersion]]):
    pass


class ResolveSubmitResponseData(EncryptedResponse):
    """Schema for resolve submit response data."""
    resolve_id: str = Field(..., description="Resolve ID")
    error_list: list[str] | None = Field(None, description="Errors")
    result: ResultData | None = Field(
        None,
        description="Resolve result",
    )
    lawyers: list[LawyerData] | None = Field(None, description="List of lawyers associated with the case")
    case: CaseInfo | None = Field(None, description="Case information")


EXAMPLE_RESOLVE_RESULT = {
    "resolve_id": "VTJ1eXQtZmc9PQ",
    "error_list": None,
    "result": {
        "result_type": "court",
        "title": "Court",
        "summary": "A summary ..",
        "version": "1"
    }
}

class ResolveSubmitResponse(BaseResponse):
    """Schema for resolve submit response."""
    data: ResolveSubmitResponseData = Field(..., description="Resolve submit response data", examples=[EXAMPLE_RESOLVE_RESULT])


class ResolveListRequest(BaseRequest):
    """Schema for resolve list request."""

    search: str | None = Field(None, description="Search by customer name or email")
    status: ResolveListStatusEnum | None = Field(ResolveListStatusEnum.ALL, description="Filter by status: All, In progress, Completed, Moving Forward")


class CustomerInfo(EncryptedResponse):
    """Schema for customer information."""
    first_name: str = Field(..., description="Customer first name", examples=["John"])
    last_name: str = Field(..., description="Customer last name", examples=["Doe"])
    email: str = Field(..., description="Customer email", examples=["john.doe@example.com"])
    id: str = Field(..., description="Customer ID", examples=["Z0FBQUFBQm9rRHN4UU1UMVp"])

    model_config = ConfigDict(from_attributes=True)


class ResolveListItem(EncryptedResponse):
    """Schema for resolve list item."""

    title: str | None = Field(None, description="Title", examples=["Court"])
    resolve_id: str = Field(..., description="Resolve ID", examples=["Z0FBQUFBQm9rRHN4UU1UMVp"])
    case_type: str = Field(..., description="Case type", examples=["Family Law"])
    resolve_status: str = Field(..., description="Resolve status", examples=["Completed"])
    start_date: date = Field(..., description="Start date", examples=["2024-01-15"])
    completed_date: datetime | None = Field(None, description="Completed date", examples=["2024-01-15T10:30:00Z"])
    created_at: datetime = Field(..., description="Creation timestamp", examples=["2024-01-15T10:30:00Z"])
    updated_at: datetime = Field(..., description="Last update timestamp", examples=["2024-01-15T10:30:00Z"])
    no_of_questions_answered: int | None = Field(None, description="No of questions answered", examples=[10])
    customer: CustomerInfo | None = Field(None, description="Customer information")

    model_config = ConfigDict(from_attributes=True)


class ResolveListResponseData(EncryptedResponse):
    """Schema for resolve list response data."""

    total_count: int = Field(..., description="Total number of records", examples=[100])
    records_in_page: int = Field(
        ..., description="Number of records in current page", examples=[20]
    )
    resolves: list[ResolveListItem] = Field(..., description="List of resolve records")


class ResolveListResponse(BaseResponse):
    """Schema for resolve list response."""

    data: ResolveListResponseData = Field(..., description="Resolve list response data")
