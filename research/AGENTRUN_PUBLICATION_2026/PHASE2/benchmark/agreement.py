"""Blind-annotation agreement and the primary-analysis item set (pre-registered rule).

    py -3.11 agreement.py --split eval3 --dir <dir> --tags llama8b qwen14b [--quiet]

For every valid item (in <split>_groups.jsonl) compares each annotator's label with the gold
label fixed by the skeleton (answer:<value> | conflict | abstain).
  kappa       Cohen's kappa over the three classes {answer, conflict, abstain}, annotator vs gold
  exact       agreement including the answer value
An item is FLAGGED if any annotator disagrees with the gold (class or value), returns no
parsable label, or marks confidence "low". Flagged items are excluded from the PRIMARY Phase 3
analysis and analysed separately (PREREGISTRATION.md §6). Writes <split>_PRIMARY_IDS.json
(ids only) and <split>_AGREEMENT.json (aggregates; per-item flags by id). --quiet prints aggregates only.
"""
from __future__ import annotations

import argparse
import hashlib
import json
import sys
from collections import Counter
from pathlib import Path

sys.path.insert(0, str(Path(__file__).resolve().parents[1]))
from evarb import paths  # noqa: E402,F401
import memlab  # noqa: E402


def load(p):
    return [json.loads(x) for x in Path(p).read_text(encoding="utf-8").splitlines() if x.strip()]


def cls(label):
    if not isinstance(label, str):
        return None, None
    s = label.strip()
    low = s.lower()
    if low.startswith("answer"):
        return "answer", s.split(":", 1)[1].strip() if ":" in s else ""
    if low.startswith("conflict"):
        return "conflict", None
    if low.startswith("abstain"):
        return "abstain", None
    return None, None


def kappa(pairs):
    pairs = [(a, b) for a, b in pairs if a and b]
    n = len(pairs)
    if not n:
        return None
    po = sum(a == b for a, b in pairs) / n
    ca, cb = Counter(a for a, _ in pairs), Counter(b for _, b in pairs)
    pe = sum(ca[k] * cb[k] for k in set(ca) | set(cb)) / n ** 2
    return round((po - pe) / (1 - pe), 4) if pe < 1 else 1.0


def main():
    ap = argparse.ArgumentParser()
    ap.add_argument("--split", required=True)
    ap.add_argument("--dir", required=True)
    ap.add_argument("--tags", nargs="+", required=True)
    ap.add_argument("--quiet", action="store_true")
    a = ap.parse_args()
    d = Path(a.dir)
    groups = {g["fixture_id"]: g for g in load(d / f"{a.split}_groups.jsonl")}
    sk = {x["item_id"]: x for x in load(d / f"{a.split}_skeleton.jsonl")}
    flags = {i: [] for i in groups}
    stats = {}
    for tag in a.tags:
        ann = {x["item_id"]: x for x in load(d / f"{a.split}_annotations_{tag}.jsonl")}
        pairs, exact, low, unparsed = [], 0, 0, 0
        for i in groups:
            g = sk[i]["gold"]
            gk = g["kind"]
            x = ann.get(i, {})
            k, v = cls(x.get("label"))
            pairs.append((k, gk))
            if k is None:
                unparsed += 1
                flags[i].append(f"{tag}:unparsed")
                continue
            ok = k == gk and (gk != "answer" or memlab.value_matches(g["value"], "num" if isinstance(g["value"], (int, float))
                                                                       else "text", v))
            exact += ok
            if not ok:
                flags[i].append(f"{tag}:disagree")
            if str(x.get("confidence", "")).lower() == "low":
                low += 1
                flags[i].append(f"{tag}:low_confidence")
        stats[tag] = {"n": len(groups), "kappa_class": kappa(pairs), "exact_agreement": [exact, len(groups)],
                      "low_confidence": low, "unparsed": unparsed}
    primary = sorted(i for i, f in flags.items() if not f)
    by_cat = Counter(groups[i]["category"] for i in primary)
    out = {"split": a.split, "annotators": stats, "n_valid": len(groups), "n_primary": len(primary),
           "n_flagged": len(groups) - len(primary), "primary_by_category": dict(sorted(by_cat.items())),
           "flags": {i: f for i, f in flags.items() if f}}
    (d / f"{a.split}_AGREEMENT.json").write_text(json.dumps(out, indent=1) + "\n", encoding="utf-8")
    blob = (json.dumps(primary) + "\n").encode()
    (d / f"{a.split}_PRIMARY_IDS.json").write_bytes(blob)
    summary = {k: v for k, v in out.items() if k != "flags"}
    summary["primary_ids_sha256"] = hashlib.sha256(blob).hexdigest()
    print(json.dumps(summary, indent=1) if a.quiet else json.dumps(out, indent=1))


if __name__ == "__main__":
    main()
