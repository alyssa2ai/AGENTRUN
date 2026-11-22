"""Independent recomputation of every number used in the MITACS dossier.

    py -3.11 build/verify_numbers.py          (from research/AGENTRUN_MITACS_INTERVIEW_2026-11-12)

Reads only raw outputs (raw_results/*/runs.jsonl, scores.json, results.jsonl,
results/results_verified.json, checkpoint-18/trainer_state.json) and scores
agent runs with the frozen scorer memlab.score_run. Aggregation, paired
differences, bootstrap intervals and McNemar tests are implemented here from
scratch, deliberately not reusing analyze.py / analyze_c2.py, so the result is
a second, independent computation.

Writes build/verified_numbers.json and prints a check of every figure the
dossier brief quotes against the recomputed value.
"""

from __future__ import annotations

import json
import random
import sys
from collections import Counter, defaultdict
from math import comb, sqrt
from pathlib import Path

HERE = Path(__file__).resolve().parent.parent
STUDY = HERE.parent / "AGENTRUN_DEEPENING_2026-11-11"
REPO = HERE.parent.parent
RAW = STUDY / "raw_results"
sys.path.insert(0, str(STUDY / "scripts"))
import memlab  # noqa: E402  (frozen scorer)

CFGS = "ABCDE"
SCEN = ["S1_context_loss", "S2_retrieval", "S3_conflict", "S4_stale", "S5_unsupported", "S6_tool_failure"]
SEED = 20261112


def tasks(split):
    return {json.loads(x)["task_id"]: json.loads(x)
            for x in (STUDY / "benchmark" / f"{split}.jsonl").read_text(encoding="utf-8").splitlines() if x.strip()}


T = {**tasks("dev"), **tasks("eval"), **tasks("eval2")}


def load_run(run_id):
    """{task_id: {config: score}} for complete blocks only (all five configs present)."""
    by = defaultdict(dict)
    for line in (RAW / run_id / "runs.jsonl").read_text(encoding="utf-8").splitlines():
        if line.strip():
            r = json.loads(line)
            s = memlab.score_run(T[r["task_id"]], r)
            s["n_tool_calls_raw"] = len(r["tool_calls"])
            s["repair_used"] = bool(r.get("repair_used"))
            s["final_value"] = (r.get("final") or {}).get("value")
            by[r["task_id"]][r["config"]] = s
    cfgs_present = {c for d in by.values() for c in d}
    return {t: d for t, d in by.items() if cfgs_present <= set(d)}


def wilson(k, n, z=1.96):
    p = k / n
    d = 1 + z * z / n
    c = (p + z * z / (2 * n)) / d
    h = z * sqrt(p * (1 - p) / n + z * z / (4 * n * n)) / d
    return max(0.0, c - h), min(1.0, c + h)


def mcnemar(b, c):
    n = b + c
    return 1.0 if n == 0 else min(1.0, 2 * sum(comb(n, i) for i in range(min(b, c) + 1)) / 2 ** n)


def paired(blocks, a, b, key="success", scen=None):
    """blocks: list of (cluster_id, {config: score}). a - b, bootstrap over clusters (tasks)."""
    units = [(cl, d[a][key], d[b][key]) for cl, d in blocks
             if a in d and b in d and (scen is None or d[a]["scenario"] == scen)]
    diffs = [int(x) - int(y) for _, x, y in units]
    plus, minus = diffs.count(1), diffs.count(-1)
    by = defaultdict(list)
    for (cl, _, _), dv in zip(units, diffs):
        by[cl].append(dv)
    keys = sorted(by)
    rng = random.Random(SEED)
    boots = []
    for _ in range(4000):
        s = [v for k in (rng.choice(keys) for _ in keys) for v in by[k]]
        boots.append(sum(s) / len(s))
    boots.sort()
    n = len(diffs)
    return {"n": n, "first": sum(int(x) for _, x, _ in units) / n, "second": sum(int(y) for _, _, y in units) / n,
            "diff_pp": 100 * sum(diffs) / n, "ci_pp": [100 * boots[int(0.025 * len(boots))],
                                                       100 * boots[int(0.975 * len(boots)) - 1]],
            "first_only": plus, "second_only": minus, "p_mcnemar": mcnemar(plus, minus)}


def summarise(blocks):
    out = {"n_blocks": len(blocks), "configs": {}}
    for c in CFGS:
        rows = [d[c] for _, d in blocks if c in d]
        if not rows:
            continue
        k = sum(r["success"] for r in rows)
        lo, hi = wilson(k, len(rows))
        out["configs"][c] = {"n": len(rows), "success": k, "pct": 100 * k / len(rows), "wilson95": [100 * lo, 100 * hi],
                             "harmful": sum(r["harmful"] for r in rows),
                             "format_or_steps": sum(r["outcome"] in ("format_error", "max_steps") for r in rows),
                             "outcomes": dict(Counter(r["outcome"] for r in rows)),
                             "by_scenario": {s: [sum(r["success"] for r in rows if r["scenario"] == s),
                                                 sum(r["scenario"] == s for r in rows)] for s in SCEN}}
    out["verifier"] = {}
    for c in "CDE":
        rows = [d[c] for _, d in blocks if c in d and d[c]["verdict"] is not None]
        bad = [r["draft_outcome"] != "correct" for r in rows]
        rej = [r["verdict"] in ("UNSUPPORTED", "CONFLICT") for r in rows]
        out["verifier"][c] = {"checked": len(rows), "tp": sum(b and j for b, j in zip(bad, rej)),
                              "fp": sum((not b) and j for b, j in zip(bad, rej)),
                              "fn": sum(b and not j for b, j in zip(bad, rej)),
                              "tn": sum((not b) and not j for b, j in zip(bad, rej))}
    pairs = [("B", "A"), ("C", "B"), ("D", "C"), ("E", "D"), ("E", "B"), ("E", "A")]
    out["paired"] = {f"{a}-{b}": paired(blocks, a, b) for a, b in pairs
                     if all(a in d and b in d for _, d in blocks)}
    out["paired_harmful"] = {f"{a}-{b}": paired(blocks, a, b, "harmful") for a, b in pairs
                             if all(a in d and b in d for _, d in blocks)}
    return out


def blocks_of(run_ids):
    out = []
    for rid in run_ids:
        for t, d in load_run(rid).items():
            out.append((t, d))  # cluster = task id, so a task's results across models resample together
    return out


V = {"_note": "Recomputed from raw outputs by build/verify_numbers.py; see the module docstring."}

# ---- historical 23-task results (committed result files, re-tallied by results/verify_results.py)
hist = json.loads((REPO / "results" / "results_verified.json").read_text(encoding="utf-8"))
V["historical_23"] = {k: {"passed": v["passed"], "total": v["total"], "pct": v["pct"]} for k, v in hist["conditions"].items()}

# ---- campaign 1 (48-task eval split)
local1 = ["hpc_qwen25_7b_greedy_t1", "hpc_qwen3_8b_greedy_t1", "hpc_qwen25_7b_lora_greedy_t1"]
hosted1 = ["eval_qwen38_27b_t1", "eval_gptoss120b_t1", "eval_gptoss20b_t1"]
V["c1_local_greedy"] = summarise(blocks_of(local1))
V["c1_local_greedy"]["per_run"] = {r: summarise(blocks_of([r]))["configs"] for r in local1}
V["c1_hosted"] = summarise(blocks_of(hosted1))
V["c1_hosted"]["per_run_blocks"] = {r: len(load_run(r)) for r in hosted1}
local_all = local1 + ["hpc_qwen25_7b_temp07_seed1", "hpc_qwen25_7b_temp07_seed2", "hpc_qwen3_8b_temp07_seed1"]
V["c1_local_all6"] = {"n_blocks": len(blocks_of(local_all)),
                      "per_run": {r: {c: v["success"] for c, v in summarise(blocks_of([r]))["configs"].items()}
                                  for r in local_all}}

# ---- campaign 2 (96-task eval2 split)
c2 = {}
for rid in ["c2_qwen25_7b_v1", "c2_qwen3_8b_v1", "c2_qwen25_7b_v2", "c2_qwen3_8b_v2", "c2_qwen25_1p5b_v1",
            "c2_qwen25_1p5b_v2", "c2_qwen25_3b_v1", "c2_qwen25_3b_v2", "c2_qwen25_14b_v1", "c2_qwen25_14b_v2"]:
    b = blocks_of([rid])
    s = summarise(b)
    rows = [d[c] for _, d in b for c in d]
    s["all"] = {"runs": len(rows), "success": sum(r["success"] for r in rows), "harmful": sum(r["harmful"] for r in rows),
                "harmful_empty_value": sum(r["harmful"] and (r["final_value"] is None or str(r["final_value"]).strip() == "")
                                           for r in rows),
                "harmful_zero_tool_calls": sum(r["harmful"] and r["n_tool_calls_raw"] == 0 for r in rows),
                "format_or_steps": sum(r["outcome"] in ("format_error", "max_steps") for r in rows),
                "outcomes": dict(Counter(r["outcome"] for r in rows)),
                "repair_used": sum(r["repair_used"] for r in rows),
                "repair_then_correct": sum(r["repair_used"] and r["success"] for r in rows),
                "memory_used_S1_S4_BtoE": [sum(d[c]["n_memory_calls"] > 0 for _, d in b for c in "BCDE"
                                               if d[c]["scenario"][:2] in ("S1", "S2", "S3", "S4")),
                                           sum(1 for _, d in b for c in "BCDE" if d[c]["scenario"][:2] in ("S1", "S2", "S3", "S4"))],
                "fallback_success_BtoE": [sum(d[c]["success"] for _, d in b for c in "BCDE"
                                              if d[c]["variant"] == "permanent_memory_fallback"),
                                          sum(1 for _, d in b for c in "BCDE" if d[c]["variant"] == "permanent_memory_fallback")]}
    c2[rid] = s
V["c2_runs"] = c2
pool_v1 = blocks_of(["c2_qwen25_7b_v1"]) + [(t + "|q3", d) for t, d in blocks_of(["c2_qwen3_8b_v1"])]
pool_v2 = blocks_of(["c2_qwen25_7b_v2"]) + [(t + "|q3", d) for t, d in blocks_of(["c2_qwen3_8b_v2"])]
# pooled: cluster on task id so both models' results for a task resample together
pool_v1 = [(t.split("|")[0], d) for t, d in pool_v1]
pool_v2 = [(t.split("|")[0], d) for t, d in pool_v2]
V["c2_pooled_v1"] = summarise(pool_v1)
V["c2_pooled_v2"] = summarise(pool_v2)


def harness_pair(m):
    a, b = load_run(f"c2_{m}_v2"), load_run(f"c2_{m}_v1")
    units = [(t, {"v2": a[t][c], "v1": b[t][c], "scenario": a[t][c]["scenario"]}) for t in a for c in CFGS]
    return paired([(t, {"v2": u["v2"], "v1": u["v1"]}) for t, u in units], "v2", "v1")


V["c2_harness_v2_minus_v1"] = {m: harness_pair(m) for m in ["qwen25_7b", "qwen3_8b"]}

# retriever end to end: S1-S4, configs B, D, E; paired on (task, config)
def e2e(rid, base=None):
    d = load_run(rid)
    rows = {(t, c): d[t][c] for t in d for c in "BDE" if d[t][c]["scenario"][:2] in ("S1", "S2", "S3", "S4")}
    return rows


nopad = e2e("c2_qwen25_7b_v2")
hashp = e2e("c2_qwen25_7b_v2_hash_pad2000")
bm25p = e2e("c2_qwen25_7b_v2_bm25_pad2000")


def pair_rows(x, y):
    keys = sorted(set(x) & set(y))
    return paired([(k[0], {"x": x[k], "y": y[k]}) for k in keys], "x", "y")


V["c2_retriever_e2e"] = {
    "success": {n: [sum(r["success"] for r in rows.values()), len(rows)]
                for n, rows in [("no_padding_hash", nopad), ("hash_2000", hashp), ("bm25_2000", bm25p)]},
    "by_config": {n: {c: sum(r["success"] for (t, cc), r in rows.items() if cc == c) for c in "BDE"}
                  for n, rows in [("no_padding_hash", nopad), ("hash_2000", hashp), ("bm25_2000", bm25p)]},
    "harmful": {n: sum(r["harmful"] for r in rows.values())
                for n, rows in [("no_padding_hash", nopad), ("hash_2000", hashp), ("bm25_2000", bm25p)]},
    "gold_recall_union_mean": {n: (lambda xs: sum(xs) / len(xs))([r["recall_union"] for r in rows.values()
                                                                   if r["recall_union"] is not None])
                               for n, rows in [("no_padding_hash", nopad), ("hash_2000", hashp), ("bm25_2000", bm25p)]},
    "hash2000_minus_nopad": pair_rows(hashp, nopad), "bm25_minus_hash2000": pair_rows(bm25p, hashp)}

# ---- repository benchmarks (client-matched)
bench = {}
for d in sorted(RAW.glob("c2_legacy23_*")) + sorted(RAW.glob("c2_v2dev55_*")):
    f = d / "scores.json"
    if f.exists():
        s = json.loads(f.read_text(encoding="utf-8"))
        if "legacy" in d.name:
            bench[d.name] = {"r0_pass": sum(bool(x["r0"]) for x in s["per_task"]), "n": len(s["per_task"]),
                             "failed": [x["task_id"] for x in s["per_task"] if not x["r0"]]}
        else:
            bench[d.name] = {"r2_correct": sum(bool(x["correct"]) for x in s["per_task"]), "n": len(s["per_task"])}
V["repo_benchmarks"] = bench
raw_header = (REPO / "adapter_model.safetensors").open("rb")
hlen = int.from_bytes(raw_header.read(8), "little")
header = json.loads(raw_header.read(hlen))
raw_header.close()
n_params, shapes = 0, Counter()
for name, meta in header.items():
    if name == "__metadata__":
        continue
    k = 1
    for d in meta["shape"]:
        k *= d
    n_params += k
    shapes[(name.split(".")[-2] if "lora_" in name else name, tuple(meta["shape"]))] += 1
V["adapter_params"] = {"trainable_params": n_params, "tensors": len(header) - ("__metadata__" in header),
                       "dtype": sorted({m["dtype"] for n, m in header.items() if n != "__metadata__"}),
                       "example_shapes": {f"{k[0]} {list(k[1])}": v for k, v in sorted(shapes.items())[:8]}}
st = json.loads((REPO / "checkpoint-18" / "trainer_state.json").read_text(encoding="utf-8"))
V["adapter_identity"] = {"global_step": st["global_step"], "epochs": st["epoch"],
                         "steps_per_epoch": st["global_step"] / st["epoch"],
                         "expected_steps_per_epoch": {"V1 (35 examples)": -(-(-(-35 // 2)) // 4),
                                                      "V2 (46 examples)": -(-(-(-46 // 2)) // 4)}}

# ---- retrieval only (campaign 1 follow-up, job 4144): mean over seeds
rr = [json.loads(x) for x in (RAW / "hpc_retrieval_bench" / "results.jsonl").read_text(encoding="utf-8").splitlines() if x.strip()]
agg = defaultdict(list)
for r in rr:
    agg[(r["retriever"].split(" (")[0] + (" (cuda)" if "(cuda)" in r["retriever"] else " (cpu)" if "(cpu)" in r["retriever"] else ""),
         r["query_style"], r["size"])].append(r)
V["retrieval_only"] = {f"{k[0]} | {k[1]} | {k[2]}": {
    "seeds": len(v), "recall@4": sum(x["metrics"]["k4"]["recall"] for x in v) / len(v),
    "recall@10": sum(x["metrics"]["k10"]["recall"] for x in v) / len(v),
    "mrr@10": sum(x["metrics"]["k10"]["mrr"] for x in v) / len(v),
    "stale_exposure@4": sum(x["metrics"]["k4"]["pair_only_older_retrieved"] for x in v) / len(v),
    "index_s": sum(x["index_s"] for x in v) / len(v), "query_ms": sum(x["query_ms_mean"] for x in v) / len(v)}
    for k, v in sorted(agg.items())}

# ---- counts
V["counts"] = {"c1_local_runs": sum(len(load_run(r)) * 5 for r in local_all),
               "c2_agent_runs": sum(c2[r]["all"]["runs"] for r in c2) + len(hashp) + len(bm25p),
               "c2_benchmark_task_evals_local": sum(v["n"] for v in bench.values()),
               "c2_benchmark_task_evals_incl_log_only": sum(v["n"] for v in bench.values()) + 55}

(HERE / "build" / "verified_numbers.json").write_text(json.dumps(V, indent=1), encoding="utf-8")

# ---- check against the figures quoted in the brief
def pct(run, c):
    return round(V[run]["configs"][c]["pct"], 1)


checks = [
    ("c1 local A-E", [pct("c1_local_greedy", c) for c in CFGS], [21.5, 45.8, 36.1, 53.5, 63.2]),
    ("c1 hosted A-E", [pct("c1_hosted", c) for c in CFGS], [28.2, 67.6, 66.2, 71.8, 70.4]),
    ("c2 Qwen2.5-7B v1 A-E", [round(c2["c2_qwen25_7b_v1"]["configs"][c]["pct"], 1) for c in CFGS], [25.0, 50.0, 41.7, 58.3, 72.9]),
    ("c2 Qwen3-8B v1 A-E", [round(c2["c2_qwen3_8b_v1"]["configs"][c]["pct"], 1) for c in CFGS], [24.0, 63.5, 61.5, 65.6, 77.1]),
    ("c2 pooled v1 A-E", [pct("c2_pooled_v1", c) for c in CFGS], [24.5, 56.8, 51.6, 62.0, 75.0]),
    ("c2 pooled v2 A-E", [pct("c2_pooled_v2", c) for c in CFGS], [29.2, 81.8, 70.3, 75.5, 92.2]),
    ("c2 pooled v1 diffs B-A, C-B, D-C, E-D", [round(V["c2_pooled_v1"]["paired"][k]["diff_pp"], 1) for k in ("B-A", "C-B", "D-C", "E-D")],
     [32.3, -5.2, 10.4, 13.0]),
    ("harness v2-v1 (7B, Q3)", [round(V["c2_harness_v2_minus_v1"][m]["diff_pp"], 1) for m in ("qwen25_7b", "qwen3_8b")], [15.8, 15.8]),
    ("adapter steps/epoch", [V["adapter_identity"]["steps_per_epoch"]], [6.0]),
    ("legacy adapter 23/23 x5", sorted(v["r0_pass"] for k, v in bench.items() if "legacy23_adapter" in k), [23, 23, 23, 23, 23]),
    ("v2dev base b6, adapter b6 (pct)", [round(100 * bench["c2_v2dev55_base_b6"]["r2_correct"] / 55, 1),
                                         round(100 * bench["c2_v2dev55_adapter_b6"]["r2_correct"] / 55, 1)], [94.5, 92.7]),
    ("e2e success no-pad, hash2000, bm25 (pct)", [round(100 * a / b, 1) for a, b in V["c2_retriever_e2e"]["success"].values()],
     [71.4, 41.7, 70.3]),
    ("retrieval-only hash nl recall@4 2k/100k", [round(V["retrieval_only"]["hash256 | nl | 2000"]["recall@4"], 2),
                                                 round(V["retrieval_only"]["hash256 | nl | 100000"]["recall@4"], 2)], [0.46, 0.05]),
]
bad = 0
for name, got, exp in checks:
    ok = all(abs(g - e) < 0.051 for g, e in zip(got, exp)) and len(got) == len(exp)
    bad += not ok
    print(("MATCH   " if ok else "MISMATCH") + f" {name}: recomputed {got} | quoted {exp}")
print("counts:", V["counts"])
print("mismatches:", bad)
