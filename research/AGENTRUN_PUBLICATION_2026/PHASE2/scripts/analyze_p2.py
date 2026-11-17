"""Analysis for Phase 2 development runs and the pre-registered Phase 3 analysis (PREREGISTRATION.md §8).

    py -3.11 analyze_p2.py --tasks <tasks.jsonl> --runs <run_dir> [<run_dir> ...] --out <prefix>
        [--contrasts EBG-RT,EBG-T,...] [--holm EBG-RT,EBG-T,EBG-LG,EBG-B] [--n-perm 100000]

Units and rules (fixed in the pre-registration):
  * a run = task x config x model x decoding; scored with the frozen memlab scorer;
  * a missing run (no row for an expected task x config) or a harness error counts as a failure
    (outcome "missing") and is also reported separately;
  * success per task = mean over decodings; contrasts are paired within model and decoding;
  * family = (scenario, variant): for p2val/eval3 that is category x attribute;
  * test = two-sided sign-flip permutation of family-level summed differences, families pooled across
    models (a family's sign is flipped for all models together); exact when <= 20 families, else
    Monte-Carlo with --n-perm draws (seeded);
  * 95% CI = percentile bootstrap over families (10,000 resamples, seeded) of the mean task-level difference;
  * Holm correction over the contrasts named in --holm; every other contrast is exploratory (BH reported).
Outputs <prefix>.json and <prefix>.md.
"""
from __future__ import annotations

import argparse
import itertools
import json
import random
import sys
from collections import Counter, defaultdict
from pathlib import Path

P2 = Path(__file__).resolve().parents[1]
sys.path.insert(0, str(P2))
from evarb import paths  # noqa: E402,F401
import memlab  # noqa: E402

HARM = {"wrong_value", "stale_value", "unsupported_claim", "arbitrary_pick"}


def load_jsonl(p):
    return [json.loads(x) for x in Path(p).read_text(encoding="utf-8").splitlines() if x.strip()]


def load_runs(tasks, run_dirs):
    rows = []
    for d in run_dirs:
        d = Path(d)
        man = load_jsonl(d / "manifest.jsonl")[0]
        model = man["client"]["model"]
        dec = "greedy" if man["temperature"] == 0 else f"T{man['temperature']}_s{man['seed']}"
        seen = set()
        for r in load_jsonl(d / "runs.jsonl"):
            t = tasks.get(r["task_id"])
            if t is None:
                continue
            seen.add((r["task_id"], r["config"]))
            if "error" in r:
                s = {"outcome": "missing", "success": False, "harmful": False}
            else:
                s = memlab.score_run(t, r)
            rows.append({"model": model, "decoding": dec, "task_id": r["task_id"], "config": r["config"],
                         "scenario": t["scenario"], "variant": t["variant"], "expected": t["expected"]["kind"],
                         "outcome": s["outcome"], "success": bool(s["success"]), "harmful": s["outcome"] in HARM,
                         "reverted": bool(r.get("reverted")), "notice": bool(r.get("rcs_events")),
                         "n_api": len(r.get("api_calls") or []), "latency": (r.get("timing") or {}).get("total_s", 0.0),
                         "arb_calls": sum(1 for x in (r.get("llm_arbiter_log") or []) if x.get("called"))})
        for tid, t in tasks.items():  # missing runs
            for c in man["configs"]:
                if (tid, c) not in seen:
                    rows.append({"model": model, "decoding": dec, "task_id": tid, "config": c, "scenario": t["scenario"],
                                 "variant": t["variant"], "expected": t["expected"]["kind"], "outcome": "missing",
                                 "success": False, "harmful": False, "reverted": False, "notice": False, "n_api": 0,
                                 "latency": 0.0, "arb_calls": 0})
    return rows


def paired(rows, a, b, metric="success", filt=None):
    cell = defaultdict(dict)
    for r in rows:
        if filt and not filt(r):
            continue
        cell[(r["model"], r["decoding"], r["task_id"])][r["config"]] = (float(r[metric]), r)
    per_task = defaultdict(list)
    fam_of = {}
    for (m, dec, tid), c in cell.items():
        if a in c and b in c:
            per_task[(m, tid)].append(c[a][0] - c[b][0])
            fam_of[(m, tid)] = (c[a][1]["scenario"], c[a][1]["variant"])
    diffs = {k: sum(v) / len(v) for k, v in per_task.items()}
    fam = defaultdict(float)
    fam_n = defaultdict(int)
    for k, x in diffs.items():
        fam[fam_of[k]] += x
        fam_n[fam_of[k]] += 1
    return diffs, fam, fam_n


def signflip(fam, n_perm, seed=0):
    d = list(fam.values())
    if not d or all(abs(x) < 1e-12 for x in d):
        return None
    obs = abs(sum(d))
    if len(d) <= 20:
        hits = sum(abs(sum(s * x for s, x in zip(sg, d))) >= obs - 1e-12 for sg in itertools.product((1, -1), repeat=len(d)))
        return hits / 2 ** len(d)
    rng = random.Random(seed)
    hits = sum(abs(sum(x if rng.random() < .5 else -x for x in d)) >= obs - 1e-12 for _ in range(n_perm))
    return (hits + 1) / (n_perm + 1)


def boot_ci(fam, fam_n, n=10000, seed=1):
    keys = list(fam)
    if not keys:
        return None
    rng = random.Random(seed)
    vals = []
    for _ in range(n):
        s = [keys[rng.randrange(len(keys))] for _ in keys]
        tot, cnt = sum(fam[k] for k in s), sum(fam_n[k] for k in s)
        vals.append(100 * tot / cnt if cnt else 0.0)
    vals.sort()
    return [round(vals[int(0.025 * n)], 1), round(vals[int(0.975 * n) - 1], 1)]


def holm(ps):
    items = sorted((p, k) for k, p in ps.items() if p is not None)
    out, m, run = {}, len(items), 0.0
    for i, (p, k) in enumerate(items):
        run = max(run, min(1.0, (m - i) * p))
        out[k] = run
    return out


def bh(ps):
    items = sorted((p, k) for k, p in ps.items() if p is not None)
    m, out, prev = len(items), {}, 1.0
    for i in range(m - 1, -1, -1):
        p, k = items[i]
        prev = min(prev, p * m / (i + 1))
        out[k] = prev
    return out


def main():
    ap = argparse.ArgumentParser()
    ap.add_argument("--tasks", required=True)
    ap.add_argument("--runs", nargs="+", required=True)
    ap.add_argument("--out", required=True)
    ap.add_argument("--contrasts", default="EBG-RT,EBG-T,EBG-LG,EBG-B,EBG-EB,EBG-R,EB-T,EB-G,LG-LA,EBG-EBG-all,EBG-EBG-unsafe")
    ap.add_argument("--holm", default="")
    ap.add_argument("--n-perm", type=int, default=100000)
    a = ap.parse_args()
    tasks = {t["task_id"]: t for t in load_jsonl(a.tasks)}
    rows = load_runs(tasks, a.runs)
    models = sorted({r["model"] for r in rows})
    configs = sorted({r["config"] for r in rows})
    res = {"n_tasks": len(tasks), "models": models, "configs": configs, "n_rows": len(rows),
           "n_families": len({(t["scenario"], t["variant"]) for t in tasks.values()}), "per_model": {}, "per_category": {},
           "contrasts": {}}
    for m in models + ["ALL"]:
        R = [r for r in rows if m == "ALL" or r["model"] == m]
        res["per_model"][m] = {}
        for c in configs:
            X = [r for r in R if r["config"] == c]
            n = len(X)
            res["per_model"][m][c] = {
                "n": n, "success": sum(r["success"] for r in X), "harmful": sum(r["harmful"] for r in X),
                "missing": sum(r["outcome"] == "missing" for r in X),
                "format_error": sum(r["outcome"] == "format_error" for r in X),
                "step_limit": sum(r["outcome"] == "max_steps" for r in X),
                "over_abstain": sum(r["outcome"] == "over_abstain" for r in X),
                "false_conflict": sum(r["outcome"] == "false_conflict" for r in X),
                "arbitrary_pick": sum(r["outcome"] == "arbitrary_pick" for r in X),
                "stale_value": sum(r["outcome"] == "stale_value" for r in X),
                "unsupported": sum(r["outcome"] == "unsupported_claim" for r in X),
                "notices": sum(r["notice"] for r in X), "reverted": sum(r["reverted"] for r in X),
                "model_calls_mean": round(sum(r["n_api"] for r in X) / max(1, n), 2),
                "arbiter_calls_mean": round(sum(r["arb_calls"] for r in X) / max(1, n), 2),
                "latency_s_mean": round(sum(r["latency"] for r in X) / max(1, n), 2)}
        res["per_category"][m] = {c: {s: [sum(r["success"] for r in R if r["config"] == c and r["scenario"] == s),
                                          sum(1 for r in R if r["config"] == c and r["scenario"] == s)]
                                      for s in sorted({r["scenario"] for r in R})} for c in configs}
    ps = {}
    for spec in a.contrasts.split(","):
        x, y = spec.split("-", 1)  # "EBG-EBG-all" -> ("EBG", "EBG-all")
        if x not in configs or y not in configs:
            continue
        for m in models + ["ALL"]:
            R = [r for r in rows if m == "ALL" or r["model"] == m]
            out = {}
            for metric in ("success", "harmful"):
                diffs, fam, fam_n = paired(R, x, y, metric)
                p = signflip(fam, a.n_perm)
                out[metric] = {"n_task_pairs": len(diffs), "n_families": len(fam),
                               "mean_diff_pp": round(100 * sum(diffs.values()) / max(1, len(diffs)), 1),
                               "ci95_pp": boot_ci(fam, fam_n), "families_pos": sum(v > 1e-12 for v in fam.values()),
                               "families_neg": sum(v < -1e-12 for v in fam.values()), "p": p}
                if metric == "success":
                    ps[(spec, m)] = p
            res["contrasts"].setdefault(spec, {})[m] = out
    holm_set = {(s, "ALL") for s in a.holm.split(",") if s}
    hp = holm({k: v for k, v in ps.items() if k in holm_set})
    bp = bh({k: v for k, v in ps.items() if k not in holm_set})
    for (s, m), p in ps.items():
        c = res["contrasts"][s][m]["success"]
        c["p_holm"] = hp.get((s, m))
        c["p_bh_exploratory"] = bp.get((s, m))
        c["confirmatory"] = (s, m) in holm_set
    Path(a.out + ".json").write_text(json.dumps(res, indent=1), encoding="utf-8")
    md = [f"# Analysis: {Path(a.tasks).name} ({len(tasks)} tasks, {res['n_families']} families)\n",
          f"Runs: {', '.join(Path(d).name for d in a.runs)}\n", "## Per model and configuration\n",
          "| Model | Config | success | harmful | over-abstain | false conflict | arbitrary pick | stale | unsupported | "
          "format err | step limit | missing | notices | reverted | model calls | arbiter calls | latency s |",
          "|---|---|---|---|---|---|---|---|---|---|---|---|---|---|---|---|---|"]
    for m in models + ["ALL"]:
        for c, x in res["per_model"][m].items():
            md.append(f"| {m.split('/')[-1]} | {c} | {x['success']}/{x['n']} | {x['harmful']} | {x['over_abstain']} | "
                      f"{x['false_conflict']} | {x['arbitrary_pick']} | {x['stale_value']} | {x['unsupported']} | "
                      f"{x['format_error']} | {x['step_limit']} | {x['missing']} | {x['notices']} | {x['reverted']} | "
                      f"{x['model_calls_mean']} | {x['arbiter_calls_mean']} | {x['latency_s_mean']} |")
    md += ["\n## Paired contrasts (success; harmful in brackets)\n",
           "| Contrast | Model | task pairs | families | diff pp [95% CI] | fam +/- | p | p Holm | p BH (exploratory) | harmful diff pp |",
           "|---|---|---|---|---|---|---|---|---|---|"]
    for s, by in res["contrasts"].items():
        for m, o in by.items():
            x, h = o["success"], o["harmful"]
            fmt = lambda v: "-" if v is None else f"{v:.4f}"  # noqa: E731
            md.append(f"| {s} | {m.split('/')[-1]} | {x['n_task_pairs']} | {x['n_families']} | {x['mean_diff_pp']} "
                      f"{x['ci95_pp']} | {x['families_pos']}/{x['families_neg']} | {fmt(x['p'])} | {fmt(x.get('p_holm'))} | "
                      f"{fmt(x.get('p_bh_exploratory'))} | {h['mean_diff_pp']} |")
    md.append("\n## Per category (ALL models; successes / runs)\n")
    pc = res["per_category"]["ALL"]
    cats = sorted(next(iter(pc.values())))
    md.append("| Category | " + " | ".join(configs) + " |")
    md.append("|---|" + "---|" * len(configs))
    for s in cats:
        md.append(f"| {s} | " + " | ".join(f"{pc[c][s][0]}/{pc[c][s][1]}" for c in configs) + " |")
    Path(a.out + ".md").write_text("\n".join(md) + "\n", encoding="utf-8")
    print("\n".join(md[:60]))


if __name__ == "__main__":
    main()
