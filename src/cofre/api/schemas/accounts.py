from datetime import datetime

from pydantic import BaseModel, Field, SecretStr

# Structural bounds, so oversized input is refused before NFKC or Argon2 run on it.
# The business limits (RN-01, RN-02) are enforced by the service.
Email = Field(max_length=320)
Password = Field(max_length=1024)


class RegisterRequest(BaseModel):
    email: str = Email
    master_password: SecretStr = Password


class AccountResponse(BaseModel):
    id: str
    email: str
    created_at: datetime


class ChangePasswordRequest(BaseModel):
    current_master_password: SecretStr = Password
    new_master_password: SecretStr = Password


class DeleteAccountRequest(BaseModel):
    master_password: SecretStr = Password
