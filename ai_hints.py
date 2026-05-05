"""RAG-based hint engine. No Streamlit imports.

Pipeline:
  1. Load and chunk knowledge_base/*.md files
  2. TF-IDF vectorize all chunks + query
  3. Cosine similarity → retrieve top-k chunks
  4. Call Claude with retrieved context + game state → hint
"""

import math
import re
from pathlib import Path

KB_DIR = Path(__file__).parent / "knowledge_base"
CHUNK_SIZE = 500  # target chars per chunk
_CACHE: list[dict] | None = None  # module-level chunk cache


def _load_chunks() -> list[dict]:
    global _CACHE
    if _CACHE is not None:
        return _CACHE

    chunks = []
    for md_file in sorted(KB_DIR.glob("*.md")):
        text = md_file.read_text(encoding="utf-8")
        paragraphs = re.split(r"\n\n+", text)
        current = ""
        for p in paragraphs:
            if len(current) + len(p) < CHUNK_SIZE:
                current = current + "\n\n" + p if current else p
            else:
                if current:
                    chunks.append({"source": md_file.stem, "text": current.strip()})
                current = p
        if current:
            chunks.append({"source": md_file.stem, "text": current.strip()})

    _CACHE = chunks
    return chunks


def _tokenize(text: str) -> list[str]:
    return re.findall(r"\b\w+\b", text.lower())


def _cosine_scores(chunks: list[dict], query: str) -> list[float]:
    """TF-IDF cosine similarity between query and each chunk. Pure Python."""
    docs = [c["text"] for c in chunks]
    all_docs = docs + [query]
    tokenized = [_tokenize(d) for d in all_docs]

    vocab = list({tok for tokens in tokenized for tok in tokens})
    n = len(all_docs)

    # IDF: log((N+1)/(df+1)) + 1  (smoothed)
    idf = {}
    for term in vocab:
        df = sum(1 for tokens in tokenized if term in tokens)
        idf[term] = math.log((n + 1) / (df + 1)) + 1

    def tfidf_vec(tokens: list[str]) -> list[float]:
        freq = {}
        for t in tokens:
            freq[t] = freq.get(t, 0) + 1
        length = len(tokens) or 1
        return [(freq.get(v, 0) / length) * idf[v] for v in vocab]

    def cosine(a: list[float], b: list[float]) -> float:
        dot = sum(x * y for x, y in zip(a, b))
        na = math.sqrt(sum(x * x for x in a))
        nb = math.sqrt(sum(x * x for x in b))
        return dot / (na * nb) if na and nb else 0.0

    query_vec = tfidf_vec(tokenized[-1])
    return [cosine(tfidf_vec(tokenized[i]), query_vec) for i in range(len(chunks))]


def _retrieve(query: str, k: int = 3) -> list[dict]:
    chunks = _load_chunks()
    if not chunks:
        return []
    scores = _cosine_scores(chunks, query)
    ranked = sorted(zip(scores, chunks), key=lambda x: x[0], reverse=True)
    return [c for _, c in ranked[:k]]


def generate_hint(api_key: str, game_type: str, game_state: dict) -> str:
    """RAG pipeline: retrieve strategy docs → call Claude → return hint string."""
    from anthropic import Anthropic

    if game_type == "number_guesser":
        query = (
            f"number guesser binary search range {game_state.get('lo')}-{game_state.get('hi')} "
            f"guess history {game_state.get('history')} outcome {game_state.get('last_outcome')} "
            "scoring strategy attempts"
        )
    else:
        query = (
            f"mastermind code breaker constraint elimination strategy "
            f"exact close feedback guess history {game_state.get('history')} "
            "scoring optimize attempts"
        )

    chunks = _retrieve(query, k=3)
    context = "\n\n---\n\n".join(
        f"[Source: {c['source']}]\n{c['text']}" for c in chunks
    )

    if game_type == "number_guesser":
        user_msg = (
            f"Number Guesser — Range: {game_state['lo']}–{game_state['hi']} | "
            f"Attempts: {game_state['attempts']}/{game_state['max_attempts']} | "
            f"Guess history (guess, outcome): {game_state.get('history', [])} | "
            f"Last outcome: {game_state.get('last_outcome', 'N/A')}. "
            "Give me a specific tactical hint for my next guess."
        )
    else:
        user_msg = (
            f"Code Breaker — Attempts: {game_state['attempts']}/10 | "
            f"Guess history (code, exact, close): {game_state.get('history', [])}. "
            "Give me a tactical hint to narrow down the secret code."
        )

    client = Anthropic(api_key=api_key)
    response = client.messages.create(
        model="claude-haiku-4-5-20251001",
        max_tokens=200,
        system=(
            "You are a hacker AI assistant embedded in a terminal game suite. "
            "Give a concise tactical hint (2–3 sentences max). "
            "Be specific — reference the actual game state numbers. "
            "Stay terse and terminal-like. Use the retrieved strategy context below.\n\n"
            f"RETRIEVED STRATEGY CONTEXT:\n{context}"
        ),
        messages=[{"role": "user", "content": user_msg}],
    )
    return response.content[0].text
