"""Local LLM client for Ollama (PRD FR-04, FR-08).

Answers are constrained to the retrieved passages by prompt, and we detect an
"insufficient information" reply. NOTE: citation badges are NOT produced here —
the caller builds them from retrieval metadata (PRD section 15), because a model
will happily invent a page number.
"""

from __future__ import annotations

from typing import List

import requests

import config

INSUFFICIENT_MARKER = "INSUFFICIENT_INFORMATION"

_SYSTEM_PROMPT = (
    "You are RescueDesk AI, an emergency-preparedness reference assistant. "
    "Answer ONLY using the CONTEXT blocks provided by the user. Each context "
    "block has a numeric id. Cite nothing yourself; the app attaches sources. "
    "If the context does not contain enough information to answer, reply with "
    f"exactly this token and nothing else: {INSUFFICIENT_MARKER}. "
    "Do not give medical, evacuation or official-order instructions that are "
    "not present in the context. Be concise."
)


class ModelUnavailableError(Exception):
    """Raised when the local runtime cannot be reached or cannot answer."""


def model_available() -> bool:
    """Health probe against the loopback Ollama API (PRD FR-01/FR-08)."""
    try:
        resp = requests.get(
            f"{config.OLLAMA_BASE_URL}/api/tags", timeout=5
        )
        if resp.status_code != 200:
            return False
        names = {m.get("name", "") for m in resp.json().get("models", [])}
        wanted = config.OLLAMA_MODEL
        # Ollama reports names like "llama3.2:3b"; match with or without tag.
        return any(n == wanted or n.split(":")[0] == wanted.split(":")[0]
                   for n in names) or wanted in names
    except Exception:
        return False


def _build_prompt(question: str, passages: List[dict]) -> str:
    blocks = []
    for i, p in enumerate(passages, start=1):
        meta = f"doc={p['doc_name']}"
        if p.get("page"):
            meta += f" page={p['page']}"
        if p.get("section"):
            meta += f" section={p['section']}"
        blocks.append(f"[context {i} | {meta}]\n{p['content']}")
    context = "\n\n".join(blocks)
    return (
        f"CONTEXT:\n{context}\n\n"
        f"QUESTION: {question}\n\n"
        "ANSWER (from context only, or the insufficient token):"
    )


def answer_question(question: str, passages: List[dict]) -> str:
    if not passages:
        return INSUFFICIENT_MARKER
    payload = {
        "model": config.OLLAMA_MODEL,
        "prompt": _build_prompt(question, passages),
        "system": _SYSTEM_PROMPT,
        "stream": False,
        "options": {"temperature": 0},
    }
    try:
        resp = requests.post(
            f"{config.OLLAMA_BASE_URL}/api/generate",
            json=payload,
            timeout=config.OLLAMA_TIMEOUT_SECONDS,
        )
    except requests.RequestException as exc:
        raise ModelUnavailableError(
            f"Could not reach local model runtime at {config.OLLAMA_BASE_URL}: {exc}"
        ) from exc
    if resp.status_code != 200:
        raise ModelUnavailableError(
            f"Local model returned HTTP {resp.status_code}: {resp.text[:200]}"
        )
    text = (resp.json().get("response") or "").strip()
    if not text:
        raise ModelUnavailableError("Local model returned an empty response.")
    return text
