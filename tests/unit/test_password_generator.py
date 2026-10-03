from collections.abc import Callable
from itertools import cycle

import pytest

from cofre.services.passwords import AMBIGUOUS, DIGITS, LOWER, SYMBOLS, UPPER, PasswordGenerator

pytestmark = [pytest.mark.unit, pytest.mark.req("RF-14", "RN-10", "RNF-05")]

SETS = {"lowercase": LOWER, "uppercase": UPPER, "digits": DIGITS, "symbols": SYMBOLS}


def _selected(**flags: bool) -> list[str]:
    return [SETS[name] for name, on in {**dict.fromkeys(SETS, True), **flags}.items() if on]


def _assert_rn10(password: str, length: int, sets: list[str], ambiguous_free: bool = False) -> None:
    assert len(password) == length
    allowed = set("".join(sets))
    assert set(password) <= allowed
    for chars in sets:
        assert any(c in chars for c in password), f"faltou um caractere de {chars[:5]}..."
    if ambiguous_free:
        assert not set(password) & AMBIGUOUS


@pytest.mark.parametrize("length", [8, 20, 128])
def test_length_and_one_character_of_every_set(length):
    _assert_rn10(PasswordGenerator().generate(length), length, _selected())


@pytest.mark.parametrize(
    "flags",
    [
        {"symbols": False},
        {"lowercase": False, "uppercase": False, "symbols": False},
        {"lowercase": False, "uppercase": False, "digits": False},
        {"uppercase": False, "digits": False, "symbols": False},
    ],
)
def test_only_the_selected_sets_are_used(flags):
    password = PasswordGenerator().generate(24, **flags)

    _assert_rn10(password, 24, _selected(**flags))


def test_length_8_with_four_sets_and_no_ambiguous_characters():
    for _ in range(200):
        password = PasswordGenerator().generate(8, exclude_ambiguous=True)

        _assert_rn10(
            password,
            8,
            [chars for chars in (LOWER, UPPER, DIGITS, SYMBOLS)],
            ambiguous_free=True,
        )


@pytest.mark.parametrize("exclude", [False, True])
def test_one_thousand_generations_always_satisfy_rn10(exclude):
    generator = PasswordGenerator()
    sets = _selected()

    for _ in range(1000):
        password = generator.generate(12, exclude_ambiguous=exclude)

        _assert_rn10(password, 12, sets, ambiguous_free=exclude)


def test_ambiguous_characters_are_removed_from_every_set():
    assert AMBIGUOUS == set("0Oo1lI|")
    for _ in range(300):
        assert not set(PasswordGenerator().generate(30, exclude_ambiguous=True)) & AMBIGUOUS


def test_no_set_selected_is_an_error():
    with pytest.raises(ValueError, match="conjunto"):
        PasswordGenerator().generate(
            20, lowercase=False, uppercase=False, digits=False, symbols=False
        )


def test_length_shorter_than_the_selected_sets_is_an_error():
    with pytest.raises(ValueError, match="comprimento"):
        PasswordGenerator().generate(3)


def test_injected_source_makes_the_result_deterministic():
    def source() -> Callable[[int], int]:
        values = cycle([0, 5, 2, 7, 1])
        return lambda bound: next(values) % bound

    first = PasswordGenerator(source()).generate(16)
    second = PasswordGenerator(source()).generate(16)

    assert first == second
    assert first != PasswordGenerator().generate(16)


def test_source_is_asked_for_values_below_the_bound():
    seen: list[tuple[int, int]] = []

    def spy(bound: int) -> int:
        value = bound - 1
        seen.append((bound, value))
        return value

    PasswordGenerator(spy).generate(10)

    assert seen and all(0 <= value < bound for bound, value in seen)


def test_two_real_generations_differ():
    generator = PasswordGenerator()

    assert len({generator.generate(20) for _ in range(50)}) == 50


def test_every_position_can_be_any_character():
    # The guaranteed characters are shuffled: the first position is not always lowercase.
    firsts = {PasswordGenerator().generate(8)[0] in LOWER for _ in range(300)}

    assert firsts == {True, False}
