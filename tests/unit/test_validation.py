import pytest

from cofre.core.errors import ValidationFailedError
from cofre.services.validation import normalize_email, validate_email, validate_master_password

pytestmark = [pytest.mark.unit, pytest.mark.req("RN-01", "RN-02")]


def _local(size: int) -> str:
    return "a" * (size - len("@x.co")) + "@x.co"


def test_email_is_stripped_and_lowercased():
    assert normalize_email("  Ana@Email.COM ") == "ana@email.com"


@pytest.mark.parametrize("email", ["ana@email.com", _local(254)])
def test_valid_emails(email):
    validate_email(email)


@pytest.mark.parametrize("email", [_local(255), "sem-arroba", "a@b", "a b@c.com", "@x.com", ""])
def test_invalid_emails(email):
    with pytest.raises(ValidationFailedError) as raised:
        validate_email(email)

    assert raised.value.details[0][0] == "email"


@pytest.mark.parametrize("size", [12, 128])
def test_password_length_boundaries_accepted(size):
    validate_master_password("x" * size, "ana@email.com")


@pytest.mark.parametrize("size", [0, 11, 129])
def test_password_length_boundaries_rejected(size):
    with pytest.raises(ValidationFailedError) as raised:
        validate_master_password("x" * size, "ana@email.com", field="new_master_password")

    assert raised.value.details[0][0] == "new_master_password"


def test_password_accepts_accents_and_emoji():
    validate_master_password("sênha-çom-emoji-🔐-ok", "ana@email.com")


def test_password_cannot_contain_the_email_in_any_case():
    with pytest.raises(ValidationFailedError):
        validate_master_password("xx-ANA@Email.com-xx", "ana@email.com")


def test_validation_messages_never_echo_the_value():
    with pytest.raises(ValidationFailedError) as raised:
        validate_master_password("segredo", "ana@email.com")

    assert "segredo" not in repr(raised.value.details)
