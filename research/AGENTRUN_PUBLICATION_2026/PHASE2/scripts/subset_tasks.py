"""Write the pre-registered PRIMARY item subset of a task file (PREREGISTRATION.md §5).

    python subset_tasks.py --tasks <split>_tasks.jsonl --ids <split>_PRIMARY_IDS.json --out <split>_tasks_primary.jsonl

Prints only counts and sha256s (safe for the sealed eval3). The complement ("flagged" items) is written to
--out-flagged when given. Order and bytes of each kept line are unchanged.
"""
import argparse
import hashlib
import json
from pathlib import Path

ap = argparse.ArgumentParser()
ap.add_argument("--tasks", required=True)
ap.add_argument("--ids", required=True)
ap.add_argument("--out", required=True)
ap.add_argument("--out-flagged")
a = ap.parse_args()
keep = set(json.loads(Path(a.ids).read_text(encoding="utf-8")))
lines = [x for x in Path(a.tasks).read_text(encoding="utf-8").splitlines() if x.strip()]
prim = [x for x in lines if json.loads(x)["task_id"] in keep]
flag = [x for x in lines if json.loads(x)["task_id"] not in keep]
Path(a.out).write_text("\n".join(prim) + "\n", encoding="utf-8")
if a.out_flagged:
    Path(a.out_flagged).write_text("\n".join(flag) + "\n", encoding="utf-8")
print(json.dumps({"n_tasks": len(lines), "n_primary": len(prim), "n_flagged": len(flag),
                  "ids_without_task": len(keep - {json.loads(x)["task_id"] for x in lines}),
                  "primary_sha256": hashlib.sha256(Path(a.out).read_bytes()).hexdigest()}))
