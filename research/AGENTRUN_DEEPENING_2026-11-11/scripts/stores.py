"""Memory stores with background padding and a choice of retriever.

Used for the end-to-end "retriever x store size" experiment: every task's
memory is padded with background records about other fictional projects, and
the agent's memory_search is served by one of three retrievers:

  hash   the repository's memory.embed_text + cosine (vectorised; same ranking)
  bm25   rank_bm25 Okapi over normalised tokens
  dense  BAAI/bge-small-en-v1.5 sentence embeddings (GPU when available)

The interface matches memlab.MemoryStore (search, same_key), so the
configurations A-E, the reliability gate and the scorer are unchanged.
"""

from __future__ import annotations

import hashlib
import random

import numpy as np

import memlab
from memory import embed_text

_DENSE = {}
_PAD_CACHE = {}


def _pad_names(seed: int, n: int) -> list[str]:
    """Three-syllable names: cannot collide with the two-syllable benchmark names."""
    rng = random.Random(seed)
    seen, out = set(), []
    while len(out) < n:
        s = "".join(rng.choice(memlab._ON) + rng.choice(memlab._NU) for _ in range(3)) + rng.choice(memlab._CO)
        if s not in seen:
            seen.add(s)
            out.append(s.capitalize())
    return out


def background(n: int) -> list[dict]:
    """The same n background records for every task (deterministic)."""
    if n not in _PAD_CACHE:
        rng = random.Random(77001)
        names = _pad_names(77002, 2 * n + 50)
        w = memlab._World("eval2", 77003)
        w.names, w._i = names[n:], 0  # surnames for "lead" values
        attrs = list(memlab.ATTRS)
        recs = []
        for i in range(n):
            a = rng.choice(attrs)
            e = "Project " + names[i]
            v = w.value(a)
            recs.append({"entity": e, "attribute": a, "value": v, "recorded_on": w.day(),
                         "source": rng.choice(memlab._SOURCES), "text": memlab.ATTRS[a]["t"].format(e=e, v=v),
                         "record_id": f"b-{i:05d}"})
        _PAD_CACHE[n] = recs
    return _PAD_CACHE[n]


def _dense_model():
    if "m" not in _DENSE:
        import torch
        from sentence_transformers import SentenceTransformer
        _DENSE["m"] = SentenceTransformer("BAAI/bge-small-en-v1.5",
                                          device="cuda" if torch.cuda.is_available() else "cpu")
    return _DENSE["m"]


class PaddedStore:
    def __init__(self, task: dict, retriever: str, pad: int):
        self.retriever = retriever
        self.entries = list(task["memory"]) + background(pad)
        self.texts = [e["text"] for e in self.entries]
        key = (retriever, pad)
        # the background part of the index is identical for every task: build it once
        if key not in _DENSE:
            bg = [e["text"] for e in background(pad)]
            _DENSE[key] = self._index(bg)
        own = self._index(self.texts[:len(task["memory"])]) if retriever != "bm25" else None
        if retriever == "bm25":
            from rank_bm25 import BM25Okapi
            self.bm25 = BM25Okapi([memlab._norm(t).split() for t in self.texts])
        else:
            self.m = np.vstack([own, _DENSE[key]])

    def _index(self, texts):
        if self.retriever == "hash":
            m = np.array([embed_text(t) for t in texts], dtype=np.float32)
            return m / np.maximum(np.linalg.norm(m, axis=1, keepdims=True), 1e-12)
        if self.retriever == "dense":
            return _dense_model().encode(texts, batch_size=512, normalize_embeddings=True, convert_to_numpy=True,
                                         show_progress_bar=False)
        return None

    def search(self, query: str, top_k: int = memlab.TOP_K, min_similarity: float = memlab.MIN_SIM) -> list[dict]:
        if self.retriever == "bm25":
            sc = self.bm25.get_scores(memlab._norm(query).split())
            idx = np.argsort(-sc, kind="stable")[:top_k]
            return [self.entries[i] for i in idx if sc[i] > 0]
        if self.retriever == "hash":
            q = np.array(embed_text(query), dtype=np.float32)
            q = q / max(float(np.linalg.norm(q)), 1e-12)
            thr = min_similarity
        else:
            q = _dense_model().encode([query], normalize_embeddings=True, convert_to_numpy=True,
                                      show_progress_bar=False)[0]
            thr = -1.0  # the 0.2 threshold is specific to the hash embedding
        sc = self.m @ q
        idx = np.argsort(-sc, kind="stable")[:top_k]
        return [self.entries[i] for i in idx if sc[i] >= thr]

    def same_key(self, rec: dict) -> list[dict]:
        return [e for e in self.entries if e["entity"] == rec["entity"] and e["attribute"] == rec["attribute"]]


def make_factory(retriever: str, pad: int):
    return lambda task: PaddedStore(task, retriever, pad)


def describe(retriever: str, pad: int) -> dict:
    bg = background(pad)
    return {"retriever": retriever, "pad": pad,
            "background_sha256": hashlib.sha256("\n".join(r["text"] for r in bg).encode()).hexdigest()}
