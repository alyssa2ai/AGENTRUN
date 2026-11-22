"""Figures for the MITACS dossier. Every chart reads build/verified_numbers.json
(produced from raw outputs by verify_numbers.py); diagrams are drawn here.

    py -3.11 build/make_figures.py
"""

from __future__ import annotations

import json
from pathlib import Path

import matplotlib

matplotlib.use("Agg")
import matplotlib.pyplot as plt  # noqa: E402
from matplotlib.patches import FancyArrowPatch, FancyBboxPatch  # noqa: E402

HERE = Path(__file__).resolve().parent.parent
FIG = HERE / "figures"
FIG.mkdir(exist_ok=True)
V = json.loads((HERE / "build" / "verified_numbers.json").read_text(encoding="utf-8"))

INK, INK2, MUTED, GRID, SURF, BASE = "#0b0b0b", "#52514e", "#898781", "#e1e0d9", "#ffffff", "#c3c2b7"
CFG = ["A", "B", "C", "D", "E"]
CFG_LABEL = {"A": "A stateless", "B": "B memory", "C": "C + text verifier", "D": "D + provenance", "E": "E + staleness gate"}
COL = dict(zip(CFG, ["#2a78d6", "#eb6834", "#1baf7a", "#eda100", "#e87ba4"]))
GOOD, WARN, BAD, DARK = "#0ca30c", "#fab219", "#d03b3b", "#52514e"
plt.rcParams.update({"font.family": "DejaVu Sans", "font.size": 9, "axes.titlesize": 10.5, "savefig.dpi": 200})


def style(ax, grid="y"):
    ax.set_facecolor(SURF)
    for s in ("top", "right", "left"):
        ax.spines[s].set_visible(False)
    ax.spines["bottom"].set_color(BASE)
    ax.tick_params(colors=INK2, length=0)
    if grid:
        getattr(ax, f"{grid}axis").grid(True, color=GRID, linewidth=0.7)
    ax.set_axisbelow(True)


def save(fig, name):
    fig.savefig(FIG / name, bbox_inches="tight", facecolor=SURF)
    plt.close(fig)


def pct(block, c):
    return block["configs"][c]["pct"]


# ---------------------------------------------------------------- diagrams
def box(ax, x, y, w, h, text, fc="#f4f6fa", ec="#5b6b82", fs=8.2, bold=False, ls="-"):
    ax.add_patch(FancyBboxPatch((x, y), w, h, boxstyle="round,pad=0.012,rounding_size=0.018", fc=fc, ec=ec,
                                lw=1.1, ls=ls))
    ax.text(x + w / 2, y + h / 2, text, ha="center", va="center", fontsize=fs, color=INK,
            fontweight="bold" if bold else "normal", wrap=True)


def arrow(ax, x0, y0, x1, y1, text="", col="#5b6b82", ls="-", off=(0, 0.012), fs=7):
    ax.add_patch(FancyArrowPatch((x0, y0), (x1, y1), arrowstyle="-|>", mutation_scale=10, color=col, lw=1.0, ls=ls))
    if text:
        ax.text((x0 + x1) / 2 + off[0], (y0 + y1) / 2 + off[1], text, ha="center", va="bottom", fontsize=fs, color=INK2)


def canvas(w=10, h=5.6):
    fig, ax = plt.subplots(figsize=(w, h))
    ax.set_xlim(0, 1)
    ax.set_ylim(0, 1)
    ax.axis("off")
    return fig, ax


def fig_arch_original():
    fig, ax = canvas(10, 5.6)
    ax.add_patch(FancyBboxPatch((0.01, 0.40), 0.62, 0.57, boxstyle="round,pad=0.005", fc="#fbfbf9", ec=BASE, lw=0.8))
    ax.text(0.02, 0.955, "Runtime (agent.py with main.py; ft_agent.py for the Qwen models)", fontsize=8, color=INK2, va="top")
    box(ax, 0.03, 0.77, 0.14, 0.10, "User prompt", fc="#ffffff")
    box(ax, 0.25, 0.71, 0.19, 0.19, "Agent loop\nthink / act / observe\nmax 6 steps\n(Gemini; Qwen via HTTP)")
    box(ax, 0.03, 0.46, 0.14, 0.10, "Final answer", fc="#ffffff")
    box(ax, 0.25, 0.44, 0.22, 0.15, "memory.py  VectorMemory\n256-d hashed bag-of-words\ncosine, top-3, sim >= 0.2\nmemory_store.json", fc="#fff4e8", ec="#c27a2c")
    arrow(ax, 0.17, 0.82, 0.25, 0.82)
    arrow(ax, 0.25, 0.74, 0.17, 0.53)
    arrow(ax, 0.31, 0.71, 0.31, 0.59)
    ax.text(0.305, 0.655, "search(prompt)", ha="right", fontsize=7, color=INK2)
    arrow(ax, 0.40, 0.59, 0.40, 0.71)
    ax.text(0.41, 0.655, "top-3 texts\nprepended", ha="left", fontsize=7, color=INK2, va="center")
    arrow(ax, 0.17, 0.48, 0.25, 0.48, col="#c27a2c", ls="--")
    ax.text(0.21, 0.415, "answer stored\nas a new memory", ha="center", fontsize=6.8, color="#c27a2c", va="top")
    ax.add_patch(FancyBboxPatch((0.67, 0.40), 0.32, 0.57, boxstyle="round,pad=0.005", fc="#f6f8fb", ec=BASE, lw=0.8))
    ax.text(0.68, 0.955, "Tools over MCP (stdio) and model serving", fontsize=8, color=INK2, va="top")
    box(ax, 0.70, 0.72, 0.27, 0.17, "mcp_server.py (FastMCP)\ncalculator, word_count,\nweb_search (Tavily),\nget_weather (Open-Meteo)")
    box(ax, 0.70, 0.44, 0.27, 0.16, "serving/colab_server*.py\nQwen2.5-7B + LoRA adapter\non a Colab T4, with the\nserver-side tool-call parser")
    arrow(ax, 0.44, 0.85, 0.70, 0.85)
    ax.text(0.57, 0.86, "MCP call_tool", ha="center", fontsize=7, color=INK2)
    arrow(ax, 0.70, 0.78, 0.44, 0.78)
    ax.text(0.57, 0.755, "observation", ha="center", fontsize=7, color=INK2, va="top")
    arrow(ax, 0.44, 0.72, 0.70, 0.52, ls="--")
    ax.text(0.60, 0.555, "HTTP /chat\n(ft_agent.py only)", ha="left", fontsize=7, color=INK2, va="top")
    ax.add_patch(FancyBboxPatch((0.01, 0.03), 0.98, 0.31, boxstyle="round,pad=0.005", fc="#fbfbf9", ec=BASE, lw=0.8))
    ax.text(0.02, 0.325, "Offline: training and evaluation", fontsize=8, color=INK2, va="top")
    box(ax, 0.03, 0.07, 0.20, 0.18, "training/*.jsonl\nV1: 35 trajectories\nV2: 46 (35 + 11 targeted)")
    box(ax, 0.29, 0.07, 0.20, 0.18, "colab_train_7b*.py\nQLoRA: 4-bit NF4,\nr=16, alpha=16, q/k/v/o")
    box(ax, 0.55, 0.07, 0.19, 0.18, "eval/tasks.py\n23 tasks, 12 categories\neval/harness.py (R0)")
    box(ax, 0.79, 0.07, 0.18, 0.18, "results/*.json\nBase 22, V1 18,\nE4 18, V2 23 of 23")
    arrow(ax, 0.23, 0.16, 0.29, 0.16)
    arrow(ax, 0.49, 0.16, 0.55, 0.16)
    arrow(ax, 0.74, 0.16, 0.79, 0.16)
    ax.text(0.5, -0.02, "Memory is an in-process Python store, not an MCP service. Only the Gemini agent uses it; "
            "the Qwen agents and both benchmarks never do.", ha="center", fontsize=7.6, color=INK2)
    save(fig, "fig01_architecture_original.png")


def fig_arch_research():
    fig, ax = canvas(10, 6.0)
    ax.add_patch(FancyBboxPatch((0.01, 0.05), 0.98, 0.93, boxstyle="round,pad=0.005", fc="#fbfbf9", ec=BASE, lw=0.8))
    ax.text(0.02, 0.968, "Research harness: research/AGENTRUN_DEEPENING_2026-11-11/scripts/memlab.py "
            "(experimental; not part of the production runtime)", fontsize=8, color=INK2, va="top")
    box(ax, 0.03, 0.75, 0.14, 0.13, "Frozen task\n(only the prompt\nreaches the model)", fc="#ffffff")
    box(ax, 0.23, 0.71, 0.20, 0.21, "Agent loop (run_task)\nsame model, prompt and\ndecoding for A-E\nmax 6 steps\nharness v1 or v2")
    box(ax, 0.50, 0.75, 0.17, 0.13, "Draft answer\nsubmit_answer(status,\nvalue, evidence)")
    box(ax, 0.74, 0.73, 0.22, 0.17, "Verifier (C, D, E)\nsame model, no tools\nSUPPORTED / UNSUPPORTED\n/ CONFLICT", fc="#eaf6f0", ec="#1b8a5a")
    box(ax, 0.03, 0.47, 0.14, 0.11, "calculator\n(tools.calculator)")
    box(ax, 0.03, 0.27, 0.14, 0.13, "registry_lookup\nfixture, scripted\nfailures in S6")
    box(ax, 0.23, 0.27, 0.20, 0.31, "memory_search (B-E)\nper-task JSON store\nmemory.embed_text\n+ cosine, top-4,\nsim >= 0.2\n(BM25 or dense in the\npadded-store runs)", fc="#fff4e8", ec="#c27a2c")
    box(ax, 0.50, 0.46, 0.17, 0.11, "B, C: record\ntext only", fc="#ffffff", ec="#c27a2c")
    box(ax, 0.50, 0.29, 0.17, 0.12, "D, E: + record id,\ndate, source", fc="#ffffff", ec="#c27a2c")
    box(ax, 0.74, 0.27, 0.19, 0.30, "E only: reliability gate\nfor each (entity,\nattribute): current,\nsuperseded,\nconflicting or\nunchallenged; adds\nsame-key records", fc="#fdeef3", ec="#b04b74")
    box(ax, 0.40, 0.08, 0.28, 0.12, "Scorer: memlab.classify\n(ground truth never sent to the model)", fc="#f1f1ee")
    box(ax, 0.74, 0.08, 0.19, 0.12, "Final answer", fc="#ffffff")
    arrow(ax, 0.17, 0.815, 0.23, 0.815)
    arrow(ax, 0.23, 0.74, 0.17, 0.53)
    arrow(ax, 0.23, 0.72, 0.17, 0.35)
    arrow(ax, 0.33, 0.71, 0.33, 0.58)
    arrow(ax, 0.43, 0.515, 0.50, 0.515)
    arrow(ax, 0.43, 0.35, 0.50, 0.35)
    arrow(ax, 0.67, 0.35, 0.74, 0.40)
    arrow(ax, 0.43, 0.815, 0.50, 0.815)
    arrow(ax, 0.67, 0.815, 0.74, 0.815)
    ax.text(0.705, 0.83, "status =\nanswer", ha="center", fontsize=6.6, color=INK2, va="bottom")
    arrow(ax, 0.955, 0.73, 0.955, 0.20, ls=":")
    ax.text(0.965, 0.64, "UNSUPPORTED\n-> abstain\nCONFLICT\n-> conflict", fontsize=6.4, color=INK2, va="center", ha="left")
    ax.text(0.585, 0.725, "A, B: the draft is the final answer", fontsize=6.6, color=INK2, ha="center", va="top")
    arrow(ax, 0.74, 0.14, 0.68, 0.14)
    ax.text(0.20, 0.215, "Tool results, with or without provenance\nand gate labels, return to the agent loop\nas observations.",
            fontsize=6.8, color=INK2, ha="center", va="center")
    ax.text(0.5, 0.01, "Orange: memory path. Pink: computed in code, not by the model. Green: second LLM call. "
            "Configurations A-E differ only in which parts are switched on.", ha="center", fontsize=7.4, color=INK2)
    save(fig, "fig02_architecture_research.png")


def fig_timeline():
    fig, ax = canvas(10, 2.6)
    ax.plot([0.03, 0.97], [0.5, 0.5], color=BASE, lw=2)
    ev = [(0.05, "Aug-Sep 2026", "Gemini agent, MCP tools,\nhashed vector memory"),
          (0.20, "1 Sep", "Base 22/23, V1 18/23,\nV2 23/23 (Colab T4)"),
          (0.35, "16 Sep", "E4: V1 adapter, new\nparser + client: 18/23"),
          (0.50, "Oct", "Audit: E4 confound,\nbenchmark v2 (185 tasks)\nbuilt and sealed"),
          (0.66, "11 Nov", "Campaign 1: 48 tasks,\nhosted + SIT HPC L40,\n1,440 local runs"),
          (0.83, "12 Nov", "Campaign 2: 96 fresh tasks,\n14/21 Slurm jobs,\n5,184 agent runs"),
          (0.96, "today", "interview")]
    for i, (x, d, t) in enumerate(ev):
        ax.plot([x], [0.5], "o", color="#2a78d6" if i < 4 else "#e87ba4", ms=8, zorder=3)
        up = i % 2 == 0
        ax.text(x, 0.66 if up else 0.34, d, ha="center", va="bottom" if up else "top", fontsize=8.5, fontweight="bold")
        ax.text(x, 0.86 if up else 0.14, t, ha="center", va="bottom" if up else "top", fontsize=7.4, color=INK2) if False else \
            ax.text(x, 0.78 if up else 0.22, t, ha="center", va="bottom" if up else "top", fontsize=7.2, color=INK2)
    save(fig, "fig03_timeline.png")


def fig_workflow():
    fig, ax = canvas(10, 3.0)
    steps = [("Generate tasks\nseeded, fictional\nentities", 0.02), ("Freeze\nSHA-256 of tasks,\nprompts, configs", 0.18),
             ("Leakage audit\n17 static checks", 0.34), ("Run A-E per task\nSlurm array on L40\nraw transcripts", 0.50),
             ("Score\nfrozen classifier\n+ transcript audit", 0.66), ("Paired analysis\nMcNemar, task\nbootstrap", 0.82)]
    for t, x in steps:
        box(ax, x, 0.38, 0.145, 0.42, t, fs=8)
    for (_, x0), (_, x1) in zip(steps, steps[1:]):
        arrow(ax, x0 + 0.145, 0.59, x1, 0.59)
    ax.text(0.5, 0.17, "Development tasks (12) used for prompt changes; evaluation splits (48, then 96) run once per frozen "
            "harness; the sealed 130-task split was never touched.", ha="center", fontsize=7.8, color=INK2)
    save(fig, "fig04_workflow.png")


# ---------------------------------------------------------------- charts
def grouped(ax, groups, series, values, colors, labels, ylim=100, fmt="{:.0f}"):
    import numpy as np
    n = len(series)
    w = 0.8 / n
    x = np.arange(len(groups))
    for i, s in enumerate(series):
        vals = values[s]
        b = ax.bar(x + (i - (n - 1) / 2) * w, vals, w * 0.92, color=colors[s], label=labels[s], edgecolor=SURF, lw=0.8)
        for rect, v in zip(b, vals):
            ax.text(rect.get_x() + rect.get_width() / 2, v + ylim * 0.012, fmt.format(v), ha="center", va="bottom",
                    fontsize=7, color=INK)
    ax.set_xticks(x)
    ax.set_xticklabels(groups, color=INK)
    ax.set_ylim(0, ylim * 1.1)


def fig_campaign1():
    fig, ax = plt.subplots(figsize=(8.6, 3.5))
    style(ax)
    groups = ["Local 7-8B on L40\n(144 task blocks)", "Hosted larger models\n(71 task blocks)"]
    vals = {c: [pct(V["c1_local_greedy"], c), pct(V["c1_hosted"], c)] for c in CFG}
    grouped(ax, groups, CFG, vals, COL, CFG_LABEL)
    ax.set_ylabel("Task success (%)", color=INK2)
    ax.legend(ncol=5, frameon=False, fontsize=7.6, loc="upper center", bbox_to_anchor=(0.5, -0.13))
    save(fig, "fig05_campaign1.png")


def fig_replication():
    fig, ax = plt.subplots(figsize=(8.6, 3.6))
    style(ax)
    R = V["c2_runs"]
    groups = ["Qwen2.5-7B\n(96 tasks)", "Qwen3-8B\n(96 tasks)", "Pooled\n(192 task blocks)"]
    vals = {c: [R["c2_qwen25_7b_v1"]["configs"][c]["pct"], R["c2_qwen3_8b_v1"]["configs"][c]["pct"],
                pct(V["c2_pooled_v1"], c)] for c in CFG}
    grouped(ax, groups, CFG, vals, COL, CFG_LABEL)
    ax.set_ylabel("Task success (%)", color=INK2)
    ax.legend(ncol=5, frameon=False, fontsize=7.6, loc="upper center", bbox_to_anchor=(0.5, -0.13))
    save(fig, "fig06_replication.png")


def fig_effects():
    fig, axes = plt.subplots(1, 2, figsize=(9.2, 3.2), sharey=True)
    axes[0].invert_yaxis()
    keys = ["B-A", "C-B", "D-C", "E-D", "E-B"]
    names = ["Memory\n(B - A)", "Text verifier\n(C - B)", "Provenance\n(D - C)", "Staleness gate\n(E - D)", "All three\n(E - B)"]
    for ax, blk, title in zip(axes, ["c2_pooled_v1", "c2_pooled_v2"], ["Original harness (v1)", "Revised harness (v2)"]):
        style(ax, grid="x")
        for i, k in enumerate(keys):
            p = V[blk]["paired"][k]
            sig = p["p_mcnemar"] < 0.05
            col = (GOOD if p["diff_pp"] > 0 else BAD) if sig else MUTED
            ax.plot(p["ci_pp"], [i, i], color=col, lw=2.2, solid_capstyle="round")
            ax.plot([p["diff_pp"]], [i], "o", color=col, ms=7)
            ax.text(max(p["ci_pp"][1], 0) + 1.5, i, f"{p['diff_pp']:+.1f}  (p={p['p_mcnemar']:.2g})", va="center", fontsize=7.2,
                    color=INK)
        ax.axvline(0, color=INK2, lw=0.8)
        ax.set_yticks(range(len(keys)))
        ax.set_yticklabels(names, color=INK)
        ax.set_xlim(-25, 85)
        ax.set_xlabel("Difference, percentage points (95% CI)", color=INK2, fontsize=8)
        ax.set_title(title, loc="left")
    save(fig, "fig07_effects.png")


def fig_scenarios():
    import numpy as np
    scen = ["S1 context loss", "S2 retrieval", "S3 conflict", "S4 stale", "S5 unsupported", "S6 tool failure"]
    keys = ["S1_context_loss", "S2_retrieval", "S3_conflict", "S4_stale", "S5_unsupported", "S6_tool_failure"]
    fig, axes = plt.subplots(1, 2, figsize=(9.2, 3.4))
    for ax, blk, title in zip(axes, ["c2_pooled_v1", "c2_pooled_v2"], ["Original harness (v1)", "Revised harness (v2)"]):
        m = np.array([[V[blk]["configs"][c]["by_scenario"][k][0] for c in CFG] for k in keys])
        ax.imshow(m / 32, cmap="Blues", vmin=0, vmax=1.15, aspect="auto")
        for i in range(m.shape[0]):
            for j in range(m.shape[1]):
                ax.text(j, i, f"{m[i, j]}", ha="center", va="center", fontsize=8,
                        color="#ffffff" if m[i, j] / 32 > 0.6 else INK)
        ax.set_xticks(range(5))
        ax.set_xticklabels(CFG)
        ax.set_yticks(range(6))
        ax.set_yticklabels(scen if ax is axes[0] else [""] * 6)
        ax.tick_params(length=0)
        for s in ax.spines.values():
            s.set_visible(False)
        ax.set_title(title + "  (successes of 32)", loc="left")
    save(fig, "fig08_scenarios.png")


def fig_sizes():
    sizes = [("1.5B", "1p5b"), ("3B", "3b"), ("7B", "7b"), ("14B", "14b")]
    fig, axes = plt.subplots(1, 2, figsize=(9.2, 3.4), sharey=True)
    for ax, h in zip(axes, ["v1", "v2"]):
        style(ax)
        for c in CFG:
            ys = [V["c2_runs"][f"c2_qwen25_{k}_{h}"]["configs"][c]["pct"] for _, k in sizes]
            ax.plot(range(4), ys, color=COL[c], lw=2, marker="o", ms=5.5, label=CFG_LABEL[c])
        ax.set_xticks(range(4))
        ax.set_xticklabels([s for s, _ in sizes])
        ax.set_ylim(0, 100)
        ax.set_xlabel("Qwen2.5-Instruct size", color=INK2)
        ax.set_title(f"Harness {h}", loc="left")
    axes[0].set_ylabel("Task success (%)", color=INK2)
    axes[0].legend(frameon=False, fontsize=7.4, ncol=5, loc="upper center", bbox_to_anchor=(1.05, -0.2))
    save(fig, "fig09_sizes.png")


def fig_retrieval_only():
    fig, ax = plt.subplots(figsize=(6.4, 3.2))
    style(ax)
    R = V["retrieval_only"]
    sizes = [2000, 10000, 100000]
    series = [("hash256 (AGENTRUN default)", "hash256", "#2a78d6"), ("BM25", "bm25", "#eb6834"),
              ("all-MiniLM-L6-v2", "dense sentence-transformers/all-MiniLM-L6-v2 (cuda)", "#1baf7a"),
              ("bge-small-en-v1.5", "dense BAAI/bge-small-en-v1.5 (cuda)", "#eda100")]
    for lab, key, col in series:
        ys = [R[f"{key} | nl | {s}"]["recall@4"] for s in sizes]
        ax.plot(range(3), ys, color=col, lw=2, marker="o", ms=6, label=lab)
        if key == "hash256":
            ax.text(2.07, ys[-1], f"{ys[-1]:.2f}", fontsize=7.4, va="center")
    ax.set_xticks(range(3))
    ax.set_xticklabels(["2,000", "10,000", "100,000"])
    ax.set_xlim(-0.2, 2.35)
    ax.set_ylim(0, 1.05)
    ax.set_xlabel("Records in the store", color=INK2)
    ax.set_ylabel("Recall@4", color=INK2)
    ax.text(2.07, 0.985, "0.96-1.00", fontsize=7.4, va="center")
    ax.legend(frameon=False, fontsize=7.4, ncol=2, loc="upper center", bbox_to_anchor=(0.5, -0.2))
    save(fig, "fig10_retrieval_only.png")


def fig_retrieval_e2e():
    E = V["c2_retriever_e2e"]["by_config"]
    fig, ax = plt.subplots(figsize=(7.4, 3.2))
    style(ax)
    groups = ["B memory", "D + provenance", "E + staleness gate"]
    cols = {"no_padding_hash": "#9aa6b2", "hash_2000": "#2a78d6", "bm25_2000": "#eb6834"}
    labs = {"no_padding_hash": "7-12 records, hash256", "hash_2000": "+2,000 records, hash256",
            "bm25_2000": "+2,000 records, BM25"}
    vals = {k: [100 * E[k][c] / 64 for c in "BDE"] for k in cols}
    grouped(ax, groups, list(cols), vals, cols, labs)
    ax.set_ylabel("Task success, S1-S4 (%)", color=INK2)
    ax.legend(ncol=3, frameon=False, fontsize=7.6, loc="upper center", bbox_to_anchor=(0.5, -0.12))
    save(fig, "fig11_retrieval_e2e.png")


def fig_outcomes():
    runs = [("1.5B v1", "c2_qwen25_1p5b_v1"), ("1.5B v2", "c2_qwen25_1p5b_v2"), ("3B v1", "c2_qwen25_3b_v1"),
            ("3B v2", "c2_qwen25_3b_v2"), ("7B v1", "c2_qwen25_7b_v1"), ("7B v2", "c2_qwen25_7b_v2"),
            ("14B v1", "c2_qwen25_14b_v1"), ("14B v2", "c2_qwen25_14b_v2"), ("Qwen3-8B v1", "c2_qwen3_8b_v1"),
            ("Qwen3-8B v2", "c2_qwen3_8b_v2")]
    groups = [("Correct", ["correct"], GOOD), ("Over-abstain", ["over_abstain"], "#c3c2b7"),
              ("False conflict", ["false_conflict"], WARN),
              ("Harmful", ["wrong_value", "stale_value", "unsupported_claim", "arbitrary_pick"], BAD),
              ("Format error", ["format_error"], DARK), ("Step limit", ["max_steps"], "#8a7fbf")]
    fig, ax = plt.subplots(figsize=(9.0, 4.0))
    style(ax, grid="x")
    import numpy as np
    left = np.zeros(len(runs))
    for name, outs, col in groups:
        vals = np.array([100 * sum(V["c2_runs"][r]["all"]["outcomes"].get(o, 0) for o in outs) / 480 for _, r in runs])
        ax.barh(range(len(runs)), vals, left=left, color=col, edgecolor=SURF, lw=1.2, height=0.7, label=name)
        for i, (v, l0) in enumerate(zip(vals, left)):
            if v >= 6:
                ax.text(l0 + v / 2, i, f"{v:.0f}", ha="center", va="center", fontsize=7,
                        color=INK if col in ("#c3c2b7", WARN) else "#ffffff")
        left += vals
    ax.set_yticks(range(len(runs)))
    ax.set_yticklabels([n for n, _ in runs])
    ax.invert_yaxis()
    ax.set_xlim(0, 100)
    ax.set_xlabel("Share of 480 runs (%), all five configurations", color=INK2)
    ax.legend(ncol=6, frameon=False, fontsize=7.4, loc="upper center", bbox_to_anchor=(0.45, -0.12))
    save(fig, "fig12_outcomes.png")


def fig_adapter():
    B = V["repo_benchmarks"]
    fig, axes = plt.subplots(1, 2, figsize=(8.6, 2.9))
    ax = axes[0]
    style(ax)
    base = [B[k]["r0_pass"] for k in ["c2_legacy23_base_b3", "c2_legacy23_base_b6", "c2_legacy23_base_b3_T07_s1",
                                      "c2_legacy23_base_b3_T07_s2", "c2_legacy23_base_b3_T07_s3"]]
    adp = [B[k]["r0_pass"] for k in ["c2_legacy23_adapter_b3", "c2_legacy23_adapter_b6", "c2_legacy23_adapter_b3_T07_s1",
                                     "c2_legacy23_adapter_b3_T07_s2", "c2_legacy23_adapter_b3_T07_s3"]]
    lab = ["greedy\nb3", "greedy\nb6", "T0.7\ns1", "T0.7\ns2", "T0.7\ns3"]
    grouped(ax, lab, ["base", "adapter"], {"base": base, "adapter": adp}, {"base": "#9aa6b2", "adapter": "#2a78d6"},
            {"base": "Base Qwen2.5-7B", "adapter": "V2 adapter"}, ylim=23)
    ax.set_ylim(0, 26)
    ax.set_title("Original 23 tasks (passes of 23)", loc="left")
    ax.legend(frameon=False, fontsize=7.4, loc="upper center", bbox_to_anchor=(1.1, -0.2), ncol=2)
    ax = axes[1]
    style(ax)
    grouped(ax, ["budget 3", "budget 6"], ["base", "adapter"],
            {"base": [100 * B["c2_v2dev55_base_b3"]["r2_correct"] / 55, 100 * B["c2_v2dev55_base_b6"]["r2_correct"] / 55],
             "adapter": [92.727, 100 * B["c2_v2dev55_adapter_b6"]["r2_correct"] / 55]},
            {"base": "#9aa6b2", "adapter": "#2a78d6"}, {"base": "Base", "adapter": "V2 adapter"}, fmt="{:.1f}")
    ax.set_ylim(0, 108)
    ax.set_title("55 fresh v2-dev tasks (% correct)", loc="left")
    save(fig, "fig13_adapter.png")


for f in [fig_arch_original, fig_arch_research, fig_timeline, fig_workflow, fig_campaign1, fig_replication,
          fig_effects, fig_scenarios, fig_sizes, fig_retrieval_only, fig_retrieval_e2e, fig_outcomes, fig_adapter]:
    f()
print("figures:", sorted(p.name for p in FIG.glob("*.png")))
