"""Input rules RN-01 and RN-02. Messages never repeat the received value."""

import re

from cofre.core.errors import ValidationFailedError

_EMAIL = re.compile(r"[^@\s]+@[^@\s]+\.[^@\s]+")
MAX_EMAIL = 254
MIN_PASSWORD, MAX_PASSWORD = 12, 128


def normalize_email(email: str) -> str:
    return email.strip().lower()


def validate_email(email: str, field: str = "email") -> None:
    """``email`` must already be normalized."""
    if len(email) > MAX_EMAIL or not _EMAIL.fullmatch(email):
        raise ValidationFailedError(field, "E-mail inválido.")


def validate_master_password(password: str, email: str, field: str = "master_password") -> None:
    """``password`` must already be NFKC-normalized; ``email`` normalized."""
    if not MIN_PASSWORD <= len(password) <= MAX_PASSWORD:
        raise ValidationFailedError(
            field, f"A senha mestra deve ter de {MIN_PASSWORD} a {MAX_PASSWORD} caracteres."
        )
    if email.casefold() in password.casefold():
        raise ValidationFailedError(field, "A senha mestra não pode conter o e-mail.")
