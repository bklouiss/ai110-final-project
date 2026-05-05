# Hacker Game Suite — AI110 Final Project

## Project Context (for AI assistants and collaborators)

## Video Demo Link: [TBD — add Google Drive share link here]

This is the final project for the AI110 course. It extends the **Game Glitch Investigator** (Module 1 starter) into a two-game Streamlit application with an AI hint engine, optimal AI solver, hacker terminal aesthetic, and an admin debug panel. The developer works between the terminal (Claude Code CLI) and VSCode (Claude Code extension). This README is the primary context file — read it in full before suggesting changes or implementations.

**Tech stack:** Python 3.11+, Anthropic Claude API, Streamlit, pytest  
**Entry point:** `app.py` (Streamlit UI)  
**Key modules:** `logic_utils.py`, `codebreaker_logic.py`, `ai_hints.py`, `ai_solver.py`, `debug_panel.py`  
**Environment variable required:** `ANTHROPIC_API_KEY` in `.env` or Streamlit secrets

---

## Original Project: Game Glitch Investigator (Module 1 Starter)

The project this system extends is the **Game Glitch Investigator**, built during Module 1 of the AI110 course. The starter was a single number-guessing game with intentional bugs: the secret number regenerated on every button click, hints were backwards (reporting "too high" when the guess was too low), and "New Game" did not fully reset state. The student's mission was to find and fix those bugs, refactor logic into utility functions, run pytest until all tests passed, and document the process.

The original system's limitations — single game, plain Streamlit UI, no AI integration, minimal debug output — are the direct motivation for this upgrade.

---

## Title and Summary

**Hacker Game Suite** is a two-game, AI-assisted Streamlit application styled as a hacker terminal: crack a hidden number, crack a secret code, and optionally ask an AI assistant for a strategic hint or watch an AI solver demonstrate its optimal solution step by step.

Most game UIs are passive output boxes. This project makes the AI visible: players can compare their guesses against an AI solver's optimal sequence, and the hint system explains *why* it recommends a move, not just *what* to guess next. The result is a game that doubles as an interactive tutorial on binary search and constraint elimination.

**Why it matters:** It applies the same "AI as teacher, not black box" principle that motivated AlgoAssist's Explainer Agent, but in a game context. Every AI output is grounded in the knowledge base and explains its reasoning — the same transparency philosophy, applied to play.

---

## Architecture Overview

```
[Streamlit UI — app.py]
    |
    |── [Number Guesser]
    |       logic_utils.py     pure functions: parse, check, score, build records
    |       ai_hints.py        Claude API: hint for current game state + history
    |       ai_solver.py       Claude API: binary search solver with step reasoning
    |
    |── [Code Breaker]
    |       codebreaker_logic.py  pure functions: generate, evaluate, score
    |       ai_hints.py           Claude API: constraint-elimination hint
    |       ai_solver.py          Claude API: Knuth-style optimal solver
    |
    |── [AI Solver page]
    |       Runs a full automated solve of either game
    |       Displays step-by-step reasoning in terminal style
    |
    |── [Admin Panel]
            debug_panel.py    session state viewer, logs, chart, cheat view, inject

Knowledge Base  knowledge_base/
    binary_search.md      optimal number guessing strategy (O(log n), midpoint math)
    mastermind_theory.md  Code Breaker theory (Knuth algorithm, 1296 possibilities)
    scoring_strategy.md   scoring formulas and risk/reward optimization
```

The app has four navigation pages:

| Page | Description |
|------|-------------|
| **Number Guesser** | Improved UI — progress bar, color-coded feedback, midpoint hints, timestamped history |
| **Code Breaker** | Mastermind variant — 4-digit code, ●○· feedback, constraint-based strategy |
| **AI Solver** | Watch Claude solve either game step by step with plain-language reasoning |
| **Admin Panel** | Debug interface: raw session state, guess logs, cheat view, manual state injection |

---

## Setup Instructions

### 1. Navigate to this directory

```bash
cd ai110-final-project
```

### 2. Create a virtual environment

```bash
python -m venv .venv

# Windows
.venv\Scripts\activate

# macOS / Linux
source .venv/bin/activate
```

### 3. Install dependencies

```bash
pip install -r requirements.txt
```

### 4. Configure your API key

Create a `.env` file at the project root:

```
ANTHROPIC_API_KEY=your_api_key_here
```

Or add it to `.streamlit/secrets.toml`:

```toml
ANTHROPIC_API_KEY = "your_api_key_here"
```

The AI Solver and hint buttons require this key. Both games are fully playable without it — AI features simply show a "no key configured" message.

### 5. Run the application

```bash
streamlit run app.py
```

### 6. Run tests

```bash
pytest tests/ -v
```

---

## Sample Interactions

### Number Guesser — AI Hint (Normal difficulty, range 1–100)

**Player guesses so far:** 50 (too high), 25 (too low)  
**Remaining range:** 26–49, 6 attempts left

**AI Hint output:**
```
Current range: 26–49  (24 candidates remaining)

Optimal next guess: 37

Why: Binary search midpoint of [26, 49] is 37. This splits the range into
two halves of 11 and 12 candidates. Any other guess produces a worse
worst-case split — guessing 40 leaves 14 candidates if "too low".

At 6 attempts remaining and ≤ 24 candidates, binary search guarantees
a solution. Stay on the midpoint strategy.
```

---

### Code Breaker — AI Hint (attempt 2)

**Guess 1:** `1234` → `●○··` (1 exact, 1 close)

**AI Hint output:**
```
After guess 1234 with feedback ●○··:

What you know:
  - Exactly 1 digit is in the correct position
  - Exactly 1 digit exists in the code but is misplaced
  - The other 2 digits from {1,2,3,4} are NOT in the code at all

Remaining possibilities: ~256 out of 1296

Recommended next guess: 1356

Why: This guess:
  - Keeps digit 1 in position 1 (tests if 1 was the exact match)
  - Introduces 5 and 6 (not yet tested)
  - Removes 2 and 4 (confirmed absent)
  - Will reduce remaining candidates by ~75% regardless of outcome
```

---

### AI Solver Demo — Code Breaker full solve

**AI Solver output (Mode: Code Breaker):**
```
> INITIALIZING SOLVER — secret code withheld until solve complete

Attempt 1: Guess 1122
  Feedback: ●○··
  Reasoning: 1122 is a strong opener — tests two pairs, covers digits 1–2.
             1 exact, 1 close means one of {1,1,2,2} is placed correctly
             and one appears elsewhere. Eliminates ~77% of possibilities.
  Remaining: ~294 codes

Attempt 2: Guess 3344
  Feedback: ·●··
  Reasoning: Tests the other four digits. 3344 tells us 4 is in position 2.
             None of {3,3,4} contribute in other positions.
  Remaining: ~42 codes

Attempt 3: Guess 1452
  Feedback: ●●●·
  Reasoning: 3 exact matches — positions 1, 2, 3 confirmed. Digit 2 absent.
  Remaining: 6 codes

Attempt 4: Guess 1456
  Feedback: ●●●●
  SOLVED in 4 attempts. Secret was 1456.

Score: max(10, 120 - 10×4) = 80 pts
Knuth's algorithm guarantees solution in ≤ 5 guesses.
```

---

## Design Decisions

### Why extend the Game Glitch Investigator?

The starter project established the debugging and testing foundation for this course. Using it as the base connects the final project directly to Module 1's core lesson — code can be subtly broken in ways that only edge-case testing reveals. Adding AI features on top of debugged, well-tested logic reinforces that AI is most useful when the foundation it sits on is solid.

### Why a hacker terminal aesthetic?

The black-and-green terminal theme reinforces the "cracking" metaphor of both games — you're solving puzzles that require systematic elimination, not luck. The aesthetic also makes the AI's step-by-step output feel native: a terminal printing a solver's reasoning is visually coherent in a way that the same text in a default Streamlit pastel UI would not be.

### Why the Anthropic Claude API instead of another provider?

The course developer environment uses Claude Code (CLI and VSCode extension), so Claude is the natural choice for understanding how the tools work end-to-end. The API also has a clean Python SDK with straightforward prompt construction — no framework required for the relatively simple hint and solver use cases here.

Trade-off: Students who used the Gemini API in Module 4 (DocuBot) encounter a new SDK. The transition is low-friction since both APIs share the same request/response pattern.

### Why two separate logic modules (logic_utils.py, codebreaker_logic.py)?

Each game has fundamentally different state (integer vs. digit list) and different evaluation logic (comparison vs. exact/close counting). Keeping them separate means each module is independently testable and importable without Streamlit. The same separation that made DocuBot's retrieval logic testable in isolation applies here.

### Why keep the Admin Panel fully open in prototype mode?

Prototype transparency is more valuable than prototype security. Being able to inspect every piece of session state — including the secret values — is how you verify the game logic is actually correct during development. The admin panel's "cheat view" replaces the blunt `st.write(st.session_state)` from the starter with a structured, labeled interface. Hiding it would make debugging slower without any real security benefit in a local prototype.

---

## Testing Summary

### What works

- Pure logic functions pass all pytest cases for both games
- `parse_guess` correctly handles floats, strings, empty input, and None
- `evaluate_guess` (Code Breaker) handles duplicate-digit edge cases correctly — secret `1144`, guess `1111` returns 2 exact, 0 close (not 4)
- Difficulty ranges and attempt limits are enforced cleanly
- Session state resets correctly on "New Game" without carrying over old secrets

### What did not work as expected

- The original starter's Hard difficulty (1–50) was too easy for Hard — reworked to 1–200 with 6 attempts, which now actually requires near-optimal binary search play
- AI hints are stateless per call — they don't remember previous hint responses within a session, so consecutive hints can repeat reasoning if the game state hasn't changed
- The AI Solver's step-by-step output for Code Breaker can be slower than expected on first call due to the Anthropic API response latency — adding a spinner helps UX

### What was learned

Clean logic separation (no Streamlit in logic files) makes the AI integration much simpler: `ai_hints.py` only needs to import the pure logic functions to describe game state to Claude — no Streamlit state dependencies leak into the AI layer.

The admin panel's state injection feature was more useful than expected during development. Being able to manually set `ng_secret` to a known value made it trivial to test specific game-over paths without playing through them.

---

## Reflection

### What this project taught about AI and problem-solving

Debugging the Game Glitch Investigator in Module 1 made the gap between "code that looks right" and "code that works right" visible in a concrete, frustrating way. Building on that debugged foundation showed the opposite: when logic is clean and well-tested, adding AI on top is straightforward — the AI just needs a clear description of the problem state.

The transparency goal — showing players *why* the AI makes each guess — forced an architectural decision that wouldn't exist in a pure productivity tool. The AI hint and solver features exist not to win the game for the player, but to make the winning strategy legible. This is the same values choice embedded in AlgoAssist's Explainer Agent: the AI's job is to transfer understanding, not just produce output.

The hacker aesthetic was a deliberate choice that shaped the interaction design. A terminal printing solver steps feels like watching a program run — which is exactly what binary search and Knuth's algorithm are. Framing the UI that way made the algorithmic content of the games feel native rather than academic.

---

## Module Progression Context

This project draws on skills built across all modules of the course:

| Module | Skill Applied Here |
|---|---|
| Module 1 (Game Glitch Investigator) | Direct foundation: the buggy game this project extends; debugging session state; pytest-driven fixes |
| Module 1 (Playlist Chaos) | Edge case thinking: duplicate inputs, boundary values, type mismatches |
| Module 2 (PawPal Scheduler) | Upfront design before implementation; dataclass modeling for clean input/output contracts |
| Module 3 (Music Recommender) | Scoring system design, evaluation methodology |
| Module 3 (Mood Machine) | Rule-based logic vs. AI-assisted logic — when to hard-code vs. when to prompt |
| Module 4 (DocuBot) | Claude API integration, prompt construction, grounding AI output in source material |

---

## Project Structure

```
ai110-final-project/
├── app.py                      # Streamlit UI — routing, CSS, all pages
├── logic_utils.py              # Number Guesser pure logic
├── codebreaker_logic.py        # Code Breaker pure logic
├── ai_hints.py                 # Claude API: per-game hints
├── ai_solver.py                # Claude API: step-by-step solver for both games
├── debug_panel.py              # Admin debug panel
├── requirements.txt
├── .env                        # ANTHROPIC_API_KEY (not committed)
│
├── .streamlit/
│   └── config.toml             # Black-and-green hacker theme
│
├── assets/
│   ├── design_doc.md           # System design: modes, data shapes, module responsibilities
│   └── diagram.md              # Mermaid architecture diagram
│
├── knowledge_base/
│   ├── binary_search.md        # Optimal number guessing strategy
│   ├── mastermind_theory.md    # Code Breaker theory and Knuth algorithm
│   └── scoring_strategy.md     # Scoring formulas and optimization
│
├── tests/
│   ├── test_logic_utils.py
│   └── test_codebreaker_logic.py
│
├── README.md                   # This file — primary context document
└── CLAUDE.md                   # Claude Code context: architecture, standards, extension guide
```

---

## Requirements

- Python 3.11+
- `ANTHROPIC_API_KEY` for AI Solver and hint features (games work without it)
- No external server, no database
- Internet connection required for Claude API calls and Google Fonts (terminal theme)
