# CLAUDE.md — Hacker Game Suite

## Role of This File

This file gives Claude Code full context to work autonomously on this project inside VSCode or the terminal. **Read README.md first** for the full project narrative, sample interactions, design decisions, and reflection. This file covers the implementation details README does not: module responsibilities, data shapes, session state, coding standards, and how to extend the system.

---

## What This Project Is

A two-game Streamlit app that extends the **Game Glitch Investigator** (AI110 Module 1 starter) with a reworked number-guessing UI, a second game (Code Breaker — Mastermind variant), an AI hint/solver engine powered by the Anthropic Claude API, a black-and-green hacker terminal aesthetic, and a full admin debug panel.

**Do not treat the starter project as authoritative** — this codebase is the source of truth. The starter is historical reference only.

---

## Tech Stack

- Python 3.11+
- Streamlit ≥ 1.32 (UI, session state)
- Anthropic Python SDK ≥ 0.40 (Claude API)
- pytest (logic unit tests)

**Entry point:** `streamlit run app.py`  
**API key:** `ANTHROPIC_API_KEY` — read by `_get_api_key()` in `app.py` from `st.secrets` first, then `os.environ`.

---

## Module Map

| File | Role |
|---|---|
| `app.py` | Page routing, CSS injection, session-state init, sidebar, renders all pages |
| `logic_utils.py` | Number Guesser pure logic — no Streamlit imports |
| `codebreaker_logic.py` | Code Breaker pure logic — no Streamlit imports |
| `ai_hints.py` | Claude API calls: per-game contextual hints |
| `ai_solver.py` | Claude API calls: full step-by-step solver for both games |
| `debug_panel.py` | Admin panel — session state viewer, logs, chart, cheat, inject |
| `.streamlit/config.toml` | Streamlit theme (primaryColor=#00ff41, bg=#0a0a0a) |
| `knowledge_base/` | Markdown strategy docs used as grounding context for AI prompts |
| `tests/` | pytest suites — one file per logic module |
| `assets/design_doc.md` | System design reference: modes, data shapes, module responsibilities |
| `assets/diagram.md` | Mermaid architecture diagram |

---

## Data Shapes

### Number Guesser — guess record

```python
# built by logic_utils.build_guess_record()
{
    "attempt":   int,        # 1-indexed
    "guess":     int,
    "outcome":   str,        # "correct" | "too_high" | "too_low"
    "timestamp": str,        # ISO 8601 seconds precision
}
```

### Code Breaker — guess record

```python
# built by codebreaker_logic.build_cb_record()
{
    "attempt":   int,
    "guess":     str,        # e.g. "1234"
    "exact":     int,        # ● count
    "close":     int,        # ○ count
    "symbols":   str,        # e.g. "●○··"
    "timestamp": str,
}
```

### AI hint request (informal contract for ai_hints.py)

```python
# what the caller passes in
{
    "game":      str,        # "number_guesser" | "codebreaker"
    "history":   list[dict], # guess records from session state
    "lo":        int,        # current low bound (number guesser only)
    "hi":        int,        # current high bound (number guesser only)
    "attempts":  int,
    "max":       int,
    "api_key":   str,
}
```

### AI solver output (informal contract for ai_solver.py)

```python
# what render functions expect back
{
    "steps":  list[str],  # one string per solver step (rendered in st.code blocks)
    "solved": bool,
    "final":  str,        # summary line
}
```

---

## Session State Keys

All keys initialized in `app.py:init_state()`.

### Number Guesser — prefix `ng_`

| Key | Type | Purpose |
|---|---|---|
| `ng_secret` | `int \| None` | The hidden number |
| `ng_difficulty` | `str` | `"Easy"` / `"Normal"` / `"Hard"` |
| `ng_attempts` | `int` | Guesses made this game |
| `ng_max` | `int` | Attempt limit for current difficulty |
| `ng_score` | `int` | Running score (persists across games) |
| `ng_history` | `list[dict]` | All guess records this game |
| `ng_game_over` | `bool` | Whether game has ended |
| `ng_won` | `bool` | Whether player won |
| `ng_hint` | `str` | Last AI hint text (empty string if not requested) |

### Code Breaker — prefix `cb_`

| Key | Type | Purpose |
|---|---|---|
| `cb_secret` | `list[str] \| None` | e.g. `["1","3","2","4"]` |
| `cb_attempts` | `int` | Guesses made this game |
| `cb_score` | `int` | Running score (persists across games) |
| `cb_history` | `list[dict]` | All guess records this game |
| `cb_game_over` | `bool` | Whether game has ended |
| `cb_won` | `bool` | Whether player won |
| `cb_hint` | `str` | Last AI hint text |

### AI / Solver

| Key | Type | Purpose |
|---|---|---|
| `solver_steps` | `list[str]` | Step strings from the last solver run |

### Admin

| Key | Type | Purpose |
|---|---|---|
| `admin_auth` | `bool` | Whether admin panel is unlocked |

---

## Game Logic Rules

### Number Guesser (`logic_utils.py`)

- **Ranges:** Easy 1–20 (10 tries), Normal 1–100 (8 tries), Hard 1–200 (6 tries)
- **Win score:** `max(10, 100 - 10 × attempt_number)`
- **Too-high on even attempt:** +5; **odd attempt:** −5
- **Too-low:** always −5
- `parse_guess` returns `(int, None)` on success, `(None, error_str)` on failure; rejects floats and non-numeric strings

### Code Breaker (`codebreaker_logic.py`)

- **Secret:** 4 digits from `["1","2","3","4","5","6"]`, repeats allowed (1296 total combinations)
- **Max attempts:** 10
- **Feedback:** `●` = exact position, `○` = correct digit wrong position, `·` = no match
- **Win score:** `max(10, 120 - 10 × attempt_number)` — added to `cb_score` on win only
- `evaluate_guess` counts `close` by digit frequency — it does not double-count. A secret with one `"1"` and a guess with two `"1"`s counts at most one close for `"1"`.

---

## Coding Standards

- **No Streamlit imports in logic files.** `logic_utils.py` and `codebreaker_logic.py` must be importable without Streamlit installed — this is what makes them unit-testable and AI-callable without side effects.
- **No Streamlit imports in `ai_hints.py` or `ai_solver.py`.** These modules receive data as arguments and return data. The caller in `app.py` handles all UI rendering.
- **Use dict-style session state access:** `st.session_state["key"]`, not `st.session_state.key`.
- **Call `st.rerun()` immediately after every state mutation.** Never mutate state and then render without rerunning — the UI will be one frame behind.
- **All hacker CSS lives in `HACKER_CSS` in `app.py:inject_css()`.** Do not add `unsafe_allow_html` inline style tags scattered through render functions — add selectors to the single CSS string instead.
- **All logic functions must have pytest tests in `tests/`.** If you add a function to a logic module, add a test case. The test file mirrors the module name (`test_logic_utils.py`, `test_codebreaker_logic.py`).
- **Admin panel is intentionally open.** Do not add real auth or hide state. Prototype transparency is the goal.

---

## Theme / Visual Guidelines

| Token | Value |
|---|---|
| Primary green | `#00ff41` |
| Background | `#0a0a0a` |
| Secondary background | `#111111` |
| Font | `Share Tech Mono` (Google Fonts) → fallback `Courier New` |
| Header glow | `text-shadow: 0 0 6px #00ff4188` |
| Guess card — correct | border-left `#00ff41` |
| Guess card — too high | border-left `#ff4444` |
| Guess card — too low | border-left `#ffaa00` |

Buttons invert (black text on green bg) on hover. All inputs have a green border on `#111` background.

---

## AI Integration

`ai_hints.py` and `ai_solver.py` are called by `app.py` render functions. Both modules:
- Accept plain Python data (no session state objects)
- Return plain Python data (strings, lists, dicts)
- Use the `anthropic` Python SDK directly
- Are grounded in the knowledge base — relevant markdown content from `knowledge_base/` is injected into prompts as context

`_get_api_key()` in `app.py` checks `st.secrets` first, then `os.environ`. If no key is found, AI features display a "configure ANTHROPIC_API_KEY" message and return gracefully — the games remain fully playable.

---

## Extending the Project

### Adding a third game

1. Create `<name>_logic.py` with pure functions and constants. No Streamlit imports.
2. Add tests in `tests/test_<name>_logic.py`.
3. Add `<NAME>_DEFAULTS` dict and `reset_<name>()` function in `app.py:init_state()`.
4. Add `render_<name>()` function in `app.py`.
5. Add the page name to the sidebar radio options in `render_sidebar()`.
6. Add its score metric to the sidebar score block.
7. Add a knowledge base doc in `knowledge_base/` if the AI should have strategy context.

### Updating the AI hint logic

Edit `ai_hints.py`. The prompt construction and API call live there. To change what context is sent to Claude, adjust which knowledge base file is loaded and how the game state is serialized into the prompt.

### Persisting scores between sessions

Replace in-memory `ng_score` / `cb_score` with reads/writes to `scores.json` or a SQLite database. Add `load_scores()` and `save_scores()` helpers in a new `persistence.py`. Call `load_scores()` in `init_state()` and `save_scores()` after every score update.

### Changing the visual theme

Edit `.streamlit/config.toml` for Streamlit's built-in color tokens. For per-element CSS overrides, edit the `HACKER_CSS` string in `app.py:inject_css()`.

---

## Known Prototype Limitations

- Admin password is plaintext in `debug_panel.py:_ADMIN_PASSWORD` (`gl1tch`).
- Scores reset on browser refresh — no persistence layer.
- No user accounts or leaderboard.
- AI hints are stateless per call — no memory of previous hint responses within a session.
- `assets/` images/audio slots are reserved but empty.
- Altair guess-trajectory chart in admin panel requires `altair` — install separately if needed.
