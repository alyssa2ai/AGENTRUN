"""Phase 1: extract short, verbatim, traceable failure examples from Campaign 2 raw runs.

    py -3.11 PHASE1/scripts/extract_examples.py

All entities in memlab are fictional (generated names); no personal data is involved.
Writes PHASE1/data/representative_examples.json.
"""
from __future__ import annotations

import json
import sys
from pathlib import Path

HERE = Path(__file__).resolve().parent
P1 = HERE.parent
DEEP = P1.parent.parent / "AGENTRUN_DEEPENING_2026-11-11"
sys.path.insert(0, str(DEEP / "scripts"))
import memlab  # noqa: E402

TASKS = {json.loads(x)["task_id"]: json.loads(x)
         for x in (DEEP / "benchmark" / "eval2.jsonl").read_text(encoding="utf-8").splitlines() if x.strip()}


def runs(rid):
    for x in (DEEP / "raw_results" / rid / "runs.jsonl").read_text(encoding="utf-8").splitlines():
        if x.strip():
            r = json.loads(x)
            yield r, TASKS[r["task_id"]], memlab.score_run(TASKS[r["task_id"]], r)


def first(rid, pred):
    for r, t, s in runs(rid):
        if pred(r, t, s):
            return r, t, s
    return None


def summarise(rid, r, t, s, why):
    mem_obs = [c["observation"][:600] for c in r["tool_calls"] if c["name"] == "memory_search"][:1]
    return {"why_selected": why, "run_id": rid, "task_id": t["task_id"], "config": r["config"],
            "scenario": t["scenario"], "prompt": t["prompt"], "expected": t["expected"], "outcome": s["outcome"],
            "draft_outcome": s["draft_outcome"], "tool_sequence": [c["name"] for c in r["tool_calls"]],
            "first_memory_observation": mem_obs, "draft": r.get("draft"),
            "verdict": (r.get("verdict") or {}).get("raw", "")[:300] or None, "final": r.get("final")}


def gate_superseded(r):
    return any('"superseded"' in c["observation"] for c in r["tool_calls"] if c["name"] == "memory_search")


SPECS = [
    ("c2_qwen25_3b_v2", lambda r, t, s: r["config"] == "E" and t["scenario"] == "S4_stale"
     and s["outcome"] == "false_conflict" and gate_superseded(r),
     "3B ignores the gate's 'superseded' annotation and reports a conflict (14 of 16 S4 tasks in config E)"),
    ("c2_qwen25_7b_v2", lambda r, t, s: r["config"] == "E" and t["scenario"] == "S4_stale" and s["success"],
     "7B follows the same annotation on the same task type (16 of 16)"),
    ("c2_qwen25_7b_v2", lambda r, t, s: r["config"] == "C" and s["draft_outcome"] == "correct"
     and s["verdict"] == "UNSUPPORTED", "same-model verifier overturns a correct draft"),
    ("c2_qwen25_7b_v2", lambda r, t, s: r["config"] == "E" and t["scenario"] == "S1_context_loss"
     and s["n_memory_calls"] == 0, "memory never searched although the prompt says the facts were given earlier"),
    ("c2_qwen3_8b_v1", lambda r, t, s: r["config"] == "B" and s["outcome"] == "max_steps"
     and s["n_memory_calls"] >= 3, "search loop until the step limit with the gold records already retrieved"),
    ("c2_qwen25_7b_v2", lambda r, t, s: r["config"] == "B" and t["scenario"] == "S4_stale"
     and s["outcome"] == "false_conflict", "without the gate, 7B reports a conflict for an older/newer pair"),
]


def main():
    out = []
    for rid, pred, why in SPECS:
        hit = first(rid, pred)
        out.append(summarise(rid, *hit, why) if hit else {"why_selected": why, "run_id": rid, "found": False})
    (P1 / "data" / "representative_examples.json").write_text(json.dumps(out, indent=1, ensure_ascii=False),
                                                               encoding="utf-8")
    for e in out:
        print(json.dumps({k: e.get(k) for k in ("run_id", "task_id", "config", "outcome", "tool_sequence", "draft",
                                                "verdict", "final")}, ensure_ascii=False)[:700])
        print("   mem:", (e.get("first_memory_observation") or [""])[0][:400])


if __name__ == "__main__":
    main()
