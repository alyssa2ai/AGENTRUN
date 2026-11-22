"""Retrieval experiment at scale (no language model).

Compares the repository's hashed bag-of-words embedding (memory.embed_text)
with BM25 and dense sentence embeddings on memory stores of growing size, and
measures how often a fixed top-k shows the agent a stale record without the
newer one, or only one side of a conflict.

    python retrieval_bench.py --out ../raw_results/hpc_retrieval_bench --sizes 1000,10000,100000 --seeds 1,2,3

Appends one JSON line per (seed, size, retriever, query style) to
results.jsonl and skips combinations that are already there.
"""

from __future__ import annotations

import argparse
import json
import platform
import random
import time
from pathlib import Path

import numpy as np

import memlab
from memory import cosine_similarity, embed_text

KS = (1, 4, 10)
N_FACT, N_PAIR = 150, 150  # single-fact queries; stale/conflict pair queries


def names(seed: int, n: int) -> list[str]:
    rng = random.Random(seed)
    seen, out = set(), []
    while len(out) < n:
        s = "".join(rng.choice(memlab._ON) + rng.choice(memlab._NU) for _ in range(3)) + rng.choice(memlab._CO)
        if s not in seen:
            seen.add(s)
            out.append("Project " + s.capitalize())
    return out


def build(seed: int, size: int):
    """Return (texts, queries). Each query: {"nl", "kw", "gold": [idx], "newer": idx or None}."""
    rng = random.Random(seed)
    attrs = list(memlab.ATTRS)
    w = memlab._World("eval", seed)  # only used for value generation
    pool = names(seed, size + 10)
    # person surnames for "lead" values: the memlab pool (1,450 names) is too small for large stores
    w.names = [x.split(" ")[1] for x in names(seed + 100000, size + 10)]
    w._i = 0
    texts, queries = [], []

    def add(e, a, v):
        texts.append(memlab.ATTRS[a]["t"].format(e=e, v=v))
        return len(texts) - 1

    kw = {"budget_usd": "approved budget", "team_size": "team size", "port": "staging server port",
          "lead": "lead", "region": "cloud region", "deadline": "delivery deadline"}
    it = iter(pool)
    for i in range(N_FACT + N_PAIR):
        e, a = next(it), attrs[i % len(attrs)]
        v = w.value(a)
        gold = [add(e, a, v)]
        newer = None
        if i >= N_FACT:  # same key, second value: index order = older then newer
            newer = add(e, a, w.value(a, avoid=v))
            gold.append(newer)
        for x in rng.sample([b for b in attrs if b != a], 3):  # same project, other attributes
            add(e, x, w.value(x))
        queries.append({"nl": memlab.ATTRS[a]["q"].format(e=e), "kw": f"{e} {kw[a]}", "gold": gold, "newer": newer})
    while len(texts) < size:  # background records
        a = rng.choice(attrs)
        add(next(it, None) or "Project " + str(len(texts)), a, w.value(a))
    return texts, queries


class Hash256:
    name = "hash256 (memory.embed_text, AGENTRUN default)"

    def index(self, texts):
        self.m = np.array([embed_text(t) for t in texts], dtype=np.float32)
        self.m /= np.maximum(np.linalg.norm(self.m, axis=1, keepdims=True), 1e-12)

    def topk(self, qs, k):
        q = np.array([embed_text(t) for t in qs], dtype=np.float32)
        q /= np.maximum(np.linalg.norm(q, axis=1, keepdims=True), 1e-12)
        return np.argsort(-(q @ self.m.T), axis=1, kind="stable")[:, :k]


class BM25:
    name = "bm25 (rank_bm25 Okapi)"

    def index(self, texts):
        from rank_bm25 import BM25Okapi
        self.b = BM25Okapi([memlab._norm(t).split() for t in texts])

    def topk(self, qs, k):
        return np.array([np.argsort(-self.b.get_scores(memlab._norm(q).split()), kind="stable")[:k] for q in qs])


class Dense:
    def __init__(self, model_id, device):
        from sentence_transformers import SentenceTransformer
        self.name = f"dense {model_id} ({device})"
        self.model = SentenceTransformer(model_id, device=device)
        self.device = device

    def index(self, texts):
        self.m = self.model.encode(texts, batch_size=1024, normalize_embeddings=True, convert_to_numpy=True,
                                   show_progress_bar=False)

    def topk(self, qs, k):
        q = self.model.encode(qs, batch_size=256, normalize_embeddings=True, convert_to_numpy=True,
                              show_progress_bar=False)
        return np.argsort(-(q @ self.m.T), axis=1, kind="stable")[:, :k]


def metrics(queries, top, style):
    out = {}
    for k in KS:
        rec, prec, mrr, both, stale_only, newer_only, neither = [], [], [], 0, 0, 0, 0
        n_pair = 0
        for q, row in zip(queries, top):
            hits = list(row[:k])
            g = set(q["gold"])
            rec.append(len(g & set(hits)) / len(g))
            prec.append(len(g & set(hits)) / k)
            rank = next((i + 1 for i, h in enumerate(row[:k]) if h in g), None)
            mrr.append(1 / rank if rank else 0.0)
            if q["newer"] is not None:
                n_pair += 1
                older = q["gold"][0]
                o, n = older in hits, q["newer"] in hits
                both += o and n
                stale_only += o and not n
                newer_only += n and not o
                neither += (not o) and (not n)
        out[f"k{k}"] = {"recall": float(np.mean(rec)), "precision": float(np.mean(prec)), "mrr": float(np.mean(mrr)),
                        "pair_both_retrieved": both / n_pair, "pair_only_older_retrieved": stale_only / n_pair,
                        "pair_only_newer_retrieved": newer_only / n_pair, "pair_neither": neither / n_pair,
                        "n_queries": len(queries), "n_pair_queries": n_pair}
    return out


def main() -> int:
    p = argparse.ArgumentParser()
    p.add_argument("--out", type=Path, required=True)
    p.add_argument("--sizes", default="1000,10000,100000")
    p.add_argument("--seeds", default="1,2,3")
    p.add_argument("--dense", default="sentence-transformers/all-MiniLM-L6-v2,BAAI/bge-small-en-v1.5")
    p.add_argument("--no-gpu", action="store_true")
    a = p.parse_args()
    a.out.mkdir(parents=True, exist_ok=True)
    res = a.out / "results.jsonl"
    done = set()
    if res.exists():
        for line in res.read_text(encoding="utf-8").splitlines():
            r = json.loads(line)
            done.add((r["seed"], r["size"], r["retriever"], r["query_style"]))

    env = {"python": platform.python_version(), "numpy": np.__version__, "host": platform.node()}
    retrievers = [Hash256(), BM25()]
    device = "cpu"
    try:
        import torch
        env["torch"] = torch.__version__
        if torch.cuda.is_available() and not a.no_gpu:
            device = "cuda"
            env["gpu"] = torch.cuda.get_device_name(0)
        import sentence_transformers
        env["sentence_transformers"] = sentence_transformers.__version__
        for mid in [m for m in a.dense.split(",") if m]:
            retrievers.append(Dense(mid, device))
            if device == "cuda":
                retrievers.append(Dense(mid, "cpu"))  # same model on CPU, for the throughput comparison only
    except Exception as e:  # dense retrievers unavailable: still run the lexical ones
        env["dense_unavailable"] = repr(e)
    (a.out / "manifest.json").write_text(json.dumps({"env": env, "args": {k: str(v) for k, v in vars(a).items()},
                                                    "n_fact_queries": N_FACT, "n_pair_queries": N_PAIR, "ks": KS,
                                                    "started_utc": time.strftime("%Y-%m-%dT%H:%M:%SZ", time.gmtime())},
                                                   indent=1))
    # equivalence check: vectorised cosine ranks like memory.cosine_similarity
    t, q = build(1, 1000)
    h = Hash256()
    h.index(t)
    ref = sorted(range(len(t)), key=lambda i: (-cosine_similarity(embed_text(q[0]["nl"]), embed_text(t[i])), i))[:4]
    print("hash256 vectorised top-4 equals pure-Python top-4:", list(h.topk([q[0]["nl"]], 4)[0]) == ref, flush=True)

    with open(res, "a", encoding="utf-8") as f:
        for seed in [int(s) for s in a.seeds.split(",")]:
            for size in [int(s) for s in a.sizes.split(",")]:
                texts, queries = build(seed, size)
                for r in retrievers:
                    if all((seed, size, r.name, st) in done for st in ("nl", "kw")):
                        continue
                    if isinstance(r, Dense) and r.device == "cpu" and size > 10000:
                        continue  # CPU dense encoding of 100k records is only a timing duplicate
                    t0 = time.perf_counter()
                    r.index(texts)
                    t_index = time.perf_counter() - t0
                    for st in ("nl", "kw"):
                        qs = [x[st] for x in queries]
                        t0 = time.perf_counter()
                        top = r.topk(qs, max(KS))
                        t_q = time.perf_counter() - t0
                        row = {"seed": seed, "size": size, "retriever": r.name, "query_style": st,
                               "index_s": round(t_index, 4), "records_per_s_index": round(size / t_index, 1),
                               "query_ms_mean": round(1000 * t_q / len(qs), 4), "metrics": metrics(queries, top, st)}
                        if "cuda" in r.name:
                            import torch
                            row["gpu_peak_mem_mib"] = round(torch.cuda.max_memory_allocated() / 2 ** 20, 1)
                        f.write(json.dumps(row) + "\n")
                        f.flush()
                        m = row["metrics"]["k4"]
                        print(f"seed={seed} size={size} {r.name} [{st}] recall@4={m['recall']:.3f} "
                              f"only_older@4={m['pair_only_older_retrieved']:.3f} index={t_index:.2f}s", flush=True)
    (a.out / "DONE").write_text(time.strftime("%Y-%m-%dT%H:%M:%SZ", time.gmtime()))
    print("done exit 0", flush=True)
    return 0


if __name__ == "__main__":
    raise SystemExit(main())
