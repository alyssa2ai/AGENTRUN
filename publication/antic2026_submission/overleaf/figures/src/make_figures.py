"""Generate the paper's figures from figures/data/results_snapshot.json.

Run from the Overleaf project root:  python figures/src/make_figures.py
Requires matplotlib (tested with 3.11). Output: figures/fig*.pdf (vector).

Every plotted value is read from the snapshot, which was extracted from the
committed result files (paths and SHA-256 hashes recorded in the snapshot).
"""

import json
import os

import matplotlib

matplotlib.use("Agg")
import matplotlib.pyplot as plt  # noqa: E402
from matplotlib.patches import FancyBboxPatch  # noqa: E402

HERE = os.path.dirname(os.path.abspath(__file__))
FIG = os.path.dirname(HERE)
SNAP = json.load(open(os.path.join(FIG, "data", "results_snapshot.json"), encoding="utf-8"))

# Springer: vector output, no Type 3 fonts, lettering >= 6 pt, legible in grayscale.
plt.rcParams.update({
    "pdf.fonttype": 42,
    "ps.fonttype": 42,
    "font.family": "serif",
    "font.serif": ["DejaVu Serif"],
    "font.size": 8,
    "axes.linewidth": 0.6,
    "hatch.linewidth": 0.5,
})
TEXTWIDTH_IN = 122 / 25.4  # llncs text block width (122 mm)
CONDS = ["Base", "V1", "E4", "V2"]

# Restrained colour, chosen from the Okabe-Ito colour-blind-safe palette.
# Colour is never the only cue: every figure also uses text labels,
# border style or hatching, so it stays readable in black and white.
BLUE, BLUE_FILL = "#0072B2", "#E1EEF7"      # shared stack components
AMBER, AMBER_FILL = "#B86E00", "#F3C470"    # components that differ in E4
COND_COLOR = {"Base": "#0072B2", "V1": "#E69F00", "E4": "#E69F00", "V2": "#009E73"}
PASS_FILL, PASS_EDGE = "#E2F0E2", "#3B7D3B"  # muted green
FAIL_FILL, FAIL_EDGE = "#F6D2CE", "#000000"  # muted red


def save(fig, name):
    path = os.path.join(FIG, name)
    fig.savefig(path, bbox_inches="tight", pad_inches=0.02)
    plt.close(fig)
    print("wrote", path)


# ---------------------------------------------------------------- Figure 1
def fig_stack():
    """Two evaluation stacks as vertical pipelines; E4 components that differ are amber, dashed."""
    stages = [
        ("Qwen2.5-7B (4-bit) + LoRA adapter", "same base model + V1 adapter", False),
        ("Server: generate, parse tool calls", "server with two-pass parser", False),
        ("Client loop: ft_agent.py (3 steps)", "notebook loop (3 steps)", True),
        ("MCP schemas; tool-call text history", "short schemas; JSON tool messages", True),
        ("Tools via MCP (Tavily, Open-Meteo)", "notebook tool functions (live APIs)", True),
        ("Scorer: score_task()", "score_task() (uploaded copy)", False),
    ]
    fig, ax = plt.subplots(figsize=(TEXTWIDTH_IN, 2.5))
    ax.set_xlim(0, 100)
    ax.set_ylim(1, 100)
    ax.axis("off")
    cols = [(2, "Base, V1, V2\n(run 2026-09-01, full traces)"),
            (52, "E4\n(run 2026-09-16, pass/fail only)")]
    bw, bh, top, step = 46, 9.5, 83, 13.6
    for ci, (x, title) in enumerate(cols):
        ax.text(x + bw / 2, 96, title, ha="center", va="center", fontsize=7)
        for si, (left, right, differs) in enumerate(stages):
            y = top - si * step
            e4diff = ci == 1 and differs
            ax.add_patch(FancyBboxPatch((x, y - bh / 2), bw, bh,
                                        boxstyle="round,pad=0.0,rounding_size=1.2",
                                        linewidth=1.0 if e4diff else 0.7,
                                        linestyle=(0, (3, 1.5)) if e4diff else "solid",
                                        edgecolor=AMBER if e4diff else BLUE,
                                        facecolor=AMBER_FILL if e4diff else BLUE_FILL))
            label = left if ci == 0 else right
            ax.text(x + bw / 2, y, label, ha="center", va="center", fontsize=6.5, color="black")
            if si < len(stages) - 1:
                ax.annotate("", xy=(x + bw / 2, y - step + bh / 2 + 0.3), xytext=(x + bw / 2, y - bh / 2 - 0.3),
                            arrowprops=dict(arrowstyle="-|>", lw=0.5, mutation_scale=5, color="0.25"))
    # Key (text + border style, so it also works in black and white).
    for kx, (fill, edge, ls, lw, txt) in zip(
            (2, 52),
            ((BLUE_FILL, BLUE, "solid", 0.7, "same as the Base/V1/V2 stack"),
             (AMBER_FILL, AMBER, (0, (3, 1.5)), 1.0, "differs in E4 (dashed border)"))):
        ax.add_patch(FancyBboxPatch((kx, 4), 4.5, 4, boxstyle="round,pad=0.0,rounding_size=0.6",
                                    linewidth=lw, linestyle=ls, edgecolor=edge, facecolor=fill))
        ax.text(kx + 6, 6, txt, ha="left", va="center", fontsize=6.5)
    save(fig, "fig1_eval_stacks.pdf")


# ---------------------------------------------------------------- Figure 2
def fig_scores():
    passed = {c: sum(SNAP["outcomes"][c].values()) for c in CONDS}
    total = len(SNAP["tasks"])
    fig, ax = plt.subplots(figsize=(TEXTWIDTH_IN * 0.62, 1.55))
    ys = list(range(len(CONDS)))[::-1]
    for y, c in zip(ys, CONDS):
        e4 = c == "E4"
        # E4: white bar hatched in V1's colour (same adapter, different stack).
        ax.barh(y, passed[c], height=0.55, color="white" if e4 else COND_COLOR[c],
                edgecolor=COND_COLOR[c] if e4 else "black", linewidth=0.8 if e4 else 0.6,
                hatch="////" if e4 else None)
        if e4:  # black outline on top of the coloured hatch, for print legibility
            ax.barh(y, passed[c], height=0.55, color="none", edgecolor="black", linewidth=0.6)
        ax.text(passed[c] + 0.25, y, f"{passed[c]}/{total}", va="center", fontsize=7)
    ax.set_yticks(ys)
    ax.set_yticklabels(["Base (no adapter)", "V1 (35 traj.)", "E4 (V1 adapter)†", "V2 (46 traj.)"],
                       fontsize=7)
    ax.set_xlim(0, total + 3)
    ax.set_xticks([0, 5, 10, 15, 20, 23])
    ax.set_xlabel("Tasks passed (of 23; one run per condition)", fontsize=7)
    ax.tick_params(axis="both", labelsize=7, width=0.5, length=2)
    for s in ("top", "right"):
        ax.spines[s].set_visible(False)
    save(fig, "fig2_scores.pdf")


# ---------------------------------------------------------------- Figure 3
def fig_matrix():
    """Outcome matrix for the seven tasks whose outcome differs across conditions."""
    out = SNAP["outcomes"]
    tasks = [t["id"] for t in SNAP["tasks"] if len({out[c][t["id"]] for c in CONDS}) > 1]
    tr = SNAP["traces"]

    def note(c, tid):
        if c == "E4":
            return ""
        r = tr[c][tid]
        if out[c][tid]:
            return ""
        reasons = " ".join(r["failure_reasons"])
        if r["hit_max_steps"]:
            return "step budget"
        if "missing_required_tools" in reasons and not r["tools"]:
            return "no tool call"
        if "missing_required_tools" in reasons:
            return "calc. skipped"
        if "missing_expected_content" in reasons:
            return "wording"
        return "other"

    fig, ax = plt.subplots(figsize=(TEXTWIDTH_IN, 0.42 * len(tasks) + 0.5))
    ax.set_xlim(-0.5, len(CONDS) - 0.5)
    ax.set_ylim(len(tasks) - 0.5, -0.9)
    for xi, c in enumerate(CONDS):
        if c == "E4":
            ax.add_patch(plt.Rectangle((xi - 0.5, -0.5), 1, len(tasks), facecolor="none",
                                       edgecolor="0.4", hatch="////", linewidth=0))
        for yi, tid in enumerate(tasks):
            ok = out[c][tid]
            ax.text(xi, yi - 0.13, "pass" if ok else "FAIL", ha="center", va="center", fontsize=7,
                    fontweight="normal" if ok else "bold",
                    bbox=dict(facecolor=PASS_FILL if ok else FAIL_FILL,
                              edgecolor=PASS_EDGE if ok else FAIL_EDGE,
                              boxstyle="square,pad=0.25", linewidth=0.4 if ok else 0.7))
            n = note(c, tid)
            if n:
                ax.text(xi, yi + 0.25, n, ha="center", va="center", fontsize=6, style="italic",
                        bbox=dict(facecolor="white", edgecolor="none", pad=0.3))
    ax.set_xticks(range(len(CONDS)))
    ax.set_xticklabels(["Base", "V1", "E4†\n(no traces)", "V2"], fontsize=7)
    ax.xaxis.tick_top()
    ax.set_yticks(range(len(tasks)))
    ax.set_yticklabels([t.replace("adversarial_", "adv_") for t in tasks], fontsize=6.5,
                       family="monospace")
    ax.tick_params(length=0)
    for s in ax.spines.values():
        s.set_visible(False)
    for yi in range(len(tasks) - 1):
        ax.axhline(yi + 0.5, color="0.85", lw=0.4)
    save(fig, "fig3_task_matrix.pdf")


if __name__ == "__main__":
    fig_stack()
    fig_scores()
    fig_matrix()
