"""Score raw runs and produce tables, statistics and figures.

    py -3.11 scripts/analyze.py raw_results/eval_qwen38_27b_t1 raw_results/eval_gptoss120b_t1 ...

Only "complete blocks" are analysed: a (model, task) pair counts only if all
five configurations finished for it, so every comparison is paired. Writes
tables/*.csv, tables/summary.json, tables/RESULTS_TABLES.md,
tables/failure_examples.json and figures/*.png.
"""

from __future__ import annotations

import csv
import json
import statistics
import sys
from collections import Counter, defaultdict
from math import comb, sqrt
from pathlib import Path

import numpy as np

import memlab
from lenient import lenient_final

LENIENT = False

HERE = Path(__file__).resolve().parent.parent
CFGS = list(memlab.CONFIGS)
SCEN = ["S1_context_loss", "S2_retrieval", "S3_conflict", "S4_stale", "S5_unsupported", "S6_tool_failure"]
PAIRS = [("B", "A"), ("C", "B"), ("D", "C"), ("E", "D"), ("E", "B"), ("E", "A")]
RNG_SEED = 20261111
TAG = ""
NL = "\n"


def wilson(k, n, z=1.96):
    if n == 0:
        return (float("nan"), float("nan"))
    p = k / n
    d = 1 + z * z / n
    c = (p + z * z / (2 * n)) / d
    h = z * sqrt(p * (1 - p) / n + z * z / (4 * n * n)) / d
    return (max(0.0, c - h), min(1.0, c + h))


def mcnemar_exact(b, c):
    """Two-sided exact McNemar p-value from the discordant counts."""
    n = b + c
    if n == 0:
        return 1.0
    k = min(b, c)
    return min(1.0, 2 * sum(comb(n, i) for i in range(k + 1)) / 2 ** n)


def holm(ps):
    order = sorted(range(len(ps)), key=lambda i: ps[i])
    out, running = [0.0] * len(ps), 0.0
    for rank, i in enumerate(order):
        running = max(running, min(1.0, (len(ps) - rank) * ps[i]))
        out[i] = running
    return out


def pfmt(p):
    return "<0.0001" if p < 0.0001 else f"{p:.4f}"


def pct(k, n):
    return f"{100 * k / n:.1f}%" if n else "n/a"


def rate_ci(k, n):
    lo, hi = wilson(k, n)
    return f"{k}/{n} ({pct(k, n)}; {100 * lo:.0f}-{100 * hi:.0f})" if n else "n/a"


def load(run_dirs):
    tasks = {}
    for name in ("dev.jsonl", "eval.jsonl"):
        for x in (HERE / "benchmark" / name).read_text(encoding="utf-8").splitlines():
            if x.strip():
                t = json.loads(x)
                tasks[t["task_id"]] = t
    rows, raw, manifests = [], {}, {}
    for rd in run_dirs:
        rd = Path(rd)
        manifests[rd.name] = json.loads((rd / "manifest.jsonl").read_text(encoding="utf-8").splitlines()[0])
        cl = manifests[rd.name]["client"]
        model = cl["model"]
        if cl.get("backend") == "hf-local":  # local-GPU runs: label by model, adapter and decoding
            model += " [L40" + (" +LoRA" if cl.get("adapter") else "") +                      (f" T={cl['temperature']} seed={cl['seed']}" if cl.get("temperature") else " greedy") + "]"
        by_task = defaultdict(dict)
        for x in (rd / "runs.jsonl").read_text(encoding="utf-8").splitlines():
            if x.strip():
                r = json.loads(x)
                if LENIENT and not r["hit_max_steps"] and not (r.get("final") or {}).get("status"):
                    lf = lenient_final(r.get("draft_text"))
                    if lf:  # note: the verifier never saw these drafts
                        r["final"], r["draft"] = lf, lf
                by_task[r["task_id"]][r["config"]] = r
        for tid, d in by_task.items():
            if all(c in d for c in CFGS):  # complete block only
                for c in CFGS:
                    s = memlab.score_run(tasks[tid], d[c])
                    s["model"] = model
                    rows.append(s)
                    raw[(model, tid, c)] = d[c]
    return tasks, rows, raw, manifests


def paired(rows, a, b, key, rng):
    """Config a minus config b on a 0/1 metric; units are (model, task),
    bootstrap resamples tasks (clustered over models)."""
    va = {(r["model"], r["task_id"]): int(r[key]) for r in rows if r["config"] == a}
    vb = {(r["model"], r["task_id"]): int(r[key]) for r in rows if r["config"] == b}
    units = sorted(va)
    d = np.array([va[u] - vb[u] for u in units])
    by_task = defaultdict(list)
    for i, u in enumerate(units):
        by_task[u[1]].append(i)
    tids = sorted(by_task)
    boots = []
    for _ in range(5000):
        idx = [i for t in rng.choice(len(tids), len(tids)) for i in by_task[tids[t]]]
        boots.append(d[idx].mean())
    lo, hi = np.percentile(boots, [2.5, 97.5])
    plus, minus = int((d == 1).sum()), int((d == -1).sum())
    return {"a": a, "b": b, "metric": key, "n": len(units), "rate_a": float(np.mean([va[u] for u in units])),
            "rate_b": float(np.mean([vb[u] for u in units])), "diff": float(d.mean()), "ci_lo": float(lo),
            "ci_hi": float(hi), "a_only": plus, "b_only": minus, "p_mcnemar": mcnemar_exact(plus, minus)}


def table_md(header, lines):
    out = ["| " + " | ".join(header) + " |", "|" + "|".join("---" for _ in header) + "|"]
    out += ["| " + " | ".join(str(x) for x in ln) + " |" for ln in lines]
    return "\n".join(out) + "\n"


def write_csv(name, header, lines):
    with open(HERE / "tables" / TAG / name, "w", newline="", encoding="utf-8") as f:
        w = csv.writer(f)
        w.writerow(header)
        w.writerows(lines)


def main(argv) -> int:
    global TAG, LENIENT
    if argv and argv[0] == "--lenient":
        LENIENT, argv = True, argv[1:]
    if argv and argv[0] == "--tag":  # write to tables/<tag>/ and figures/<tag>/ instead of the top level
        TAG, argv = argv[1], argv[2:]
    tasks, rows, raw, manifests = load(argv)
    (HERE / "tables" / TAG).mkdir(parents=True, exist_ok=True)
    (HERE / "figures" / TAG).mkdir(parents=True, exist_ok=True)
    models = sorted({r["model"] for r in rows})
    md = ["# Result tables (generated by scripts/analyze.py; do not edit)\n"]
    summary = {"models": {}, "manifests": manifests}
    write_csv("per_run_scores.csv", list(rows[0].keys()), [list(r.values()) for r in rows])

    def sel(model=None, cfg=None, scen=None, variant=None):
        return [r for r in rows if (model is None or r["model"] == model) and (cfg is None or r["config"] == cfg)
                and (scen is None or r["scenario"] == scen) and (variant is None or r["variant"] == variant)]

    groups = [(m, m) for m in models] + ([("POOLED (all models)", None)] if len(models) > 1 else [])
    for gname, gm in groups:
        g = sel(gm)
        n_units = len({(r["model"], r["task_id"]) for r in g})
        md.append(f"\n## {gname}: {n_units} complete (model, task) blocks x 5 configurations, 1 trial\n")
        per_scen = Counter(r["scenario"] for r in g if r["config"] == "A")
        md.append("Blocks per scenario: " + ", ".join(f"{s} {per_scen[s]}" for s in SCEN) + "\n")
        gs = {"n_blocks": n_units, "configs": {}}

        # T1 headline
        lines = []
        for c in CFGS:
            x = sel(gm, c)
            n = len(x)
            k, h = sum(r["success"] for r in x), sum(r["harmful"] for r in x)
            safe = sum(r["outcome"] in ("over_abstain", "false_conflict") for r in x)
            brk = sum(r["outcome"] in ("format_error", "max_steps") for r in x)
            ans = [r for r in x if r["final_status"] == "answer"]
            gr = sum(bool(r["value_in_evidence"]) for r in ans)
            lines.append([memlab.CONFIGS[c]["label"], n, rate_ci(k, n), rate_ci(h, n), f"{safe}/{n}", f"{brk}/{n}",
                          rate_ci(gr, len(ans))])
            gs["configs"][c] = {"n": n, "success": k, "harmful": h, "safe_non_answer": safe, "broken": brk,
                                "answers": len(ans), "answers_value_in_evidence": gr}
        hdr = ["Config", "n", "Task success (95% Wilson CI)", "Harmful assertion", "Safe miss", "Format/steps",
               "Answers whose value is in tool evidence"]
        md.append("### Headline\n\n" + table_md(hdr, lines))
        write_csv(f"headline_{gname.replace('/', '_').replace(' ', '_').replace('[', '').replace(']', '').replace('=', '')[:60]}.csv", hdr, lines)

        # T2 success by scenario
        lines = [[s] + [f"{sum(r['success'] for r in sel(gm, c, s))}/{len(sel(gm, c, s))}" for c in CFGS]
                 for s in SCEN]
        md.append("### Task success by scenario\n\n" + table_md(["Scenario"] + CFGS, lines))
        lines = [[s] + [f"{sum(r['harmful'] for r in sel(gm, c, s))}/{len(sel(gm, c, s))}" for c in CFGS]
                 for s in SCEN]
        md.append("### Harmful assertions by scenario\n\n" + table_md(["Scenario"] + CFGS, lines))

        # T3 outcome categories
        lines = [[o] + [sum(r["outcome"] == o for r in sel(gm, c)) for c in CFGS] for o in memlab.OUTCOMES]
        md.append("### Outcome counts\n\n" + table_md(["Outcome"] + CFGS, lines))
        gs["outcomes"] = {c: dict(Counter(r["outcome"] for r in sel(gm, c))) for c in CFGS}

        # T4 named rates
        def rr(cfg, scen, key="success", variants=None):
            x = [r for r in sel(gm, cfg, scen) if variants is None or r["variant"] in variants]
            return f"{sum(bool(r[key]) for r in x)}/{len(x)}"
        named = [
            ("Conflict detection (S3 flagged as conflict)", lambda c: rr(c, "S3_conflict")),
            ("Arbitrary pick on conflict (S3 harmful)", lambda c: rr(c, "S3_conflict", "harmful")),
            ("Stale handling: newest value (S4, date in text)", lambda c: rr(c, "S4_stale", variants=["date_in_text"])),
            ("Stale handling: newest value (S4, date in metadata only)",
             lambda c: rr(c, "S4_stale", variants=["date_in_metadata_only"])),
            ("Stale value asserted (S4)", lambda c: f"{sum(r['outcome'] == 'stale_value' for r in sel(gm, c, 'S4_stale'))}"
                                                    f"/{len(sel(gm, c, 'S4_stale'))}"),
            ("Unsupported claim (S5 answered)", lambda c: rr(c, "S5_unsupported", "harmful")),
            ("Recovery after transient/malformed tool failure (S6)",
             lambda c: rr(c, "S6_tool_failure", variants=["transient_timeout", "malformed_then_ok"])),
            ("Retried after injected failure (S6, any variant)", lambda c: rr(c, "S6_tool_failure", "retried_after_failure")),
            ("Honest abstention on permanent failure (S6, no memory)",
             lambda c: rr(c, "S6_tool_failure", variants=["permanent_no_memory"])),
            ("Memory fallback on permanent failure (S6)",
             lambda c: rr(c, "S6_tool_failure", variants=["permanent_memory_fallback"])),
            ("Needed tools all called (tool selection)", lambda c: rr(c, None, "needed_tools_called")),
        ]
        lines = [[n] + [f(c) for c in CFGS] for n, f in named]
        md.append("### Named reliability rates (count/total)\n\n" + table_md(["Metric"] + CFGS, lines))
        write_csv(f"named_rates_{gname.replace('/', '_').replace(' ', '_').replace('[', '').replace(']', '').replace('=', '')[:60]}.csv", ["Metric"] + CFGS, lines)
        lines = []
        for c in CFGS:
            x = sel(gm, c)
            tc, ok = sum(r["n_tool_calls"] for r in x), sum(r["n_tool_ok"] for r in x)
            inj, ag = sum(r["n_injected_failures"] for r in x), sum(r["n_agent_tool_errors"] for r in x)
            lines.append([c, tc, f"{ok}/{tc}", inj, ag])
        md.append("### Tool execution\n\n" + table_md(
            ["Config", "Tool calls", "Returned normally", "Injected failures", "Agent-caused errors"], lines))

        # T5 retrieval
        lines = []
        for c in CFGS[1:]:
            for s in SCEN:
                x = [r for r in sel(gm, c, s) if r["recall_at_k_first"] is not None]
                if x:
                    lines.append([c, s, len(x), f"{statistics.mean(r['recall_at_k_first'] for r in x):.2f}",
                                  f"{statistics.mean(r['precision_at_k_first'] for r in x):.2f}",
                                  f"{statistics.mean(r['recall_union'] for r in x):.2f}",
                                  f"{statistics.mean(r['precision_union'] for r in x):.2f}",
                                  f"{statistics.mean(r['n_memory_calls'] for r in x):.2f}"])
        hdr = ["Config", "Scenario", "runs with a memory call", f"recall@{memlab.TOP_K} (first query)",
               f"precision@{memlab.TOP_K} (first query)", "recall (all queries)", "precision (all queries)",
               "memory calls/run"]
        md.append("### Retrieval (tasks with gold records; the query is whatever the model wrote)\n\n"
                  + table_md(hdr, lines))
        write_csv(f"retrieval_{gname.replace('/', '_').replace(' ', '_').replace('[', '').replace(']', '').replace('=', '')[:60]}.csv", hdr, lines)

        # T6 verifier as a detector of wrong answer-drafts
        lines = []
        for c in ("C", "D", "E"):
            x = [r for r in sel(gm, c) if r["verdict"] is not None]
            bad = lambda r: r["draft_outcome"] != "correct"  # noqa: E731
            rej = lambda r: r["verdict"] in ("UNSUPPORTED", "CONFLICT")  # noqa: E731
            tp = sum(bad(r) and rej(r) for r in x)
            fp = sum((not bad(r)) and rej(r) for r in x)
            fn = sum(bad(r) and not rej(r) for r in x)
            tn = sum((not bad(r)) and not rej(r) for r in x)
            lines.append([c, len(x), tp, fp, fn, tn, f"{tp}/{tp + fp}" if tp + fp else "n/a (no rejections)",
                          f"{tp}/{tp + fn}" if tp + fn else "n/a (no wrong drafts)",
                          sum(r["verdict"] == "UNPARSED" for r in x)])
            gs.setdefault("verifier", {})[c] = {"checked": len(x), "tp": tp, "fp": fp, "fn": fn, "tn": tn}
        md.append("### Verifier (positive = draft rejected; truth = draft answer was wrong)\n\n" + table_md(
            ["Config", "Drafts checked", "TP", "FP", "FN", "TN", "Precision", "Recall", "Unparsed"], lines))

        # T7 efficiency
        lines = []
        n_susp = sum(r["total_s"] - r["model_s"] > 30 for r in g)
        md.append(f"Runs excluded from the timing rows because the wall clock jumped by more than 30 s beyond "
                  f"model time (the PC suspended mid-run; outcomes are unaffected): {n_susp}\n")
        for c in CFGS:
            x = [r for r in sel(gm, c) if r["total_s"] - r["model_s"] <= 30]
            f = lambda k, fn=statistics.mean: fn(r[k] for r in x)  # noqa: E731
            lines.append([c, f"{f('total_s'):.2f}", f"{f('total_s', statistics.median):.2f}", f"{f('model_s'):.2f}",
                          f"{f('model_s', statistics.median):.2f}",
                          f"{f('n_api_calls'):.2f}", f"{f('n_tool_calls'):.2f}", f"{f('prompt_tokens'):.0f}",
                          f"{f('completion_tokens'):.0f}"])
            gs["configs"][c].update({"mean_total_s": f("total_s"), "median_total_s": f("total_s", statistics.median),
                                     "mean_tokens": f("prompt_tokens") + f("completion_tokens"),
                                     "mean_api_calls": f("n_api_calls")})
        hdr = ["Config", "End-to-end s (mean)", "(median)", "Model s (mean)", "(median)",
               "API calls", "Tool calls", "Prompt tokens", "Completion tokens"]
        md.append("### Efficiency per task (rate-limit waiting excluded)\n\n" + table_md(hdr, lines))
        write_csv(f"efficiency_{gname.replace('/', '_').replace(' ', '_').replace('[', '').replace(']', '').replace('=', '')[:60]}.csv", hdr, lines)

        # T7b memory access and exploratory conditional view
        mem_sc = ("S1_context_loss", "S2_retrieval", "S3_conflict", "S4_stale")
        lines = []
        for m in ([gm] if gm else models):
            lines.append([m] + [f"{sum(r['n_memory_calls'] > 0 for r in sel(m, c) if r['scenario'] in mem_sc)}"
                                f"/{sum(r['scenario'] in mem_sc for r in sel(m, c))}" for c in CFGS[1:]])
        md.append("### Memory access: runs in S1-S4 (answer only in memory) where memory_search was called at "
                  "least once" + "\n" + "\n" + table_md(["Model"] + CFGS[1:], lines))
        lines = []
        for s_ in list(mem_sc) + ["S4 date_in_text", "S4 date_in_metadata_only"]:
            row = [s_]
            for c in CFGS[1:]:
                x = [r for r in sel(gm, c) if r["n_memory_calls"] > 0 and
                     (r["scenario"] == s_ or (s_.startswith("S4 ") and r["variant"] == s_[3:]))]
                row.append(f"{sum(r['success'] for r in x)}/{len(x)} ok, {sum(r['harmful'] for r in x)} harmful")
            lines.append(row)
        md.append("### EXPLORATORY (post hoc, conditions on the agent's own behaviour, not a paired comparison): "
                  "outcomes among runs that did call memory_search" + "\n" + "\n" + table_md(["Subset"] + CFGS[1:], lines))
        # T7c run-to-run noise: B and C send the agent identical inputs up to the draft
        b = {(r["model"], r["task_id"]): r for r in sel(gm, "B")}
        c_ = {(r["model"], r["task_id"]): r for r in sel(gm, "C")}
        diff = [k for k in b if b[k]["draft_outcome"] != c_[k]["draft_outcome"]]
        md.append(f"### Run-to-run noise check{NL}{NL}Configurations B and C give the agent identical inputs until "
                  f"the draft (the verifier runs afterwards). Their draft outcomes differ in {len(diff)} of {len(b)} "
                  f"blocks, although temperature is 0 and the seed is fixed: {sorted(diff)}{NL}")
        gs["draft_disagreement_B_vs_C"] = {"n": len(b), "differ": len(diff)}

        # T8 paired comparisons
        rng = np.random.default_rng(RNG_SEED)
        comps = [paired(g, a, b, k, rng) for k in ("success", "harmful") for a, b in PAIRS]
        for k in ("success", "harmful"):
            sub = [c for c in comps if c["metric"] == k]
            for c, ph in zip(sub, holm([c["p_mcnemar"] for c in sub])):
                c["p_holm"] = ph
        lines = [[c["metric"], f"{c['a']} - {c['b']}", c["n"], f"{100 * c['rate_a']:.1f}%", f"{100 * c['rate_b']:.1f}%",
                  f"{100 * c['diff']:+.1f}", f"[{100 * c['ci_lo']:+.1f}, {100 * c['ci_hi']:+.1f}]",
                  f"{c['a_only']} / {c['b_only']}", pfmt(c["p_mcnemar"]), pfmt(c["p_holm"])] for c in comps]
        hdr = ["Metric", "Comparison", "n pairs", "first", "second", "diff (pp)", "95% bootstrap CI (pp)",
               "discordant first-only / second-only", "McNemar exact p", "Holm p (6 tests)"]
        md.append("### Paired comparisons\n\n" + table_md(hdr, lines))
        write_csv(f"paired_{gname.replace('/', '_').replace(' ', '_').replace('[', '').replace(']', '').replace('=', '')[:60]}.csv", hdr, lines)
        gs["paired"] = comps
        summary["models"][gname] = gs

    # retrieval latency, measured offline with a high-resolution timer (the in-run timer is too coarse)
    import time as _t
    lat = []
    for t in tasks.values():
        if t["split"] == "eval":
            st = memlab.MemoryStore(t["memory"])
            for _ in range(20):
                t0 = _t.perf_counter()
                st.search(t["prompt"])
                lat.append(1000 * (_t.perf_counter() - t0))
    summary["retrieval_latency_ms_offline"] = {"n": len(lat), "mean": statistics.mean(lat),
                                               "median": statistics.median(lat), "p95": float(np.percentile(lat, 95))}
    md.append(f"\n## Retrieval latency (offline, perf_counter, {len(lat)} searches over the eval stores)\n\n"
              f"mean {statistics.mean(lat):.2f} ms, median {statistics.median(lat):.2f} ms, "
              f"p95 {np.percentile(lat, 95):.2f} ms (pure-Python hash embedding + cosine over 7-12 records)\n")

    # failure examples: every harmful / broken run, with the evidence it saw
    ex = []
    for r in rows:
        if r["harmful"] or r["outcome"] in ("format_error", "max_steps", "false_conflict") or \
                (r["outcome"] == "over_abstain" and r["config"] != "A"):
            run, t = raw[(r["model"], r["task_id"], r["config"])], tasks[r["task_id"]]
            ex.append({"model": r["model"], "task_id": r["task_id"], "config": r["config"], "variant": r["variant"],
                       "outcome": r["outcome"], "prompt": t["prompt"], "expected": t["expected"],
                       "tool_calls": [{"name": c["name"], "arguments": c["arguments"], "status": c["status"],
                                       "observation": c["observation"][:1200]} for c in run["tool_calls"]],
                       "draft": run["draft"], "verdict": run["verdict"], "final": run["final"],
                       "draft_text": None if run["draft"] else (run["draft_text"] or "")[:500],
                       "api_errors": [a["error"][:300] for a in run["api_calls"] if a["error"]]})
    (HERE / "tables" / TAG / "failure_examples.json").write_text(json.dumps(ex, indent=1, ensure_ascii=False),
                                                         encoding="utf-8")
    (HERE / "tables" / TAG / "summary.json").write_text(json.dumps(summary, indent=1), encoding="utf-8")
    (HERE / "tables" / TAG / "RESULTS_TABLES.md").write_text("\n".join(md), encoding="utf-8")
    figures(rows, models)
    print("\n".join(md))
    return 0


# ----------------------------------------------------------------------------
# Figures (static PNG). Palette: validated categorical slots 1-5 in fixed order
# for configurations; reserved status colours for outcome classes.
# ----------------------------------------------------------------------------
INK, MUTED, GRID, SURFACE = "#0b0b0b", "#898781", "#e1e0d9", "#fcfcfb"
CFG_COL = dict(zip(CFGS, ["#2a78d6", "#eb6834", "#1baf7a", "#eda100", "#e87ba4"]))
OUT_GROUPS = [("Correct", ["correct"], "#0ca30c"),
              ("Safe miss (abstained / flagged conflict)", ["over_abstain", "false_conflict"], "#c3c2b7"),
              ("Harmful assertion (wrong, stale, unsupported, arbitrary)",
               ["wrong_value", "stale_value", "unsupported_claim", "arbitrary_pick"], "#d03b3b"),
              ("Format error / step limit", ["format_error", "max_steps"], "#52514e")]


def _style(ax):
    ax.set_facecolor(SURFACE)
    for s in ("top", "right", "left"):
        ax.spines[s].set_visible(False)
    ax.spines["bottom"].set_color("#c3c2b7")
    ax.tick_params(colors=MUTED, length=0, labelsize=9)
    ax.yaxis.grid(True, color=GRID, linewidth=0.8)
    ax.set_axisbelow(True)


def figures(rows, models):
    import matplotlib
    matplotlib.use("Agg")
    import matplotlib.pyplot as plt
    plt.rcParams["font.family"] = "DejaVu Sans"
    n_units = len({(r["model"], r["task_id"]) for r in rows})
    sub = f"{n_units} (model, task) blocks pooled over {len(models)} model(s); 1 trial each"

    # Fig 1: task success by scenario and configuration
    fig, ax = plt.subplots(figsize=(11, 4.6), facecolor=SURFACE)
    _style(ax)
    w = 0.15
    for j, c in enumerate(CFGS):
        ys, ns = [], []
        for s in SCEN:
            x = [r for r in rows if r["config"] == c and r["scenario"] == s]
            ys.append(100 * sum(r["success"] for r in x) / len(x) if x else 0)
            ns.append(len(x))
        xs = [i + (j - 2) * (w + 0.012) for i in range(len(SCEN))]
        ax.bar(xs, ys, w, color=CFG_COL[c], label=memlab.CONFIGS[c]["label"], edgecolor=SURFACE, linewidth=1)
        for x_, y_ in zip(xs, ys):
            ax.text(x_, y_ + 1.5, f"{y_:.0f}", ha="center", va="bottom", fontsize=7, color=INK)
    ax.set_xticks(range(len(SCEN)))
    ax.set_xticklabels([f"{s.replace('_', ' ', 1).replace('_', ' ')}\n(n={n})" for s, n in zip(SCEN, ns)],
                       color=INK, fontsize=9)
    ax.set_ylim(0, 112)
    ax.set_ylabel("Task success (%)", color=MUTED, fontsize=9)
    ax.set_title("Task success by scenario and configuration", loc="left", color=INK, fontsize=12, pad=22)
    ax.text(0, 1.03, sub, transform=ax.transAxes, color=MUTED, fontsize=8.5)
    ax.legend(ncol=5, frameon=False, fontsize=8.5, loc="upper center", bbox_to_anchor=(0.5, -0.16))
    fig.tight_layout()
    fig.savefig(HERE / "figures" / TAG / "fig1_success_by_scenario.png", dpi=170)
    plt.close(fig)

    # Fig 2: outcome composition per configuration (failure analysis)
    fig, ax = plt.subplots(figsize=(8.6, 4.4), facecolor=SURFACE)
    _style(ax)
    ax.yaxis.grid(False)
    ax.xaxis.grid(True, color=GRID, linewidth=0.8)
    left = np.zeros(len(CFGS))
    for name, outs, col in OUT_GROUPS:
        vals = np.array([100 * sum(r["outcome"] in outs for r in rows if r["config"] == c)
                         / max(1, sum(r["config"] == c for r in rows)) for c in CFGS])
        ax.barh(range(len(CFGS)), vals, left=left, color=col, edgecolor=SURFACE, linewidth=2, height=0.62,
                label=name)
        for i, (v, l0) in enumerate(zip(vals, left)):
            if v >= 4:
                ax.text(l0 + v / 2, i, f"{v:.0f}%", ha="center", va="center", fontsize=8.5,
                        color="#ffffff" if col != "#c3c2b7" else INK)
        left += vals
    ax.set_yticks(range(len(CFGS)))
    ax.set_yticklabels([memlab.CONFIGS[c]["label"] for c in CFGS], color=INK, fontsize=9)
    ax.invert_yaxis()
    ax.set_xlim(0, 100)
    ax.set_xlabel("Share of runs (%)", color=MUTED, fontsize=9)
    ax.set_title("What each configuration does when it is not correct", loc="left", color=INK, fontsize=12, pad=22)
    ax.text(0, 1.03, sub, transform=ax.transAxes, color=MUTED, fontsize=8.5)
    ax.legend(ncol=2, frameon=False, fontsize=8.5, loc="upper center", bbox_to_anchor=(0.45, -0.17))
    fig.tight_layout()
    fig.savefig(HERE / "figures" / TAG / "fig2_outcome_composition.png", dpi=170)
    plt.close(fig)

    # Fig 3: cost of each configuration (small multiples, one measure per panel)
    fig, axes = plt.subplots(1, 3, figsize=(11, 3.4), facecolor=SURFACE)
    for ax, (key, title, scale) in zip(axes, [("total_s", "End-to-end latency per task (s, mean)", 1),
                                              ("tokens", "Tokens per task (mean)", 1),
                                              ("n_api_calls", "Model calls per task (mean)", 1)]):
        _style(ax)
        vals = []
        for c in CFGS:
            x = [r for r in rows if r["config"] == c]
            vals.append(statistics.mean((r["prompt_tokens"] + r["completion_tokens"]) if key == "tokens" else r[key]
                                        for r in x) * scale)
        ax.bar(range(len(CFGS)), vals, 0.6, color=[CFG_COL[c] for c in CFGS], edgecolor=SURFACE)
        for i, v in enumerate(vals):
            ax.text(i, v, f"{v:,.0f}" if v >= 100 else f"{v:.2f}", ha="center", va="bottom", fontsize=8, color=INK)
        ax.set_xticks(range(len(CFGS)))
        ax.set_xticklabels(CFGS, color=INK)
        ax.set_title(title, loc="left", color=INK, fontsize=10)
        ax.set_ylim(0, max(vals) * 1.15)
    fig.suptitle("Cost of each configuration - " + sub, x=0.01, ha="left", color=MUTED, fontsize=8.5, y=0.02)
    fig.tight_layout()
    fig.savefig(HERE / "figures" / TAG / "fig3_cost.png", dpi=170)
    plt.close(fig)


if __name__ == "__main__":
    raise SystemExit(main(sys.argv[1:]))
