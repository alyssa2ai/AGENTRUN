"""Independent re-computation of the headline numbers from raw run files (verification, not a new analysis).

    python crosscheck_phase3.py --tasks <tasks.jsonl> --runs <run dirs...> --analysis <CONFIRMATORY_primary_cells.json> --out <prefix>

Re-implements, without importing analyze_p2.py, (1) per model x configuration success / harmful / missing counts and
(2) the pooled mean task-level difference of the four primary contrasts (task success = mean over the model's decodings,
missing pair = failure), then compares them with the frozen analysis output. The scorer is the frozen memlab.score_run
(the scoring rule is part of the frozen protocol; re-implementing it would test a different rule).
Exit 1 on any disagreement. Writes <prefix>.json / .md.
"""
import argparse
import json
import sys
from collections import defaultdict
from pathlib import Path

P2 = Path(__file__).resolve().parents[2] / "PHASE2"
sys.path.insert(0, str(P2))
from evarb import paths  # noqa: E402,F401
import memlab  # noqa: E402

HARM = {"wrong_value", "stale_value", "unsupported_claim", "arbitrary_pick"}
PRIMARY = ["EBG-RT", "EBG-T", "EBG-LG", "EBG-B"]


def jl(p):
    with open(p, encoding="utf-8") as f:
        return [json.loads(x) for x in f if x.strip()]


def main():
    ap = argparse.ArgumentParser()
    ap.add_argument("--tasks", required=True); ap.add_argument("--runs", nargs="+", required=True)
    ap.add_argument("--analysis", required=True); ap.add_argument("--out", required=True)
    a = ap.parse_args()
    tasks = {t["task_id"]: t for t in jl(a.tasks)}
    succ = {}                       # (model, decoding, task, config) -> 0/1
    counts = defaultdict(lambda: [0, 0, 0, 0])  # (model, config) -> n, success, harmful, missing
    for d in map(Path, a.runs):
        man = jl(d / "manifest.jsonl")[0]
        model, dec = man["client"]["model"], (man["temperature"], man["seed"])
        got = {}
        for r in jl(d / "runs.jsonl"):
            if r["task_id"] in tasks and (r["task_id"], r["config"]) not in got:
                got[(r["task_id"], r["config"])] = r
        for tid, t in tasks.items():
            for c in man["configs"]:
                r = got.get((tid, c))
                if r is None or "error" in r:
                    ok, harm, miss = 0, 0, 1
                else:
                    s = memlab.score_run(t, r)
                    ok, harm, miss = int(bool(s["success"])), int(s["outcome"] in HARM), 0
                succ[(model, dec, tid, c)] = ok
                for key in ((model, c), ("ALL", c)):
                    x = counts[key]; x[0] += 1; x[1] += ok; x[2] += harm; x[3] += miss
    ref = json.loads(Path(a.analysis).read_text(encoding="utf-8"))
    problems, table = [], []
    for (m, c), (n, s, h, mi) in sorted(counts.items()):
        r = ref["per_model"].get(m, {}).get(c)
        ok = r is not None and (r["n"], r["success"], r["harmful"], r["missing"]) == (n, s, h, mi)
        table.append({"model": m, "config": c, "n": n, "success": s, "harmful": h, "missing": mi, "matches_analysis": ok})
        if not ok:
            problems.append(f"counts differ for {m} {c}: crosscheck {(n, s, h, mi)} vs analysis {r and (r['n'], r['success'], r['harmful'], r['missing'])}")
    diffs = {}
    for spec in PRIMARY:
        x, y = spec.split("-", 1)
        per_task = defaultdict(list)
        for (m, dec, tid, c), v in succ.items():
            if c == x and (m, dec, tid, y) in succ:
                per_task[(m, tid)].append(v - succ[(m, dec, tid, y)])
        md = round(100 * sum(sum(v) / len(v) for v in per_task.values()) / max(1, len(per_task)), 1)
        rv = ref["contrasts"].get(spec, {}).get("ALL", {}).get("success", {})
        diffs[spec] = {"crosscheck_pp": md, "analysis_pp": rv.get("mean_diff_pp"), "task_pairs": len(per_task),
                       "analysis_task_pairs": rv.get("n_task_pairs")}
        if md != rv.get("mean_diff_pp") or len(per_task) != rv.get("n_task_pairs"):
            problems.append(f"{spec}: crosscheck {md} pp / {len(per_task)} pairs vs analysis {rv.get('mean_diff_pp')} / {rv.get('n_task_pairs')}")
    out = {"n_tasks": len(tasks), "counts": table, "primary_diffs": diffs, "problems": problems}
    Path(a.out + ".json").write_text(json.dumps(out, indent=1) + "\n", encoding="utf-8")
    L = ["# Independent cross-check of the analysis output", "",
         f"{len(table)} model x configuration counts and {len(diffs)} pooled primary differences recomputed from raw runs.", "",
         "| Contrast | cross-check pp | analysis pp | task pairs (cross-check / analysis) |", "|---|---|---|---|"]
    L += [f"| {k} | {v['crosscheck_pp']} | {v['analysis_pp']} | {v['task_pairs']} / {v['analysis_task_pairs']} |" for k, v in diffs.items()]
    L += ["", f"Count rows matching the analysis: {sum(r['matches_analysis'] for r in table)} / {len(table)}", "",
          "Result: " + ("**all values agree**" if not problems else "**DISAGREEMENT**: " + "; ".join(problems))]
    Path(a.out + ".md").write_text("\n".join(L) + "\n", encoding="utf-8")
    print("\n".join(L))
    sys.exit(1 if problems else 0)


if __name__ == "__main__":
    main()
