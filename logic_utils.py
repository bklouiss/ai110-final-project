"""Number guessing game logic — pure functions, no Streamlit state."""

from datetime import datetime


DIFFICULTY_RANGES = {
    "Easy":   (1, 20),
    "Normal": (1, 100),
    "Hard":   (1, 200),
}

DIFFICULTY_LIMITS = {
    "Easy":   10,
    "Normal": 8,
    "Hard":   6,
}


def get_range_for_difficulty(difficulty: str) -> tuple[int, int]:
    return DIFFICULTY_RANGES.get(difficulty, (1, 100))


def get_limit_for_difficulty(difficulty: str) -> int:
    return DIFFICULTY_LIMITS.get(difficulty, 8)


def parse_guess(raw) -> tuple[int | None, str | None]:
    """Return (int_value, None) on success or (None, error_message) on failure."""
    if raw is None or str(raw).strip() == "":
        return None, "Enter a number first."
    try:
        val = float(str(raw).strip())
    except ValueError:
        return None, f"'{raw}' is not a valid number."
    if val != int(val):
        return None, "Whole numbers only — no decimals."
    return int(val), None


def check_guess(guess: int, secret: int) -> str:
    """Return 'correct', 'too_high', or 'too_low'."""
    if guess == secret:
        return "correct"
    return "too_high" if guess > secret else "too_low"


def update_score(current: int, outcome: str, attempt: int) -> int:
    if outcome == "correct":
        bonus = max(10, 100 - 10 * attempt)
        return current + bonus
    if outcome == "too_high":
        return current + (5 if attempt % 2 == 0 else -5)
    return current - 5


def build_guess_record(guess: int, outcome: str, attempt: int) -> dict:
    return {
        "attempt": attempt,
        "guess": guess,
        "outcome": outcome,
        "timestamp": datetime.now().isoformat(timespec="seconds"),
    }
