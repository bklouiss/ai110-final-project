"""Code Breaker (Mastermind variant) — pure logic, no Streamlit state.

Secret: 4-digit code, each digit 1–6, digits may repeat.
Feedback per guess:
  - exact  : correct digit, correct position  (shown as ●)
  - close  : correct digit, wrong position    (shown as ○)
"""

import random
from datetime import datetime

CODE_LENGTH = 4
CODE_DIGITS = list("123456")
MAX_ATTEMPTS = 10


def generate_secret() -> list[str]:
    return [random.choice(CODE_DIGITS) for _ in range(CODE_LENGTH)]


def evaluate_guess(guess: list[str], secret: list[str]) -> dict:
    """Return {'exact': int, 'close': int} counts."""
    exact = sum(g == s for g, s in zip(guess, secret))
    # close = digits in common minus the exact matches
    guess_counts = {}
    secret_counts = {}
    for g, s in zip(guess, secret):
        if g != s:
            guess_counts[g] = guess_counts.get(g, 0) + 1
            secret_counts[s] = secret_counts.get(s, 0) + 1
    close = sum(min(guess_counts.get(d, 0), secret_counts.get(d, 0)) for d in CODE_DIGITS)
    return {"exact": exact, "close": close}


def parse_code_input(raw: str) -> tuple[list[str] | None, str | None]:
    """Validate raw string input for a code guess."""
    cleaned = raw.strip().replace(" ", "")
    if len(cleaned) != CODE_LENGTH:
        return None, f"Enter exactly {CODE_LENGTH} digits."
    for ch in cleaned:
        if ch not in CODE_DIGITS:
            return None, f"Digits must be 1–6. Got '{ch}'."
    return list(cleaned), None


def feedback_symbols(result: dict) -> str:
    exact_sym = "●" * result["exact"]
    close_sym = "○" * result["close"]
    blank_sym = "·" * (CODE_LENGTH - result["exact"] - result["close"])
    return exact_sym + close_sym + blank_sym


def codebreaker_score(exact: int, attempt: int) -> int:
    """Points awarded only on a winning guess (exact == CODE_LENGTH)."""
    if exact == CODE_LENGTH:
        return max(10, 120 - 10 * attempt)
    return 0


def build_cb_record(guess: list[str], result: dict, attempt: int) -> dict:
    return {
        "attempt": attempt,
        "guess": "".join(guess),
        "exact": result["exact"],
        "close": result["close"],
        "symbols": feedback_symbols(result),
        "timestamp": datetime.now().isoformat(timespec="seconds"),
    }
