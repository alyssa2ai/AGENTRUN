"""Static audit of the p2val2 and eval3 generators BEFORE any text exists (CPU; counts only).

    python audit_generators.py --out ../data/GENERATOR_AUDIT.json

Rebuilds the deterministic skeletons and writer inputs IN MEMORY (exactly as skeleton.main does) and checks:
  determinism            two builds are byte-identical; p2val2 equals the skeleton on disk
  entity_slices          every split's entities come from its own name slice; pairwise disjoint across
                         p2val, p2val2, eval3 and the development files (dev, regression, p2dev)
  lead_value_names       person-name values ("<First> <Surname>") use surnames from the split's own slice
  distractor_slices      the assembler's split-specific distractor slices are disjoint from every entity slice
                         and from each other, and inside the name pool
  dup_entities           no entity used twice within a split
  writer_input_leak      writer input has no gold / stale / category / record date / source fields, and no
                         label words (conflict, abstain, gold, ground truth, correct answer)
  brief_templates        number of distinct brief templates per split (values masked) and how many are shared
                         between p2val2 and eval3 (shared BY DESIGN: the same generator); reported, not a failure
  balance                items per category, per gold kind, per attribute; families and items per family
Nothing printed or written contains an entity name, value, text or label of eval3: only counts and booleans.
"""
from __future__ import annotations

import argparse
import hashlib
import json
import re
import sys
from collections import Counter
from pathlib import Path

HERE = Path(__file__).resolve().parent
P2 = HERE.parent
sys.path.insert(0, str(P2))
sys.path.insert(0, str(HERE))
from evarb import paths  # noqa: E402,F401
import memlab  # noqa: E402
from assemble import DISTRACTOR_NAMES  # noqa: E402
from skeleton import SPLITS, build, fact  # noqa: E402
from seal_checks import SLICES, base  # noqa: E402

LABEL_WORDS = re.compile(r"\b(conflict|abstain|gold|ground truth|correct answer|stale)\b", re.I)


def writer_input(items):
    return [{"item_id": x["item_id"], "entity": x["entity"], "fact": x["fact"],
             "records": [{"slot": r["slot"], "value": r["value"], "attribute_fact": fact(r["attribute"]), "brief": r["brief"]}
                         for r in x["records"]], "question_brief": x["question_brief"]} for x in items]


def blob(items):
    return ("\n".join(json.dumps(x, sort_keys=True, ensure_ascii=False) for x in items) + "\n").encode("utf-8")


def mask_brief(b, item):
    s = b
    for r in item["records"]:
        s = s.replace(str(r["value"]), "<V>")
    s = s.replace(item["entity"], "<E>")
    return re.sub(r"\d{4}-\d{2}-\d{2}", "<D>", s)


def file_entities(p):
    out = set()
    for line in Path(p).read_text(encoding="utf-8").splitlines():
        if line.strip():
            r = json.loads(line)
            for m in (r.get("records") or r.get("memory") or []):
                out.add(base(m["entity"]))
    return out


def main():
    ap = argparse.ArgumentParser()
    ap.add_argument("--out", required=True)
    a = ap.parse_args()
    hi = max(h for _, h in SLICES.values())
    pool = memlab._name_pool(hi)
    res = {"name_pool_size": len(pool), "name_pool_unique": len(set(pool)) == len(pool), "splits": {}, "pairs": {}}
    ents, briefs = {}, {}
    for split in ("p2val", "p2val2", "eval3"):
        it1, it2 = build(split), build(split)
        lo, h = SPLITS[split]["names"]
        own = set(pool[lo:h])
        e = [base(x["entity"]) for x in it1]
        ents[split] = set(e)
        leads = [r["value"] for x in it1 for r in x["records"] if isinstance(r["value"], str) and " " in r["value"]
                 and not re.match(r"\d", r["value"])]
        wi = writer_input(it1)
        leak_fields = sum(bool({"gold", "stale", "category", "recorded_on", "source", "expected"} &
                               (set(w) | {k for r in w["records"] for k in r})) for w in wi)
        leak_words = sum(bool(LABEL_WORDS.search(json.dumps(w))) for w in wi)
        briefs[split] = Counter(mask_brief(r["brief"], x) for x in it1 for r in x["records"])
        fam = Counter((x["category"], x["attribute"]) for x in it1)
        d = {"n_items": len(it1), "deterministic": blob(it1) == blob(it2),
             "skeleton_sha256": hashlib.sha256(blob(it1)).hexdigest() if split != "eval3" else "(not reported before sealing)",
             "entities_in_own_slice": [sum(x in own for x in set(e)), len(set(e))],
             "dup_entities": len(e) - len(set(e)),
             "lead_values": len(leads), "lead_surnames_in_own_slice": sum(v.split(" ", 1)[1] in own for v in leads),
             "writer_input_leak_fields": leak_fields, "writer_input_label_words": leak_words,
             "n_categories": len({x["category"] for x in it1}),
             "by_gold_kind": dict(Counter(x["gold"]["kind"] for x in it1)),
             "by_attribute": dict(sorted(Counter(x["attribute"] for x in it1).items())),
             "n_families": len(fam), "items_per_family": dict(Counter(fam.values())),
             "distinct_brief_templates": len(briefs[split])}
        if split == "eval3":
            d.pop("by_gold_kind")  # reported as category balance in the spec; keep the audit label-free
        disk = P2 / "data" / split / f"{split}_skeleton.jsonl"
        if disk.exists():
            d["matches_skeleton_on_disk"] = disk.read_bytes() == blob(it1)
        res["splits"][split] = d
    for k, p in {"dev": P2 / "data" / "dev_groups.jsonl", "regression": P2 / "data" / "regression_groups.jsonl",
                 "p2dev": P2 / "data" / "p2dev_tasks.jsonl"}.items():
        ents[k] = file_entities(p)
    names = list(ents)
    for i, x in enumerate(names):
        for y in names[i + 1:]:
            res["pairs"][f"{x}&{y}"] = len(ents[x] & ents[y])
    dsl = {s: set(pool[lo:h]) for s, (lo, h) in DISTRACTOR_NAMES.items()}
    esl = {s: set(pool[c["names"][0]:c["names"][1]]) for s, c in SPLITS.items()}
    res["distractor_slices"] = {s: {"size": len(v), "within_pool": DISTRACTOR_NAMES[s][1] <= len(pool),
                                    "overlap_any_entity_slice": len(v & set().union(*esl.values())),
                                    "overlap_other_distractor_slices": len(v & set().union(*(w for t, w in dsl.items() if t != s)))}
                                for s, v in dsl.items()}
    res["brief_templates_shared_p2val2_eval3"] = len(set(briefs["p2val2"]) & set(briefs["eval3"]))
    s = res["splits"]
    res["hard_checks_pass"] = bool(
        res["name_pool_unique"] and all(v["deterministic"] and v["dup_entities"] == 0 and v["writer_input_leak_fields"] == 0
                                        and v["entities_in_own_slice"][0] == v["entities_in_own_slice"][1]
                                        and v["lead_surnames_in_own_slice"] == v["lead_values"] for v in s.values())
        and all(v == 0 for v in res["pairs"].values())
        and all(v["within_pool"] and v["overlap_any_entity_slice"] == 0 and v["overlap_other_distractor_slices"] == 0
                for v in res["distractor_slices"].values())
        and s["p2val2"].get("matches_skeleton_on_disk", False))
    Path(a.out).write_text(json.dumps(res, indent=1) + "\n", encoding="utf-8")
    print(json.dumps(res, indent=1))
    return 0 if res["hard_checks_pass"] else 3


if __name__ == "__main__":
    raise SystemExit(main())
