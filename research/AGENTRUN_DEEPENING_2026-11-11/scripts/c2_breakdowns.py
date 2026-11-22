"""Breakdowns quoted in RESULTS_CAMPAIGN2.md that are not in tables/c2/C2_TABLES.md.

    py -3.11 scripts/c2_breakdowns.py

For every campaign-2 agent run: harmful answers split into empty-value answers
and genuinely asserted values, harmful answers given with zero tool calls,
repair-turn use and its outcome, step-limit runs that called the calculator
with round(), and how often memory was consulted. Also prints the repository
adapter's optimizer steps per epoch (to identify V1 vs V2).
"""

from __future__ import annotations

import json
from collections import Counter
from pathlib import Path

import memlab

HERE = Path(__file__).resolve().parent.parent
TASKS = {json.loads(x)["task_id"]: json.loads(x)
         for x in (HERE / "benchmark" / "eval2.jsonl").read_text(encoding="utf-8").splitlines() if x.strip()}
MEM_SC = ("S1", "S2", "S3", "S4")

print(f"{'run':32s} {'harm':>4s} {'empty':>5s} {'real':>4s} {'0-tool':>6s} {'repair':>6s} {'rep->ok':>7s} "
      f"{'round()':>7s} {'mem used S1-4,B-E':>17s}")
for d in sorted((HERE / "raw_results").glob("c2_qwen*")):
    harm = empty = notool = rep = rep_ok = rnd = mem = memn = 0
    for line in (d / "runs.jsonl").read_text(encoding="utf-8").splitlines():
        if not line.strip():
            continue
        r = json.loads(line)
        s = memlab.score_run(TASKS[r["task_id"]], r)
        if s["harmful"]:
            harm += 1
            v = (r.get("final") or {}).get("value")
            empty += v is None or str(v).strip() == ""
            notool += not r["tool_calls"]
        if r.get("repair_used"):
            rep += 1
            rep_ok += s["success"]
        if s["outcome"] == "max_steps" and any("round" in str((c["arguments"] or {}).get("expression", ""))
                                               for c in r["tool_calls"] if c["name"] == "calculator"):
            rnd += 1
        if r["config"] in "BCDE" and s["scenario"][:2] in MEM_SC:
            memn += 1
            mem += s["n_memory_calls"] > 0
    print(f"{d.name:32s} {harm:4d} {empty:5d} {harm - empty:4d} {notool:6d} {rep:6d} {rep_ok:7d} {rnd:7d} "
          f"{f'{mem}/{memn}':>17s}")

st = json.loads((memlab.REPO / "checkpoint-18" / "trainer_state.json").read_text(encoding="utf-8"))
steps_per_epoch = st["global_step"] / st["epoch"]
print(f"\nrepository adapter: {st['global_step']} steps over {st['epoch']} epochs = {steps_per_epoch:.0f} steps/epoch; "
      "batch 2 x accumulation 4 gives 5 steps/epoch for 35 examples (V1) and 6 for 46 examples (V2)")
