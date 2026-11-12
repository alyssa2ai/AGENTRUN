"""Leakage and isolation audit for the memlab ablation.

    py -3.11 scripts/leakage_audit.py [--runs raw_results/<run-id> ...]

Static checks run on the benchmark files; transcript checks run on every raw
run directory given. Writes tables/leakage_audit.json and exits non-zero if a
hard gate fails.
"""

from __future__ import annotations

import argparse
import hashlib
import json
import re
import sys
from pathlib import Path

import memlab

HERE = Path(__file__).resolve().parent.parent
REPO = memlab.REPO


def load(name):
    return [json.loads(x) for x in (HERE / "benchmark" / name).read_text(encoding="utf-8").splitlines() if x.strip()]


def entities(tasks):
    return ({r["entity"] for t in tasks for r in t["memory"]}
            | {f["entity"] for t in tasks for f in t["registry"]["facts"]})


def secret_values(t):
    e = t["expected"]
    return [v for v in [e.get("value"), e.get("stale_value"), *e.get("conflict_values", [])] if v is not None]


def contains(value, text) -> bool:
    if isinstance(value, (int, float)):
        nums = re.findall(r"-?\d+(?:\.\d+)?", text.replace(",", ""))
        return any(abs(float(n) - float(value)) < 0.011 for n in nums)
    return memlab._norm(value) in memlab._norm(text)


def main() -> int:
    p = argparse.ArgumentParser()
    p.add_argument("--runs", nargs="*", default=[])
    p.add_argument("--split", choices=["eval", "eval2"], default="eval")
    a = p.parse_args()
    dev, ev = load("dev.jsonl"), load(a.split + ".jsonl")
    freeze = json.loads((HERE / "benchmark" / ("FREEZE.json" if a.split == "eval" else "FREEZE_eval2.json"))
                        .read_text(encoding="utf-8"))
    freeze["eval"] = freeze[a.split]
    per = freeze["eval"].get("per_scenario", 8)
    other = load("eval.jsonl") if a.split == "eval2" else []
    res, hard = {}, []

    def gate(name, ok, detail=None):
        res[name] = {"pass": bool(ok), "detail": detail}
        if not ok:
            hard.append(name)

    # 1 freeze integrity
    sha = hashlib.sha256((HERE / "benchmark" / (a.split + ".jsonl")).read_bytes()).hexdigest()
    gate("eval_file_matches_freeze", sha == freeze["eval"]["sha256"], sha)
    gate("prompts_match_freeze", memlab.prompts_sha256() == freeze["prompts_sha256"])
    gate("eval_regenerates_from_seed", memlab.build_split(a.split, freeze["eval"]["seed"], per) == ev)

    # 2 split separation
    gate("dev_eval_entities_disjoint", not entities(dev) & entities(ev), len(entities(ev)))
    if other:
        gate("eval2_entities_disjoint_from_first_eval_split", not entities(other) & entities(ev))
        gate("eval2_prompts_disjoint_from_first_eval_split",
             not {t["prompt"] for t in other} & {t["prompt"] for t in ev})
        gate("harness_variants_match_freeze", memlab.harness_sha256() == freeze["harness_sha256"])
    gate("dev_eval_prompts_disjoint", not {t["prompt"] for t in dev} & {t["prompt"] for t in ev})
    gate("eval_prompts_unique", len({t["prompt"] for t in ev}) == len(ev))
    lead_names = ({str(r["value"]) for t in dev for r in t["memory"] if r["attribute"] == "lead"}
                  & {str(r["value"]) for t in ev for r in t["memory"] if r["attribute"] == "lead"})
    gate("dev_eval_person_names_disjoint", not lead_names, sorted(lead_names))

    # 3 ground truth not exposed in anything sent unconditionally to the model
    static_text = memlab.SYSTEM_PROMPT + memlab.VERIFIER_PROMPT + json.dumps(
        [memlab.CALC_TOOL, memlab.REG_TOOL, memlab.MEM_TOOL, memlab.SUBMIT_TOOL])
    bad = [t["task_id"] for t in ev for v in secret_values(t) if contains(v, t["prompt"])]
    gate("expected_values_absent_from_prompts", not bad, bad)
    bad = [t["task_id"] for t in ev for v in secret_values(t) if not isinstance(v, (int, float))
           and contains(v, static_text)]
    gate("expected_values_absent_from_system_prompt_and_schemas", not bad, bad)
    ents = entities(ev)
    gate("no_eval_entity_in_system_prompt_or_schemas", not [e for e in ents if e in static_text])

    # 4 scenario construction
    bad = []
    for t in ev:
        keys = [(r["entity"], r["attribute"]) for r in t["memory"]]
        if t["scenario"] == "S5_unsupported":
            asked = [e for e in {r["entity"] for r in t["memory"]} if e in t["prompt"]]
            attr = next(a_ for a_, s in memlab.ATTRS.items() if s["q"].split("{e}")[0] in t["prompt"])
            if any((e, attr) in keys for e in asked) or t["registry"]["facts"] or t["gold_record_ids"]:
                bad.append(t["task_id"])
        if t["scenario"] == "S6_tool_failure" and t["variant"] != "permanent_memory_fallback" \
                and t["gold_record_ids"]:
            bad.append(t["task_id"])
        if t["scenario"] in ("S1_context_loss", "S2_retrieval", "S3_conflict", "S4_stale") \
                and t["registry"]["facts"]:
            bad.append(t["task_id"])
    gate("scenario_fixtures_consistent", not bad, bad)
    # each task's memory is self-contained: no entity is shared between two tasks
    seen, shared = {}, set()
    for t in ev:
        for e in {r["entity"] for r in t["memory"]} | {f["entity"] for f in t["registry"]["facts"]}:
            if e in seen and seen[e] != t["task_id"]:
                shared.add(e)
            seen[e] = t["task_id"]
    gate("no_entity_shared_between_eval_tasks", not shared, sorted(shared))

    # 5 overlap with existing training / benchmark data and the real memory store
    ref_files = ["training/training_data.jsonl", "training/training_data_augmented.jsonl", "eval/tasks.py",
                 "benchmark_v2/dev.jsonl", "agentrun_v2/env/env_data/corpus.jsonl", "memory_store.json"]
    blob = {f: (REPO / f).read_text(encoding="utf-8", errors="ignore") for f in ref_files if (REPO / f).exists()}
    names = {e.replace("Project ", "") for e in ents}
    hits = {f: sorted(n for n in names if re.search(r"\b" + re.escape(n) + r"\b", txt)) for f, txt in blob.items()}
    gate("no_eval_entity_name_in_training_or_existing_benchmarks", not any(hits.values()),
         {"files_checked": list(blob), "hits": {k: v for k, v in hits.items() if v}})
    try:
        from agentrun_v2.benchmark import leakage
        rep = leakage.check(ev)
        gate("no_exact_or_template_match_with_training_and_legacy_prompts",
             not rep["exact_matches"] and not rep["template_matches"],
             {"tfidf_max_overall": rep["tfidf_max_overall"], "tfidf_flagged_ge_0.80": rep["tfidf_flagged"],
              "n_reference_prompts": rep["n_reference_prompts"]})
    except Exception as e:  # sklearn missing etc.
        res["training_prompt_similarity"] = {"pass": None, "detail": f"not run: {e}"}
    res["real_memory_store_sha256"] = hashlib.sha256((REPO / "memory_store.json").read_bytes()).hexdigest()

    # 6 transcript checks on raw runs
    by_id = {t["task_id"]: t for t in dev + ev}
    for rd in a.runs:
        rd = Path(rd)
        runs = [json.loads(x) for x in (rd / "runs.jsonl").read_text(encoding="utf-8").splitlines() if x.strip()]
        leaks, prov, a_mem, store_bad, a_val = [], [], [], [], []
        for r in runs:
            t = by_id[r["task_id"]]
            cfg = memlab.CONFIGS[r["config"]]
            sent = json.dumps(r["messages"], ensure_ascii=False)
            if any(k in sent for k in ("gold_record_ids", '"expected"', "stale_value", "conflict_values",
                                       "needed_tools")):
                leaks.append((r["task_id"], r["config"]))
            for c in r["tool_calls"]:
                # an empty result list carries no fields at all, so there is nothing to check (or leak)
                if c["name"] == "memory_search" and c["retrieved_ids"]:
                    if ("recorded_on" in c["observation"]) != cfg["provenance"] or \
                            ("reliability" in c["observation"]) != cfg["reliability"]:
                        prov.append((r["task_id"], r["config"]))
                    if not cfg["memory"]:
                        a_mem.append((r["task_id"], r["config"]))
            if not cfg["memory"] and t["scenario"] != "S6_tool_failure":
                tool_obs = " ".join(c["observation"] for c in r["tool_calls"] if c["name"] != "calculator")
                if any(contains(v, tool_obs) for v in secret_values(t)):
                    a_val.append(r["task_id"])
            sp = rd / "stores" / f"{r['task_id']}__{r['config']}.json"
            if cfg["memory"] and not sp.exists():
                pass  # padded-store runs keep no per-run store file
            elif cfg["memory"]:
                stored = json.loads(sp.read_text(encoding="utf-8"))
                if sorted((e["record_id"], e["entity"]) for e in stored) != \
                        sorted((m["record_id"], m["entity"]) for m in t["memory"]):
                    store_bad.append((r["task_id"], r["config"]))
            elif sp.exists():
                store_bad.append((r["task_id"], r["config"]))
        k = rd.name
        gate(f"{k}:no_ground_truth_fields_in_any_message", not leaks, leaks)
        gate(f"{k}:provenance_and_reliability_fields_only_in_their_configs", not prov, prov)
        gate(f"{k}:baseline_never_received_memory", not a_mem, a_mem)
        gate(f"{k}:baseline_tools_never_returned_a_memory_only_answer", not a_val, a_val)
        gate(f"{k}:each_store_holds_exactly_its_own_task_records", not store_bad, store_bad)
        res[f"{k}:n_runs"] = len(runs)

    out = HERE / "tables" / ("leakage_audit.json" if a.split == "eval" else "leakage_audit_eval2.json")
    out.parent.mkdir(exist_ok=True)
    out.write_text(json.dumps({"hard_failures": hard, "checks": res}, indent=2, default=str) + "\n",
                   encoding="utf-8")
    for k, v in res.items():
        tag = "INFO " if not isinstance(v, dict) or v.get("pass") is None else ("PASS " if v["pass"] else "FAIL ")
        print(tag + k)
    print("hard failures:", hard)
    return 1 if hard else 0


if __name__ == "__main__":
    sys.exit(main())
