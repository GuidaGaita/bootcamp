"""Domain errors translated to HTTP by the API layer (research R5)."""


class CofreError(Exception):
    """Base error carrying a stable ``code`` and its HTTP ``status``."""

    code: str = "INTERNAL_ERROR"
    status: int = 500

    def __init__(self, code: str | None = None, status: int | None = None) -> None:
        if code is not None:
            self.code = code
        if status is not None:
            self.status = status
        super().__init__(self.code)


class ServiceUnavailableError(CofreError):
    """A required dependency, such as the database, is unreachable."""

    code = "SERVICE_UNAVAILABLE"
    status = 503
