from datetime import datetime

from pydantic import BaseModel, Field, SecretStr


class LoginRequest(BaseModel):
    """Structural limits only: the size rules of RN-02 apply at registration, not at login."""

    email: str = Field(min_length=1, max_length=320)
    master_password: SecretStr = Field(min_length=1, max_length=1024)


class SessionResponse(BaseModel):
    token: str
    expires_at: datetime
