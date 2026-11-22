"""Phase 1: where do non-successes come from? (read-only over Campaign 2 raw runs)

    py -3.11 PHASE1/scripts/abstention_breakdown.py

For each run that failed on a task that should be answered, attribute the
failure to the first applicable cause, in this order:
  verifier_overturned   draft was correct, verifier changed it
  never_searched        memory-dependent task, memory_search never called
  gold_not_retrieved    searched, but some gold record never returned
  gold_in_hand          all gold records returned to the model, still failed
  other                 everything else (S6 registry tasks, config A, ...)
and split gold_in_hand by final outcome. Writes PHASE1/data/failure_attribution.json.
"""
from __future__ import annotations

import json
import sys
from collections import Counter, defaultdict
from pathlib import Path

HERE = Path(__file__).resolve().parent
P1 = HERE.parent
DEEP = P1.parent.parent / "AGENTRUN_DEEPENING_2026-11-11"
sys.path.insert(0, str(DEEP / "scripts"))
import memlab  # noqa: E402

TASKS = {json.loads(x)["task_id"]: json.loads(x)
         for x in (DEEP / "benchmark" / "eval2.jsonl").read_text(encoding="utf-8").splitlines() if x.strip()}
RUNS = ["c2_qwen25_3b_v2", "c2_qwen25_7b_v1", "c2_qwen25_7b_v2", "c2_qwen3_8b_v1", "c2_qwen3_8b_v2",
        "c2_qwen25_14b_v2"]


def main():
    out = {}
    for rid in RUNS:
        cause = defaultdict(Counter)
        inhand = defaultdict(Counter)
        inhand_ex = []
        for line in (DEEP / "raw_results" / rid / "runs.jsonl").read_text(encoding="utf-8").splitlines():
            if not line.strip():
                continue
            run = json.loads(line)
            t = TASKS[run["task_id"]]
            sc = memlab.score_run(t, run)
            cfg, scen = run["config"], t["scenario"][:2]
            if cfg == "A" or scen not in ("S1", "S2", "S3", "S4"):
                continue
            key = f"{cfg}"
            cause[key]["_n"] += 1
            if sc["success"]:
                cause[key]["success"] += 1
                continue
            gold = set(t["gold_record_ids"])
            got = {i for c in run["tool_calls"] if c["retrieved_ids"] for i in c["retrieved_ids"]}
            if sc["draft_outcome"] == "correct":
                c = "verifier_overturned"
            elif sc["n_memory_calls"] == 0:
                c = "never_searched"
            elif not gold <= got:
                c = "gold_not_retrieved"
            else:
                c = "gold_in_hand"
                inhand[cfg][f"{scen}:{sc['outcome']}"] += 1
                if len(inhand_ex) < 60:
                    inhand_ex.append({"task_id": t["task_id"], "config": cfg, "outcome": sc["outcome"],
                                      "n_memory_calls": sc["n_memory_calls"]})
            cause[key][c] += 1
        out[rid] = {"cause_by_config": {k: dict(v) for k, v in cause.items()},
                    "gold_in_hand_by_config": {k: dict(v) for k, v in inhand.items()}, "gold_in_hand_examples": inhand_ex}
        print(rid)
        for k in sorted(cause):
            print("  ", k, dict(cause[k]))
        for k in sorted(inhand):
            print("     in-hand", k, dict(inhand[k]))
    (P1 / "data" / "failure_attribution.json").write_text(json.dumps(out, indent=1), encoding="utf-8")


if __name__ == "__main__":
    main()
