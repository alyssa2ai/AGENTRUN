"""Phase 1 pilot: cross-run analysis (exploratory, development split only).

    py -3.11 PHASE1/scripts/pilot_deep_analysis.py [raw_dir ...]

Reads every PHASE1/raw_pilot/<run>/ (and any extra raw dirs given), scores each run
with the frozen memlab scorer (via analyze_pilot.load) and writes
PHASE1/data/pilot_deep_analysis.json and PHASE1/data/pilot_deep_tables.md.

Units. A *task* is one p1dev item; a *family* is scenario|variant (the unit of the
permutation tests); repeated decodings of one task are averaged before any test and
are never counted as independent tasks.
"""
from __future__ import annotations

import itertools
import json
import random
import re
import sys
from collections import Counter, defaultdict
from pathlib import Path

HERE = Path(__file__).resolve().parent
P1 = HERE.parent
sys.path.insert(0, str(HERE))
import analyze_pilot as ap  # noqa: E402

MODEL_OF = {"qwen25_3b": "Qwen2.5-3B", "qwen25_7b": "Qwen2.5-7B", "qwen25_14b": "Qwen2.5-14B",
            "qwen3_8b": "Qwen3-8B"}
INSUFFICIENT = ("S7", "S8")  # metadata cannot order the records; the text can
DEV_SUBSETS = {"metadata_sufficient_S1_S6": lambda s: s[:2] not in INSUFFICIENT,
               "metadata_insufficient_S7_S8": lambda s: s[:2] in INSUFFICIENT}
HOLD_SUBSETS = {"tea_resolves_H7a_H8a_H9": lambda s: s[:3] in ("H7a", "H8a", "H9_"),
                "tea_cannot_H7b": lambda s: s.startswith("H7b"),
                "genuine_conflict_N1_N3": lambda s: s[:1] == "N",
                "control_C4": lambda s: s.startswith("C4")}


def run_meta(name: str):
    m = re.match(r"^(?:p1|p1h)_(qwen\d+_\d+b)_(greedy|T07_s\d)(?:_\w+)?$", name)
    if not m:
        return None
    return MODEL_OF.get(m.group(1), m.group(1)), m.group(2)


def rate(rows, pred, base=lambda r: True):
    b = [r for r in rows if base(r)]
    return [sum(1 for r in b if pred(r)), len(b)]


def metrics(R):
    ans = lambda r: r["expected_kind"] == "answer"  # noqa: E731
    out = {
        "n_runs": len(R), "n_tasks": len({r["task_id"] for r in R}),
        "n_families": len({r["family"] for r in R}),
        "success": rate(R, lambda r: r["success"]),
        "correct_answer_rate_answerable": rate(R, lambda r: r["success"], ans),
        "unnecessary_abstention_answerable": rate(R, lambda r: r["outcome"] == "over_abstain", ans),
        "false_conflict_answerable": rate(R, lambda r: r["outcome"] == "false_conflict", ans),
        "unsupported_answer_on_abstain_tasks": rate(R, lambda r: r["outcome"] == "unsupported_claim",
                                                    lambda r: r["expected_kind"] == "abstain"),
        "stale_value_S4_S7_S8": rate(R, lambda r: r["outcome"] == "stale_value",
                                     lambda r: r["scenario"][:2] in ("S4", "S7", "S8")),
        "same_day_correction_S7": rate(R, lambda r: r["success"], lambda r: r["scenario"][:2] == "S7"),
        "text_date_order_S8": rate(R, lambda r: r["success"], lambda r: r["scenario"][:2] == "S8"),
        "stale_metadata_order_S4": rate(R, lambda r: r["success"], lambda r: r["scenario"][:2] == "S4"),
        "conflict_resolution_S3": rate(R, lambda r: r["success"], lambda r: r["scenario"][:2] == "S3"),
        "harmful": rate(R, lambda r: r["harmful"]),
        "format_error": rate(R, lambda r: r["outcome"] == "format_error"),
        "step_limit": rate(R, lambda r: r["hit_max"]),
        "tool_calls_mean": round(sum(r["n_tool_calls"] for r in R) / max(1, len(R)), 2),
        "model_calls_mean": round(sum(r["n_api_calls"] for r in R) / max(1, len(R)), 2),
        "latency_s_mean": round(sum(r["total_s"] for r in R) / max(1, len(R)), 2),
        "records_shown_mean": round(sum(r["records_shown"] for r in R) / max(1, len(R)), 2),
        "memory_obs_chars_mean": round(sum(r["mem_obs_chars"] for r in R) / max(1, len(R)), 1),
    }
    v = [r for r in R if r.get("draft_outcome") == "correct"]
    out["correct_draft_rejected_by_verifier"] = [sum(1 for r in v if not r["success"]), len(v)]
    return out


def family_permutation(diff_by_family: dict, n_rand: int = 200_000, seed: int = 0):
    """Two-sided sign-flip permutation test on family-level mean differences."""
    d = [x for x in diff_by_family.values()]
    if not d or all(abs(x) < 1e-12 for x in d):
        return None
    obs = abs(sum(d))
    n = len(d)
    if n <= 20:
        hits = sum(1 for s in itertools.product((1, -1), repeat=n) if abs(sum(a * b for a, b in zip(s, d))) >= obs - 1e-12)
        return hits / 2 ** n
    rng = random.Random(seed)
    hits = sum(1 for _ in range(n_rand) if abs(sum(x if rng.random() < .5 else -x for x in d)) >= obs - 1e-12)
    return (hits + 1) / (n_rand + 1)


def paired_pooled(rows, a, b, scen_filter=None):
    """a - b paired within each decoding, averaged over the decodings both configs share;
    family sums; exact family sign-flip test."""
    per = defaultdict(dict)
    fam = {}
    for r in rows:
        if scen_filter and not scen_filter(r["scenario"]):
            continue
        per[(r["task_id"], r["_decoding"])][r["config"]] = int(r["success"])
        fam[r["task_id"]] = r["family"]
    by_task = defaultdict(list)
    for (t, _), c in per.items():
        if a in c and b in c:
            by_task[t].append(c[a] - c[b])
    diffs = {t: sum(v) / len(v) for t, v in by_task.items()}
    fam_d = defaultdict(float)
    for t, x in diffs.items():
        fam_d[fam[t]] += x
    return {"n_tasks": len(diffs), "n_families": len(fam_d),
            "mean_diff_pp": round(100 * sum(diffs.values()) / max(1, len(diffs)), 1),
            "tasks_a_better": sum(x > 0 for x in diffs.values()), "tasks_b_better": sum(x < 0 for x in diffs.values()),
            "families_pos": sum(x > 1e-12 for x in fam_d.values()), "families_neg": sum(x < -1e-12 for x in fam_d.values()),
            "family_signflip_p": family_permutation(fam_d)}


def rcs_ledger(rows, cfg="R"):
    R = [r for r in rows if r["config"] == cfg and r["rcs_rule"]]
    led = Counter((r["rcs_rule"], r["rcs_pre"], r["outcome"]) for r in R)
    return {"fired": len(R), "of_runs": sum(1 for r in rows if r["config"] == cfg),
            "fixed": sum(1 for r in R if r["rcs_pre"] != "correct" and r["success"]),
            "broke_correct": [r["task_id"] + f" [{r['_run']}] {r['rcs_rule']} -> {r['outcome']}"
                              for r in R if r["rcs_pre"] == "correct" and not r["success"]],
            "fired_no_change": sum(1 for r in R if r["rcs_pre"] == r["outcome"]),
            "transitions": {" | ".join(map(str, k)): v for k, v in sorted(led.items(), key=lambda x: -x[1])}}


def main():
    srcs = [Path(p) for p in sys.argv[1:]] or [P1 / "raw_pilot"]
    allrows, runs = [], {}
    for src in srcs:
        for d in sorted(src.iterdir()):
            meta = run_meta(d.name)
            if not meta or not (d / "runs.jsonl").exists():
                continue
            _, rows = ap.load(d)
            man = json.loads((d / "manifest.jsonl").read_text(encoding="utf-8").splitlines()[0])
            for r in rows:
                r["_run"], r["_model"], r["_decoding"], r["_split"] = d.name, *meta, man.get("split", "p1dev")
            runs[d.name] = {"model": meta[0], "decoding": meta[1], "split": man.get("split", "p1dev"),
                            "n_runs": len(rows),
                            "complete": (d / "DONE").exists(), "configs": sorted({r["config"] for r in rows}),
                            "temperature": man.get("temperature"), "seed": man.get("seed"),
                            "split_sha256": man.get("split_sha256"), "p1_version": man.get("p1_version")}
            allrows += rows
    res = {"runs": runs, "per_run": {}, "per_model_pooled": {}, "contrasts": {}, "rcs": {}, "label_overtrust": {}}
    for name in runs:
        R = [r for r in allrows if r["_run"] == name]
        res["per_run"][name] = {c: metrics([r for r in R if r["config"] == c]) for c in sorted({r["config"] for r in R})}
    splits = sorted({r["_split"] for r in allrows})
    models = [m for m in MODEL_OF.values() if any(r["_model"] == m for r in allrows)]
    for sp in splits:
        for m in models:
            R = [r for r in allrows if r["_model"] == m and r["_split"] == sp]
            if not R:
                continue
            key = f"{m} | {sp}"
            decs = sorted({r["_decoding"] for r in R})
            cfgs = sorted({r["config"] for r in R})
            res["per_model_pooled"][key] = {"decodings": decs,
                                            **{c: metrics([r for r in R if r["config"] == c]) for c in cfgs}}
            pairs = [(a, b) for a, b in [("R", "G"), ("G", "B"), ("R", "B"), ("E", "G"), ("T", "G"), ("T", "B"),
                                         ("RT", "R"), ("RT", "T"), ("RT", "B")] if a in cfgs and b in cfgs]
            subsets = HOLD_SUBSETS if sp == "p1hold" else DEV_SUBSETS
            res["contrasts"][key] = {f"{a}-{b}": {"all": paired_pooled(R, a, b),
                                                  **{sn: paired_pooled(R, a, b, fn) for sn, fn in subsets.items()}}
                                     for a, b in pairs}
            res["rcs"][key] = {c: rcs_ledger(R, c) for c in ("R", "RT") if c in cfgs}
            res.setdefault("per_scenario", {})[key] = {
                c: {s: rate([r for r in R if r["config"] == c and r["scenario"] == s], lambda r: r["success"])
                    for s in sorted({r["scenario"] for r in R})} for c in cfgs}
            # label over-trust: tasks B solved but G failed, on S7/S8, with task ids
            idx = defaultdict(dict)
            for r in R:
                idx[(r["task_id"], r["_decoding"])][r["config"]] = r
            lost = [f"{t} [{d}] G={x['G']['outcome']}" for (t, d), x in sorted(idx.items())
                    if "B" in x and "G" in x and x["B"]["success"] and not x["G"]["success"]
                    and x["G"]["scenario"][:2] in INSUFFICIENT]
            gained = [f"{t} [{d}]" for (t, d), x in sorted(idx.items())
                      if "B" in x and "G" in x and not x["B"]["success"] and x["G"]["success"]
                      and x["G"]["scenario"][:2] in INSUFFICIENT]
            res["label_overtrust"][key] = {"B_ok_G_fail_S7S8": lost, "B_fail_G_ok_S7S8": gained}
    (P1 / "data" / "pilot_deep_analysis.json").write_text(json.dumps(res, indent=1), encoding="utf-8")

    f = lambda p: f"{p[0]}/{p[1]}"  # noqa: E731
    md = ["# Phase 1 pilot: cross-run tables (exploratory)\n",
          "Generated by `scripts/pilot_deep_analysis.py`. Counts are runs (task x decoding); tests use task means "
          "over decodings and families as the unit.\n", "## Runs\n",
          "| Run | Model | Decoding | Split | Runs | Complete | Configs |", "|---|---|---|---|---|---|---|"]
    for n, x in runs.items():
        md.append(f"| {n} | {x['model']} | {x['decoding']} | {x['split']} | {x['n_runs']} | {x['complete']} | "
                  f"{','.join(x['configs'])} |")
    cols = [("success", "success"), ("correct_answer_rate_answerable", "correct (answerable)"),
            ("unnecessary_abstention_answerable", "over-abstain"), ("false_conflict_answerable", "false conflict"),
            ("unsupported_answer_on_abstain_tasks", "unsupported"), ("stale_value_S4_S7_S8", "stale"),
            ("stale_metadata_order_S4", "S4 ok"), ("same_day_correction_S7", "S7 ok"), ("text_date_order_S8", "S8 ok"),
            ("conflict_resolution_S3", "S3 ok"), ("format_error", "format err"), ("step_limit", "step limit")]
    for key, block in res["per_model_pooled"].items():
        md.append(f"\n## {key} (decodings: {', '.join(block['decodings'])})\n")
        md.append("| Config | " + " | ".join(c[1] for c in cols) + " | tool calls | model calls | latency s |")
        md.append("|---|" + "---|" * (len(cols) + 3))
        for c, x in block.items():
            if c == "decodings":
                continue
            md.append(f"| {c} | " + " | ".join(f(x[k]) for k, _ in cols)
                      + f" | {x['tool_calls_mean']} | {x['model_calls_mean']} | {x['latency_s_mean']} |")
        md.append("\nPaired contrasts (task means over decodings; p = exact family sign-flip):\n")
        md.append("| Contrast | subset | tasks | families | mean diff pp | tasks +/- | families +/- | p |")
        md.append("|---|---|---|---|---|---|---|---|")
        for cn, sub in res["contrasts"][key].items():
            for sn, x in sub.items():
                p = x["family_signflip_p"]
                md.append(f"| {cn} | {sn} | {x['n_tasks']} | {x['n_families']} | {x['mean_diff_pp']} | "
                          f"{x['tasks_a_better']}/{x['tasks_b_better']} | {x['families_pos']}/{x['families_neg']} | "
                          f"{'-' if p is None else round(p, 4)} |")
        ps = res["per_scenario"][key]
        scs = sorted(next(iter(ps.values())))
        md.append("\nPer scenario (successes / runs):\n")
        md.append("| Config | " + " | ".join(scs) + " |")
        md.append("|---|" + "---|" * len(scs))
        for c, x in ps.items():
            md.append(f"| {c} | " + " | ".join(f(x[s]) for s in scs) + " |")
        for c, L in res["rcs"][key].items():
            md.append(f"\nRCS in {c}: fired {L['fired']}/{L['of_runs']}, fixed {L['fixed']}, broke correct "
                      f"{len(L['broke_correct'])} {L['broke_correct']}, no change {L['fired_no_change']}.")
            md.append(f"Transitions (rule | before | after): {json.dumps(L['transitions'])}")
        o = res["label_overtrust"][key]
        md.append(f"\nLabel over-trust on S7/S8: B correct and G wrong in {len(o['B_ok_G_fail_S7S8'])} runs; "
                  f"the reverse in {len(o['B_fail_G_ok_S7S8'])}.")
    (P1 / "data" / "pilot_deep_tables.md").write_text("\n".join(md) + "\n", encoding="utf-8")
    print("\n".join(md))


if __name__ == "__main__":
    main()
