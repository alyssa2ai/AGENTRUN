"""Phase 3 GPU budget from MEASURED per-run times (CPU).

    python budget_phase3.py --out ../data/BUDGET_phase3                      # Phase 1 / job 4183 / job 4189 measurements
    python budget_phase3.py --runs ../raw/p2val2_*_greedy --out ../data/BUDGET_phase3   # replace with p2val2 measurements

Model: GPU-seconds of a cell = sum over configs of n_tasks x s_per_run(model, decoding, config), where
s_per_run = (measured agent wall time per run) + (for LA/LG) arbiter calls per run x measured arbiter latency.
With --runs, s_per_run is the mean `timing.total_s` per (model, config) from real greedy runs (which already
include arbiter calls), and T=0.7 cells are scaled by the measured T0.7/greedy ratio of the same family.
"""
from __future__ import annotations

import argparse
import json
from collections import defaultdict
from pathlib import Path

CONFIGS = "B,G,R,T,RT,EB,EBG,LA,LG,EBG-all,EBG-unsafe,EBG-noR3".split(",")
CELLS = [("Qwen/Qwen2.5-3B-Instruct", "greedy"), *[("Qwen/Qwen2.5-3B-Instruct", f"T07_s{i}") for i in (1, 2, 3)],
         ("Qwen/Qwen2.5-7B-Instruct", "greedy"), *[("Qwen/Qwen2.5-7B-Instruct", f"T07_s{i}") for i in (1, 2, 3)],
         ("meta-llama/Llama-3.1-8B-Instruct", "greedy"), *[("meta-llama/Llama-3.1-8B-Instruct", f"T07_s{i}") for i in (1, 2, 3)],
         ("Qwen/Qwen3-8B", "greedy"), *[("Qwen/Qwen3-8B", f"T07_s{i}") for i in (1, 2, 3)],
         ("Qwen/Qwen2.5-14B-Instruct", "greedy"), ("meta-llama/Llama-3.2-3B-Instruct", "greedy")]
# measured seconds per agent run, one L40, with provenance
MEASURED = {
    "Qwen/Qwen2.5-3B-Instruct": {"greedy": (2.1, "Phase 1 pilot p1/p1h greedy, 3 run sets (2.18, 1.80, 2.27)"),
                                 "T07": (3.2, "Phase 1 pilot T0.7 s1, s2 (2.11, 4.29)")},
    "Qwen/Qwen2.5-7B-Instruct": {"greedy": (4.0, "Phase 1 pilot greedy, 3 run sets (3.90, 3.81, 4.28)"),
                                 "T07": (8.2, "Phase 1 pilot T0.7 s1, s2 (7.90, 8.54)")},
    "meta-llama/Llama-3.1-8B-Instruct": {"greedy": (4.8, "Slurm job 4183: (117 s - 20.3 s load) / 20 runs, incl. process start"),
                                         "T07": (9.8, "greedy x 2.05, the measured Qwen2.5-7B T0.7/greedy ratio (not measured for Llama)")},
    "Qwen/Qwen3-8B": {"greedy": (5.5, "Phase 1 pilot greedy, 3 run sets (8.76, 3.79, 4.06), thinking disabled"),
                      "T07": (11.3, "greedy x 2.05, the measured Qwen2.5-7B T0.7/greedy ratio (not measured for Qwen3)")},
    "Qwen/Qwen2.5-14B-Instruct": {"greedy": (27.1, "Phase 1 pilot greedy, one run set (outside Slurm, 6.8 s/call; "
                                                    "scaled from job 4189 arbiter latency it would be ~9 s)")},
    "meta-llama/Llama-3.2-3B-Instruct": {"greedy": (2.2, "Slurm job 4183: (55 s - 11.2 s load) / 20 runs")},
}
ARBITER_S = {"Qwen/Qwen2.5-3B-Instruct": 0.70, "Qwen/Qwen2.5-7B-Instruct": 1.19, "meta-llama/Llama-3.1-8B-Instruct": 1.34,
             "Qwen/Qwen3-8B": 1.34,  # not measured; Llama-3.1-8B value used
             "Qwen/Qwen2.5-14B-Instruct": 2.76, "meta-llama/Llama-3.2-3B-Instruct": 0.70}  # job 4189, s per arbiter call
ARBITER_CALLS_PER_RUN = 1.5  # assumption until p2val2 runs exist (one call per retrieved multi-record group)


def from_runs(dirs):
    acc = defaultdict(list)
    for d in dirs:
        d = Path(d)
        man = json.loads((d / "manifest.jsonl").read_text(encoding="utf-8").splitlines()[0])
        for line in (d / "runs.jsonl").read_text(encoding="utf-8").splitlines():
            if line.strip():
                r = json.loads(line)
                acc[(man["client"]["model"], r["config"])].append((r.get("timing") or {}).get("total_s", 0.0))
    return {k: sum(v) / len(v) for k, v in acc.items() if v}


def main():
    ap = argparse.ArgumentParser()
    ap.add_argument("--n-tasks", type=int, default=276, help="eval3 valid tasks (upper bound 276 until sealed)")
    ap.add_argument("--runs", nargs="*", default=[])
    ap.add_argument("--contingency", type=float, default=0.10)
    ap.add_argument("--out", required=True)
    a = ap.parse_args()
    meas = from_runs(a.runs) if a.runs else {}
    rows, tot, prim = [], 0.0, 0.0
    for m, dec in CELLS:
        kind = "greedy" if dec == "greedy" else "T07"
        s = 0.0
        for c in CONFIGS:
            if (m, c) in meas:
                base = meas[(m, c)]
                if kind == "T07":
                    base *= MEASURED[m]["T07"][0] / MEASURED[m]["greedy"][0]
                s += base
            else:
                s += MEASURED[m][kind][0] + (ARBITER_CALLS_PER_RUN * ARBITER_S[m] if c in ("LA", "LG") else 0.0)
        h = a.n_tasks * s / 3600
        tot += h
        prim += h if not m.endswith(("14B-Instruct", "3.2-3B-Instruct")) else 0
        rows.append({"model": m, "decoding": dec, "runs": a.n_tasks * len(CONFIGS), "gpu_h": round(h, 2),
                     "source": "p2val2 runs" if any((m, c) in meas for c in CONFIGS) else MEASURED[m][kind][1]})
    out = {"n_tasks": a.n_tasks, "configs": len(CONFIGS), "cells": rows, "subtotal_gpu_h": round(tot, 1),
           "primary_cells_gpu_h": round(prim, 1), "contingency": a.contingency,
           "total_gpu_h": round(tot * (1 + a.contingency), 1), "concurrent_gpus": 1,
           "wall_days_single_gpu": round(tot * (1 + a.contingency) / 24, 1),
           "arbiter_calls_per_run_assumed": None if meas else ARBITER_CALLS_PER_RUN}
    md = ["# Phase 3 GPU budget (generated by `scripts/budget_phase3.py`)\n",
          f"eval3 tasks: {a.n_tasks} (upper bound until sealed); 12 configurations; one L40 at a time.\n",
          "| Model | Decoding | runs | GPU-h | timing source |", "|---|---|---|---|---|"]
    md += [f"| {r['model'].split('/')[-1]} | {r['decoding']} | {r['runs']} | {r['gpu_h']} | {r['source']} |" for r in rows]
    md += ["", f"Subtotal **{out['subtotal_gpu_h']} GPU-h** (primary cells {out['primary_cells_gpu_h']}); with "
           f"{int(100 * a.contingency)}% contingency **{out['total_gpu_h']} GPU-h**, about {out['wall_days_single_gpu']} days on one GPU (continuous)."]
    Path(a.out + ".json").write_text(json.dumps(out, indent=1) + "\n", encoding="utf-8")
    Path(a.out + ".md").write_text("\n".join(md) + "\n", encoding="utf-8")
    print("\n".join(md))


if __name__ == "__main__":
    main()
