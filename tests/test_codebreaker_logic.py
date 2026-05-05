import pytest
from codebreaker_logic import (
    generate_secret,
    evaluate_guess,
    parse_code_input,
    feedback_symbols,
    codebreaker_score,
    CODE_LENGTH,
    CODE_DIGITS,
)


class TestGenerateSecret:
    def test_length(self):
        s = generate_secret()
        assert len(s) == CODE_LENGTH

    def test_valid_digits(self):
        s = generate_secret()
        assert all(d in CODE_DIGITS for d in s)


class TestEvaluateGuess:
    def test_exact_match(self):
        result = evaluate_guess(["1", "2", "3", "4"], ["1", "2", "3", "4"])
        assert result == {"exact": 4, "close": 0}

    def test_no_match(self):
        result = evaluate_guess(["1", "1", "1", "1"], ["2", "2", "2", "2"])
        assert result == {"exact": 0, "close": 0}

    def test_all_close(self):
        result = evaluate_guess(["2", "1", "4", "3"], ["1", "2", "3", "4"])
        assert result["exact"] == 0
        assert result["close"] == 4

    def test_mixed(self):
        result = evaluate_guess(["1", "2", "5", "6"], ["1", "3", "5", "4"])
        assert result["exact"] == 2
        assert result["close"] == 0

    def test_duplicate_handling(self):
        # secret has one '1', guess has two '1's — close count should not double-count
        result = evaluate_guess(["1", "1", "2", "3"], ["1", "4", "4", "4"])
        assert result["exact"] == 1
        assert result["close"] == 0


class TestParseCodeInput:
    def test_valid(self):
        val, err = parse_code_input("1234")
        assert val == ["1", "2", "3", "4"] and err is None

    def test_with_spaces(self):
        val, err = parse_code_input(" 1234 ")
        assert val == ["1", "2", "3", "4"] and err is None

    def test_too_short(self):
        val, err = parse_code_input("12")
        assert val is None and "4" in err

    def test_too_long(self):
        val, err = parse_code_input("12345")
        assert val is None

    def test_invalid_digit(self):
        val, err = parse_code_input("1270")
        assert val is None and "0" in err

    def test_alpha_rejected(self):
        val, err = parse_code_input("12ab")
        assert val is None


class TestFeedbackSymbols:
    def test_all_exact(self):
        assert feedback_symbols({"exact": 4, "close": 0}) == "●●●●"

    def test_all_close(self):
        assert feedback_symbols({"exact": 0, "close": 4}) == "○○○○"

    def test_mixed(self):
        sym = feedback_symbols({"exact": 2, "close": 1})
        assert sym.count("●") == 2
        assert sym.count("○") == 1
        assert sym.count("·") == 1


class TestCodebreakerScore:
    def test_win_attempt_1(self):
        assert codebreaker_score(4, 1) == 110

    def test_win_minimum(self):
        assert codebreaker_score(4, 100) == 10

    def test_no_win(self):
        assert codebreaker_score(3, 1) == 0
