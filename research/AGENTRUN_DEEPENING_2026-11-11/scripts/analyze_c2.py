"""Cross-run analysis for campaign 2 (eval2 split, SIT HPC).

    py -3.11 scripts/analyze_c2.py

Reads every raw_results/c2_* directory that exists, scores it, and writes
tables/c2/C2_TABLES.md, tables/c2/c2_summary.json and figures/c2/*.png.
Runs that are missing or incomplete are listed as such and never filled in.
Comparisons between runs are paired on (task, configuration).
"""

from __future__ import annotations

import json
from collections import Counter, defaultdict
from pathlib import Path

import numpy as np

import memlab
from analyze import mcnemar_exact, pfmt, wilson

HERE = Path(__file__).resolve().parent.parent
RAW = HERE / "raw_results"
OUT = HERE / "tables" / "c2"
FIG = HERE / "figures" / "c2"
CFGS = list(memlab.CONFIGS)
SCEN = ["S1_context_loss", "S2_retrieval", "S3_conflict", "S4_stale", "S5_unsupported", "S6_tool_failure"]
TASKS = {}
for line in (HERE / "benchmark" / "eval2.jsonl").read_text(encoding="utf-8").splitlines():
    if line.strip():
        t = json.loads(line)
        TASKS[t["task_id"]] = t
BROKEN = ("format_error", "max_steps")
rng = np.random.default_rng(20261112)


def load(run_id):
    """{(task_id, config): score row} for one run, or None if the run does not exist."""
    p = RAW / run_id / "runs.jsonl"
    if not p.exists():
        return None
    rows = {}
    for line in p.read_text(encoding="utf-8").splitlines():
        if line.strip():
            r = json.loads(line)
            s = memlab.score_run(TASKS[r["task_id"]], r)
            s["repair_used"] = bool(r.get("repair_used"))
            rows[(r["task_id"], r["config"])] = s
    return rows


def status(run_id, rows, expected):
    if rows is None:
        return "not run"
    done = (RAW / run_id / "DONE").exists()
    return f"complete ({len(rows)} runs)" if done and len(rows) >= expected else f"INCOMPLETE ({len(rows)}/{expected} runs)"


def cell(rows, cfg, key="success", scen=None):
    x = [r for (t, c), r in rows.items() if c == cfg and (scen is None or r["scenario"] == scen)]
    if not x:
        return "-"
    k = sum(bool(r[key]) if key in ("success", "harmful") else r["outcome"] in key for r in x)
    return f"{k}/{len(x)}"


def rate(rows, cfg, scen=None):
    x = [r for (t, c), r in rows.items() if c == cfg and (scen is None or r["scenario"] == scen)]
    return (sum(r["success"] for r in x), len(x))


def pct(k, n):
    lo, hi = wilson(k, n)
    return f"{k}/{n} = {100 * k / n:.1f}% ({100 * lo:.0f}-{100 * hi:.0f})" if n else "-"


def paired(a_rows, b_rows, keys, field="success"):
    """a minus b on shared (task, config) keys; bootstrap over tasks."""
    keys = [k for k in keys if k in a_rows and k in b_rows]
    if not keys:
        return None
    d = np.array([int(a_rows[k][field]) - int(b_rows[k][field]) for k in keys])
    by_task = defaultdict(list)
    for i, k in enumerate(keys):
        by_task[k[0]].append(i)
    tids = sorted(by_task)
    boots = [d[[i for t in rng.choice(len(tids), len(tids)) for i in by_task[tids[t]]]].mean() for _ in range(4000)]
    lo, hi = np.percentile(boots, [2.5, 97.5])
    plus, minus = int((d == 1).sum()), int((d == -1).sum())
    return {"n": len(keys), "a": float(np.mean([a_rows[k][field] for k in keys])),
            "b": float(np.mean([b_rows[k][field] for k in keys])), "diff": float(d.mean()), "lo": float(lo),
            "hi": float(hi), "a_only": plus, "b_only": minus, "p": mcnemar_exact(plus, minus)}


def prow(label, c):
    if c is None:
        return [label, "-", "-", "-", "-", "-", "-", "-"]
    return [label, c["n"], f"{100 * c['a']:.1f}%", f"{100 * c['b']:.1f}%", f"{100 * c['diff']:+.1f}",
            f"[{100 * c['lo']:+.1f}, {100 * c['hi']:+.1f}]", f"{c['a_only']} / {c['b_only']}", pfmt(c["p"])]


PH = ["Comparison", "n pairs", "first", "second", "diff (pp)", "95% bootstrap CI", "discordant", "McNemar p"]


def table(header, lines):
    out = ["| " + " | ".join(header) + " |", "|" + "|".join("---" for _ in header) + "|"]
    return "\n".join(out + ["| " + " | ".join(str(x) for x in ln) + " |" for ln in lines]) + "\n"


def cfg_pairs(rows, a, b, scen=None):
    """Config a minus config b inside one run (paired on task)."""
    keys = [t for (t, c) in rows if c == a and (scen is None or rows[(t, c)]["scenario"] == scen)]
    A = {(t, "x"): rows[(t, a)] for t in keys if (t, b) in rows}
    B = {(t, "x"): rows[(t, b)] for t in keys if (t, b) in rows}
    return paired(A, B, list(A))


def merge(*runs):
    """Pool several runs: keys become (model-tag|task, config) so tasks stay the bootstrap cluster."""
    out = {}
    for tag, rows in runs:
        if rows:
            for (t, c), r in rows.items():
                out[(t + "|" + tag, c)] = r
    return out


def main() -> int:
    OUT.mkdir(parents=True, exist_ok=True)
    FIG.mkdir(parents=True, exist_ok=True)
    ids = ["c2_qwen25_7b_v1", "c2_qwen3_8b_v1", "c2_qwen25_7b_v2", "c2_qwen3_8b_v2", "c2_qwen25_7b_v1r",
           "c2_qwen3_8b_v1r", "c2_qwen25_14b_v1", "c2_qwen25_3b_v1", "c2_qwen25_1p5b_v1", "c2_qwen25_14b_v2",
           "c2_qwen25_3b_v2", "c2_qwen25_1p5b_v2", "c2_qwen25_7b_lora_v1", "c2_qwen25_7b_lora_v2",
           "c2_qwen25_7b_v2_T07_s1", "c2_qwen25_7b_v2_T07_s2", "c2_qwen25_7b_v2_hash_pad2000",
           "c2_qwen25_7b_v2_bm25_pad2000", "c2_qwen25_7b_v2_dense_pad2000"]
    R = {i: load(i) for i in ids}
    md = ["# Campaign 2 tables (generated by scripts/analyze_c2.py; do not edit)\n",
          "Split: eval2 (96 tasks, 16 per scenario). One trial per cell unless stated. SIT HPC, NVIDIA L40.\n",
          "## Run status\n",
          table(["Run", "Status"], [[i, status(i, R[i], 192 if "pad2000" in i else 480)] for i in ids])]
    summ = {"status": {i: status(i, R[i], 192 if "pad2000" in i else 480) for i in ids}}

    # ---- 1 replication of the first study with the frozen v1 harness
    md.append("\n## 1. Replication on fresh tasks (frozen v1 harness)\n")
    v1 = [("q25", R["c2_qwen25_7b_v1"]), ("q3", R["c2_qwen3_8b_v1"])]
    for name, rows in [("Qwen2.5-7B-Instruct", v1[0][1]), ("Qwen3-8B", v1[1][1]), ("Pooled (both)", merge(*v1))]:
        if not rows:
            continue
        md.append(f"### {name}\n")
        lines = []
        for c in CFGS:
            k, n = rate(rows, c)
            h = sum(r["harmful"] for (t, cc), r in rows.items() if cc == c)
            b = sum(r["outcome"] in BROKEN for (t, cc), r in rows.items() if cc == c)
            lines.append([memlab.CONFIGS[c]["label"], pct(k, n), f"{h}/{n}", f"{b}/{n}"])
        md.append(table(["Config", "Task success (95% Wilson CI)", "Harmful", "Format/step-limit"], lines))
        md.append(table(["Scenario"] + CFGS, [[s] + [cell(rows, c, scen=s) for c in CFGS] for s in SCEN]))
        md.append(table(PH, [prow(f"{a} - {b}", cfg_pairs(rows, a, b)) for a, b in
                             [("B", "A"), ("C", "B"), ("D", "C"), ("E", "D"), ("E", "B"), ("E", "A")]]))
        summ.setdefault("replication", {})[name] = {c: rate(rows, c) for c in CFGS}

    # ---- 2 harness variants
    md.append("\n## 2. Harness variants on the same tasks (v1 control, v1r = repair turn, v2 = repair + two rules)\n")
    for mname, key in [("Qwen2.5-7B-Instruct", "c2_qwen25_7b"), ("Qwen3-8B", "c2_qwen3_8b")]:
        runs = {h: R.get(f"{key}_{h}") for h in ("v1", "v1r", "v2")}
        if not runs["v1"]:
            continue
        md.append(f"### {mname}\n")
        lines = []
        for h, rows in runs.items():
            if rows:
                lines.append([h] + [cell(rows, c) for c in CFGS]
                             + [f"{sum(r['outcome'] in BROKEN for r in rows.values())}/{len(rows)}",
                                f"{sum(r['harmful'] for r in rows.values())}/{len(rows)}",
                                f"{sum(r['repair_used'] for r in rows.values())}"])
        md.append(table(["Harness"] + [f"success {c}" for c in CFGS] + ["format/step-limit (all)", "harmful (all)",
                                                                           "repair turns used"], lines))
        lines = []
        for h in ("v1r", "v2"):
            if runs[h]:
                keys = list(runs["v1"])
                lines.append(prow(f"{h} - v1, all configs", paired(runs[h], runs["v1"], keys)))
                for c in CFGS:
                    lines.append(prow(f"{h} - v1, config {c}", paired(runs[h], runs["v1"], [k for k in keys if k[1] == c])))
        md.append(table(PH, lines))
        lines = []
        for h, rows in runs.items():
            if rows:
                oc = Counter(r["outcome"] for r in rows.values())
                s5 = [cell(rows, cc, scen="S5_unsupported") for cc in ("A", "B", "E")]
                mem = [r for (t, c), r in rows.items() if c in "BCDE" and r["scenario"][:2] in ("S1", "S2", "S3", "S4")]
                fb = [r for (t, c), r in rows.items() if c in "BCDE" and r["variant"] == "permanent_memory_fallback"]
                lines.append([h, oc["format_error"], oc["max_steps"], oc["over_abstain"], oc["false_conflict"]]
                             + s5 + [f"{sum(r['n_memory_calls'] > 0 for r in mem)}/{len(mem)}",
                                     f"{sum(r['success'] for r in fb)}/{len(fb)}"])
        md.append(table(["Harness", "format_error", "max_steps", "over_abstain", "false_conflict", "S5 correct A",
                         "S5 correct B", "S5 correct E", "memory consulted (S1-S4, B-E)",
                         "memory fallback when tool is down (B-E)"], lines))
        md.append(f"By scenario, {mname}, v2:\n")
        if runs["v2"]:
            md.append(table(["Scenario"] + CFGS, [[s] + [cell(runs["v2"], c, scen=s) for c in CFGS] for s in SCEN]))
    v2 = [("q25", R["c2_qwen25_7b_v2"]), ("q3", R["c2_qwen3_8b_v2"])]
    pooled2 = merge(*v2)
    if pooled2:
        md.append("### Pooled (both models), v2 harness: do the component effects survive the fixes?\n")
        md.append(table(["Config", "Task success", "Harmful", "Format/step-limit"],
                        [[memlab.CONFIGS[c]["label"], pct(*rate(pooled2, c)),
                          f"{sum(r['harmful'] for (t, cc), r in pooled2.items() if cc == c)}",
                          f"{sum(r['outcome'] in BROKEN for (t, cc), r in pooled2.items() if cc == c)}"] for c in CFGS]))
        md.append(table(PH, [prow(f"{a} - {b}", cfg_pairs(pooled2, a, b)) for a, b in
                             [("B", "A"), ("C", "B"), ("D", "C"), ("E", "D"), ("E", "B"), ("E", "A")]]))
        md.append(table(["Scenario"] + CFGS, [[s] + [cell(pooled2, c, scen=s) for c in CFGS] for s in SCEN]))

    # ---- 3 size sweep
    md.append("\n## 3. Model size inside one family (Qwen2.5-Instruct, same backend)\n")
    sizes = [("1.5B", "c2_qwen25_1p5b"), ("3B", "c2_qwen25_3b"), ("7B", "c2_qwen25_7b"), ("14B", "c2_qwen25_14b")]
    for h in ("v1", "v2"):
        lines, eff = [], []
        for sz, key in sizes:
            rows = R.get(f"{key}_{h}")
            if not rows:
                lines.append([sz] + ["not run"] * 7)
                continue
            n = len(rows)
            lines.append([sz] + [cell(rows, c) for c in CFGS]
                         + [f"{sum(r['outcome'] in BROKEN for r in rows.values())}/{n}",
                            f"{sum(r['harmful'] for r in rows.values())}/{n}"])
            e = [sz]
            for a, b in [("B", "A"), ("C", "B"), ("D", "C"), ("E", "D"), ("E", "B")]:
                c = cfg_pairs(rows, a, b)
                e.append(f"{100 * c['diff']:+.1f} (p={pfmt(c['p'])})" if c else "-")
            eff.append(e)
            summ.setdefault("sizes", {}).setdefault(h, {})[sz] = {c: rate(rows, c) for c in CFGS}
        md.append(f"### Harness {h}\n")
        md.append(table(["Size"] + [f"success {c}" for c in CFGS] + ["format/step-limit (all)", "harmful (all)"], lines))
        md.append("Paired effect of each added component, in percentage points:\n")
        md.append(table(["Size", "B - A (memory)", "C - B (verifier)", "D - C (provenance)", "E - D (gate)",
                         "E - B (all three)"], eff))

    # ---- 4 retriever end to end
    md.append("\n## 4. Retriever inside the agent, 2,000 background records per store "
              "(Qwen2.5-7B, v2 harness, scenarios S1-S4, configs B, D, E)\n")
    base = R.get("c2_qwen25_7b_v2")
    lines = []
    sub = lambda rows, c: [r for (t, cc), r in rows.items() if cc == c and r["scenario"][:2] in ("S1", "S2", "S3", "S4")]  # noqa: E731
    for label, key in [("hash256, no padding (7-12 records)", "c2_qwen25_7b_v2"),
                       ("hash256 + 2,000", "c2_qwen25_7b_v2_hash_pad2000"),
                       ("BM25 + 2,000", "c2_qwen25_7b_v2_bm25_pad2000"),
                       ("bge-small + 2,000", "c2_qwen25_7b_v2_dense_pad2000")]:
        rows = R.get(key)
        if not rows:
            lines.append([label] + ["not run"] * 5)
            continue
        row = [label]
        for c in ("B", "D", "E"):
            x = sub(rows, c)
            row.append(f"{sum(r['success'] for r in x)}/{len(x)}")
        x = [r for c in ("B", "D", "E") for r in sub(rows, c) if r["recall_union"] is not None]
        row.append(f"{np.mean([r['recall_union'] for r in x]):.2f} (n={len(x)})" if x else "-")
        row.append(f"{sum(r['harmful'] for c in ('B', 'D', 'E') for r in sub(rows, c))}")
        lines.append(row)
    md.append(table(["Retriever and store", "success B", "success D", "success E",
                     "gold-record recall over the agent's queries", "harmful"], lines))
    if base:
        cmp_lines = []
        for label, key in [("hash256+2000 - no padding", "c2_qwen25_7b_v2_hash_pad2000"),
                           ("BM25+2000 - hash256+2000", "c2_qwen25_7b_v2_bm25_pad2000"),
                           ("bge-small+2000 - hash256+2000", "c2_qwen25_7b_v2_dense_pad2000")]:
            rows = R.get(key)
            ref = base if "no padding" in label else R.get("c2_qwen25_7b_v2_hash_pad2000")
            if rows and ref:
                cmp_lines.append(prow(label, paired(rows, ref, list(rows))))
        md.append(table(PH, cmp_lines))

    # ---- 5 adapter and repeats
    md.append("\n## 5. Repository adapter and run-to-run spread\n")
    lines = []
    for label, key in [("Qwen2.5-7B, v1", "c2_qwen25_7b_v1"), ("Qwen2.5-7B + adapter, v1", "c2_qwen25_7b_lora_v1"),
                       ("Qwen2.5-7B, v2 (greedy)", "c2_qwen25_7b_v2"), ("Qwen2.5-7B + adapter, v2", "c2_qwen25_7b_lora_v2"),
                       ("Qwen2.5-7B, v2, T=0.7 seed 1", "c2_qwen25_7b_v2_T07_s1"),
                       ("Qwen2.5-7B, v2, T=0.7 seed 2", "c2_qwen25_7b_v2_T07_s2")]:
        rows = R.get(key)
        lines.append([label] + ([cell(rows, c) for c in CFGS]
                                + [f"{sum(r['outcome'] in BROKEN for r in rows.values())}/{len(rows)}"]
                                if rows else ["not run"] * 6))
    md.append(table(["Run"] + [f"success {c}" for c in CFGS] + ["format/step-limit (all)"], lines))

    # ---- 6 AGENTRUN's own benchmarks
    md.append("\n## 6. AGENTRUN's own benchmarks, client-matched, frozen tool environment\n")
    lines, per = [], {}
    for rid in sorted(p.name for p in RAW.glob("c2_legacy23_*")):
        f = RAW / rid / "scores.json"
        if f.exists():
            s = json.loads(f.read_text(encoding="utf-8"))
            per[rid] = {x["task_id"]: bool(x["r0"]) for x in s["per_task"]}
            lines.append([rid, s["condition"], s["max_steps"], f"{s['summary']['r0_pass']}/23",
                          ", ".join(t for t, ok in per[rid].items() if not ok) or "-"])
        else:
            lines.append([rid, "INCOMPLETE", "-", "-", "-"])
    md.append("### Legacy 23 tasks, scored by the frozen `eval/harness.py` (R0)\n")
    md.append(table(["Run", "Condition", "Step budget", "R0 pass", "Failed tasks"], lines))
    for b in ("b3", "b6"):
        a, c = per.get(f"c2_legacy23_adapter_{b}"), per.get(f"c2_legacy23_base_{b}")
        if a and c:
            plus = sum(a[t] and not c[t] for t in a)
            minus = sum(c[t] and not a[t] for t in a)
            md.append(f"Adapter vs base, budget {b[1]}: adapter-only passes {plus}, base-only passes {minus}, "
                      f"exact McNemar p = {pfmt(mcnemar_exact(plus, minus))}.\n")
    lines = []
    for rid in sorted(p.name for p in RAW.glob("c2_v2dev55_*")):
        f = RAW / rid / "scores.json"
        if f.exists():
            s = json.loads(f.read_text(encoding="utf-8"))
            sm = s["summary"]
            bn = sm["by_necessity"]
            lines.append([rid, s["condition"], s["max_steps"], f"{100 * sm['r2_correct']:.1f}%",
                          f"{100 * sm['r0_rule']:.1f}%", f"{100 * sm['exhausted']:.1f}%"]
                         + [f"{100 * bn[k]['r2_correct']:.0f}% (n={bn[k]['n']})" for k in ("necessary", "optional", "unnecessary")]
                         + ["; ".join(f"{k}:{v}" for k, v in sm["failure_modes"].items() if v)])
            per[rid] = {x["task_id"]: bool(x["correct"]) for x in s["per_task"]}
        else:
            lines.append([rid, "INCOMPLETE"] + ["-"] * 8)
    md.append("### Benchmark v2, dev split (55 tasks), scored by `scorer_v2` (exploratory; the sealed test split was not used)\n")
    md.append(table(["Run", "Condition", "Budget", "R2 correct", "R0-rule", "Exhausted", "R2 tool-necessary",
                     "R2 tool-optional", "R2 tool-unnecessary", "Failure modes"], lines))
    for b in ("b3", "b6"):
        a, c = per.get(f"c2_v2dev55_adapter_{b}"), per.get(f"c2_v2dev55_base_{b}")
        if a and c:
            plus = sum(a[t] and not c[t] for t in a)
            minus = sum(c[t] and not a[t] for t in a)
            md.append(f"Adapter vs base on R2, budget {b[1]}: adapter-only correct {plus}, base-only correct {minus}, "
                      f"exact McNemar p = {pfmt(mcnemar_exact(plus, minus))}.\n")

    (OUT / "C2_TABLES.md").write_text("\n".join(md), encoding="utf-8")
    (OUT / "c2_summary.json").write_text(json.dumps(summ, indent=1, default=str), encoding="utf-8")
    figures(R, sizes)
    print("\n".join(md))
    return 0


def figures(R, sizes):
    import matplotlib
    matplotlib.use("Agg")
    import matplotlib.pyplot as plt
    INK, MUTED, GRID, SURFACE = "#0b0b0b", "#898781", "#e1e0d9", "#fcfcfb"
    COL = dict(zip(CFGS, ["#2a78d6", "#eb6834", "#1baf7a", "#eda100", "#e87ba4"]))

    def style(ax):
        ax.set_facecolor(SURFACE)
        for s in ("top", "right", "left"):
            ax.spines[s].set_visible(False)
        ax.spines["bottom"].set_color("#c3c2b7")
        ax.tick_params(colors=MUTED, length=0, labelsize=9)
        ax.yaxis.grid(True, color=GRID, linewidth=0.8)
        ax.set_axisbelow(True)

    # size sweep: one panel per harness, one line per configuration
    have = [h for h in ("v1", "v2") if any(R.get(f"{k}_{h}") for _, k in sizes)]
    if have:
        fig, axes = plt.subplots(1, len(have), figsize=(5.6 * len(have), 4.3), facecolor=SURFACE, squeeze=False)
        for ax, h in zip(axes[0], have):
            style(ax)
            xs = [i for i, (_, k) in enumerate(sizes) if R.get(f"{k}_{h}")]
            for c in CFGS:
                ys = []
                for i in xs:
                    k, n = rate(R[f"{sizes[i][1]}_{h}"], c)
                    ys.append(100 * k / n)
                ax.plot(xs, ys, color=COL[c], linewidth=2, marker="o", markersize=7, label=memlab.CONFIGS[c]["label"])
                if c in ("A", "E"):  # label only the two extremes; the middle lines overlap at 14B
                    ax.text(xs[-1] + 0.07, ys[-1], f"{c} {ys[-1]:.0f}", fontsize=8, color=INK, va="center")
            ax.set_xticks(range(len(sizes)))
            ax.set_xticklabels([s for s, _ in sizes], color=INK)
            ax.set_xlim(-0.25, len(sizes) - 0.55)
            ax.set_ylim(0, 100)
            ax.set_xlabel("Qwen2.5-Instruct model size", color=MUTED, fontsize=9)
            ax.set_ylabel("Task success (%)", color=MUTED, fontsize=9)
            ax.set_title(f"Harness {h}", loc="left", color=INK, fontsize=11)
        axes[0][0].legend(frameon=False, fontsize=8, loc="upper left")
        fig.suptitle("Task success by model size and configuration; eval2, 96 tasks, greedy, NVIDIA L40", x=0.01,
                     ha="left", color=MUTED, fontsize=8.5, y=0.02)
        fig.tight_layout()
        fig.savefig(FIG / "fig5_size_sweep.png", dpi=170)
        plt.close(fig)

    # harness effect: outcome composition per harness and model (failure analysis)
    groups = [("Correct", ["correct"], "#0ca30c"), ("Safe miss", ["over_abstain", "false_conflict"], "#c3c2b7"),
              ("Harmful assertion", ["wrong_value", "stale_value", "unsupported_claim", "arbitrary_pick"], "#d03b3b"),
              ("Format error / step limit", ["format_error", "max_steps"], "#52514e")]
    bars = [(f"{m} {h}", R.get(f"{k}_{h}")) for m, k in [("Qwen2.5-7B", "c2_qwen25_7b"), ("Qwen3-8B", "c2_qwen3_8b")]
            for h in ("v1", "v1r", "v2")]
    bars = [(n, r) for n, r in bars if r]
    if bars:
        fig, ax = plt.subplots(figsize=(8.8, 0.62 * len(bars) + 1.9), facecolor=SURFACE)
        style(ax)
        ax.yaxis.grid(False)
        ax.xaxis.grid(True, color=GRID, linewidth=0.8)
        left = np.zeros(len(bars))
        for name, outs, col in groups:
            vals = np.array([100 * sum(r["outcome"] in outs for r in rows.values()) / len(rows) for _, rows in bars])
            ax.barh(range(len(bars)), vals, left=left, color=col, edgecolor=SURFACE, linewidth=2, height=0.62, label=name)
            for i, (v, l0) in enumerate(zip(vals, left)):
                if v >= 4:
                    ax.text(l0 + v / 2, i, f"{v:.0f}%", ha="center", va="center", fontsize=8.5,
                            color=INK if col == "#c3c2b7" else "#ffffff")
            left += vals
        ax.set_yticks(range(len(bars)))
        ax.set_yticklabels([n for n, _ in bars], color=INK, fontsize=9)
        ax.invert_yaxis()
        ax.set_xlim(0, 100)
        ax.set_xlabel("Share of runs, all five configurations (%)", color=MUTED, fontsize=9)
        ax.set_title("Outcome mix by harness: v1 frozen vs v2 (repair turn + two rules)", loc="left",
                     color=INK, fontsize=11)
        ax.legend(ncol=4, frameon=False, fontsize=8.5, loc="upper center", bbox_to_anchor=(0.45, -0.22))
        fig.tight_layout()
        fig.savefig(FIG / "fig6_harness_outcomes.png", dpi=170)
        plt.close(fig)


if __name__ == "__main__":
    raise SystemExit(main())
