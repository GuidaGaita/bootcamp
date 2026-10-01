from datetime import datetime

from pydantic import BaseModel, SecretStr


class RegisterRequest(BaseModel):
    email: str
    master_password: SecretStr


class AccountResponse(BaseModel):
    id: str
    email: str
    created_at: datetime


class ChangePasswordRequest(BaseModel):
    current_master_password: SecretStr
    new_master_password: SecretStr


class DeleteAccountRequest(BaseModel):
    master_password: SecretStr
