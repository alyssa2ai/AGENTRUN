"""Build and freeze the second held-out split (eval2): 96 fresh tasks, 16 per scenario.

    py -3.11 scripts/build_eval2.py

eval2 exists because the harness changes tested on 2026-11-12 (repair turn,
two extra prompt rules) were designed after looking at failures on the first
eval split. They are therefore evaluated on tasks nobody had seen, with the
unchanged v1 harness re-run on the same tasks as the control. Names are drawn
from a third slice of the name pool, disjoint from dev and eval.
"""

from __future__ import annotations

import hashlib
import json
import time
from pathlib import Path

import memlab

HERE = Path(__file__).resolve().parent.parent
SEED, PER = 20261113, 16


def main() -> int:
    out = HERE / "benchmark"
    if (out / "FREEZE_eval2.json").exists():
        raise SystemExit("benchmark/FREEZE_eval2.json exists; eval2 is frozen")
    tasks = memlab.build_split("eval2", SEED, PER)
    data = "".join(json.dumps(t, sort_keys=True, ensure_ascii=False) + "\n" for t in tasks).encode("utf-8")
    (out / "eval2.jsonl").write_bytes(data)
    freeze = {"frozen_utc": time.strftime("%Y-%m-%dT%H:%M:%SZ", time.gmtime()),
              "eval2": {"n": len(tasks), "seed": SEED, "per_scenario": PER,
                        "sha256": hashlib.sha256(data).hexdigest()},
              "prompts_sha256": memlab.prompts_sha256(), "harness_sha256": memlab.harness_sha256(),
              "memlab_py_sha256": hashlib.sha256((HERE / "scripts" / "memlab.py").read_bytes()).hexdigest()}
    (out / "FREEZE_eval2.json").write_text(json.dumps(freeze, indent=2) + "\n", encoding="utf-8")
    print(json.dumps(freeze, indent=2))
    return 0


if __name__ == "__main__":
    raise SystemExit(main())
