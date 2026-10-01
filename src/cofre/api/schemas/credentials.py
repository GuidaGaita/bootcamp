"""Credential schemas; field limits follow RN-06."""

from datetime import datetime
from typing import Any, Self
from urllib.parse import urlsplit

from pydantic import BaseModel, Field, SecretStr, field_validator, model_validator


def _check_title(value: str | None) -> str | None:
    if value is not None and not value.strip():
        raise ValueError("título vazio")
    return value


def _check_url(value: str | None) -> str | None:
    if value is not None:
        parts = urlsplit(value)
        if parts.scheme not in ("http", "https") or not parts.netloc:
            raise ValueError("URL deve usar http ou https")
    return value


class CredentialCreate(BaseModel):
    title: str = Field(min_length=1, max_length=100)
    password: SecretStr = Field(min_length=1, max_length=1024)
    username: str | None = Field(default=None, max_length=255)
    url: str | None = Field(default=None, max_length=2048)
    notes: str | None = Field(default=None, max_length=10_000)

    _title = field_validator("title")(_check_title)
    _url = field_validator("url")(_check_url)

    def content(self) -> dict[str, Any]:
        data = self.model_dump()
        data["password"] = self.password.get_secret_value()
        return data


class CredentialUpdate(BaseModel):
    """Only the fields sent change. ``title`` and ``password`` cannot be cleared."""

    title: str | None = Field(default=None, min_length=1, max_length=100)
    password: SecretStr | None = Field(default=None, min_length=1, max_length=1024)
    username: str | None = Field(default=None, max_length=255)
    url: str | None = Field(default=None, max_length=2048)
    notes: str | None = Field(default=None, max_length=10_000)

    _title = field_validator("title")(_check_title)
    _url = field_validator("url")(_check_url)

    @model_validator(mode="after")
    def _check_sent_fields(self) -> Self:
        if not self.model_fields_set:
            raise ValueError("nenhum campo enviado")
        for name in ("title", "password"):
            if name in self.model_fields_set and getattr(self, name) is None:
                raise ValueError("campo obrigatório não pode ser nulo")
        return self

    def changes(self) -> dict[str, Any]:
        data = {name: getattr(self, name) for name in self.model_fields_set}
        if isinstance(data.get("password"), SecretStr):
            data["password"] = data["password"].get_secret_value()
        return data


class CredentialResponse(BaseModel):
    id: str
    title: str
    username: str | None
    url: str | None
    notes: str | None
    created_at: datetime
    updated_at: datetime


class CredentialFullResponse(CredentialResponse):
    password: str


class CredentialItem(BaseModel):
    id: str
    title: str
    username: str | None
    url: str | None
    created_at: datetime
    updated_at: datetime


class CredentialPage(BaseModel):
    items: list[CredentialItem]
    total: int
    limit: int
    offset: int
