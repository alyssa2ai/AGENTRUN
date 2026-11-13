"""Stage-1 statistical audit, part 2 (13 Nov 2026).

    py -3.11 scripts/cluster_permutation_and_decomposition.py

1. Exact family-level sign-flip permutation test for each headline paired contrast.
   The unit is the scenario-variant family (22 in eval2; 16 for the S1-S4
   retrieval runs). Under H0 (no configuration effect, exchangeable within a
   family) each family's summed paired difference is equally likely to have
   either sign; enumerating all 2^F sign patterns gives an exact two-sided p
   that does not assume tasks within a family are independent. It complements
   the family-bootstrap CIs in analysis/family_clustered_results.md, whose
   percentile intervals can be unreliable with ~20 clusters.
2. Per-scenario decomposition of each pooled contrast: which scenarios carry the
   effect. A pooled average over the six scenarios depends on the benchmark's
   scenario mix (one sixth of tasks each), which the designer chose.

Reads the raw run files of AGENTRUN_DEEPENING_2026-11-11 and scores them with
the frozen scorer memlab.score_run. Writes analysis/cluster_permutation.{md,json}.
"""

from __future__ import annotations

import itertools
import json
import sys
from collections import defaultdict
from pathlib import Path

import numpy as np

HERE = Path(__file__).resolve().parent
DEEP = HERE.parent.parent / "AGENTRUN_DEEPENING_2026-11-11"
sys.path.insert(0, str(DEEP / "scripts"))
import memlab  # noqa: E402

TASKS = {json.loads(x)["task_id"]: json.loads(x)
         for x in (DEEP / "benchmark" / "eval2.jsonl").read_text(encoding="utf-8").splitlines() if x.strip()}
SCEN = ["S1_context_loss", "S2_retrieval", "S3_conflict", "S4_stale", "S5_unsupported", "S6_tool_failure"]


def load(run_id):
    rows = {}
    for x in (DEEP / "raw_results" / run_id / "runs.jsonl").read_text(encoding="utf-8").splitlines():
        if x.strip():
            r = json.loads(x)
            rows[(r["task_id"], r["config"])] = memlab.score_run(TASKS[r["task_id"]], r)["success"]
    return rows


def fam(tid):
    t = TASKS[tid]
    return f"{t['scenario']}|{t['variant']}"


def units_cfg(runs, a, b, scen_filter=None):
    """List of (family, scenario, diff) for config a minus config b, over the given runs (models)."""
    out = []
    for rows in runs:
        for (t, c), v in rows.items():
            if c == a and (t, b) in rows and (scen_filter is None or TASKS[t]["scenario"][:2] in scen_filter):
                out.append((fam(t), TASKS[t]["scenario"], int(v) - int(rows[(t, b)])))
    return out


def units_runs(a_rows, b_rows):
    return [(fam(t), TASKS[t]["scenario"], int(v) - int(b_rows[(t, c)])) for (t, c), v in a_rows.items()
            if (t, c) in b_rows]


def exact_signflip(units):
    sums = defaultdict(int)
    for f, _, d in units:
        sums[f] += d
    s = np.array(list(sums.values()), dtype=np.int64)
    obs = abs(int(s.sum()))
    n = len(s)
    total = 0
    count = 0
    # enumerate sign patterns in chunks to bound memory
    chunk = 16 if n > 16 else n
    head, tail = s[:n - chunk], s[n - chunk:]
    tail_signs = np.array(list(itertools.product([1, -1], repeat=chunk)), dtype=np.int64)
    tail_sums = tail_signs @ tail
    for hs in itertools.product([1, -1], repeat=n - chunk):
        h = int(np.dot(hs, head)) if len(head) else 0
        count += int(np.sum(np.abs(h + tail_sums) >= obs))
        total += len(tail_sums)
    return count / total, n


def decompose(units):
    by = defaultdict(list)
    for _, s, d in units:
        by[s].append(d)
    n = len(units)
    return {s: {"n": len(by[s]), "diff_pp": 100 * sum(by[s]) / len(by[s]) if by[s] else None,
                "share_of_pooled_effect_pp": 100 * sum(by[s]) / n} for s in SCEN if by[s]}


def main():
    R = {r: load(r) for r in ["c2_qwen25_7b_v1", "c2_qwen3_8b_v1", "c2_qwen25_7b_v2", "c2_qwen3_8b_v2",
                              "c2_qwen25_7b_v2_hash_pad2000", "c2_qwen25_7b_v2_bm25_pad2000",
                              "c2_qwen25_3b_v2", "c2_qwen25_14b_v2"]}
    v1 = [R["c2_qwen25_7b_v1"], R["c2_qwen3_8b_v1"]]
    v2 = [R["c2_qwen25_7b_v2"], R["c2_qwen3_8b_v2"]]
    nopad = {k: v for k, v in R["c2_qwen25_7b_v2"].items()
             if k[1] in "BDE" and TASKS[k[0]]["scenario"][:2] in ("S1", "S2", "S3", "S4")}
    contrasts = [
        ("v1 pooled: B - A (memory)", units_cfg(v1, "B", "A")),
        ("v1 pooled: C - B (text verifier)", units_cfg(v1, "C", "B")),
        ("v1 pooled: D - C (provenance)", units_cfg(v1, "D", "C")),
        ("v1 pooled: E - D (gate)", units_cfg(v1, "E", "D")),
        ("v2 pooled: B - A (memory)", units_cfg(v2, "B", "A")),
        ("v2 pooled: C - B (text verifier)", units_cfg(v2, "C", "B")),
        ("v2 pooled: D - C (provenance)", units_cfg(v2, "D", "C")),
        ("v2 pooled: E - D (gate)", units_cfg(v2, "E", "D")),
        ("Qwen2.5-7B: v2 - v1 (harness)", units_runs(R["c2_qwen25_7b_v2"], R["c2_qwen25_7b_v1"])),
        ("Qwen3-8B: v2 - v1 (harness)", units_runs(R["c2_qwen3_8b_v2"], R["c2_qwen3_8b_v1"])),
        ("hash+2000 - no padding (7B v2, S1-S4, B/D/E)", units_runs(R["c2_qwen25_7b_v2_hash_pad2000"], nopad)),
        ("BM25+2000 - hash+2000", units_runs(R["c2_qwen25_7b_v2_bm25_pad2000"], R["c2_qwen25_7b_v2_hash_pad2000"])),
        ("3B v2: E - D (gate)", units_cfg([R["c2_qwen25_3b_v2"]], "E", "D")),
        ("14B v2: E - D (gate)", units_cfg([R["c2_qwen25_14b_v2"]], "E", "D")),
    ]
    res, md = {}, ["# Exact family-level sign-flip permutation tests and per-scenario decomposition\n",
                   "Generated by `scripts/cluster_permutation_and_decomposition.py`. Unit of randomisation: the "
                   "scenario-variant family (all of a family's paired differences flip sign together). "
                   "p is exact (all 2^F sign patterns), two-sided.\n",
                   "| Contrast | pairs | families F | diff (pp) | exact family sign-flip p |",
                   "|---|---|---|---|---|"]
    for name, u in contrasts:
        p, f = exact_signflip(u)
        d = 100 * sum(x[2] for x in u) / len(u)
        res[name] = {"pairs": len(u), "families": f, "diff_pp": d, "p_signflip_exact": p,
                     "by_scenario": decompose(u)}
        md.append(f"| {name} | {len(u)} | {f} | {d:+.1f} | {p:.4f} |")
    md += ["", "## Per-scenario decomposition (difference within each scenario, pp; contribution to the pooled "
               "average in brackets)\n",
           "| Contrast | " + " | ".join(s.split("_", 1)[0] for s in SCEN) + " |", "|---|" + "---|" * len(SCEN)]
    for name, r in res.items():
        cells = []
        for s in SCEN:
            b = r["by_scenario"].get(s)
            cells.append("-" if not b else f"{b['diff_pp']:+.0f} [{b['share_of_pooled_effect_pp']:+.1f}]")
        md.append(f"| {name} | " + " | ".join(cells) + " |")
    out = HERE.parent / "analysis"
    (out / "cluster_permutation.md").write_text("\n".join(md) + "\n", encoding="utf-8")
    (out / "cluster_permutation.json").write_text(json.dumps(res, indent=1), encoding="utf-8")
    print("\n".join(md))


if __name__ == "__main__":
    main()
