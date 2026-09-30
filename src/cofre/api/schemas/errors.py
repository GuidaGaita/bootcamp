"""Standard error response (docs/03 §6.3)."""

from pydantic import BaseModel, Field


class ValidationDetail(BaseModel):
    field: str = Field(min_length=1)
    issue: str = Field(min_length=1)


class ErrorBody(BaseModel):
    code: str
    message: str
    details: list[ValidationDetail] | None = Field(default=None, min_length=1)


class ErrorResponse(BaseModel):
    error: ErrorBody
