"""Local keyword retrieval: BM25 over the chunk corpus (PRD section 8).

Implemented in pure Python so there is no extra dependency and so the whole
retrieval step is provably offline (no embeddings, no vector DB in the MVP).
Returns the top-K passages with their BM25 score and original metadata; the
caller uses these for BOTH the model context and the citation badges, keeping
citations grounded in retrieval rather than model output (PRD section 15).
"""

from __future__ import annotations

import math
import re
from collections import Counter
from typing import Dict, List

import config

_TOKEN_RE = re.compile(r"[a-z0-9]+")


def tokenize(text: str) -> List[str]:
    return _TOKEN_RE.findall(text.lower())


# Common English stop words; tiny list is enough for a demo corpus and keeps
# BM25 from matching on "the/a/is".
_STOP = {
    "the", "a", "an", "and", "or", "of", "to", "in", "on", "for", "is", "are",
    "be", "as", "at", "by", "with", "that", "this", "it", "from", "you", "your",
}


def _filter(tokens: List[str]) -> List[str]:
    return [t for t in tokens if t not in _STOP and len(t) > 1]


class Bm25Index:
    """Okapi BM25 index rebuilt from the (small) chunk corpus."""

    def __init__(self, chunks: List[dict]):
        self.chunks = chunks
        self.doc_tokens = [_filter(tokenize(c["content"])) for c in chunks]
        self.doc_freqs = [Counter(t) for t in self.doc_tokens]
        self.doc_lens = [len(t) for t in self.doc_tokens]
        self.n_docs = len(chunks)
        self.avg_len = (sum(self.doc_lens) / self.n_docs) if self.n_docs else 0.0
        self.k1 = 1.5
        self.b = 0.75
        self.df: Dict[str, int] = Counter()
        for freq in self.doc_freqs:
            for term in freq:
                self.df[term] += 1

    def _idf(self, term: str) -> float:
        df = self.df.get(term, 0)
        return math.log(1 + (self.n_docs - df + 0.5) / (df + 0.5))

    def score(self, query_tokens: List[str]) -> List[float]:
        scores = [0.0] * self.n_docs
        for i in range(self.n_docs):
            freqs = self.doc_freqs[i]
            dl = self.doc_lens[i] or 1
            norm = self.k1 * (1 - self.b + self.b * dl / (self.avg_len or 1))
            s = 0.0
            for term in query_tokens:
                tf = freqs.get(term, 0)
                if not tf:
                    continue
                idf = self._idf(term)
                s += idf * (tf * (self.k1 + 1)) / (tf + norm)
            scores[i] = s
        return scores


_INDEX: Bm25Index | None = None
_INDEX_SIGNATURE: tuple | None = None


def get_index(chunks: List[dict]) -> Bm25Index:
    """Cache the index; rebuild only when the corpus contents change."""
    global _INDEX, _INDEX_SIGNATURE
    signature = tuple(c["id"] for c in chunks)
    if _INDEX is None or signature != _INDEX_SIGNATURE:
        _INDEX = Bm25Index(chunks)
        _INDEX_SIGNATURE = signature
    return _INDEX


def retrieve(question: str, chunks: List[dict],
             top_k: int = None) -> List[dict]:
    """Return top-K scored passages. Empty list if corpus is empty."""
    if not chunks:
        return []
    top_k = top_k or config.TOP_K
    index = get_index(chunks)
    scores = index.score(_filter(tokenize(question)))
    ranked = sorted(
        ({"chunk": c, "score": s} for c, s in zip(chunks, scores)),
        key=lambda r: r["score"],
        reverse=True,
    )[:top_k]
    # Keep only passages that actually scored above the floor.
    return [r for r in ranked if r["score"] >= config.SCORE_THRESHOLD]
