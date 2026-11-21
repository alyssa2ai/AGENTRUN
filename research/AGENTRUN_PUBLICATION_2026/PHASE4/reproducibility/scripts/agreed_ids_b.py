"""Sensitivity item set (b), PREREGISTRATION.md section 5: the Qwen2.5-14B annotator agrees with gold (class and value).
Unlike set (a), low confidence does not exclude an item. Reads the <split>_AGREEMENT.json written by the frozen
benchmark/agreement.py (run with --tags qwen14b) and writes the agreeing ids. Prints counts and a hash only.
    python agreed_ids_b.py --agreement <dir>/<split>_AGREEMENT.json --groups <dir>/<split>_groups.jsonl --out <ids.json>
"""
import argparse, hashlib, json
from pathlib import Path
ap = argparse.ArgumentParser(); ap.add_argument("--agreement", required=True); ap.add_argument("--groups", required=True)
ap.add_argument("--out", required=True); a = ap.parse_args()
flags = json.loads(Path(a.agreement).read_text(encoding="utf-8"))["flags"]
ids = [json.loads(x)["fixture_id"] for x in Path(a.groups).read_text(encoding="utf-8").splitlines() if x.strip()]
keep = sorted(i for i in ids if not any(f.endswith((":disagree", ":unparsed")) for f in flags.get(i, [])))
blob = (json.dumps(keep) + "\n").encode(); Path(a.out).write_bytes(blob)
print(json.dumps({"n_valid": len(ids), "n_agreed_b": len(keep), "sha256": hashlib.sha256(blob).hexdigest()}))
