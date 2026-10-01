"""Domain errors translated to HTTP by the API layer (research R5)."""

from collections.abc import Iterable, Mapping


class CofreError(Exception):
    """Base error carrying a stable ``code`` and its HTTP ``status``.

    ``headers`` are added to the response; ``details`` is a list of ``(field, issue)`` pairs
    for ``VALIDATION_ERROR``. Neither may carry secrets or received values.
    """

    code: str = "INTERNAL_ERROR"
    status: int = 500

    def __init__(
        self,
        code: str | None = None,
        status: int | None = None,
        *,
        headers: Mapping[str, str] | None = None,
        details: Iterable[tuple[str, str]] | None = None,
    ) -> None:
        if code is not None:
            self.code = code
        if status is not None:
            self.status = status
        self.headers: dict[str, str] = dict(headers or {})
        self.details: list[tuple[str, str]] = list(details or [])
        super().__init__(self.code)


class ServiceUnavailableError(CofreError):
    """A required dependency, such as the database, is unreachable."""

    code = "SERVICE_UNAVAILABLE"
    status = 503


class ValidationFailedError(CofreError):
    """A business rule on the input was violated (RN-01, RN-02...)."""

    code = "VALIDATION_ERROR"
    status = 422

    def __init__(self, field: str, issue: str) -> None:
        super().__init__(details=[(field, issue)])


class UnauthenticatedError(CofreError):
    code = "UNAUTHENTICATED"
    status = 401

    def __init__(self) -> None:
        super().__init__(headers={"WWW-Authenticate": "Bearer"})


class InvalidCredentialsError(CofreError):
    code = "INVALID_CREDENTIALS"
    status = 401


class InvalidMasterPasswordError(CofreError):
    code = "INVALID_MASTER_PASSWORD"
    status = 403


class EmailAlreadyRegisteredError(CofreError):
    code = "EMAIL_ALREADY_REGISTERED"
    status = 409


class TooManyAttemptsError(CofreError):
    code = "TOO_MANY_ATTEMPTS"
    status = 429

    def __init__(self, retry_after_seconds: int) -> None:
        super().__init__(headers={"Retry-After": str(max(1, retry_after_seconds))})


class NotFoundError(CofreError):
    """Missing resource, or one that belongs to someone else (RNF-03)."""

    code = "NOT_FOUND"
    status = 404


class VaultLimitReachedError(CofreError):
    code = "VAULT_LIMIT_REACHED"
    status = 409


class DataIntegrityError(CofreError):
    """Stored data failed authentication. Generic 500: nothing about the data is revealed."""

    code = "INTERNAL_ERROR"
    status = 500
