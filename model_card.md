# Model Card — Hacker Game Suite
**AI110 Final Project**  
**Author:** Brandon Louissaint  
**Date:** May 2026

---

## 1. System Overview

The Hacker Game Suite is a two-game Streamlit application with two embedded AI subsystems:

| Subsystem | Role | Model Used |
|---|---|---|
| **AI Hint Engine** (`ai_hints.py`) | RAG pipeline — retrieves strategy docs, generates a game-state-aware hint | Claude Haiku (`claude-haiku-4-5-20251001`) |
| **AI Solver** (`ai_solver.py`) | Agentic loop — autonomously plays either game to completion via tool-use | Claude Haiku (`claude-haiku-4-5-20251001`) |

Neither subsystem makes decisions for the human player. They are advisory (hints) and demonstrative (solver) tools.

---

## 2. Intended Use

| Use Case | Supported |
|---|---|
| Player requests a hint during an active game | ✅ |
| Watching Claude solve a game step by step | ✅ |
| Automated game-playing or score farming | ❌ Not intended |
| Any use outside a local development environment | ❌ Not designed for |

The system is a local prototype for an AI110 course final project. It is not hardened for production, multi-user deployment, or untrusted input.

---

## 3. AI Components in Detail

### 3a. RAG Hint Engine

**Pipeline:**
1. Load and chunk three knowledge base markdown files (~500 chars per chunk)
2. Build TF-IDF vectors for all chunks and the query (pure Python — no external embedding model)
3. Cosine similarity ranking → retrieve top-3 chunks
4. Inject retrieved chunks + current game state into a Claude Haiku prompt
5. Return 2–3 sentence hint grounded in the retrieved strategy context

**Knowledge base documents:**

| File | Content |
|---|---|
| `binary_search.md` | Optimal bisection strategy, score optimization, attempt budgets per difficulty |
| `mastermind_theory.md` | Constraint elimination, Knuth algorithm, opening guess theory, feedback interpretation |
| `scoring_strategy.md` | Scoring formulas for both games, risk/reward tradeoffs |

The knowledge base was authored specifically for this project. It is not sourced from external datasets.

### 3b. Agentic Solver

**Loop structure:**
1. Claude receives a system prompt describing the game rules and the goal
2. Claude calls a tool (`submit_guess` or `submit_code`) with its chosen input
3. The tool executes the actual game logic (`check_guess` / `evaluate_guess`) and returns real feedback
4. Claude observes the result and reasons about its next move
5. Loop continues until the game is solved or attempts are exhausted

**Tools available to the agent:**

| Tool | Game | Returns |
|---|---|---|
| `submit_guess(n)` | Number Guesser | `"correct"` / `"too_high"` / `"too_low"` |
| `submit_code(digits)` | Code Breaker | `exact=N, close=M, symbols=●○··` |
| `get_history()` | Both | JSON list of all prior guesses |

The solver plays a **separate instance** of the game — it does not interact with the human player's active session state.

---

## 4. AI Collaboration Reflection

### How AI was used to build this project

This project was developed using **Claude Code** (both the CLI and the VSCode extension) as the primary development assistant throughout the implementation phase. Claude Code was used to:

- Generate the initial structure for `ai_hints.py` and `ai_solver.py` based on described requirements
- Write and refine the TF-IDF retrieval logic in `ai_hints.py` (pure Python implementation, no external dependencies)
- Implement the Anthropic tool-use agentic loop in `ai_solver.py`, including correct message-passing structure for multi-turn tool calls
- Integrate both AI subsystems into the existing `app.py` without breaking existing game logic
- Identify and fix security issues (API key exposed in UI, admin password hardcoded in source, secrets moved to `.env.local`)
- Write the `.gitignore`, knowledge base markdown files, and this model card
- Debug issues including lazy import errors, secrets lookup inconsistencies, and CSS contrast problems in the Mermaid diagram

### What decisions were made by the developer vs. the AI

| Decision | Made by |
|---|---|
| What features to include (RAG hints + agentic solver) | Developer |
| Which model to use (Haiku for speed/cost) | Developer |
| Knowledge base content and strategy framing | Developer, written by Claude Code per specification |
| Tool names, input schemas, and system prompts | Developer-specified, Claude Code implemented |
| Removing API key display from UI (security concern) | Developer identified, Claude Code implemented |
| Moving secrets to `.env.local` | Developer directed |
| TF-IDF instead of embedding-based retrieval | Developer (to avoid heavy dependencies) |
| Hacker terminal aesthetic and color scheme | Developer |

### What the AI got right

- The tool-use agentic loop structure was implemented correctly on the first attempt, including proper message history management for multi-turn conversations
- The lazy import pattern for `anthropic` (importing inside function bodies to avoid startup crashes) was applied correctly without being asked explicitly after the bug was pointed out
- Security issues were identified proactively before the developer noticed them

### What required correction

- The initial `_get_api_key()` function checked `st.secrets` before `os.environ`, and the display in the UI showed the actual secrets format and key placeholder — a security antipattern that required explicit correction
- The `architecture.mmd` styles used near-black fills (`#0a0a0a`, `#111`) that made arrows invisible on Mermaid Live's white background — required a second pass with light pastel fills
- The `design_doc.md` in assets describes the knowledge base as being "included directly in a single prompt," which was outdated once TF-IDF retrieval was implemented — the document was not auto-updated

### Limitations of AI-assisted development

Claude Code writes code that compiles and runs but cannot observe the rendered Streamlit UI. Visual issues (arrow visibility in diagrams, layout problems) were only caught by the developer running the app. AI-generated tests validate logic correctness, not visual or UX correctness.

---

## 5. Potential Biases

### 5a. Knowledge Base Bias

The three strategy documents were written by Claude Code at the developer's direction. They reflect a specific framing of "optimal play":

- **Binary search as universally optimal:** The `binary_search.md` document presents midpoint guessing as always correct. This is true for minimizing expected attempts, but not always true for maximizing score under the specific scoring formula (where "too high" on even attempts yields +5). A player optimizing for score rather than attempts might rationally deviate from pure binary search, and the hint engine does not account for this nuance unless the scoring strategy document is retrieved.
- **Knuth's algorithm framing:** The `mastermind_theory.md` describes Knuth's 5-guess guarantee as the benchmark. This is academically accepted but assumes perfect constraint tracking, which a human player cannot realistically perform mentally. The AI hint assumes optimal play capacity that the user may not have.
- **Single-language, single-author corpus:** All knowledge base content is in English and reflects one author's interpretation of game theory. Alternative strategies or cultural framings of the games are not represented.

### 5b. Retrieval Bias

The TF-IDF retrieval system ranks chunks by term frequency against the query. This means:

- Chunks containing exact terminology from the game state description (e.g., "binary search," "too high") score higher regardless of strategic relevance
- Short chunks with high keyword density may outrank longer, more contextually relevant passages
- The retrieval is not semantic — it cannot recognize that a question about "narrowing the range" is related to "constraint elimination" unless those terms co-occur in training chunks

### 5c. Model Bias (Claude Haiku)

Claude Haiku, like all large language models, may:

- Exhibit a preference for certain guessing strategies over others based on patterns in pretraining data
- Occasionally generate confident-sounding hints that are suboptimal for the specific game state
- Produce non-deterministic outputs — the same game state can yield different hints across calls, which may confuse players who request hints multiple times

### 5d. Scoring System Asymmetry

The Number Guesser scoring rule itself contains a structural asymmetry: "too high" on even attempts yields +5 points while "too low" always yields -5. This means a player who has memorized the attempt parity could rationally guess slightly too high on even attempts to farm points. The hint engine does not advise this strategy (it is not in the knowledge base), which is consistent with teaching binary search but may not reflect the actual score-optimal policy.

---

## 6. Testing Results

### 6a. Unit Tests (pytest)

All tests are in `tests/` and cover the two pure logic modules. AI subsystems are not unit tested (outputs are non-deterministic).

**`test_logic_utils.py` — 19 tests**

| Test Class | Tests | Coverage |
|---|---|---|
| `TestRanges` | 5 | Difficulty ranges and attempt limits for all three levels + unknown fallback |
| `TestParseGuess` | 6 | Valid int, valid string int, decimal rejection, alpha rejection, empty, None |
| `TestCheckGuess` | 3 | Correct, too high, too low |
| `TestUpdateScore` | 5 | Win at attempt 1, win at high attempt (floor), too-high even, too-high odd, too-low |

**`test_codebreaker_logic.py` — 19 tests**

| Test Class | Tests | Coverage |
|---|---|---|
| `TestGenerateSecret` | 2 | Length is 4, all digits in valid set |
| `TestEvaluateGuess` | 5 | Exact match, no match, all close, mixed, duplicate-digit edge case |
| `TestParseCodeInput` | 6 | Valid, with spaces, too short, too long, invalid digit (0), alpha |
| `TestFeedbackSymbols` | 3 | All exact, all close, mixed |
| `TestCodebreakerScore` | 3 | Win attempt 1 (110 pts), win at high attempt (floor 10), no win (0 pts) |

**Total: 38 tests, all passing.**

### 6b. Notable Edge Case — Duplicate Digit Handling

The most important test case is `TestEvaluateGuess::test_duplicate_handling`:

```python
# Secret has one "1". Guess has two "1"s.
# Correct: exact=1, close=0  (not exact=1, close=1)
result = evaluate_guess(["1", "1", "2", "3"], ["1", "4", "4", "4"])
assert result["exact"] == 1
assert result["close"] == 0
```

This edge case (the same digit appearing more times in the guess than in the secret must not double-count close matches) was explicitly tested because it is the most common source of bugs in Mastermind implementations.

### 6c. What Was Not Tested

| Area | Reason Not Tested |
|---|---|
| AI hint relevance or accuracy | Non-deterministic — no ground-truth "correct hint" exists |
| AI solver win rate | Non-deterministic — solver may fail on some runs; failure is a valid outcome |
| TF-IDF retrieval correctness | No labeled relevance dataset; retrieval was validated manually |
| Streamlit UI behavior | No UI testing framework in scope |
| `.env.local` loading at startup | Integration test; confirmed manually by running the app |

### 6d. Known Failure Modes

- **AI Solver — Code Breaker:** Claude Haiku occasionally submits a repeated guess it already tried. The game logic still processes it, but it wastes an attempt. A constraint-tracking guard was not implemented.
- **AI Hints — stateless:** Requesting a hint twice with the same game state can produce different (or contradictory) advice since each call is a fresh API request with no memory of prior hints.
- **Hard difficulty solver:** The Number Guesser Hard configuration (range 1–200, 6 attempts) requires near-perfect binary search. The agent occasionally uses a suboptimal first guess and then runs out of attempts.

---

## 7. Ethical Considerations

### Academic Integrity

This project was built with AI assistance (Claude Code). The AI generated code, documentation, and knowledge base content at the direction of the developer. All architectural decisions, feature specifications, and design choices were made by the developer. The use of Claude Code as a development assistant is analogous to using a senior developer for pair programming — the ideas and requirements originated with the developer.

### Data Privacy

No user data is collected, stored, or transmitted beyond:
- The current session's game state (held in `st.session_state`, cleared on browser refresh)
- API calls to Anthropic's Claude API containing only game state (guess history, score, range) — no personally identifiable information

### Security

- The `ANTHROPIC_API_KEY` and `ADMIN_PASSWORD` are stored in `.env.local`, which is gitignored
- Neither secret is displayed in the UI or logged to the console
- The admin panel has no real authentication — it is a prototype debug tool and should not be exposed in any networked deployment

---

## 8. Model Card Limitations

This model card describes the system as of the submission date. It does not account for:

- Changes to Claude Haiku's behavior in future model updates
- Changes to the Anthropic API that may affect tool-use behavior
- Scores or win rates measured over large sample sizes (no bulk testing was performed)
