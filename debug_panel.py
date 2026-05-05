"""Admin / debug panel — renders inside the main Streamlit app."""

import json
import os
import streamlit as st
from datetime import datetime


_ADMIN_PASSWORD = os.environ.get("ADMIN_PASSWORD", "")


def _section(title: str):
    st.markdown(f"<h3 style='color:#00ff41;border-bottom:1px solid #00ff41;'>{title}</h3>",
                unsafe_allow_html=True)


def render_admin_panel():
    st.markdown("## `> ADMIN TERMINAL`")
    st.caption("Prototype mode — all state exposed.")

    if not st.session_state.get("admin_auth"):
        pwd = st.text_input("Access code:", type="password", key="admin_pwd_input")
        if st.button("AUTHENTICATE", key="admin_login_btn"):
            if pwd == _ADMIN_PASSWORD:
                st.session_state["admin_auth"] = True
                st.rerun()
            else:
                st.error("ACCESS DENIED")
        return

    st.success("AUTHENTICATED — welcome, operator.")

    if st.button("LOCK SESSION", key="admin_logout"):
        st.session_state["admin_auth"] = False
        st.rerun()

    st.divider()

    # ── Raw session state ──────────────────────────────────────────────────────
    _section("Raw Session State")
    safe_state = {k: v for k, v in st.session_state.items() if k != "admin_pwd_input"}
    st.json(safe_state)

    col1, col2 = st.columns(2)
    with col1:
        if st.button("CLEAR ALL STATE", key="admin_clear_state"):
            preserved = {"admin_auth": True}
            for k in list(st.session_state.keys()):
                del st.session_state[k]
            st.session_state.update(preserved)
            st.rerun()
    with col2:
        if st.button("CLEAR GAME LOGS ONLY", key="admin_clear_logs"):
            for key in ("ng_history", "cb_history", "ng_score", "cb_score"):
                if key in st.session_state:
                    del st.session_state[key]
            st.rerun()

    # ── Number Guesser history ─────────────────────────────────────────────────
    _section("Number Guesser — Guess Log")
    ng_history = st.session_state.get("ng_history", [])
    if ng_history:
        st.dataframe(ng_history, use_container_width=True)
        _render_guess_chart(ng_history)
    else:
        st.caption("No guesses recorded yet.")

    # ── Code Breaker history ───────────────────────────────────────────────────
    _section("Code Breaker — Guess Log")
    cb_history = st.session_state.get("cb_history", [])
    if cb_history:
        st.dataframe(cb_history, use_container_width=True)
    else:
        st.caption("No guesses recorded yet.")

    # ── Score ledger ───────────────────────────────────────────────────────────
    _section("Score Ledger")
    scores = {
        "Number Guesser": st.session_state.get("ng_score", 0),
        "Code Breaker":   st.session_state.get("cb_score", 0),
        "Total":          st.session_state.get("ng_score", 0) + st.session_state.get("cb_score", 0),
    }
    st.table(scores)

    # ── Secret reveal ─────────────────────────────────────────────────────────
    _section("Secret Values (cheat view)")
    col_a, col_b = st.columns(2)
    with col_a:
        ng_secret = st.session_state.get("ng_secret")
        st.metric("Number Guesser secret", ng_secret if ng_secret is not None else "—")
    with col_b:
        cb_secret = st.session_state.get("cb_secret")
        cb_val = "".join(cb_secret) if cb_secret else "—"
        st.metric("Code Breaker secret", cb_val)

    # ── State override ────────────────────────────────────────────────────────
    _section("Manual State Override")
    st.warning("Editing raw session state. Incorrect types may break the app.")
    override_key = st.text_input("Key", key="admin_override_key")
    override_val = st.text_input("Value (JSON)", key="admin_override_val")
    if st.button("INJECT", key="admin_inject"):
        try:
            parsed = json.loads(override_val)
            st.session_state[override_key] = parsed
            st.success(f"Set `{override_key}` = `{parsed}`")
            st.rerun()
        except json.JSONDecodeError as exc:
            st.error(f"Invalid JSON: {exc}")

    # ── Timestamp ─────────────────────────────────────────────────────────────
    st.caption(f"Panel rendered at {datetime.now().isoformat(timespec='seconds')}")


def _render_guess_chart(history: list[dict]):
    """Bar chart of guess values over attempts (number guesser only)."""
    try:
        import altair as alt
        import pandas as pd
        df = pd.DataFrame(history)
        if "guess" in df.columns and "attempt" in df.columns:
            chart = (
                alt.Chart(df)
                .mark_bar(color="#00ff41")
                .encode(
                    x=alt.X("attempt:O", title="Attempt"),
                    y=alt.Y("guess:Q", title="Guess Value"),
                    tooltip=["attempt", "guess", "outcome"],
                )
                .properties(title="Guess Trajectory", background="#111111")
            )
            st.altair_chart(chart, use_container_width=True)
    except ImportError:
        st.caption("Install altair for guess charts.")
