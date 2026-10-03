"""Password generator (RF-14) and strength estimator (RF-15). Pure code: no I/O, no HTTP."""

import math
import secrets
from collections.abc import Callable
from dataclasses import dataclass

LOWER = "abcdefghijklmnopqrstuvwxyz"
UPPER = "ABCDEFGHIJKLMNOPQRSTUVWXYZ"
DIGITS = "0123456789"
SYMBOLS = "!@#$%^&*()-_=+[]{}|;:,.<>?/~"
AMBIGUOUS = frozenset("0Oo1lI|")

RandBelow = Callable[[int], int]


class PasswordGenerator:
    """Randomness comes only from ``secrets`` unless a test injects another source (RNF-05)."""

    def __init__(self, randbelow: RandBelow = secrets.randbelow) -> None:
        self._randbelow = randbelow

    def _pick(self, chars: str) -> str:
        return chars[self._randbelow(len(chars))]

    def generate(
        self,
        length: int,
        lowercase: bool = True,
        uppercase: bool = True,
        digits: bool = True,
        symbols: bool = True,
        exclude_ambiguous: bool = False,
    ) -> str:
        chosen = [
            chars
            for chars, selected in (
                (LOWER, lowercase),
                (UPPER, uppercase),
                (DIGITS, digits),
                (SYMBOLS, symbols),
            )
            if selected
        ]
        if not chosen:
            raise ValueError("nenhum conjunto de caracteres selecionado")
        if length < len(chosen):
            raise ValueError("comprimento menor que o número de conjuntos")
        if exclude_ambiguous:
            chosen = ["".join(c for c in chars if c not in AMBIGUOUS) for chars in chosen]

        union = "".join(chosen)
        result = [self._pick(chars) for chars in chosen]  # one of each selected set (RN-10)
        result += [self._pick(union) for _ in range(length - len(result))]
        for index in range(len(result) - 1, 0, -1):  # Fisher-Yates with the same source
            other = self._randbelow(index + 1)
            result[index], result[other] = result[other], result[index]
        return "".join(result)


COMMON_PASSWORDS = frozenset(
    {
        "123456", "12345678", "123456789", "1234567890", "111111", "000000", "123123", "654321",
        "password", "password1", "passw0rd", "qwerty", "qwerty123", "qwertyuiop", "abc123",
        "letmein", "welcome", "admin", "administrator", "login", "master", "monkey", "dragon",
        "iloveyou", "sunshine", "football", "baseball", "batman", "superman", "trustno1",
        "senha", "senha123", "senha1234", "mudar123", "brasil", "flamengo", "corinthians",
        "princesa", "amor", "123mudar",
    }
)  # fmt: skip

GUESSES_PER_SECOND = 1e10  # offline attack on a fast hash; on average half the space is searched
MAX_SECONDS = 1e300
SECONDS_PER_YEAR = 31_536_000
_THRESHOLDS = (28, 36, 60, 80)


@dataclass(frozen=True)
class StrengthResult:
    score: int
    weak: bool
    crack_time_seconds: float
    crack_time_display: str
    suggestions: list[str]


def _is_sequence(password: str) -> bool:
    if len(password) < 3:
        return False
    steps = {ord(b) - ord(a) for a, b in zip(password, password[1:], strict=False)}
    return steps in ({1}, {-1})


def entropy_bits(password: str) -> float:
    """FR-007: distinct characters over the pool size; repeats add one bit each, capped."""
    if not password:
        return 0.0
    if password.casefold() in COMMON_PASSWORDS:
        return 5.0
    if _is_sequence(password):
        return float(len(password))
    pool = 0
    pool += 26 if any(c in LOWER for c in password) else 0
    pool += 26 if any(c in UPPER for c in password) else 0
    pool += 10 if any(c in DIGITS for c in password) else 0
    pool += 33 if any(c.isascii() and not c.isalnum() for c in password) else 0
    pool += 100 if any(not c.isascii() for c in password) else 0
    distinct = len(set(password))
    repeats = len(password) - distinct
    return distinct * math.log2(pool) + min(repeats, distinct)  # a run of 'a' is not strength


def score_for_bits(bits: float) -> int:
    return sum(bits >= limit for limit in _THRESHOLDS)


def crack_time_seconds(bits: float) -> float:
    if bits >= 990:  # 2.0 ** bits would overflow
        return MAX_SECONDS
    return min(2.0**bits / (2 * GUESSES_PER_SECOND), MAX_SECONDS)


def _plural(value: int, singular: str, plural: str) -> str:
    return f"{value} {singular if value == 1 else plural}"


def crack_time_display(seconds: float) -> str:
    if seconds < 1:
        return "instantaneamente"
    for limit, size, singular, plural in (
        (60, 1, "segundo", "segundos"),
        (3600, 60, "minuto", "minutos"),
        (86_400, 3600, "hora", "horas"),
        (SECONDS_PER_YEAR, 86_400, "dia", "dias"),
        (SECONDS_PER_YEAR * 100, SECONDS_PER_YEAR, "ano", "anos"),
    ):
        if seconds < limit:
            return _plural(int(seconds // size), singular, plural)
    return "séculos"


class StrengthEstimator:
    def estimate(self, password: str) -> StrengthResult:
        bits = entropy_bits(password)
        score = score_for_bits(bits)
        seconds = crack_time_seconds(bits)
        return StrengthResult(
            score=score,
            weak=score <= 2,
            crack_time_seconds=seconds,
            crack_time_display=crack_time_display(seconds),
            suggestions=self._suggestions(password),
        )

    @staticmethod
    def _suggestions(password: str) -> list[str]:
        found: list[str] = []
        has_lower = any(c.islower() for c in password)  # accented letters count too
        has_upper = any(c.isupper() for c in password)
        if len(password) < 12:
            found.append("Use pelo menos 12 caracteres.")
        if not (has_lower and has_upper):
            found.append("Misture letras maiúsculas e minúsculas.")
        if not any(c in DIGITS for c in password):
            found.append("Inclua números.")
        if not any(c.isascii() and not c.isalnum() for c in password):
            found.append("Inclua símbolos.")
        if password and (len(password) - len(set(password))) / len(password) > 0.3:
            found.append("Evite caracteres repetidos.")
        if password.casefold() in COMMON_PASSWORDS:
            found.append("Essa senha é muito comum.")
        if _is_sequence(password):
            found.append("Evite sequências como abc ou 123.")
        return found
