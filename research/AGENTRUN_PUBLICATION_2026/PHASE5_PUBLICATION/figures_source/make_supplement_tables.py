"""Generate the supplement's long tables directly from the verified Phase 3 outputs.

    python make_supplement_tables.py <PUBLICATION dir>

Writes LaTeX fragments into PHASE5_PUBLICATION/submission/supplementary/. Nothing is typed by hand.
"""
from __future__ import annotations

import csv
import json
import sys
from pathlib import Path

PUB = Path(sys.argv[1]).resolve()
P3 = PUB / "PHASE3"
OUT = PUB / "PHASE5_PUBLICATION" / "submission" / "supplementary"
OUT.mkdir(parents=True, exist_ok=True)

ORDER = ["B", "G", "T", "R", "RT", "LA", "LG", "EB", "EBG", "EBG-all", "EBG-unsafe", "EBG-noR3"]
CONTRASTS = ["EBG-RT", "EBG-T", "EBG-LG", "EBG-B", "EBG-EB", "EBG-R", "EB-T", "EB-G",
             "LG-LA", "EBG-EBG-all", "EBG-EBG-unsafe"]
SHORT = {"Qwen/Qwen2.5-3B-Instruct": "Qwen2.5-3B", "Qwen/Qwen2.5-7B-Instruct": "Qwen2.5-7B",
         "Qwen/Qwen3-8B": "Qwen3-8B", "meta-llama/Llama-3.1-8B-Instruct": "Llama-3.1-8B",
         "Qwen/Qwen2.5-14B-Instruct": "Qwen2.5-14B", "meta-llama/Llama-3.2-3B-Instruct": "Llama-3.2-3B",
         "ALL": "pooled"}


def esc(s: str) -> str:
    return s.replace("_", r"\_").replace("%", r"\%").replace("&", r"\&")


def cond(c: str) -> str:
    return r"\cond{" + esc(c) + "}"


def write(name: str, lines: list[str]) -> None:
    with open(OUT / name, "w", encoding="utf-8", newline="\n") as f:
        f.write("\n".join(lines) + "\n")
    print("  wrote", name)


# ---------------------------------------------------------------- S2: per model x condition outcomes
rows = list(csv.DictReader(open(P3 / "results" / "per_model_config.csv", encoding="utf-8")))
L = [r"\begin{longtable}{@{}llrrrrrrrr@{}}",
     r"\caption{Complete outcome counts for every model $\times$ condition cell. Source: "
     r"\texttt{PHASE3/results/per\_model\_config.csv}.}\label{tab:s-permodel}\\",
     r"\toprule",
     r"\textbf{Model} & \textbf{Cond.} & $n$ & \textbf{succ.} & \textbf{harm.} & \textbf{abst.} & "
     r"\textbf{f.conf.} & \textbf{arb.} & \textbf{fmt} & \textbf{step} \\",
     r"\midrule", r"\endfirsthead", r"\toprule",
     r"\textbf{Model} & \textbf{Cond.} & $n$ & \textbf{succ.} & \textbf{harm.} & \textbf{abst.} & "
     r"\textbf{f.conf.} & \textbf{arb.} & \textbf{fmt} & \textbf{step} \\",
     r"\midrule", r"\endhead", r"\bottomrule", r"\endfoot"]
by_model: dict[str, list[dict]] = {}
for r in rows:
    by_model.setdefault(r["model"], []).append(r)
for model, rs in by_model.items():
    order = {c: i for i, c in enumerate(ORDER)}
    for r in sorted(rs, key=lambda x: order.get(x["config"], 99)):
        L.append(f"{esc(model)} & {cond(r['config'])} & {r['n']} & {r['success']} & {r['harmful']} & "
                 f"{r['over_abstain']} & {r['false_conflict']} & {r['arbitrary_pick']} & "
                 f"{r['format_error']} & {r['step_limit']} \\\\")
L.append(r"\end{longtable}")
write("tab_s_permodel.tex", L)

# ---------------------------------------------------------------- S3: complete contrast set, all item sets
SETS = [("Primary (268 tasks)", "CONFIRMATORY_primary_cells"),
        ("Double-agreement (161)", "SENSITIVITY_annotator_agreed"),
        ("Flagged complement (107)", "SENSITIVITY_flagged_complement"),
        ("Qwen2.5-14B-agreed (232)", "SENSITIVITY_qwen14b_agreed"),
        ("Exploratory: no straddling cell", "EXPLORATORY_no_straddling_cell"),
        ("Exploratory: Qwen3-8B pre-transition", "EXPLORATORY_qwen3_pre_reboot_only")]
L = [r"\begin{longtable}{@{}llrrrr@{}}",
     r"\caption{Every contrast computed, on every item set, pooled over the models each analysis includes. "
     r"Differences are percentage points of task success; the harm column is the paired difference in "
     r"harmful-answer rate. Only the first block's first four rows are confirmatory. Source: "
     r"\texttt{PHASE3/ANALYSIS/*.json}.}\label{tab:s-contrasts}\\",
     r"\toprule",
     r"\textbf{Item set} & \textbf{Contrast} & \textbf{Diff.} & \textbf{95\% CI} & $\boldsymbol p$ & \textbf{Harm} \\",
     r"\midrule", r"\endfirsthead", r"\toprule",
     r"\textbf{Item set} & \textbf{Contrast} & \textbf{Diff.} & \textbf{95\% CI} & $\boldsymbol p$ & \textbf{Harm} \\",
     r"\midrule", r"\endhead", r"\bottomrule", r"\endfoot"]
for label, fname in SETS:
    obj = json.loads((P3 / "ANALYSIS" / f"{fname}.json").read_text(encoding="utf-8"))
    first = True
    for key in CONTRASTS:
        v = obj["contrasts"].get(key, {}).get("ALL")
        if not v:
            continue
        s, h = v["success"], v.get("harmful", {})
        p = s["p"]
        ps = f"${p:.0e}$".replace("e-0", r"\!\times\!10^{-").replace("$", "$") if p < 1e-4 else f"{p:.3f}"
        if p < 1e-4:
            ps = f"$<10^{{-4}}$"
        ci = f"[{s['ci95_pp'][0]:.1f}, {s['ci95_pp'][1]:.1f}]"
        hv = f"{h.get('mean_diff_pp'):+.1f}" if h.get("mean_diff_pp") is not None else "---"
        L.append(f"{esc(label) if first else ''} & {esc(key)} & ${s['mean_diff_pp']:+.1f}$ & {ci} & {ps} & ${hv}$ \\\\")
        first = False
    L.append(r"\midrule")
L = L[:-1] + [r"\end{longtable}"]
write("tab_s_contrasts.tex", L)

# ---------------------------------------------------------------- S4: per-decoding success
rows = list(csv.DictReader(open(P3 / "results" / "per_decoding.csv", encoding="utf-8")))
decs, models = [], []
for r in rows:
    if r["decoding"] not in decs:
        decs.append(r["decoding"])
    if r["model"] not in models:
        models.append(r["model"])
L = [r"\begin{longtable}{@{}lll" + "r" * len(decs) + r"@{}}",
     r"\caption{Task success per model, decoding and condition (successes out of runs). Source: "
     r"\texttt{PHASE3/results/per\_decoding.csv}.}\label{tab:s-decoding}\\", r"\toprule",
     r"\textbf{Model} & \textbf{Cond.} & " + " & ".join(r"\textbf{" + esc(d) + "}" for d in decs) + r" \\",
     r"\midrule", r"\endfirsthead", r"\toprule",
     r"\textbf{Model} & \textbf{Cond.} & " + " & ".join(r"\textbf{" + esc(d) + "}" for d in decs) + r" \\",
     r"\midrule", r"\endhead", r"\bottomrule", r"\endfoot"]
idx = {(r["model"], r["decoding"], r["config"]): r for r in rows}
for m in models:
    for c in ORDER:
        cells = []
        for d in decs:
            r = idx.get((m, d, c))
            cells.append(f"{r['success']}/{r['runs']}" if r else "---")
        L.append(f"{esc(m)} & {cond(c)} & " + " & ".join(cells) + r" \\")
L.append(r"\end{longtable}")
write("tab_s_decoding.tex", L)

print("supplement tables generated")
