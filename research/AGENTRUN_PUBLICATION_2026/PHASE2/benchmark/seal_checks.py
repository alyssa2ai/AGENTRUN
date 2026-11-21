"""Split-boundary, leakage and template-overlap checks for a built split (counts only, no content).

    python seal_checks.py --split eval3  --dir <sealed dir> [--ref-dir PHASE2/data]
    python seal_checks.py --split p2val2 --dir PHASE2/data/p2val2

Prints and writes <dir>/<split>_SEAL_CHECKS.json. Nothing in the output quotes item text, entity
names, values or labels, so it is safe to run inside the sealed eval3 job and copy to the repository.

Checks
  name_pool_unique         the memlab name pool has no duplicates up to the highest slice used
  entities_in_own_slice    every gold entity of the split comes from the split's own name slice
  distractors_in_own_slice every distractor entity comes from the split's own distractor slice
  entity_overlap_<file>    gold+distractor entities shared with each reference file (dev, p2dev,
                           regression, p2val, p2val2 when present): must be 0
  dup_entities_within      the same gold entity used by two items: must be 0
  writer_input_leak        writer input contains a gold/stale field or a gold label word: must be 0
  annotator_input_leak     annotator input contains gold/category/stale fields: must be 0
  template_overlap         gold record texts sharing at least one masked 8-gram with any reference
                           text (entity names and numbers masked); reported, not a hard failure,
                           because shared phrasing such as "the approved budget for" is expected
  exact_masked_duplicates  gold record texts identical after masking to a reference text
"""
from __future__ import annotations

import argparse
import hashlib
import json
import re
import sys
from pathlib import Path

HERE = Path(__file__).resolve().parent
P2 = HERE.parent
sys.path.insert(0, str(P2))
sys.path.insert(0, str(HERE))
from evarb import paths  # noqa: E402,F401
import memlab  # noqa: E402
from assemble import DISTRACTOR_NAMES  # noqa: E402
from skeleton import SPLITS  # noqa: E402

SLICES = {"dev": (0, 1600), "eval2": (1600, 5200), "p1dev": (5200, 8000), "p1hold": (8000, 10400),
          "p2dev": (10400, 12800)}
for s, c in SPLITS.items():
    SLICES[s] = c["names"]
for s, c in DISTRACTOR_NAMES.items():
    SLICES[s + "_distractors"] = c


def load(p):
    return [json.loads(x) for x in Path(p).read_text(encoding="utf-8").splitlines() if x.strip()]


def mask(text, names):
    t = text.lower()
    for n in names:
        t = t.replace(n.lower(), " ENT ")
    t = re.sub(r"[\d][\d,.\-/]*", " NUM ", t)
    return re.findall(r"[a-z]+|ENT|NUM", t)


def grams(tok, n=8):
    return {tuple(tok[i:i + n]) for i in range(max(0, len(tok) - n + 1))}


def base(e):
    return e[len("Project "):] if e.startswith("Project ") else e


def entities_of_tasks(tasks):
    gold, dis = set(), set()
    for t in tasks:
        gid = set(t.get("gold_record_ids") or [])
        for m in t["memory"]:
            (gold if m["record_id"] in gid else dis).add(m["entity"])
    return gold, dis


def ref_sets(ref_dir: Path, exclude: str):
    refs = {}
    cand = {"dev_groups": ref_dir / "dev_groups.jsonl", "regression_groups": ref_dir / "regression_groups.jsonl",
            "p2dev_tasks": ref_dir / "p2dev_tasks.jsonl", "p2val_tasks": ref_dir / "p2val" / "p2val_tasks.jsonl",
            "p2val2_tasks": ref_dir / "p2val2" / "p2val2_tasks.jsonl"}
    for k, p in cand.items():
        if exclude in k or not p.exists():
            continue
        rows = load(p)
        ents, texts = set(), []
        for r in rows:
            for m in (r.get("records") or r.get("memory") or []):
                ents.add(m["entity"])
                texts.append((m["text"], m["entity"]))
        refs[k] = (ents, texts)
    return refs


def main():
    ap = argparse.ArgumentParser()
    ap.add_argument("--split", required=True, choices=list(SPLITS))
    ap.add_argument("--dir", required=True)
    ap.add_argument("--ref-dir", default=str(P2 / "data"))
    a = ap.parse_args()
    d = Path(a.dir)
    hi = max(h for _, h in SLICES.values())
    pool = memlab._name_pool(hi)
    out = {"split": a.split, "checks": {}}
    c = out["checks"]
    c["name_pool_unique"] = len(set(pool)) == len(pool)
    lo, h2 = SPLITS[a.split]["names"]
    own = set(pool[lo:h2])
    dlo, dhi = DISTRACTOR_NAMES[a.split]
    own_d = set(pool[dlo:dhi])
    others = set()
    for k, (l, h) in SLICES.items():
        if k not in (a.split, a.split + "_distractors"):
            others |= set(pool[l:h])
    sk = load(d / f"{a.split}_skeleton.jsonl")
    tasks = load(d / f"{a.split}_tasks.jsonl")
    gold_e, dis_e = entities_of_tasks(tasks)
    sk_e = [x["entity"] for x in sk]
    c["n_skeleton_items"] = len(sk)
    c["n_tasks"] = len(tasks)
    c["entities_in_own_slice"] = [sum(base(e) in own for e in set(sk_e)), len(set(sk_e))]
    c["distractors_in_own_slice"] = [sum(base(e) in own_d for e in dis_e), len(dis_e)]
    c["entities_in_any_other_slice"] = len({base(e) for e in gold_e | dis_e} & others)
    c["dup_entities_within"] = len(sk_e) - len(set(sk_e))
    refs = ref_sets(Path(a.ref_dir), a.split)
    for k, (ents, _) in refs.items():
        c[f"entity_overlap_{k}"] = len((gold_e | dis_e) & ents)
    wi = (d / f"{a.split}_writer_input.jsonl").read_text(encoding="utf-8")
    wrows = [json.loads(x) for x in wi.splitlines() if x.strip()]
    leak = 0
    for r in wrows:
        keys = set(r) | {k for rec in r.get("records", []) for k in rec}
        leak += bool(keys & {"gold", "stale", "expected", "category", "label"})
        blob = json.dumps(r).lower()
        leak += any(w in blob for w in ('"conflict"', '"abstain"', "ground truth", "gold"))
    c["writer_input_leak"] = leak
    ai = load(d / f"{a.split}_annotator_input.jsonl")
    c["annotator_input_leak"] = sum(bool((set(r) | {k for rec in r["records"] for k in rec})
                                         & {"gold", "stale", "expected", "category", "value", "role"}) for r in ai)
    texts = load(d / f"{a.split}_texts.jsonl")
    own_texts = []
    for t in texts:
        e = next(x["entity"] for x in sk if x["item_id"] == t["item_id"])
        for v in (t.get("texts") or {}).values():
            own_texts.append(mask(v, [e]))
    ref_grams, ref_full = set(), set()
    for k, (ents, rt) in refs.items():
        for text, e in rt:
            m = mask(text, [e])
            ref_grams |= grams(m)
            ref_full.add(" ".join(m))
    c["n_gold_texts"] = len(own_texts)
    c["template_overlap_8gram"] = sum(bool(grams(m) & ref_grams) for m in own_texts)
    c["exact_masked_duplicates"] = sum(" ".join(m) in ref_full for m in own_texts)
    c["duplicate_texts_within"] = len(own_texts) - len({" ".join(m) for m in own_texts})
    hard = ["dup_entities_within", "writer_input_leak", "annotator_input_leak", "entities_in_any_other_slice"] + \
        [k for k in c if k.startswith("entity_overlap_")]
    ok = c["name_pool_unique"] and all(c[k] == 0 for k in hard) and \
        c["entities_in_own_slice"][0] == c["entities_in_own_slice"][1] and \
        c["distractors_in_own_slice"][0] == c["distractors_in_own_slice"][1]
    out["hard_checks_pass"] = bool(ok)
    out["reference_files"] = sorted(refs)
    blob = json.dumps(out, indent=1) + "\n"
    (d / f"{a.split}_SEAL_CHECKS.json").write_text(blob, encoding="utf-8")
    out["sha256"] = hashlib.sha256(blob.encode()).hexdigest()
    print(json.dumps(out, indent=1))
    return 0 if ok else 3


if __name__ == "__main__":
    raise SystemExit(main())
