# Hacker Game Suite — System Design Document

## Overview

The Hacker Game Suite is a two-game, AI-assisted Streamlit application. It provides a Number Guesser (improved from the Module 1 starter) and a Code Breaker (Mastermind variant), both styled in a black-and-green terminal aesthetic. An AI Solver page lets players watch Claude solve either game optimally, and an Admin Panel exposes full session state for debugging.

---

## Navigation Pages

| Page | Entry Function | Description |
|---|---|---|
| Number Guesser | `render_number_guesser()` | Binary search guessing game — integer in a difficulty-defined range |
| Code Breaker | `render_codebreaker()` | 4-digit Mastermind variant with ●○· feedback |
| AI Solver | `render_ai_solver()` | Watch Claude solve either game step by step |
| Admin Panel | `render_admin_panel()` | Debug interface — state viewer, logs, cheat, inject |

---

## System Architecture

```
[app.py — Streamlit entry point]
    |
    |── render_number_guesser()
    |       Uses: logic_utils.py, ai_hints.py, ai_solver.py
    |
    |── render_codebreaker()
    |       Uses: codebreaker_logic.py, ai_hints.py, ai_solver.py
    |
    |── render_ai_solver()
    |       Uses: ai_solver.py
    |       Displays: solver_steps from session state
    |
    |── render_admin_panel()  [debug_panel.py]
            Reads: full st.session_state
            Writes: manual overrides via JSON injection

[Pure Logic Layer]
    logic_utils.py          — Number Guesser functions (no Streamlit)
    codebreaker_logic.py    — Code Breaker functions (no Streamlit)

[AI Layer]
    ai_hints.py             — Claude API: game-state hints
    ai_solver.py            — Claude API: step-by-step solver

[Knowledge Base]
    knowledge_base/binary_search.md
    knowledge_base/mastermind_theory.md
    knowledge_base/scoring_strategy.md
```

---

## Data Shapes

### Number Guesser — Guess Record

```python
@dataclass  # conceptual — implemented as dict
class NGGuessRecord:
    attempt:   int    # 1-indexed
    guess:     int
    outcome:   str    # "correct" | "too_high" | "too_low"
    timestamp: str    # ISO 8601, seconds precision
```

---

### Code Breaker — Guess Record

```python
@dataclass
class CBGuessRecord:
    attempt:   int
    guess:     str    # e.g. "1234"
    exact:     int    # ● count
    close:     int    # ○ count
    symbols:   str    # e.g. "●○··"
    timestamp: str
```

---

### AI Hint Request

```python
@dataclass
class HintRequest:
    game:     str          # "number_guesser" | "codebreaker"
    history:  list[dict]   # guess records for current game
    lo:       int          # current low bound (number guesser)
    hi:       int          # current high bound (number guesser)
    attempts: int
    max:      int
    api_key:  str
```

---

### AI Hint Response

```python
@dataclass
class HintResponse:
    hint:    str    # plain-language hint text from Claude
    ok:      bool   # False if API call failed
    error:   str    # error message if ok=False, else ""
```

---

### AI Solver Response

```python
@dataclass
class SolverResponse:
    steps:  list[str]   # one entry per solver step
    solved: bool
    final:  str         # summary line (e.g. "Solved in 4 attempts — 80 pts")
    ok:     bool
    error:  str
```

---

## Logic Module Contracts

### logic_utils.py

| Function | Signature | Returns |
|---|---|---|
| `get_range_for_difficulty` | `(difficulty: str) -> tuple[int, int]` | `(lo, hi)` |
| `get_limit_for_difficulty` | `(difficulty: str) -> int` | max attempts |
| `parse_guess` | `(raw) -> tuple[int \| None, str \| None]` | `(value, None)` or `(None, error)` |
| `check_guess` | `(guess: int, secret: int) -> str` | `"correct"` / `"too_high"` / `"too_low"` |
| `update_score` | `(current: int, outcome: str, attempt: int) -> int` | new score |
| `build_guess_record` | `(guess, outcome, attempt) -> dict` | guess record dict |

### codebreaker_logic.py

| Function | Signature | Returns |
|---|---|---|
| `generate_secret` | `() -> list[str]` | 4-element list of digits 1–6 |
| `evaluate_guess` | `(guess: list[str], secret: list[str]) -> dict` | `{"exact": int, "close": int}` |
| `parse_code_input` | `(raw: str) -> tuple[list[str] \| None, str \| None]` | `(code, None)` or `(None, error)` |
| `feedback_symbols` | `(result: dict) -> str` | e.g. `"●○··"` |
| `codebreaker_score` | `(exact: int, attempt: int) -> int` | points (0 if exact < 4) |
| `build_cb_record` | `(guess, result, attempt) -> dict` | guess record dict |

---

## Scoring Rules

### Number Guesser

| Event | Points |
|---|---|
| Correct guess | `max(10, 100 - 10 × attempt)` |
| Too high, even attempt | +5 |
| Too high, odd attempt | −5 |
| Too low | −5 |

### Code Breaker

| Event | Points |
|---|---|
| Correct (win) | `max(10, 120 - 10 × attempt)` |
| Wrong guess | 0 |

---

## Admin Panel Features

| Feature | Implementation |
|---|---|
| Raw session state | `st.json(st.session_state)` (excluding password input) |
| Clear all state | Deletes all keys, re-seeds `admin_auth: True` |
| Clear logs only | Deletes `ng_history`, `cb_history`, `ng_score`, `cb_score` |
| Guess log viewer | `st.dataframe()` for each game's history list |
| Guess chart | Altair bar chart of guess values over attempts (Number Guesser) |
| Score ledger | `st.table()` of per-game and total scores |
| Secret reveal | `st.metric()` showing current secret values for both games |
| State injection | `st.text_input` for key + JSON value → `st.session_state[key] = parsed` |

Access code: `gl1tch` (plaintext, prototype only — see `debug_panel.py:_ADMIN_PASSWORD`)

---

## Knowledge Base Usage

The three markdown files in `knowledge_base/` are loaded as string context and injected into Claude prompts by `ai_hints.py` and `ai_solver.py`. They are not indexed or embedded — they are small enough to include directly in a single prompt.

| File | Content | Used by |
|---|---|---|
| `binary_search.md` | Optimal guessing strategy, O(log n) analysis, score optimization | Number Guesser hints and solver |
| `mastermind_theory.md` | Knuth algorithm, opening guess theory, constraint elimination | Code Breaker hints and solver |
| `scoring_strategy.md` | Scoring formulas for both games, risk/reward analysis | Both hint prompts |
