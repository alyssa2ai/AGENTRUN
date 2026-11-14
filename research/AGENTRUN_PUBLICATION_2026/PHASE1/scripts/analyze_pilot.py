"""Phase 1 pilot analysis (exploratory).

    py -3.11 PHASE1/scripts/analyze_pilot.py

Reads PHASE1/raw_pilot/p1_*/runs.jsonl (+ tasks.jsonl), scores with the frozen
memlab scorer, and writes PHASE1/data/pilot_summary.json and pilot_tables.md.
"""
from __future__ import annotations

import json
import math
import sys
from collections import Counter, defaultdict
from pathlib import Path

HERE = Path(__file__).resolve().parent
P1 = HERE.parent
DEEP = P1.parent.parent / "AGENTRUN_DEEPENING_2026-11-11"
sys.path.insert(0, str(DEEP / "scripts"))
import memlab  # noqa: E402

CFGS = ["A", "B", "E", "G", "R"]
SCEN = ["S1", "S2", "S3", "S4", "S5", "S6", "S7", "S8"]


def wilson(k, n, z=1.96):
    if n == 0:
        return (None, None)
    p = k / n
    d = 1 + z * z / n
    c = (p + z * z / (2 * n)) / d
    h = z * math.sqrt(p * (1 - p) / n + z * z / (4 * n * n)) / d
    return (round(100 * (c - h), 1), round(100 * (c + h), 1))


def binom_two_sided(k, n):
    """Exact two-sided sign test p for k successes of n at p = 0.5."""
    if n == 0:
        return None
    pk = [math.comb(n, i) / 2 ** n for i in range(n + 1)]
    return min(1.0, sum(x for x in pk if x <= pk[k] + 1e-12))


def load(run_dir):
    tasks = {json.loads(x)["task_id"]: json.loads(x)
             for x in (run_dir / "tasks.jsonl").read_text(encoding="utf-8").splitlines() if x.strip()}
    rows = []
    for x in (run_dir / "runs.jsonl").read_text(encoding="utf-8").splitlines():
        if x.strip():
            r = json.loads(x)
            t = tasks[r["task_id"]]
            s = memlab.score_run(t, r)
            shown = 0
            obs_chars = 0
            for c in r["tool_calls"]:
                if c["name"] == "memory_search" and c["status"] == "OK":
                    obs_chars += len(c["observation"])
                    try:
                        shown += len(json.loads(c["observation"])["results"])
                    except Exception:
                        pass
            ev = r.get("rcs_events") or []
            s.update({"family": f"{t['scenario']}|{t['variant']}", "rcs_rule": ev[0]["rule"] if ev else None,
                      "rcs_pre": memlab.classify(t["expected"], memlab.parse_final(ev[0]["submission"])) if ev else None,
                      "records_shown": shown, "mem_obs_chars": obs_chars, "hit_max": r["hit_max_steps"]})
            rows.append(s)
    return tasks, rows


def summarise(rows):
    out = {}
    for c in CFGS:
        R = [r for r in rows if r["config"] == c]
        if not R:
            continue
        n = len(R)
        k = sum(r["success"] for r in R)
        by = {}
        for s in SCEN:
            rs = [r for r in R if r["scenario"].startswith(s)]
            if rs:
                by[s] = [sum(r["success"] for r in rs), len(rs)]
        abst = [r for r in R if r["expected_kind"] == "abstain"]
        ans = [r for r in R if r["expected_kind"] == "answer"]
        stale_tasks = [r for r in R if r["scenario"][:2] in ("S4", "S7", "S8")]
        conf = [r for r in R if r["expected_kind"] == "conflict"]
        prec = [r["precision_union"] for r in R if r["precision_union"] is not None]
        out[c] = {
            "n": n, "success": k, "pct": round(100 * k / n, 1), "wilson95": wilson(k, n),
            "harmful": sum(r["harmful"] for r in R),
            "unsupported_answer_rate": [sum(r["outcome"] == "unsupported_claim" for r in abst), len(abst)],
            "appropriate_abstention": [sum(r["success"] for r in abst), len(abst)],
            "over_abstain_on_answerable": [sum(r["outcome"] == "over_abstain" for r in ans), len(ans)],
            "false_conflict_on_answerable": [sum(r["outcome"] == "false_conflict" for r in ans), len(ans)],
            "stale_value_errors_S4_S7_S8": [sum(r["outcome"] == "stale_value" for r in stale_tasks), len(stale_tasks)],
            "conflict_resolution_S3": [sum(r["success"] for r in conf), len(conf)],
            "retrieval_precision_mean": round(sum(prec) / len(prec), 3) if prec else None,
            "tool_calls_mean": round(sum(r["n_tool_calls"] for r in R) / n, 2),
            "model_calls_mean": round(sum(r["n_api_calls"] for r in R) / n, 2),
            "step_limit": sum(r["hit_max"] for r in R),
            "format_error": sum(r["outcome"] == "format_error" for r in R),
            "latency_s_mean": round(sum(r["total_s"] for r in R) / n, 2),
            "records_shown_mean": round(sum(r["records_shown"] for r in R) / n, 2),
            "memory_obs_chars_mean": round(sum(r["mem_obs_chars"] for r in R) / n, 1),
            "by_scenario": by,
        }
    rr = [r for r in rows if r["config"] == "R"]
    ev = Counter((r["rcs_rule"], r["rcs_pre"], r["outcome"]) for r in rr if r["rcs_rule"])
    out["rcs_interventions"] = {"n_runs_R": len(rr), "n_fired": sum(1 for r in rr if r["rcs_rule"]),
                                "by_rule": dict(Counter(r["rcs_rule"] for r in rr if r["rcs_rule"])),
                                "transitions(rule,pre,post)": {" | ".join(map(str, k)): v for k, v in ev.items()},
                                "fixed": sum(1 for r in rr if r["rcs_rule"] and r["rcs_pre"] != "correct"
                                             and r["success"]),
                                "broke_correct": sum(1 for r in rr if r["rcs_rule"] and r["rcs_pre"] == "correct"
                                                     and not r["success"])}
    return out


def paired(rows, a, b):
    """a vs b on the same task (and same run): discordant counts and exact sign test; plus per-family sums."""
    idx = {(r["task_id"], r["config"]): r for r in rows}
    wins = losses = 0
    fam = defaultdict(int)
    for (t, c), r in idx.items():
        if c == a and (t, b) in idx:
            d = int(r["success"]) - int(idx[(t, b)]["success"])
            wins += d > 0
            losses += d < 0
            fam[r["family"]] += d
    return {"a_only": wins, "b_only": losses, "sign_test_p": binom_two_sided(min(wins, losses), wins + losses),
            "families_pos": sum(v > 0 for v in fam.values()), "families_neg": sum(v < 0 for v in fam.values())}


def main():
    res = {}
    md = ["# Phase 1 pilot tables (exploratory; development-only split p1dev, 64 tasks)\n"]
    src = Path(sys.argv[1]) if len(sys.argv) > 1 else P1 / "raw_pilot"
    for d in sorted(src.glob("p1_*")):
        if not (d / "runs.jsonl").exists():
            continue
        tasks, rows = load(d)
        man = [json.loads(x) for x in (d / "manifest.jsonl").read_text(encoding="utf-8").splitlines() if x.strip()]
        s = summarise(rows)
        s["paired"] = {f"{a}-{b}": paired(rows, a, b) for a, b in [("R", "G"), ("G", "B"), ("E", "G"), ("R", "B")]}
        s["n_runs"] = len(rows)
        s["complete"] = (d / "DONE").exists()
        s["manifest"] = {k: man[0].get(k) for k in ("split_sha256", "temperature", "seed", "p1_version",
                                                    "rcs_py_sha256", "memlab_py_sha256", "gpu", "torch",
                                                    "transformers")} if man else None
        s["manifest"]["model_snapshot"] = (man[0].get("client") or {}).get("snapshot") if man else None
        res[d.name] = s
        md.append(f"## {d.name} ({len(rows)} runs{'' if s['complete'] else ', INCOMPLETE'})\n")
        md.append("| Config | success | % [Wilson 95%] | harmful | false conflict | over-abstain | stale | S3 conflict ok | "
                  "abstain ok | tool calls | model calls | step limit | latency s | records shown |")
        md.append("|---|---|---|---|---|---|---|---|---|---|---|---|---|---|")
        for c in CFGS:
            x = s.get(c)
            if not x:
                continue
            f = lambda p: f"{p[0]}/{p[1]}"  # noqa: E731
            md.append(f"| {c} | {x['success']}/{x['n']} | {x['pct']} {list(x['wilson95'])} | {x['harmful']} | "
                      f"{f(x['false_conflict_on_answerable'])} | {f(x['over_abstain_on_answerable'])} | "
                      f"{f(x['stale_value_errors_S4_S7_S8'])} | {f(x['conflict_resolution_S3'])} | "
                      f"{f(x['appropriate_abstention'])} | {x['tool_calls_mean']} | {x['model_calls_mean']} | "
                      f"{x['step_limit']} | {x['latency_s_mean']} | {x['records_shown_mean']} |")
        md.append("\nPer scenario (successes / 8):\n")
        md.append("| Config | " + " | ".join(SCEN) + " |")
        md.append("|---|" + "---|" * len(SCEN))
        for c in CFGS:
            x = s.get(c)
            if x:
                md.append(f"| {c} | " + " | ".join(str(x["by_scenario"].get(sc, ["-"])[0]) for sc in SCEN) + " |")
        md.append(f"\nRCS: {json.dumps(s['rcs_interventions'])}\n")
        md.append("Paired: " + json.dumps(s["paired"]) + "\n")
    (P1 / "data" / "pilot_summary.json").write_text(json.dumps(res, indent=1), encoding="utf-8")
    (P1 / "data" / "pilot_tables.md").write_text("\n".join(md) + "\n", encoding="utf-8")
    print("\n".join(md))


if __name__ == "__main__":
    main()
