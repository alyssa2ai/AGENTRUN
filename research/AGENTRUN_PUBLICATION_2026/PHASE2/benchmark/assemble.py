"""Merge a skeleton with the writer's texts into benchmark files, validate, hash.

    py -3.11 assemble.py --split p2val --dir PHASE2/data/p2val
    py -3.11 assemble.py --split eval3 --dir <sealed dir> --quiet

Outputs in --dir:
  <split>_groups.jsonl   component items: question + the records of the asked (entity, attribute) + gold
  <split>_tasks.jsonl    agent tasks in memlab format (gold records + 5 seeded distractors)
  <split>_annotator_input.jsonl  question + records only (NO gold), for the blind annotator
  <split>_MANIFEST.json  counts, validation results and sha256 of every file
Validation (mechanical, no reading by the mechanism's author required): every text mentions its
project and its own value; every question present where required and free of values; slot
coverage. Items failing validation are listed by id only and excluded (`excluded_ids`).
With --quiet nothing but counts and hashes is printed (used for the sealed eval3).
"""
from __future__ import annotations

import argparse
import hashlib
import json
import random
import sys
from pathlib import Path

P2 = Path(__file__).resolve().parents[1]
sys.path.insert(0, str(P2))
from evarb import paths  # noqa: E402,F401
from evarb.cues import mentions  # noqa: E402
import memlab  # noqa: E402


DISTRACTOR_NAMES = {"eval3": (17600, 20000), "p2val": (20000, 21200), "p2val2": (22400, 23600)}  # disjoint from every entity slice


def load(p):
    return [json.loads(x) for x in Path(p).read_text(encoding="utf-8").splitlines() if x.strip()]


def dump(rows, p):
    blob = ("\n".join(json.dumps(r, sort_keys=True, ensure_ascii=False) for r in rows) + "\n").encode("utf-8")
    Path(p).write_bytes(blob)
    return hashlib.sha256(blob).hexdigest()


def main():
    ap = argparse.ArgumentParser()
    ap.add_argument("--split", required=True)
    ap.add_argument("--dir", required=True)
    ap.add_argument("--quiet", action="store_true")
    a = ap.parse_args()
    d = Path(a.dir)
    sk = load(d / f"{a.split}_skeleton.jsonl")
    tx = {r["item_id"]: r for r in load(d / f"{a.split}_texts.jsonl")}
    groups, tasks, ann, problems = [], [], [], {}
    for it in sk:
        t = tx.get(it["item_id"])
        errs = []
        if t is None:
            errs.append("no texts")
        else:
            for r in it["records"]:
                text = (t.get("texts") or {}).get(str(r["slot"]))
                if not text:
                    errs.append(f"slot {r['slot']} missing")
                    continue
                if it["entity"].lower() not in text.lower():
                    errs.append(f"slot {r['slot']} lacks entity")
                if not mentions(text, r["value"]):
                    errs.append(f"slot {r['slot']} lacks own value")
            if it["question_brief"]:
                q = t.get("question")
                if not q:
                    errs.append("question missing")
                elif any(mentions(q, r["value"]) for r in it["records"] if not isinstance(r["value"], int) or r["value"] > 31):
                    errs.append("question contains a value")
        if errs:
            problems[it["item_id"]] = errs
            continue
        q = t.get("question") or it["question"]
        recs = [{"entity": it["entity"], "attribute": r["attribute"], "value": r["value"], "recorded_on": r["recorded_on"],
                 "source": r["source"], "text": t["texts"][str(r["slot"])]} for r in it["records"]]
        g = it["gold"]
        asked = [x for x in recs if x["attribute"] == it["attribute"]]
        for k, x in enumerate(asked, 1):
            x2 = dict(x, record_id=f"g-{k:02d}")
            asked[k - 1] = x2
        if g["kind"] == "answer" and len(asked) > 1:
            gold = {"kind": "resolved", "current_value": g["value"]}
        elif g["kind"] == "answer":
            gold = {"kind": "single", "current_value": g["value"]}
        elif g["kind"] == "conflict":
            gold = {"kind": "no_current", "acceptable": ["contradiction", "unresolved"]}
        else:
            gold = {"kind": "absent"}
        groups.append({"fixture_id": it["item_id"], "category": it["category"], "question": q, "records": asked,
                       "gold": gold, "intent_gold": "historical" if it["category"] in ("historical_question", "as_of_question")
                       else "current"})
        rng = random.Random(it["distractor_seed"])
        w = memlab._World("eval", 0)
        w.rng = rng
        lo, hi = DISTRACTOR_NAMES[a.split]
        w.names = memlab._name_pool(hi)[lo:]
        rng.shuffle(w.names)
        tr = [dict(x, role="gold") for x in recs] + [dict(x, role="distractor") for x in memlab._distractors(w, 5)]
        exp = (memlab._expected("answer", value=g["value"], **({"stale_value": g["stale"]} if "stale" in g else {}))
               if g["kind"] == "answer" else memlab._expected("conflict", conflict_values=[x["value"] for x in asked])
               if g["kind"] == "conflict" else memlab._expected("abstain"))
        task = {"task_id": it["item_id"], "split": a.split, "scenario": it["category"], "variant": it["attribute"],
                "prompt": q, "expected": exp, "_records": tr, "needed_tools": ["memory_search"]}
        w2 = memlab._World("eval", 0)
        w2.rng = random.Random(it["distractor_seed"] + 1)
        tasks.append(memlab._finish(w2, task))
        ann.append({"item_id": it["item_id"], "question": q,
                    "records": [{"text": x["text"], "recorded_on": x["recorded_on"], "source": x["source"]} for x in asked]})
    man = {"split": a.split, "n_skeleton": len(sk), "n_valid": len(groups), "excluded_ids": problems,
           "skeleton.jsonl": hashlib.sha256((d / f"{a.split}_skeleton.jsonl").read_bytes()).hexdigest(),
           "texts.jsonl": hashlib.sha256((d / f"{a.split}_texts.jsonl").read_bytes()).hexdigest(),
           "groups.jsonl": dump(groups, d / f"{a.split}_groups.jsonl"),
           "tasks.jsonl": dump(tasks, d / f"{a.split}_tasks.jsonl"),
           "annotator_input.jsonl": dump(ann, d / f"{a.split}_annotator_input.jsonl"),
           "family_definition": "category x attribute"}
    (d / f"{a.split}_MANIFEST.json").write_text(json.dumps(man, indent=1) + "\n", encoding="utf-8")
    if a.quiet:
        print(json.dumps({k: (len(v) if k == "excluded_ids" else v) for k, v in man.items()}, indent=1))
    else:
        print(json.dumps(man, indent=1))


if __name__ == "__main__":
    main()
