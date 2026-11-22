"""Run the Phase 1 feasibility pilot on the development-only stress split.

    python run_pilot.py --model Qwen/Qwen2.5-3B-Instruct --run-id p1_qwen25_3b_greedy
    python run_pilot.py --model Qwen/Qwen2.5-3B-Instruct --temperature 0.7 --seed 1 --run-id p1_qwen25_3b_T07_s1

Writes PHASE1/raw_pilot/<run-id>/{runs.jsonl,manifest.json,tasks.jsonl,DONE}. Resumable.
Local GPU (hf backend) only. The split is built in memory from its seed and its hash recorded.
"""
from __future__ import annotations

import argparse
import hashlib
import json
import platform
import time
from pathlib import Path

import sys
sys.path.insert(0, str(Path(__file__).resolve().parent))
import rcs  # noqa: E402
sys.path.insert(0, str(rcs.DEEP / "scripts"))

memlab = rcs.memlab
OUT = Path(__file__).resolve().parents[1] / "raw_pilot"


def main() -> int:
    p = argparse.ArgumentParser()
    p.add_argument("--model", required=True)
    p.add_argument("--run-id", required=True)
    p.add_argument("--configs", default="A,B,E,G,R")
    p.add_argument("--harness", default="v2")
    p.add_argument("--temperature", type=float, default=0.0)
    p.add_argument("--seed", type=int, default=20261111)
    p.add_argument("--split-seed", type=int, default=20261114)
    p.add_argument("--limit", type=int)
    a = p.parse_args()

    tasks = rcs.build_p1dev(a.split_seed)
    blob = "\n".join(json.dumps(t, sort_keys=True) for t in tasks).encode()
    split_sha = hashlib.sha256(blob).hexdigest()
    tasks.sort(key=lambda t: (int(t["task_id"].rsplit("-", 1)[1]), t["scenario"]))
    if a.limit:
        tasks = tasks[:a.limit]
    out = OUT / a.run_id
    out.mkdir(parents=True, exist_ok=True)
    (out / "tasks.jsonl").write_text(blob.decode() + "\n", encoding="utf-8")
    runs = out / "runs.jsonl"
    done = set()
    if runs.exists():
        for line in runs.read_text(encoding="utf-8").splitlines():
            if line.strip():
                r = json.loads(line)
                done.add((r["task_id"], r["config"]))
    from hf_client import HFClient
    client = HFClient(a.model, temperature=a.temperature, seed=a.seed)
    import torch
    import transformers
    man = {"run_id": a.run_id, "split": "p1dev", "split_seed": a.split_seed, "split_sha256": split_sha,
           "n_tasks": len(tasks), "configs": a.configs.split(","), "harness": a.harness,
           "p1_version": rcs.P1_VERSION, "rcs_py_sha256": hashlib.sha256(Path(rcs.__file__).read_bytes()).hexdigest(),
           "memlab_py_sha256": hashlib.sha256(Path(memlab.__file__).read_bytes()).hexdigest(),
           "prompts_sha256": memlab.prompts_sha256(), "harness_sha256": memlab.harness_sha256(),
           "client": client.describe(), "temperature": a.temperature, "seed": a.seed,
           "python": platform.python_version(), "platform": platform.platform(), "torch": torch.__version__,
           "transformers": transformers.__version__, "gpu": torch.cuda.get_device_name(0),
           "started_utc": time.strftime("%Y-%m-%dT%H:%M:%SZ", time.gmtime()), "resumed_with_done": len(done)}
    with open(out / "manifest.jsonl", "a", encoding="utf-8") as f:
        f.write(json.dumps(man) + "\n")
    t0, n = time.monotonic(), 0
    with open(runs, "a", encoding="utf-8") as f:
        for task in tasks:
            for c in a.configs.split(","):
                if (task["task_id"], c) in done:
                    continue
                run = rcs.run_task(client, task, c, harness=a.harness)
                run["model"] = a.model
                f.write(json.dumps(run, ensure_ascii=False) + "\n")
                f.flush()
                n += 1
                s = memlab.score_run(task, run)
                print(f"[{time.monotonic() - t0:7.0f}s] {task['task_id']} {c} -> {s['outcome']}"
                      f"{' rcs=' + run['rcs_events'][0]['rule'] if run['rcs_events'] else ''}", flush=True)
    (out / "DONE").write_text(json.dumps({"finished_utc": time.strftime("%Y-%m-%dT%H:%M:%SZ", time.gmtime()),
                                          "runs": len(done) + n}))
    return 0


if __name__ == "__main__":
    raise SystemExit(main())
