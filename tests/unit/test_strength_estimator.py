import math

import pytest

from cofre.services.passwords import (
    COMMON_PASSWORDS,
    StrengthEstimator,
    crack_time_display,
    entropy_bits,
    score_for_bits,
)

pytestmark = [pytest.mark.unit, pytest.mark.req("RF-15", "RN-11")]

HUGE = "".join(chr(0x4E00 + i) for i in range(1024))  # 1,024 distinct characters


@pytest.mark.parametrize(
    ("bits", "score"),
    [(0, 0), (27.99, 0), (28, 1), (35.99, 1), (36, 2), (59.99, 2), (60, 3), (79.99, 3), (80, 4)],
)
def test_score_thresholds(bits, score):
    assert score_for_bits(bits) == score


def test_entropy_of_distinct_characters_uses_the_pool_size():
    assert entropy_bits("qwmzkp") == pytest.approx(6 * math.log2(26))
    assert entropy_bits("qwMZkp") == pytest.approx(6 * math.log2(52))
    assert entropy_bits("qwMZ19") == pytest.approx(6 * math.log2(62))
    assert entropy_bits("qwMZ1!") == pytest.approx(6 * math.log2(95))


def test_non_ascii_characters_enlarge_the_pool_by_100():
    assert entropy_bits("qwçzkp") == pytest.approx(6 * math.log2(126))


def test_repeated_characters_add_one_bit_each_up_to_the_number_of_distinct_ones():
    assert entropy_bits("qwmzkpqwm") == pytest.approx(6 * math.log2(26) + 3)
    assert entropy_bits("aaaaaa") == pytest.approx(math.log2(26) + 1)  # capped at 1 distinct


@pytest.mark.parametrize("password", ["a" * 100, "ab" * 50, "qwmzk" * 20])
def test_repeating_characters_never_makes_a_password_strong(password):
    result = StrengthEstimator().estimate(password)

    assert result.score <= 1 and result.weak is True
    assert "Evite caracteres repetidos." in result.suggestions


def test_empty_password_is_handled_without_errors():
    result = StrengthEstimator().estimate("")

    assert (result.score, result.weak, result.crack_time_display) == (0, True, "instantaneamente")
    assert "Use pelo menos 12 caracteres." in result.suggestions


def test_accented_letters_count_as_lower_and_upper_case():
    mixed = StrengthEstimator().estimate("ÁÉÍÓÚçãoÇÃO12!x")
    only_upper = StrengthEstimator().estimate("ÁÉÍÓÚ12!ÇÃO")

    assert "Misture letras maiúsculas e minúsculas." not in mixed.suggestions
    assert "Misture letras maiúsculas e minúsculas." in only_upper.suggestions


def test_a_sequence_inside_a_longer_password_is_not_detected():
    # Known limitation (spec 004, FR-007): only a whole-password run is flagged.
    result = StrengthEstimator().estimate("abcdefgh!Q9")

    assert "Evite sequências como abc ou 123." not in result.suggestions


def test_common_passwords_get_5_bits_in_any_case():
    assert "password" in COMMON_PASSWORDS
    assert entropy_bits("password") == 5
    assert entropy_bits("PassWord") == 5


@pytest.mark.parametrize("sequence", ["abcdef", "23456789", "zyxwv", "ABCD"])
def test_sequences_get_one_bit_per_character(sequence):
    assert entropy_bits(sequence) == len(sequence)


def test_two_characters_are_not_a_sequence():
    assert entropy_bits("ab") == pytest.approx(2 * math.log2(26))


@pytest.mark.parametrize(
    ("seconds", "text"),
    [
        (0.5, "instantaneamente"),
        (1, "1 segundo"),
        (59.9, "59 segundos"),
        (60, "1 minuto"),
        (7200, "2 horas"),
        (86_400, "1 dia"),
        (86_400 * 364, "364 dias"),
        (31_536_000, "1 ano"),
        (31_536_000 * 99, "99 anos"),
        (31_536_000 * 100, "séculos"),
        (1e300, "séculos"),
    ],
)
def test_crack_time_display(seconds, text):
    assert crack_time_display(seconds) == text


def test_crack_time_is_two_to_the_bits_over_twenty_billion():
    result = StrengthEstimator().estimate("qwmzkp")

    assert result.crack_time_seconds == pytest.approx(2 ** entropy_bits("qwmzkp") / 2e10)


def test_crack_time_is_capped_and_finite_for_huge_entropy():
    result = StrengthEstimator().estimate(HUGE)

    assert result.crack_time_seconds <= 1e300 and math.isfinite(result.crack_time_seconds)
    assert result.crack_time_display == "séculos"


def test_a_strong_password_scores_4_with_no_suggestions():
    result = StrengthEstimator().estimate("T9#kLm2$vQx8@pZr")

    assert (result.score, result.weak, result.suggestions) == (4, False, [])


def test_weak_means_score_at_most_2():
    estimator = StrengthEstimator()

    assert estimator.estimate("qwmzkp").weak is True  # 28 bits -> score 1
    assert estimator.estimate("Tr0ub4dor&3").weak is False  # score 3
    assert estimator.estimate("Tr0ub4dor&3").score == 3


def test_a_very_common_password_scores_0():
    result = StrengthEstimator().estimate("password")

    assert (result.score, result.weak) == (0, True)
    assert "Essa senha é muito comum." in result.suggestions


@pytest.mark.parametrize(
    ("password", "suggestion"),
    [
        ("Ab1!", "Use pelo menos 12 caracteres."),
        ("ABCDEFGH1234!@#$", "Misture letras maiúsculas e minúsculas."),
        ("abcdefgh!@#$XYZw", "Inclua números."),
        ("abcdefghXYZ12345", "Inclua símbolos."),
        ("aaaaaaaaaaaaaaab", "Evite caracteres repetidos."),
        ("password", "Essa senha é muito comum."),
        ("abcdefghijklm", "Evite sequências como abc ou 123."),
    ],
)
def test_each_suggestion_is_given_when_it_applies(password, suggestion):
    assert suggestion in StrengthEstimator().estimate(password).suggestions


def test_lowercase_only_is_asked_for_uppercase():
    assert (
        "Misture letras maiúsculas e minúsculas."
        in StrengthEstimator().estimate("qwmzkpxvbnhj").suggestions
    )


def test_repetition_hint_needs_more_than_30_percent():
    few = StrengthEstimator().estimate("aabcdefghijklmnopQ1!")  # 1 repeat in 20
    many = StrengthEstimator().estimate("aaaaaaaaaaaaaaab")  # 14 repeats in 16

    assert "Evite caracteres repetidos." not in few.suggestions
    assert "Evite caracteres repetidos." in many.suggestions


def test_the_estimate_is_deterministic():
    estimator = StrengthEstimator()

    assert estimator.estimate("Tr0ub4dor&3") == estimator.estimate("Tr0ub4dor&3")
