"""AI110 Final Project — Hacker Game Suite
Two games: Number Guesser (improved) + Code Breaker (Mastermind variant).
Black-and-green terminal aesthetic. Admin debug panel included.
"""

import os
import random
import streamlit as st
from dotenv import load_dotenv

load_dotenv(".env.local")

from ai_hints import generate_hint
from ai_solver import solve_number_guesser, solve_codebreaker
from logic_utils import (
    get_range_for_difficulty,
    get_limit_for_difficulty,
    parse_guess,
    check_guess,
    update_score,
    build_guess_record,
)
from codebreaker_logic import (
    generate_secret,
    evaluate_guess,
    parse_code_input,
    feedback_symbols,
    codebreaker_score,
    build_cb_record,
    CODE_LENGTH,
    MAX_ATTEMPTS,
    CODE_DIGITS,
)
from debug_panel import render_admin_panel

# ── Page config ────────────────────────────────────────────────────────────────
st.set_page_config(
    page_title="HACKER GAME SUITE",
    page_icon="💻",
    layout="wide",
    initial_sidebar_state="expanded",
)

# ── Hacker CSS ─────────────────────────────────────────────────────────────────
HACKER_CSS = """
<style>
  @import url('https://fonts.googleapis.com/css2?family=Share+Tech+Mono&display=swap');

  html, body, [class*="css"] {
    font-family: 'Share Tech Mono', 'Courier New', monospace !important;
    background-color: #0a0a0a !important;
    color: #00ff41 !important;
  }

  /* Sidebar */
  section[data-testid="stSidebar"] {
    background-color: #0d0d0d !important;
    border-right: 1px solid #00ff41 !important;
  }

  /* Buttons */
  .stButton > button {
    background-color: #0a0a0a !important;
    color: #00ff41 !important;
    border: 1px solid #00ff41 !important;
    border-radius: 2px !important;
    font-family: 'Share Tech Mono', monospace !important;
    transition: all 0.15s ease;
  }
  .stButton > button:hover {
    background-color: #00ff41 !important;
    color: #0a0a0a !important;
    box-shadow: 0 0 8px #00ff41 !important;
  }

  /* Inputs */
  .stTextInput > div > input,
  .stNumberInput > div > input,
  .stSelectbox > div > div {
    background-color: #111 !important;
    color: #00ff41 !important;
    border: 1px solid #00ff41 !important;
    border-radius: 2px !important;
    font-family: 'Share Tech Mono', monospace !important;
  }

  /* Metrics */
  [data-testid="metric-container"] {
    background-color: #111 !important;
    border: 1px solid #00ff41 !important;
    border-radius: 2px !important;
    padding: 8px !important;
  }

  /* Dividers */
  hr { border-color: #00ff41 !important; opacity: 0.3; }

  /* Success / Error / Info / Warning overrides */
  .stAlert { border-radius: 2px !important; }

  /* Dataframe */
  .stDataFrame { border: 1px solid #00ff41; }

  /* Progress bar */
  .stProgress > div > div { background-color: #00ff41 !important; }

  /* Headers */
  h1, h2, h3 { color: #00ff41 !important; text-shadow: 0 0 6px #00ff4188; }

  /* Blinking cursor on title */
  .blink { animation: blink 1s step-end infinite; }
  @keyframes blink { 50% { opacity: 0; } }

  /* Guess history cards */
  .guess-card {
    background: #111;
    border-left: 3px solid #00ff41;
    padding: 4px 10px;
    margin: 3px 0;
    font-size: 0.85em;
  }
  .guess-correct { border-left-color: #00ff41; }
  .guess-high    { border-left-color: #ff4444; }
  .guess-low     { border-left-color: #ffaa00; }
</style>
"""


def inject_css():
    st.markdown(HACKER_CSS, unsafe_allow_html=True)


def _get_api_key() -> str:
    return os.environ.get("ANTHROPIC_API_KEY", "")


# ── Session-state defaults ─────────────────────────────────────────────────────
NG_DEFAULTS = {
    "ng_secret":     None,
    "ng_difficulty": "Normal",
    "ng_attempts":   0,
    "ng_max":        8,
    "ng_score":      0,
    "ng_history":    [],
    "ng_game_over":  False,
    "ng_won":        False,
}

CB_DEFAULTS = {
    "cb_secret":    None,
    "cb_attempts":  0,
    "cb_score":     0,
    "cb_history":   [],
    "cb_game_over": False,
    "cb_won":       False,
}

AI_DEFAULTS = {
    "ng_hint":       "",
    "cb_hint":       "",
    "solver_steps":  [],
}


def init_state():
    for k, v in {**NG_DEFAULTS, **CB_DEFAULTS, **AI_DEFAULTS}.items():
        if k not in st.session_state:
            st.session_state[k] = v


def reset_ng(difficulty: str | None = None):
    diff = difficulty or st.session_state.get("ng_difficulty", "Normal")
    lo, hi = get_range_for_difficulty(diff)
    st.session_state["ng_secret"]     = random.randint(lo, hi)
    st.session_state["ng_difficulty"] = diff
    st.session_state["ng_attempts"]   = 0
    st.session_state["ng_max"]        = get_limit_for_difficulty(diff)
    st.session_state["ng_history"]    = []
    st.session_state["ng_game_over"]  = False
    st.session_state["ng_won"]        = False
    st.session_state["ng_hint"]       = ""


def reset_cb():
    st.session_state["cb_secret"]    = generate_secret()
    st.session_state["cb_attempts"]  = 0
    st.session_state["cb_history"]   = []
    st.session_state["cb_game_over"] = False
    st.session_state["cb_won"]       = False
    st.session_state["cb_hint"]      = ""


# ── Sidebar navigation ─────────────────────────────────────────────────────────
def render_sidebar() -> str:
    with st.sidebar:
        st.markdown("# `> HACKER SUITE`")
        st.divider()
        page = st.radio(
            "NAVIGATE",
            ["Number Guesser", "Code Breaker", "AI Solver", "Admin Panel"],
            key="nav_page",
            label_visibility="collapsed",
        )
        st.divider()
        st.markdown("**SCORES**")
        c1, c2 = st.columns(2)
        c1.metric("Guesser", st.session_state.get("ng_score", 0))
        c2.metric("Breaker", st.session_state.get("cb_score", 0))
        st.metric("TOTAL", st.session_state.get("ng_score", 0) + st.session_state.get("cb_score", 0))
        st.divider()
        st.caption("AI110 Final Project\nPrototype v1.0")
    return page


# ── Number Guesser ─────────────────────────────────────────────────────────────
def render_number_guesser():
    st.markdown("# `> NUMBER GUESSER`")
    st.caption("Crack the hidden integer. Every guess costs resources.")

    # — New game / difficulty controls ─────────────────────────────────────────
    col_diff, col_new = st.columns([3, 1])
    with col_diff:
        diff = st.selectbox(
            "Difficulty",
            ["Easy", "Normal", "Hard"],
            index=["Easy", "Normal", "Hard"].index(st.session_state["ng_difficulty"]),
            key="ng_diff_select",
            disabled=st.session_state["ng_secret"] is not None and not st.session_state["ng_game_over"],
        )
    with col_new:
        st.markdown("<br>", unsafe_allow_html=True)
        if st.button("NEW GAME", key="ng_new_btn", use_container_width=True):
            reset_ng(diff)
            st.rerun()

    # Auto-start first game
    if st.session_state["ng_secret"] is None:
        reset_ng(diff)
        st.rerun()

    lo, hi = get_range_for_difficulty(st.session_state["ng_difficulty"])
    attempts  = st.session_state["ng_attempts"]
    max_atts  = st.session_state["ng_max"]
    remaining = max_atts - attempts

    # — Status bar ─────────────────────────────────────────────────────────────
    st.divider()
    s1, s2, s3, s4 = st.columns(4)
    s1.metric("Range",     f"{lo}–{hi}")
    s2.metric("Attempts",  f"{attempts}/{max_atts}")
    s3.metric("Remaining", remaining)
    s4.metric("Score",     st.session_state["ng_score"])

    prog_val = attempts / max_atts if max_atts > 0 else 0
    st.progress(prog_val, text=f"Attempts used: {attempts}/{max_atts}")

    st.divider()

    # — Game over states ────────────────────────────────────────────────────────
    if st.session_state["ng_game_over"]:
        secret = st.session_state["ng_secret"]
        if st.session_state["ng_won"]:
            st.success(f"ACCESS GRANTED ✓  Secret was **{secret}**  |  +{max(10, 100 - 10*attempts)} pts")
        else:
            st.error(f"SYSTEM LOCKOUT ✗  Secret was **{secret}**  |  Game over.")
        if st.button("RESTART", key="ng_restart_btn"):
            reset_ng(diff)
            st.rerun()
        _render_ng_history()
        return

    # — Guess input ────────────────────────────────────────────────────────────
    with st.form("ng_form", clear_on_submit=True):
        guess_raw = st.number_input(
            f"Enter integer ({lo}–{hi})",
            min_value=lo,
            max_value=hi,
            step=1,
            key="ng_input",
        )
        submitted = st.form_submit_button("SUBMIT GUESS", use_container_width=True)

    if submitted:
        val, err = parse_guess(guess_raw)
        if err:
            st.error(err)
        else:
            outcome = check_guess(val, st.session_state["ng_secret"])
            st.session_state["ng_attempts"] += 1
            st.session_state["ng_score"] = update_score(
                st.session_state["ng_score"], outcome, st.session_state["ng_attempts"]
            )
            st.session_state["ng_history"].append(
                build_guess_record(val, outcome, st.session_state["ng_attempts"])
            )

            if outcome == "correct":
                st.session_state["ng_game_over"] = True
                st.session_state["ng_won"]       = True
            elif st.session_state["ng_attempts"] >= max_atts:
                st.session_state["ng_game_over"] = True

            st.rerun()

    # — Inline last-guess feedback (shown before form re-renders) ───────────────
    history = st.session_state["ng_history"]
    if history:
        last = history[-1]
        _render_ng_feedback(last["outcome"], last["guess"], lo, hi)

    # — AI Hint (RAG) ──────────────────────────────────────────────────────────
    if history:
        hc1, hc2 = st.columns([3, 1])
        with hc1:
            if st.button("REQUEST HINT [AI]", key="ng_hint_btn"):
                game_state = {
                    "lo": lo, "hi": hi,
                    "attempts": st.session_state["ng_attempts"],
                    "max_attempts": max_atts,
                    "history": [(r["guess"], r["outcome"]) for r in history],
                    "last_outcome": history[-1]["outcome"],
                }
                api_key = _get_api_key()
                if not api_key:
                    st.session_state["ng_hint"] = "Set ANTHROPIC_API_KEY in .env.local"
                else:
                    with st.spinner("QUERYING STRATEGY DATABASE..."):
                        try:
                            st.session_state["ng_hint"] = generate_hint(api_key, "number_guesser", game_state)
                        except Exception as exc:
                            st.session_state["ng_hint"] = f"Error: {exc}"
                st.rerun()
        with hc2:
            if st.button("CLEAR", key="ng_hint_clear"):
                st.session_state["ng_hint"] = ""
                st.rerun()

    if st.session_state["ng_hint"]:
        st.markdown(
            f'<div class="guess-card" style="border-left-color:#00aaff;padding:8px 12px;">'
            f'[AI HINT] {st.session_state["ng_hint"]}</div>',
            unsafe_allow_html=True,
        )

    _render_ng_history()


def _render_ng_feedback(outcome: str, guess: int, lo: int, hi: int):
    if outcome == "correct":
        st.success(f"● EXACT MATCH — {guess}")
    elif outcome == "too_high":
        mid = (lo + guess) // 2
        st.error(f"▲ TOO HIGH — try somewhere below {guess}  (hint: ~{mid}?)")
    else:
        mid = (guess + hi) // 2
        st.warning(f"▼ TOO LOW  — try somewhere above {guess}  (hint: ~{mid}?)")


def _render_ng_history():
    history = st.session_state["ng_history"]
    if not history:
        return
    st.markdown("#### Guess History")
    for rec in reversed(history):
        icon  = "✓" if rec["outcome"] == "correct" else ("▲" if rec["outcome"] == "too_high" else "▼")
        css   = {"correct": "guess-correct", "too_high": "guess-high", "too_low": "guess-low"}[rec["outcome"]]
        label = rec["outcome"].replace("_", " ").upper()
        st.markdown(
            f'<div class="guess-card {css}">'
            f'#{rec["attempt"]:02d}  {icon}  Guess: <b>{rec["guess"]}</b>  —  {label}'
            f'<span style="float:right;opacity:0.5;">{rec["timestamp"]}</span></div>',
            unsafe_allow_html=True,
        )


# ── Code Breaker ───────────────────────────────────────────────────────────────
def render_codebreaker():
    st.markdown("# `> CODE BREAKER`")
    st.caption(
        f"Crack the {CODE_LENGTH}-digit code (digits {CODE_DIGITS[0]}–{CODE_DIGITS[-1]}, repeats allowed).  "
        f"● = right digit, right place  ·  ○ = right digit, wrong place"
    )

    if st.button("NEW GAME", key="cb_new_btn"):
        reset_cb()
        st.rerun()

    if st.session_state["cb_secret"] is None:
        reset_cb()
        st.rerun()

    attempts  = st.session_state["cb_attempts"]
    remaining = MAX_ATTEMPTS - attempts

    # — Status bar ─────────────────────────────────────────────────────────────
    st.divider()
    c1, c2, c3 = st.columns(3)
    c1.metric("Attempts",  f"{attempts}/{MAX_ATTEMPTS}")
    c2.metric("Remaining", remaining)
    c3.metric("Score",     st.session_state["cb_score"])
    st.progress(attempts / MAX_ATTEMPTS if MAX_ATTEMPTS else 0,
                text=f"Attempts used: {attempts}/{MAX_ATTEMPTS}")
    st.divider()

    # — Game over ──────────────────────────────────────────────────────────────
    if st.session_state["cb_game_over"]:
        secret_str = "".join(st.session_state["cb_secret"])
        if st.session_state["cb_won"]:
            pts = codebreaker_score(CODE_LENGTH, attempts)
            st.success(f"CODE CRACKED ✓  Secret was **{secret_str}**  |  +{pts} pts")
        else:
            st.error(f"ENCRYPTION HOLDS ✗  Secret was **{secret_str}**  |  Game over.")
        if st.button("RESTART", key="cb_restart_btn"):
            reset_cb()
            st.rerun()
        _render_cb_history()
        return

    # — Guess input ────────────────────────────────────────────────────────────
    with st.form("cb_form", clear_on_submit=True):
        guess_raw = st.text_input(
            f"Enter {CODE_LENGTH}-digit code (e.g. 1234)",
            max_chars=CODE_LENGTH,
            key="cb_input",
            placeholder="1–6 only",
        )
        submitted = st.form_submit_button("SUBMIT CODE", use_container_width=True)

    if submitted:
        parsed, err = parse_code_input(guess_raw)
        if err:
            st.error(err)
        else:
            result = evaluate_guess(parsed, st.session_state["cb_secret"])
            st.session_state["cb_attempts"] += 1
            cur_att = st.session_state["cb_attempts"]
            st.session_state["cb_history"].append(build_cb_record(parsed, result, cur_att))

            if result["exact"] == CODE_LENGTH:
                pts = codebreaker_score(CODE_LENGTH, cur_att)
                st.session_state["cb_score"] += pts
                st.session_state["cb_game_over"] = True
                st.session_state["cb_won"]       = True
            elif cur_att >= MAX_ATTEMPTS:
                st.session_state["cb_game_over"] = True

            st.rerun()

    # — AI Hint (RAG) ──────────────────────────────────────────────────────────
    cb_hist = st.session_state["cb_history"]
    if cb_hist:
        hc1, hc2 = st.columns([3, 1])
        with hc1:
            if st.button("REQUEST HINT [AI]", key="cb_hint_btn"):
                game_state = {
                    "attempts": st.session_state["cb_attempts"],
                    "history": [
                        (r["guess"], r["exact"], r["close"]) for r in cb_hist
                    ],
                }
                api_key = _get_api_key()
                if not api_key:
                    st.session_state["cb_hint"] = "Set ANTHROPIC_API_KEY in .env.local"
                else:
                    with st.spinner("QUERYING STRATEGY DATABASE..."):
                        try:
                            st.session_state["cb_hint"] = generate_hint(api_key, "codebreaker", game_state)
                        except Exception as exc:
                            st.session_state["cb_hint"] = f"Error: {exc}"
                st.rerun()
        with hc2:
            if st.button("CLEAR", key="cb_hint_clear"):
                st.session_state["cb_hint"] = ""
                st.rerun()

    if st.session_state["cb_hint"]:
        st.markdown(
            f'<div class="guess-card" style="border-left-color:#00aaff;padding:8px 12px;">'
            f'[AI HINT] {st.session_state["cb_hint"]}</div>',
            unsafe_allow_html=True,
        )

    _render_cb_history()


def _render_cb_history():
    history = st.session_state["cb_history"]
    if not history:
        return
    st.markdown("#### Guess Log")
    header = f"{'#':>3}  {'CODE':<6}  {'FEEDBACK':<8}  ●  ○"
    st.code(header)
    for rec in history:
        exact_bar = "█" * rec["exact"] + "░" * (CODE_LENGTH - rec["exact"])
        line = (
            f"{rec['attempt']:>3}  {rec['guess']:<6}  "
            f"{rec['symbols']:<8}  {rec['exact']}  {rec['close']}  {exact_bar}"
        )
        color = "#00ff41" if rec["exact"] == CODE_LENGTH else ("#ffaa00" if rec["exact"] >= 2 else "#888")
        st.markdown(
            f'<div class="guess-card" style="border-left-color:{color};font-size:0.9em;">'
            f'<code>{line}</code></div>',
            unsafe_allow_html=True,
        )


# ── AI Solver ──────────────────────────────────────────────────────────────────
def render_ai_solver():
    st.markdown("# `> AI SOLVER`")
    st.caption(
        "Watch Claude autonomously crack both games via a tool-use agentic loop. "
        "Each iteration: Claude reasons → calls a game tool → observes feedback → repeats."
    )

    api_key = _get_api_key()
    if not api_key:
        st.warning("ANTHROPIC_API_KEY not set. Add it to `.env.local` and restart.")
        return

    st.divider()
    game_choice = st.radio(
        "Game for AI to solve:",
        ["Number Guesser", "Code Breaker"],
        horizontal=True,
        key="solver_game_select",
    )

    solver_diff = None
    if game_choice == "Number Guesser":
        solver_diff = st.selectbox("Difficulty", ["Easy", "Normal", "Hard"], key="solver_difficulty")

    if st.button("RUN AI SOLVER", key="solver_run_btn", use_container_width=True):
        st.session_state["solver_steps"] = []
        with st.spinner("AGENT INITIALIZING..."):
            try:
                if game_choice == "Number Guesser":
                    lo, hi = get_range_for_difficulty(solver_diff)
                    secret = random.randint(lo, hi)
                    steps = solve_number_guesser(api_key, secret, solver_diff)
                else:
                    secret_list = generate_secret()
                    steps = solve_codebreaker(api_key, secret_list)
                st.session_state["solver_steps"] = steps
            except Exception as exc:
                st.error(f"Solver error: {exc}")
                return
        st.rerun()

    steps = st.session_state.get("solver_steps", [])
    if not steps:
        st.info("Press RUN AI SOLVER to watch the agent play.")
        return

    st.divider()
    st.markdown("#### Agent Execution Log")

    for step in steps:
        stype = step["type"]

        if stype == "thought":
            with st.expander("AGENT REASONING", expanded=False):
                st.markdown(
                    f'<code style="color:#aaaaaa;white-space:pre-wrap;">{step["text"]}</code>',
                    unsafe_allow_html=True,
                )

        elif stype == "tool_call":
            st.markdown(
                f'<div class="guess-card" style="border-left-color:#555;font-size:0.85em;">'
                f'CALL → <b>{step["name"]}</b> &nbsp; <code>{step["input"]}</code></div>',
                unsafe_allow_html=True,
            )

        elif stype == "tool_result":
            name = step.get("name", "")
            if name == "submit_guess":
                outcome = step["result"]
                color = "#00ff41" if outcome == "correct" else ("#ff4444" if outcome == "too_high" else "#ffaa00")
                label = outcome.replace("_", " ").upper()
                st.markdown(
                    f'<div class="guess-card" style="border-left-color:{color};">'
                    f'#{step["attempt"]:02d} &nbsp; Guess: <b>{step["guess"]}</b> &nbsp;→&nbsp; {label}</div>',
                    unsafe_allow_html=True,
                )
            elif name == "submit_code":
                exact = step.get("exact", 0)
                color = "#00ff41" if exact == CODE_LENGTH else ("#ffaa00" if exact >= 2 else "#888888")
                st.markdown(
                    f'<div class="guess-card" style="border-left-color:{color};">'
                    f'#{step["attempt"]:02d} &nbsp; Code: <b>{step["guess"]}</b> &nbsp;→&nbsp; {step["result"]}</div>',
                    unsafe_allow_html=True,
                )

        elif stype == "done":
            icon = "✓" if step["won"] else "✗"
            msg = f"{icon}  {'SOLVED' if step['won'] else 'FAILED'} in {step['attempts']} attempt(s). Secret: {step['secret']}"
            if step["won"]:
                st.success(msg)
            else:
                st.error(msg)


# ── Main ───────────────────────────────────────────────────────────────────────
def main():
    inject_css()
    init_state()
    page = render_sidebar()

    if page == "Number Guesser":
        render_number_guesser()
    elif page == "Code Breaker":
        render_codebreaker()
    elif page == "AI Solver":
        render_ai_solver()
    elif page == "Admin Panel":
        render_admin_panel()


if __name__ == "__main__":
    main()
