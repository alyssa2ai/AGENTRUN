"""Build the dev and eval splits and freeze the eval split.

    py -3.11 research/AGENTRUN_DEEPENING_2026-11-11/scripts/build_benchmark.py

Writes benchmark/dev.jsonl, benchmark/eval.jsonl and benchmark/FREEZE.json.
Refuses to overwrite an existing freeze unless --force is given.
"""

from __future__ import annotations

import argparse
import hashlib
import json
import time
from pathlib import Path

import memlab

HERE = Path(__file__).resolve().parent.parent
DEV_SEED, EVAL_SEED = 101, 20261112
DEV_PER, EVAL_PER = 2, 8


def dump(tasks, path: Path) -> str:
    data = "".join(json.dumps(t, sort_keys=True, ensure_ascii=False) + "\n" for t in tasks).encode("utf-8")
    path.write_bytes(data)
    return hashlib.sha256(data).hexdigest()


def main() -> int:
    p = argparse.ArgumentParser()
    p.add_argument("--force", action="store_true")
    a = p.parse_args()
    out = HERE / "benchmark"
    out.mkdir(exist_ok=True)
    if (out / "FREEZE.json").exists() and not a.force:
        raise SystemExit("benchmark/FREEZE.json exists; the eval split is frozen (use --force only before any run)")
    dev = memlab.build_split("dev", DEV_SEED, DEV_PER)
    ev = memlab.build_split("eval", EVAL_SEED, EVAL_PER)
    freeze = {
        "memlab_version": memlab.MEMLAB_VERSION, "frozen_utc": time.strftime("%Y-%m-%dT%H:%M:%SZ", time.gmtime()),
        "dev": {"n": len(dev), "seed": DEV_SEED, "sha256": dump(dev, out / "dev.jsonl")},
        "eval": {"n": len(ev), "seed": EVAL_SEED, "sha256": dump(ev, out / "eval.jsonl")},
        "prompts_sha256": memlab.prompts_sha256(),
        "memlab_py_sha256": hashlib.sha256((HERE / "scripts" / "memlab.py").read_bytes()).hexdigest(),
    }
    (out / "FREEZE.json").write_text(json.dumps(freeze, indent=2) + "\n", encoding="utf-8")
    print(json.dumps(freeze, indent=2))
    return 0


if __name__ == "__main__":
    raise SystemExit(main())
