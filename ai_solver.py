"""Agentic solver — Claude autonomously plays Number Guesser and Code Breaker
via a tool-use loop. No Streamlit imports.

Each solver function returns a list of step-event dicts for the UI to render:
  {"type": "thought",     "text": str}
  {"type": "tool_call",   "name": str, "input": dict}
  {"type": "tool_result", "name": str, "result": any, ...game-specific fields}
  {"type": "done",        "won": bool, "attempts": int, "secret": str}
"""

import json

from logic_utils import check_guess, get_range_for_difficulty, get_limit_for_difficulty
from codebreaker_logic import (
    evaluate_guess,
    parse_code_input,
    feedback_symbols,
    CODE_LENGTH,
    MAX_ATTEMPTS,
)

_MODEL = "claude-haiku-4-5-20251001"

# ── Number Guesser solver ──────────────────────────────────────────────────────

_NG_TOOLS = [
    {
        "name": "submit_guess",
        "description": (
            "Submit an integer guess to the Number Guesser game. "
            "Returns 'correct', 'too_high', or 'too_low'."
        ),
        "input_schema": {
            "type": "object",
            "properties": {
                "guess": {"type": "integer", "description": "The integer to guess."},
            },
            "required": ["guess"],
        },
    },
    {
        "name": "get_history",
        "description": "Return the list of all prior guesses and their outcomes.",
        "input_schema": {"type": "object", "properties": {}, "required": []},
    },
]


def solve_number_guesser(
    api_key: str, secret: int, difficulty: str, model: str = _MODEL
) -> list[dict]:
    lo, hi = get_range_for_difficulty(difficulty)
    max_att = get_limit_for_difficulty(difficulty)
    from anthropic import Anthropic
    client = Anthropic(api_key=api_key)

    history: list[dict] = []
    steps: list[dict] = []
    messages = [
        {
            "role": "user",
            "content": (
                f"Start solving Number Guesser. Range {lo}–{hi}, {max_att} attempts max. "
                "Use binary search. Keep guessing until you get 'correct'."
            ),
        }
    ]

    system = (
        f"You are an AI agent solving a Number Guessing game autonomously. "
        f"The secret integer is in the range {lo}–{hi}. "
        f"You have {max_att} attempts. "
        "Use pure binary search: always guess the midpoint of the remaining valid range. "
        "Track your own lo/hi bounds based on feedback. "
        "You MUST keep calling submit_guess until the result is 'correct' or you exhaust attempts."
    )

    attempts = 0
    while attempts < max_att:
        response = client.messages.create(
            model=model,
            max_tokens=512,
            system=system,
            tools=_NG_TOOLS,
            messages=messages,
        )

        text_parts = [b.text for b in response.content if b.type == "text"]
        if text_parts:
            steps.append({"type": "thought", "text": " ".join(text_parts)})

        if response.stop_reason not in ("tool_use",):
            break

        tool_results = []
        for block in response.content:
            if block.type != "tool_use":
                continue

            steps.append({"type": "tool_call", "name": block.name, "input": block.input})

            if block.name == "submit_guess":
                g = int(block.input.get("guess", 0))
                outcome = check_guess(g, secret)
                attempts += 1
                history.append({"attempt": attempts, "guess": g, "outcome": outcome})
                steps.append(
                    {
                        "type": "tool_result",
                        "name": "submit_guess",
                        "result": outcome,
                        "guess": g,
                        "attempt": attempts,
                    }
                )
                tool_results.append(
                    {"type": "tool_result", "tool_use_id": block.id, "content": outcome}
                )
                if outcome == "correct":
                    steps.append(
                        {"type": "done", "won": True, "attempts": attempts, "secret": str(secret)}
                    )
                    return steps

            elif block.name == "get_history":
                hist_json = json.dumps(history)
                tool_results.append(
                    {"type": "tool_result", "tool_use_id": block.id, "content": hist_json}
                )
                steps.append({"type": "tool_result", "name": "get_history", "result": history})

        messages.append({"role": "assistant", "content": response.content})
        messages.append({"role": "user", "content": tool_results})

        if attempts >= max_att:
            break

    steps.append({"type": "done", "won": False, "attempts": attempts, "secret": str(secret)})
    return steps


# ── Code Breaker solver ────────────────────────────────────────────────────────

_CB_TOOLS = [
    {
        "name": "submit_code",
        "description": (
            f"Submit a {CODE_LENGTH}-digit code guess (each digit 1–6). "
            "Returns exact count (right digit, right position) and close count (right digit, wrong position)."
        ),
        "input_schema": {
            "type": "object",
            "properties": {
                "code": {
                    "type": "string",
                    "description": f"Exactly {CODE_LENGTH} digits, e.g. '1234'.",
                },
            },
            "required": ["code"],
        },
    },
    {
        "name": "get_history",
        "description": "Return all prior code guesses with their exact/close feedback.",
        "input_schema": {"type": "object", "properties": {}, "required": []},
    },
]


def solve_codebreaker(
    api_key: str, secret: list[str], model: str = _MODEL
) -> list[dict]:
    from anthropic import Anthropic
    client = Anthropic(api_key=api_key)
    secret_str = "".join(secret)

    history: list[dict] = []
    steps: list[dict] = []
    messages = [
        {
            "role": "user",
            "content": (
                f"Start solving Code Breaker. Secret is {CODE_LENGTH} digits (1–6, repeats allowed). "
                f"{MAX_ATTEMPTS} attempts max. Use constraint elimination. Keep guessing until exact={CODE_LENGTH}."
            ),
        }
    ]

    system = (
        f"You are an AI agent solving a Mastermind/Code Breaker game autonomously. "
        f"The secret is a {CODE_LENGTH}-digit code, each digit 1–6, repeats allowed. "
        f"You have {MAX_ATTEMPTS} attempts. "
        "Strategy: start with '1122' to test two digit pairs. "
        "Use exact/close counts to eliminate impossible codes. "
        "You MUST keep calling submit_code until exact=4 or you exhaust attempts. "
        "Think step-by-step about which codes are still possible after each response."
    )

    attempts = 0
    while attempts < MAX_ATTEMPTS:
        response = client.messages.create(
            model=model,
            max_tokens=640,
            system=system,
            tools=_CB_TOOLS,
            messages=messages,
        )

        text_parts = [b.text for b in response.content if b.type == "text"]
        if text_parts:
            steps.append({"type": "thought", "text": " ".join(text_parts)})

        if response.stop_reason not in ("tool_use",):
            break

        tool_results = []
        for block in response.content:
            if block.type != "tool_use":
                continue

            steps.append({"type": "tool_call", "name": block.name, "input": block.input})

            if block.name == "submit_code":
                parsed, err = parse_code_input(block.input.get("code", ""))
                if err:
                    err_msg = f"Invalid input: {err}"
                    tool_results.append(
                        {"type": "tool_result", "tool_use_id": block.id, "content": err_msg}
                    )
                    steps.append({"type": "tool_result", "name": "submit_code", "result": err_msg})
                    continue

                result = evaluate_guess(parsed, secret)
                attempts += 1
                symbols = feedback_symbols(result)
                record = {
                    "attempt": attempts,
                    "guess": "".join(parsed),
                    "exact": result["exact"],
                    "close": result["close"],
                    "symbols": symbols,
                }
                history.append(record)
                result_str = f"exact={result['exact']}, close={result['close']}, symbols={symbols}"
                steps.append(
                    {
                        "type": "tool_result",
                        "name": "submit_code",
                        "result": result_str,
                        "guess": "".join(parsed),
                        "attempt": attempts,
                        "exact": result["exact"],
                        "close": result["close"],
                    }
                )
                tool_results.append(
                    {"type": "tool_result", "tool_use_id": block.id, "content": result_str}
                )
                if result["exact"] == CODE_LENGTH:
                    steps.append(
                        {"type": "done", "won": True, "attempts": attempts, "secret": secret_str}
                    )
                    return steps

            elif block.name == "get_history":
                hist_json = json.dumps(history)
                tool_results.append(
                    {"type": "tool_result", "tool_use_id": block.id, "content": hist_json}
                )
                steps.append({"type": "tool_result", "name": "get_history", "result": history})

        messages.append({"role": "assistant", "content": response.content})
        messages.append({"role": "user", "content": tool_results})

        if attempts >= MAX_ATTEMPTS:
            break

    steps.append(
        {"type": "done", "won": False, "attempts": attempts, "secret": secret_str}
    )
    return steps
