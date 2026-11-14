"""Offline (no LLM, CPU only) evaluation of the record-status function.

    py -3.11 PHASE1/scripts/arbiter_offline_eval.py

For every task whose expected behaviour depends on resolving the gold records
(answer with a stale_value, or conflict), check whether the status function labels
them correctly IF the model retrieved them all:
  answer task:   every gold record with the expected value is 'current' and every
                 gold record with the stale value is 'superseded'
  conflict task: every gold record is 'conflicting'
for the legacy memlab gate and for TEA. Also a regression check: on every group of
every task, TEA's status must equal the legacy status unless TEA's basis is a text
basis (text_valid_date or explicit_correction).

Splits: p1dev (Phase 1 dev), p1hold (held-out, frozen first), eval2 (Campaign 2
validation set, read-only from AGENTRUN_DEEPENING_2026-11-11/benchmark/eval2.jsonl).
Writes PHASE1/data/arbiter_offline_eval.json.
"""
from __future__ import annotations

import json
import sys
from collections import Counter, defaultdict
from pathlib import Path

HERE = Path(__file__).resolve().parent
P1 = HERE.parent
sys.path.insert(0, str(P1 / "prototype"))
import p1hold  # noqa: E402
import rcs  # noqa: E402
import tea  # noqa: E402

memlab = rcs.memlab
LEGACY = memlab.reliability_status


def _eq(a, b):
    return rcs._matches(a, b) if isinstance(a, (int, float)) else memlab._norm(a) == memlab._norm(b)


def judge(task, status_fn):
    exp = task["expected"]
    mem = {r["record_id"]: r for r in task["memory"]}
    gold = [mem[i] for i in task["gold_record_ids"]]
    if exp["kind"] == "conflict":
        st = [status_fn(g, [r for r in task["memory"] if r["entity"] == g["entity"] and r["attribute"] == g["attribute"]])
              for g in gold]
        return all(s["status"] == "conflicting" for s in st), [s["status"] for s in st]
    if exp["kind"] == "answer" and "stale_value" in exp:
        ok, sts = True, []
        for g in gold:
            grp = [r for r in task["memory"] if r["entity"] == g["entity"] and r["attribute"] == g["attribute"]]
            s = status_fn(g, grp)["status"]
            sts.append(s)
            if _eq(exp["value"], g["value"]):
                ok &= s == "current"
            elif _eq(exp["stale_value"], g["value"]):
                ok &= s == "superseded"
        return ok, sts
    return None, None


def main():
    deep = rcs.DEEP
    splits = {"p1dev": rcs.build_p1dev(), "p1hold": p1hold.build_p1hold(),
              "eval2": [json.loads(x) for x in (deep / "benchmark" / "eval2.jsonl").read_text(encoding="utf-8")
                        .splitlines() if x.strip()]}
    out = {"tea_version": tea.TEA_VERSION, "splits": {}}
    for name, tasks in splits.items():
        by = defaultdict(lambda: Counter())
        fails = defaultdict(list)
        regress = []
        bases = Counter()
        for t in tasks:
            sc = t["scenario"]
            for label, fn in (("legacy", LEGACY), ("tea", tea.reliability_status)):
                ok, sts = judge(t, fn)
                if ok is None:
                    continue
                by[sc][f"{label}_n"] += 1
                by[sc][f"{label}_ok"] += ok
                if not ok:
                    fails[label].append(f"{t['task_id']} {sts}")
            groups = defaultdict(list)
            for r in t["memory"]:
                groups[(r["entity"], r["attribute"])].append(r)
            for grp in groups.values():
                for r in grp:
                    lt, tt = LEGACY(r, grp), tea.reliability_status(r, grp)
                    bases[tt.get("basis", "none")] += 1
                    if lt["status"] != tt["status"] and tt.get("basis") not in ("text_valid_date",
                                                                                "explicit_correction"):
                        regress.append(f"{t['task_id']} {r['record_id']} legacy={lt['status']} tea={tt}")
        out["splits"][name] = {"by_scenario": {k: dict(v) for k, v in sorted(by.items())},
                               "failures": dict(fails), "regressions": regress, "tea_basis_counts": dict(bases)}
        print(f"\n== {name}  (records by TEA basis: {dict(bases)}; regressions: {len(regress)})")
        print(f"{'scenario':38s} legacy   tea")
        for k, v in sorted(by.items()):
            print(f"{k:38s} {v['legacy_ok']}/{v['legacy_n']:<5d} {v['tea_ok']}/{v['tea_n']}")
        for f in fails["tea"]:
            print("   TEA miss:", f)
    (P1 / "data" / "arbiter_offline_eval.json").write_text(json.dumps(out, indent=1), encoding="utf-8")


if __name__ == "__main__":
    main()
