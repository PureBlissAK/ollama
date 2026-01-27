"""SmartSuggestionsEngine prototype.

This engine uses a simple token-overlap scoring function as a placeholder
for embedding-based similarity. It is intentionally dependency-free so it
can be tested without heavy ML libraries. Replace _embed/_similarity with
real embedding calls in production.
"""

import math
from typing import Dict, List, Tuple


class SmartSuggestionsEngine:
    """Prototype suggestions engine.

    Methods
    -------
    suggest(query, candidates, top_k)
        Return top-k candidate strings with scores.
    """

    def __init__(self) -> None:
        pass

    def _embed(self, text: str) -> Dict[str, int]:
        """Simple bag-of-words token counts as a stand-in for embeddings."""
        toks = [t.lower() for t in text.split() if t]
        vec: Dict[str, int] = {}
        for t in toks:
            vec[t] = vec.get(t, 0) + 1
        return vec

    def _cosine(self, a: Dict[str, int], b: Dict[str, int]) -> float:
        # dot / (|a||b|)
        dot = 0.0
        for k, v in a.items():
            dot += v * b.get(k, 0)
        na = math.sqrt(sum(v * v for v in a.values()))
        nb = math.sqrt(sum(v * v for v in b.values()))
        if na == 0 or nb == 0:
            return 0.0
        return dot / (na * nb)

    def suggest(self, query: str, candidates: List[str], top_k: int = 3) -> List[Tuple[str, float]]:
        """Return top_k candidates ranked by simple similarity score.

        Returns a list of tuples (candidate, score) sorted by score desc.
        """
        qv = self._embed(query)
        scored: List[Tuple[str, float]] = []
        for c in candidates:
            cv = self._embed(c)
            score = self._cosine(qv, cv)
            scored.append((c, round(score, 4)))
        scored.sort(key=lambda x: x[1], reverse=True)
        return scored[:top_k]
