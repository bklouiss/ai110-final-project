import pytest
from logic_utils import (
    get_range_for_difficulty,
    get_limit_for_difficulty,
    parse_guess,
    check_guess,
    update_score,
)


class TestRanges:
    def test_easy_range(self):
        assert get_range_for_difficulty("Easy") == (1, 20)

    def test_normal_range(self):
        assert get_range_for_difficulty("Normal") == (1, 100)

    def test_hard_range(self):
        assert get_range_for_difficulty("Hard") == (1, 200)

    def test_unknown_defaults(self):
        assert get_range_for_difficulty("Unknown") == (1, 100)

    def test_easy_limit(self):
        assert get_limit_for_difficulty("Easy") == 10

    def test_hard_limit(self):
        assert get_limit_for_difficulty("Hard") == 6


class TestParseGuess:
    def test_valid_int(self):
        val, err = parse_guess(42)
        assert val == 42 and err is None

    def test_valid_string_int(self):
        val, err = parse_guess("17")
        assert val == 17 and err is None

    def test_decimal_rejected(self):
        val, err = parse_guess("3.5")
        assert val is None and "decimal" in err.lower()

    def test_alpha_rejected(self):
        val, err = parse_guess("abc")
        assert val is None

    def test_empty_rejected(self):
        val, err = parse_guess("")
        assert val is None

    def test_none_rejected(self):
        val, err = parse_guess(None)
        assert val is None


class TestCheckGuess:
    def test_correct(self):
        assert check_guess(50, 50) == "correct"

    def test_too_high(self):
        assert check_guess(60, 50) == "too_high"

    def test_too_low(self):
        assert check_guess(40, 50) == "too_low"


class TestUpdateScore:
    def test_win_attempt_1(self):
        score = update_score(0, "correct", 1)
        assert score == 90  # 100 - 10*1

    def test_win_minimum(self):
        score = update_score(0, "correct", 100)
        assert score == 10  # floor at 10

    def test_too_high_even_attempt(self):
        score = update_score(100, "too_high", 2)
        assert score == 105

    def test_too_high_odd_attempt(self):
        score = update_score(100, "too_high", 3)
        assert score == 95

    def test_too_low_always_penalty(self):
        score = update_score(100, "too_low", 1)
        assert score == 95
