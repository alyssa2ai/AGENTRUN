"""Run the TEA follow-up pilot (exploratory, development splits only).

    python run_tea.py --model Qwen/Qwen2.5-3B-Instruct --split p1dev  --configs T,RT        --run-id p1_qwen25_3b_greedy_tea
    python run_tea.py --model Qwen/Qwen2.5-3B-Instruct --split p1hold --configs B,G,R,T,RT  --run-id p1h_qwen25_3b_greedy

Same output layout and resume logic as run_pilot.py (raw_pilot/<run-id>/{runs.jsonl,manifest.jsonl,
tasks.jsonl,DONE}). run_pilot.py is left unchanged because its runs are already recorded.
For p1hold the split hash is checked against FREEZE_p1hold.json before anything runs.
"""
from __future__ import annotations

import argparse
import hashlib
import json
import platform
import sys
import time
from pathlib import Path

HERE = Path(__file__).resolve().parent
sys.path.insert(0, str(HERE))
import p1hold  # noqa: E402
import rcs  # noqa: E402
import tea  # noqa: E402

sys.path.insert(0, str(rcs.DEEP / "scripts"))
memlab = rcs.memlab
OUT = HERE.parent / "raw_pilot"


def sha(p: Path) -> str:
    return hashlib.sha256(p.read_bytes()).hexdigest()


def main() -> int:
    p = argparse.ArgumentParser()
    p.add_argument("--model", required=True)
    p.add_argument("--run-id", required=True)
    p.add_argument("--split", choices=["p1dev", "p1hold"], required=True)
    p.add_argument("--configs", required=True)
    p.add_argument("--harness", default="v2")
    p.add_argument("--temperature", type=float, default=0.0)
    p.add_argument("--seed", type=int, default=20261111)
    p.add_argument("--limit", type=int)
    a = p.parse_args()

    if a.split == "p1dev":
        split_seed = 20261114
        tasks = rcs.build_p1dev(split_seed)
    else:
        split_seed = p1hold.SEED
        tasks = p1hold.build_p1hold(split_seed)
    blob = "\n".join(json.dumps(t, sort_keys=True) for t in tasks).encode()
    split_sha = hashlib.sha256(blob).hexdigest()
    if a.split == "p1hold":
        frozen = json.loads((HERE / "FREEZE_p1hold.json").read_text(encoding="utf-8"))
        if frozen["split_sha256"] != split_sha:
            raise SystemExit(f"p1hold hash {split_sha} != frozen {frozen['split_sha256']}")
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
    man = {"run_id": a.run_id, "split": a.split, "split_seed": split_seed, "split_sha256": split_sha,
           "n_tasks": len(tasks), "configs": a.configs.split(","), "harness": a.harness,
           "p1_version": rcs.P1_VERSION, "tea_version": tea.TEA_VERSION,
           "rcs_py_sha256": sha(Path(rcs.__file__)), "tea_py_sha256": sha(Path(tea.__file__)),
           "p1hold_py_sha256": sha(Path(p1hold.__file__)), "run_tea_py_sha256": sha(Path(__file__)),
           "memlab_py_sha256": sha(Path(memlab.__file__)),
           "prompts_sha256": memlab.prompts_sha256(), "harness_sha256": memlab.harness_sha256(),
           "client": client.describe(), "temperature": a.temperature, "seed": a.seed,
           "python": platform.python_version(), "platform": platform.platform(), "torch": torch.__version__,
           "transformers": transformers.__version__, "gpu": torch.cuda.get_device_name(0),
           "slurm_job_id": __import__("os").environ.get("SLURM_JOB_ID"),
           "started_utc": time.strftime("%Y-%m-%dT%H:%M:%SZ", time.gmtime()), "resumed_with_done": len(done)}
    with open(out / "manifest.jsonl", "a", encoding="utf-8") as f:
        f.write(json.dumps(man) + "\n")
    t0, n = time.monotonic(), 0
    with open(runs, "a", encoding="utf-8") as f:
        for task in tasks:
            for c in a.configs.split(","):
                if (task["task_id"], c) in done:
                    continue
                run = tea.run_task(client, task, c, harness=a.harness)
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
