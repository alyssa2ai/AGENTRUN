"""Extract every number plotted in the paper's figures from the verified Phase 3 outputs.

    python make_figure_data.py <PUBLICATION dir>

Writes tab-separated .dat files into submission/figures/data/ and a provenance index. Nothing is typed by hand:
each file records the source file and JSON path it came from, so any plotted value can be traced back.
"""
from __future__ import annotations

import csv
import json
import sys
from pathlib import Path

PUB = Path(sys.argv[1]).resolve()
P3 = PUB / "PHASE3"
OUT = PUB / "PHASE5_PUBLICATION" / "submission" / "figures" / "data"
OUT.mkdir(parents=True, exist_ok=True)

prov: list[tuple[str, str]] = []


def write(name: str, header: list[str], rows: list[list], source: str) -> None:
    with open(OUT / name, "w", encoding="utf-8", newline="\n") as f:
        f.write("# source: " + source + "\n")
        f.write("\t".join(header) + "\n")
        for r in rows:
            f.write("\t".join(str(x) for x in r) + "\n")
    prov.append((name, source))


decisions = json.loads((P3 / "PHASE3_DECISIONS.json").read_text(encoding="utf-8"))
conf = json.loads((P3 / "ANALYSIS" / "CONFIRMATORY_primary_cells.json").read_text(encoding="utf-8"))
sec = json.loads((P3 / "ANALYSIS" / "SECONDARY_cells.json").read_text(encoding="utf-8"))
sens = {k: json.loads((P3 / "ANALYSIS" / f"SENSITIVITY_{k}.json").read_text(encoding="utf-8"))
        for k in ("annotator_agreed", "flagged_complement", "qwen14b_agreed")}
expl = {k: json.loads((P3 / "ANALYSIS" / f"EXPLORATORY_{k}.json").read_text(encoding="utf-8"))
        for k in ("no_straddling_cell", "qwen3_pre_reboot_only")}

# ---------------------------------------------------------------- Figure 5: forest plot of the four contrasts
rows = []
for i, (hyp, key) in enumerate([("H-primary", "EBG-RT"), ("S1", "EBG-T"), ("S2", "EBG-LG"), ("S3", "EBG-B")]):
    h = decisions["hypotheses"][hyp]
    rows.append([len(["H-primary", "S1", "S2", "S3"]) - i, h["diff_pp"], h["ci95_pp"][0], h["ci95_pp"][1],
                 hyp, key.replace("-", "$-$")])
write("fig5_forest_primary.dat", ["y", "diff", "lo", "hi", "hyp", "contrast"], rows,
      "PHASE3/PHASE3_DECISIONS.json -> hypotheses[*].diff_pp, ci95_pp")

# Forest plot, sensitivity overlay: same four contrasts on four item sets
sets = [("Primary (268)", conf), ("Double-agreement (161)", sens["annotator_agreed"]),
        ("Flagged complement (107)", sens["flagged_complement"]), ("Qwen14B-agreed (232)", sens["qwen14b_agreed"])]
rows = []
for ci, (label, obj) in enumerate(sets):
    for ki, key in enumerate(["EBG-RT", "EBG-T", "EBG-LG", "EBG-B"]):
        s = obj["contrasts"][key]["ALL"]["success"]
        rows.append([ki, ci, s["mean_diff_pp"], s["ci95_pp"][0], s["ci95_pp"][1], label.replace(" ", "~"), key])
write("fig5b_forest_sensitivity.dat", ["contrast_idx", "set_idx", "diff", "lo", "hi", "set", "contrast"], rows,
      "PHASE3/ANALYSIS/{CONFIRMATORY_primary_cells,SENSITIVITY_*}.json -> contrasts[*].ALL.success")

# one file per sensitivity set, so the figure needs no row filtering
for label, obj, fname in [("Double-agreement (161 tasks)", sens["annotator_agreed"], "fig5c_double_agreement.dat"),
                          ("Flagged complement (107 tasks)", sens["flagged_complement"], "fig5d_flagged.dat"),
                          ("Qwen2.5-14B-agreed (232 tasks)", sens["qwen14b_agreed"], "fig5e_qwen14b.dat")]:
    r2 = []
    for ki, key in enumerate(["EBG-RT", "EBG-T", "EBG-LG", "EBG-B"]):
        s_ = obj["contrasts"][key]["ALL"]["success"]
        r2.append([4 - ki, s_["mean_diff_pp"], s_["ci95_pp"][0], s_["ci95_pp"][1], key])
    write(fname, ["y", "diff", "lo", "hi", "contrast"], r2, f"PHASE3/ANALYSIS -> {label}")

# ---------------------------------------------------------------- Figure 6: accuracy vs harm, per configuration
# Pooled primary counts come from the per-model-configuration CSV, summed over the four primary models.
PRIMARY = {"Qwen2.5-3B-Instruct", "Qwen2.5-7B-Instruct", "Qwen3-8B", "Llama-3.1-8B-Instruct"}
rows_csv = list(csv.DictReader(open(P3 / "results" / "per_model_config.csv", encoding="utf-8")))
cols = rows_csv[0].keys()
agg: dict[str, dict[str, float]] = {}
for r in rows_csv:
    if r.get("model") not in PRIMARY:
        continue
    c = r["config"]
    a = agg.setdefault(c, {"n": 0.0, "success": 0.0, "harmful": 0.0, "over_abstain": 0.0,
                           "false_conflict": 0.0, "arbitrary_pick": 0.0, "format_error": 0.0, "step_limit": 0.0})
    for k in list(a):
        if k in r and r[k] not in ("", None):
            a[k] += float(r[k])

ORDER = ["B", "G", "T", "R", "RT", "LA", "LG", "EB", "EBG", "EBG-all", "EBG-unsafe", "EBG-noR3"]
FAMILY = {"B": "none", "G": "advisory", "T": "advisory", "R": "enforced", "RT": "enforced",
          "LA": "llm", "LG": "llm", "EB": "evarb", "EBG": "evarb", "EBG-all": "evarb",
          "EBG-unsafe": "evarb", "EBG-noR3": "evarb"}
rows = []
for c in ORDER:
    a = agg.get(c)
    if not a or not a["n"]:
        continue
    rows.append([c, round(100 * a["success"] / a["n"], 1), round(100 * a["harmful"] / a["n"], 1),
                 round(100 * a["over_abstain"] / a["n"], 1), round(100 * a["false_conflict"] / a["n"], 1),
                 int(a["arbitrary_pick"]), round(100 * a["format_error"] / a["n"], 1),
                 round(100 * a["step_limit"] / a["n"], 1), int(a["n"]), FAMILY[c]])
write("fig6_accuracy_harm.dat",
      ["config", "success", "harmful", "over_abstain", "false_conflict", "arbitrary", "format_err", "step_limit",
       "n", "family"], rows,
      "PHASE3/results/per_model_config.csv, summed over the four primary models")

# ---------------------------------------------------------------- Figure 7: per-model effects
MODELS = [("Qwen/Qwen2.5-3B-Instruct", "Qwen2.5-3B"), ("Qwen/Qwen2.5-7B-Instruct", "Qwen2.5-7B"),
          ("Qwen/Qwen3-8B", "Qwen3-8B"), ("meta-llama/Llama-3.1-8B-Instruct", "Llama-3.1-8B")]
rows = []
for mi, (mk, label) in enumerate(MODELS):
    for ki, key in enumerate(["EBG-RT", "EBG-T", "EBG-LG", "EBG-B"]):
        v = conf["contrasts"][key][mk]
        s, h = v["success"], v["harmful"]
        rows.append([mi, ki, label, key, s["mean_diff_pp"], s["ci95_pp"][0], s["ci95_pp"][1],
                     h["mean_diff_pp"], h["ci95_pp"][0], h["ci95_pp"][1],
                     s["families_pos"], s["families_neg"]])
write("fig7_per_model.dat",
      ["model_idx", "contrast_idx", "model", "contrast", "diff", "lo", "hi", "harm", "harm_lo", "harm_hi",
       "fam_pos", "fam_neg"], rows,
      "PHASE3/ANALYSIS/CONFIRMATORY_primary_cells.json -> contrasts[contrast][model]")

# secondary models, EBG-RT only
rows = []
for mk, label in [("Qwen/Qwen2.5-14B-Instruct", "Qwen2.5-14B"), ("meta-llama/Llama-3.2-3B-Instruct", "Llama-3.2-3B")]:
    for ki, key in enumerate(["EBG-RT", "EBG-T", "EBG-LG", "EBG-B"]):
        v = sec["contrasts"][key][mk]["success"]
        rows.append([label, key, ki, v["mean_diff_pp"], v["ci95_pp"][0], v["ci95_pp"][1]])
# one file per contrast, so the per-model figure needs no row filtering
for key in ["EBG-RT", "EBG-T", "EBG-LG", "EBG-B"]:
    r3 = []
    for mi, (mk, label) in enumerate(MODELS):
        v = conf["contrasts"][key][mk]
        s_, h_ = v["success"], v["harmful"]
        r3.append([len(MODELS) - mi, label, s_["mean_diff_pp"], s_["ci95_pp"][0], s_["ci95_pp"][1],
                   h_["mean_diff_pp"], h_["ci95_pp"][0], h_["ci95_pp"][1],
                   s_["families_pos"], s_["families_neg"]])
    write(f"fig7_{key.replace('-', '_').lower()}.dat",
          ["y", "model", "diff", "lo", "hi", "harm", "harm_lo", "harm_hi", "fam_pos", "fam_neg"], r3,
          f"PHASE3/ANALYSIS/CONFIRMATORY_primary_cells.json -> contrasts[{key}][model]")

write("fig7b_secondary.dat", ["model", "contrast", "contrast_idx", "diff", "lo", "hi"], rows,
      "PHASE3/ANALYSIS/SECONDARY_cells.json -> contrasts[contrast][model].success")

# ---------------------------------------------------------------- Figure 8: failure taxonomy under each condition
rows = []
for c in ORDER:
    a = agg.get(c)
    if not a or not a["n"]:
        continue
    n = a["n"]
    correct = 100 * a["success"] / n
    fc = 100 * a["false_conflict"] / n
    oa = 100 * a["over_abstain"] / n
    hm = 100 * a["harmful"] / n
    fe = 100 * a["format_error"] / n
    other = max(0.0, 100 - correct - fc - oa - hm - fe)
    rows.append([c, round(correct, 1), round(fc, 1), round(oa, 1), round(hm, 1), round(fe, 1), round(other, 1)])
write("fig8_failure_mix.dat", ["config", "correct", "false_conflict", "over_abstain", "harmful", "format_err",
                               "other"], rows,
      "PHASE3/results/per_model_config.csv (primary models); categories are not mutually exclusive in the scorer, "
      "so 'other' absorbs the remainder and the bars are a decomposition of outcome rates, not a partition")

# ---------------------------------------------------------------- Figure: conflict handling (used in Fig 6 inset)
met = json.loads((P3 / "ANALYSIS" / "METRICS.json").read_text(encoding="utf-8"))
rows = []


cells = met["cells"]
pooled = cells.get("POOLED") or cells.get("ALL")
if pooled is None:  # pool by summing the per-model numerators and denominators
    pooled = {}
    for c in ORDER:
        tot = {"conflict_preservation": [0, 0], "false_resolution_rate": [0, 0],
               "unnecessary_abstention_rate": [0, 0], "answer_accuracy": [0, 0]}
        for model, by_cfg in cells.items():
            e = by_cfg.get(c)
            if not isinstance(e, dict):
                continue
            for k in tot:
                v = e.get(k)
                if isinstance(v, list) and len(v) == 2:
                    tot[k][0] += v[0]
                    tot[k][1] += v[1]
        pooled[c] = tot
for c in ORDER:
    e = pooled.get(c)
    if not isinstance(e, dict):
        continue
    cp, fr = e.get("conflict_preservation"), e.get("false_resolution_rate")
    ua = e.get("unnecessary_abstention_rate")
    if isinstance(cp, list) and isinstance(fr, list) and cp[1] and fr[1]:
        rows.append([c, round(100 * cp[0] / cp[1], 1), round(100 * fr[0] / fr[1], 1),
                     round(100 * ua[0] / ua[1], 1) if isinstance(ua, list) and ua[1] else ""])
if rows:
    write("fig6b_conflict_handling.dat", ["config", "conflict_preserved", "false_resolution", "unnecessary_abstention"], rows,
          "PHASE3/ANALYSIS/METRICS.json -> POOLED[config]")

# ---------------------------------------------------------------- Exploratory platform sensitivity (supplement)
rows = []
for label, obj in [("Confirmatory", conf), ("No~straddling~cell", expl["no_straddling_cell"])]:
    for ki, key in enumerate(["EBG-RT", "EBG-T", "EBG-LG", "EBG-B"]):
        s = obj["contrasts"][key]["ALL"]["success"]
        rows.append([label, key, ki, s["mean_diff_pp"], s["ci95_pp"][0], s["ci95_pp"][1], obj["n_rows"]])
write("figS_platform_sensitivity.dat", ["analysis", "contrast", "contrast_idx", "diff", "lo", "hi", "rows"], rows,
      "PHASE3/ANALYSIS/{CONFIRMATORY_primary_cells,EXPLORATORY_no_straddling_cell}.json")

idx = ["# Figure data provenance (generated by PHASE5_PUBLICATION/figures_source/make_figure_data.py)", ""]
idx += [f"{n}\t{s}" for n, s in prov]
with open(OUT / "PROVENANCE.txt", "w", encoding="utf-8", newline="\n") as f:
    f.write("\n".join(idx) + "\n")

print(f"wrote {len(prov)} data files to {OUT}")
for n, s in prov:
    print(f"  {n}")
