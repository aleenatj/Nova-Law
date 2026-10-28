from datetime import datetime

from pydantic import BaseModel, Field


class ResolveQuestionAnswers(BaseModel):
    """Base resolve question answers schema."""
    resolve_id: int | None = Field(None, description="Resolve ID")
    question_answer_id: int | None = Field(None, description="Question answer ID")
    score: float | None = Field(None, description="Score")
    created_at: datetime | None = Field(None, description="Creation timestamp")
    updated_at: datetime | None = Field(None, description="Last update timestamp")
