from typing import Self

from pydantic import BaseModel, Field, SecretStr, model_validator


class GenerateRequest(BaseModel):
    length: int = Field(default=20, ge=8, le=128, strict=True)
    lowercase: bool = True
    uppercase: bool = True
    digits: bool = True
    symbols: bool = True
    exclude_ambiguous: bool = False

    @model_validator(mode="after")
    def _at_least_one_set(self) -> Self:
        if not (self.lowercase or self.uppercase or self.digits or self.symbols):
            raise ValueError("nenhum conjunto de caracteres selecionado")
        return self


class GenerateResponse(BaseModel):
    password: str


class StrengthRequest(BaseModel):
    password: SecretStr = Field(min_length=1, max_length=1024)


class StrengthResponse(BaseModel):
    score: int
    weak: bool
    crack_time_seconds: float
    crack_time_display: str
    suggestions: list[str]
