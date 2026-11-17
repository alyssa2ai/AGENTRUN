"""Descriptive Phase 3 measures per model x configuration (CPU). Complements the frozen analyze_p2.py, which
does the pre-registered inference; nothing here is a confirmatory test.

    python phase3_metrics.py --tasks <tasks.jsonl> --runs <run dirs...> --out <prefix> [--models m1,m2]

Unit: a run (task x config x model x decoding), scored by the frozen memlab.score_run. A missing row or a
harness error is a failure with outcome `missing` (PREREGISTRATION.md §7) and stays in every denominator.
Measures (denominators in brackets):
  accuracy                     success [all runs]
  answer_accuracy              success [tasks whose gold is an answer]
  conflict_preservation        success [genuine-conflict tasks]
  false_resolution_rate        final status = answer, i.e. one value picked [genuine-conflict tasks]
  stale_error_rate             outcome stale_value [answer tasks]
  unnecessary_abstention_rate  outcome over_abstain [answer + conflict tasks]
  unsupported_answer_rate      outcome unsupported_claim [abstain tasks]
  format_failure_rate, step_limit_rate, missing_rate [all runs]
  tool_calls, model_calls, prompt/completion tokens, latency_s (means) [scored runs]
95% CI for accuracy: family bootstrap (families = scenario x variant; 5,000 seeded resamples) over task-level
means (decodings averaged within task), as in analyze_p2.
"""
from __future__ import annotations

import argparse
import json
import random
import sys
from collections import defaultdict
from pathlib import Path

HERE = Path(__file__).resolve().parent
P2 = HERE.parents[1] / "PHASE2"
sys.path.insert(0, str(P2))
sys.path.insert(0, str(P2 / "scripts"))
from evarb import paths  # noqa: E402,F401
import memlab  # noqa: E402
import analyze_p2 as az  # noqa: E402


def load(tasks, dirs):
    rows = []
    for d in dirs:
        d = Path(d)
        man = az.load_jsonl(d / "manifest.jsonl")[0]
        model = man["client"]["model"]
        dec = "greedy" if man["temperature"] == 0 else f"T{man['temperature']}_s{man['seed']}"
        seen = set()
        for r in az.load_jsonl(d / "runs.jsonl"):
            t = tasks.get(r["task_id"])
            if t is None or (r["task_id"], r["config"]) in seen:
                continue
            seen.add((r["task_id"], r["config"]))
            base = {"model": model, "decoding": dec, "task_id": r["task_id"], "config": r["config"],
                    "family": (t["scenario"], t["variant"]), "kind": t["expected"]["kind"]}
            if "error" in r:
                rows.append({**base, "outcome": "missing", "success": False, "final_status": None, "scored": False})
                continue
            s = memlab.score_run(t, r)
            rows.append({**base, "outcome": s["outcome"], "success": bool(s["success"]), "final_status": s["final_status"],
                         "scored": True, "tool_calls": s["n_tool_calls"], "model_calls": s["n_api_calls"],
                         "prompt_tokens": s["prompt_tokens"], "completion_tokens": s["completion_tokens"],
                         "latency_s": s["total_s"]})
        for tid, t in tasks.items():
            for c in man["configs"]:
                if (tid, c) not in seen:
                    rows.append({"model": model, "decoding": dec, "task_id": tid, "config": c,
                                 "family": (t["scenario"], t["variant"]), "kind": t["expected"]["kind"],
                                 "outcome": "missing", "success": False, "final_status": None, "scored": False})
    return rows


def rate(xs, pred):
    return [sum(1 for x in xs if pred(x)), len(xs)]


def boot(rows, n=5000, seed=3):
    per_task = defaultdict(list)
    fam = {}
    for r in rows:
        per_task[r["task_id"]].append(r["success"])
        fam[r["task_id"]] = r["family"]
    fams = defaultdict(list)
    for t, v in per_task.items():
        fams[fam[t]].append(sum(v) / len(v))
    keys = list(fams)
    if not keys:
        return None
    rng = random.Random(seed)
    vals = []
    for _ in range(n):
        s = [x for k in (rng.choice(keys) for _ in keys) for x in fams[k]]
        vals.append(sum(s) / len(s))
    vals.sort()
    return [round(vals[int(0.025 * n)], 4), round(vals[int(0.975 * n) - 1], 4)]


def cell(R):
    ans = [r for r in R if r["kind"] == "answer"]
    con = [r for r in R if r["kind"] == "conflict"]
    abst = [r for r in R if r["kind"] == "abstain"]
    sc = [r for r in R if r["scored"]]
    mean = lambda k: round(sum(r[k] for r in sc) / len(sc), 2) if sc else None  # noqa: E731
    return {"runs": len(R), "accuracy": rate(R, lambda r: r["success"]), "accuracy_ci95": boot(R),
            "answer_accuracy": rate(ans, lambda r: r["success"]),
            "conflict_preservation": rate(con, lambda r: r["success"]),
            "false_resolution_rate": rate(con, lambda r: r["final_status"] == "answer"),
            "stale_error_rate": rate(ans, lambda r: r["outcome"] == "stale_value"),
            "unnecessary_abstention_rate": rate(ans + con, lambda r: r["outcome"] == "over_abstain"),
            "unsupported_answer_rate": rate(abst, lambda r: r["outcome"] == "unsupported_claim"),
            "format_failure_rate": rate(R, lambda r: r["outcome"] == "format_error"),
            "step_limit_rate": rate(R, lambda r: r["outcome"] == "max_steps"),
            "missing_rate": rate(R, lambda r: r["outcome"] == "missing"),
            "tool_calls": mean("tool_calls"), "model_calls": mean("model_calls"),
            "prompt_tokens": mean("prompt_tokens"), "completion_tokens": mean("completion_tokens"),
            "latency_s": mean("latency_s")}


def main():
    ap = argparse.ArgumentParser()
    ap.add_argument("--tasks", required=True)
    ap.add_argument("--runs", nargs="+", required=True)
    ap.add_argument("--models", help="comma list pooled as POOLED (default: all models in the runs)")
    ap.add_argument("--out", required=True)
    a = ap.parse_args()
    tasks = {t["task_id"]: t for t in az.load_jsonl(a.tasks)}
    rows = load(tasks, a.runs)
    models = sorted({r["model"] for r in rows})
    pool = a.models.split(",") if a.models else models
    configs = sorted({r["config"] for r in rows})
    res = {"n_tasks": len(tasks), "n_rows": len(rows), "models": models, "pooled_models": pool, "cells": {}}
    for m in models + ["POOLED"]:
        R = [r for r in rows if (r["model"] in pool if m == "POOLED" else r["model"] == m)]
        res["cells"][m] = {c: cell([r for r in R if r["config"] == c]) for c in configs}
    Path(a.out + ".json").write_text(json.dumps(res, indent=1) + "\n", encoding="utf-8")
    f = lambda x: f"{x[0]}/{x[1]} ({100 * x[0] / x[1]:.1f}%)" if x and x[1] else "-"  # noqa: E731
    md = [f"# Descriptive measures: {Path(a.tasks).name} ({len(tasks)} tasks)\n",
          "Generated by `PHASE3/scripts/phase3_metrics.py`. Missing runs count as failures. POOLED = " + ", ".join(
              x.split("/")[-1] for x in pool) + ".\n",
          "| Model | Config | accuracy | 95% CI | answer acc. | conflict preserved | false resolution | stale | "
          "unnecessary abstention | unsupported | format fail | step limit | missing | tool calls | model calls | "
          "tokens in/out | latency s |", "|" + "---|" * 17]
    for m in models + ["POOLED"]:
        for c, x in res["cells"][m].items():
            ci = x["accuracy_ci95"]
            md.append(f"| {m.split('/')[-1]} | {c} | {f(x['accuracy'])} | {f'{ci[0]:.3f}-{ci[1]:.3f}' if ci else '-'} | "
                      f"{f(x['answer_accuracy'])} | {f(x['conflict_preservation'])} | {f(x['false_resolution_rate'])} | "
                      f"{f(x['stale_error_rate'])} | {f(x['unnecessary_abstention_rate'])} | {f(x['unsupported_answer_rate'])} | "
                      f"{f(x['format_failure_rate'])} | {f(x['step_limit_rate'])} | {f(x['missing_rate'])} | {x['tool_calls']} | "
                      f"{x['model_calls']} | {x['prompt_tokens']}/{x['completion_tokens']} | {x['latency_s']} |")
    Path(a.out + ".md").write_text("\n".join(md) + "\n", encoding="utf-8")
    print("\n".join(md[:6]))


if __name__ == "__main__":
    main()
