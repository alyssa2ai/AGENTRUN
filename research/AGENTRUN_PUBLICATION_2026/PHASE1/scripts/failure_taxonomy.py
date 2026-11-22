"""Phase 1: failure taxonomy over the Campaign 2 raw runs (read-only).

    py -3.11 PHASE1/scripts/failure_taxonomy.py

Classifies every run of the ten unpadded Campaign 2 datasets into the
categories of the Phase 1 brief, using only fields recorded in runs.jsonl and
the frozen scorer memlab.score_run. Each category has an explicit denominator.
Writes PHASE1/data/failure_counts.json and PHASE1/data/failure_examples.json.
Raw results are opened read-only; nothing under raw_results/ is written.
"""
from __future__ import annotations

import json
import sys
from collections import defaultdict
from pathlib import Path

HERE = Path(__file__).resolve().parent
P1 = HERE.parent
DEEP = P1.parent.parent / "AGENTRUN_DEEPENING_2026-11-11"
sys.path.insert(0, str(DEEP / "scripts"))
import memlab  # noqa: E402

TASKS = {json.loads(x)["task_id"]: json.loads(x)
         for x in (DEEP / "benchmark" / "eval2.jsonl").read_text(encoding="utf-8").splitlines() if x.strip()}
RUNS = ["c2_qwen25_1p5b_v1", "c2_qwen25_1p5b_v2", "c2_qwen25_3b_v1", "c2_qwen25_3b_v2", "c2_qwen25_7b_v1",
        "c2_qwen25_7b_v2", "c2_qwen3_8b_v1", "c2_qwen3_8b_v2", "c2_qwen25_14b_v1", "c2_qwen25_14b_v2"]
MEMORY_SCEN = ("S1", "S2", "S3", "S4")


def gate_flags(run):
    """Reliability annotations the model was shown (config E only)."""
    st = set()
    for c in run["tool_calls"]:
        if c["name"] == "memory_search" and c["status"] == "OK":
            try:
                for r in json.loads(c["observation"]).get("results", []):
                    s = (r.get("reliability") or {}).get("status")
                    if s:
                        st.add(s)
            except Exception:
                pass
    return st


def categorise(task, run, sc):
    """Yield (category, denominator_key) for one run. Denominator keys name the set the rate is over."""
    scen = task["scenario"][:2]
    cfg = run["config"]
    mem = cfg != "A"
    out = sc["outcome"]
    gold = set(task["gold_record_ids"])
    retrieved = {i for c in run["tool_calls"] if c["retrieved_ids"] for i in c["retrieved_ids"]}
    mem_calls = [c for c in run["tool_calls"] if c["name"] == "memory_search"]
    res = []
    # denominators recorded for every run they apply to
    res.append(("_all", None))
    if cfg == "A":
        res.append(("_A_runs", None))
        if out == "correct":
            res.append(("correct_without_memory", "_A_runs"))
    if mem:
        res.append(("_mem_runs", None))
        if out != "correct":
            res.append(("incorrect_despite_memory", "_mem_runs"))
        if scen in MEMORY_SCEN:
            res.append(("_mem_runs_memtask", None))
            if not mem_calls:
                res.append(("memory_never_queried", "_mem_runs_memtask"))
            if gold and gold <= retrieved:
                res.append(("_gold_fully_retrieved", None))
                if out in ("wrong_value", "stale_value", "arbitrary_pick", "over_abstain", "false_conflict"):
                    res.append(("gold_retrieved_but_wrong_outcome", "_gold_fully_retrieved"))
            if mem_calls and gold and not (gold & retrieved):
                res.append(("no_gold_retrieved_although_searched", "_mem_runs_memtask"))
        if mem_calls:
            res.append(("_searched", None))
            if retrieved and gold and not (gold & retrieved):
                res.append(("irrelevant_retrieval_only", "_searched"))
            # redundant search: another memory_search after all gold records were already returned
            seen, redundant = set(), False
            for c in mem_calls:
                if gold and gold <= seen:
                    redundant = True
                seen |= set(c["retrieved_ids"] or [])
            if redundant:
                res.append(("redundant_search_after_gold_retrieved", "_searched"))
            if len(mem_calls) >= 3:
                res.append(("three_or_more_memory_searches", "_searched"))
    if task["expected"]["kind"] == "answer" and task["expected"].get("stale_value") is not None and mem:
        res.append(("_S4_mem", None))
        if out == "stale_value":
            res.append(("stale_memory_used", "_S4_mem"))
            if cfg == "E" and "superseded" in gate_flags(run):
                res.append(("stale_used_although_gate_marked_superseded", "_S4_E"))
        if cfg == "E":
            res.append(("_S4_E", None))
    if task["expected"]["kind"] == "conflict" and mem:
        res.append(("_S3_mem", None))
        if out == "arbitrary_pick":
            res.append(("conflict_resolved_arbitrarily", "_S3_mem"))
            if cfg == "E" and "conflicting" in gate_flags(run):
                res.append(("arbitrary_pick_although_gate_marked_conflicting", "_S3_E"))
        if cfg == "E":
            res.append(("_S3_E", None))
    v = (run.get("verdict") or {}).get("verdict")
    if v:
        res.append(("_verified", None))
        if sc["draft_outcome"] == "correct" and v in ("UNSUPPORTED", "CONFLICT"):
            res.append(("verifier_rejected_correct", "_verified"))
        if v == "SUPPORTED" and sc["draft_outcome"] in memlab.HARMFUL:
            res.append(("verifier_accepted_harmful", "_verified"))
        if v in ("UNSUPPORTED", "CONFLICT") and sc["draft_outcome"] in memlab.HARMFUL:
            res.append(("verifier_caught_harmful", "_verified"))
    if run.get("hit_max_steps"):
        res.append(("hit_step_limit", "_all"))
    if scen == "S6" and task["variant"] in ("transient_timeout", "malformed_then_ok"):
        res.append(("_S6_recoverable", None))
        if sc["n_injected_failures"] and not sc["retried_after_failure"] and out != "correct":
            res.append(("tool_failure_not_retried", "_S6_recoverable"))
    if task["expected"]["kind"] == "abstain":
        res.append(("_should_abstain", None))
        if out == "unsupported_claim":
            res.append(("failure_to_abstain", "_should_abstain"))
    if task["expected"]["kind"] == "answer":
        res.append(("_should_answer", None))
        if out == "over_abstain":
            res.append(("unnecessary_abstention", "_should_answer"))
            if mem and gold and gold <= retrieved:
                res.append(("abstained_with_gold_in_hand", "_should_answer"))
    if out == "format_error":
        res.append(("format_error", "_all"))
    if (sc["final_status"] == "answer" and not str((run.get("final") or {}).get("value") or "").strip()):
        res.append(("answer_with_empty_value", "_all"))
    return res


def main():
    counts = {}
    examples = defaultdict(list)
    pooled = defaultdict(lambda: defaultdict(int))
    for rid in RUNS:
        c = defaultdict(int)
        for line in (DEEP / "raw_results" / rid / "runs.jsonl").read_text(encoding="utf-8").splitlines():
            if not line.strip():
                continue
            run = json.loads(line)
            task = TASKS[run["task_id"]]
            sc = memlab.score_run(task, run)
            for cat, _den in categorise(task, run, sc):
                c[cat] += 1
                pooled[rid.rsplit("_", 1)[1]][cat] += 1
                if not cat.startswith("_") and len(examples[cat]) < 40:
                    examples[cat].append({"run_id": rid, "task_id": run["task_id"], "config": run["config"],
                                          "outcome": sc["outcome"], "draft_outcome": sc["draft_outcome"],
                                          "verdict": sc["verdict"]})
        counts[rid] = dict(c)
    out = {"runs": counts, "by_harness": {k: dict(v) for k, v in pooled.items()},
           "denominators": DENOMS}
    (P1 / "data").mkdir(exist_ok=True)
    (P1 / "data" / "failure_counts.json").write_text(json.dumps(out, indent=1), encoding="utf-8")
    (P1 / "data" / "failure_examples.json").write_text(json.dumps(examples, indent=1), encoding="utf-8")
    cats = sorted({k for r in counts.values() for k in r if not k.startswith("_")})
    print("category | denominator | " + " | ".join(r.replace("c2_qwen", "") for r in RUNS))
    for cat in cats:
        den = DENOMS.get(cat)
        print(f"{cat} | {den} | " + " | ".join(f"{counts[r].get(cat, 0)}/{counts[r].get(den, 0)}" for r in RUNS))


DENOMS = {"correct_without_memory": "_A_runs", "incorrect_despite_memory": "_mem_runs",
          "memory_never_queried": "_mem_runs_memtask", "gold_retrieved_but_wrong_outcome": "_gold_fully_retrieved",
          "no_gold_retrieved_although_searched": "_mem_runs_memtask", "irrelevant_retrieval_only": "_searched",
          "redundant_search_after_gold_retrieved": "_searched", "three_or_more_memory_searches": "_searched",
          "stale_memory_used": "_S4_mem", "stale_used_although_gate_marked_superseded": "_S4_E",
          "conflict_resolved_arbitrarily": "_S3_mem",
          "arbitrary_pick_although_gate_marked_conflicting": "_S3_E",
          "verifier_rejected_correct": "_verified", "verifier_accepted_harmful": "_verified",
          "verifier_caught_harmful": "_verified", "hit_step_limit": "_all",
          "tool_failure_not_retried": "_S6_recoverable", "failure_to_abstain": "_should_abstain",
          "unnecessary_abstention": "_should_answer", "abstained_with_gold_in_hand": "_should_answer",
          "format_error": "_all", "answer_with_empty_value": "_all"}

if __name__ == "__main__":
    main()
