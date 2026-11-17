"""Run agent configurations on a split (Phase 2 development runs and Phase 3 confirmatory runs).

    python run_p2.py --model Qwen/Qwen2.5-3B-Instruct --split p2dev --configs B,G,R,T,RT,EB,EBG --run-id p2_qwen25_3b_greedy
    python run_p2.py --model ... --split eval3 --tasks /path/eval3_tasks.jsonl --expect-sha <sha256> ...

Splits: p1dev, p1hold (rebuilt from the frozen Phase 1 builders and hash-checked), p2dev
(PHASE2/data/p2dev_tasks.jsonl), p2val (PHASE2/data/p2val/p2val_tasks.jsonl), or any task file
given with --tasks, whose sha256 must equal --expect-sha (eval3).
Output: ../raw/<run-id>/{runs.jsonl, manifest.jsonl, DONE}; resumable: finished (task, config)
pairs are skipped. The manifest records the sha256 of every mechanism file and of the frozen
harness, so a run can be tied to the exact code version (PREREGISTRATION.md §3).
"""
from __future__ import annotations

import argparse
import hashlib
import json
import os
import platform
import sys
import time
from pathlib import Path

P2 = Path(__file__).resolve().parents[1]
sys.path.insert(0, str(P2))
from evarb import EVARB_VERSION, paths  # noqa: E402
from evarb.clients import FamilyClient  # noqa: E402
from evarb.llm_arbiter import LLMArbiter  # noqa: E402
from evarb.loop import P2_VERSION, run_any  # noqa: E402
import memlab  # noqa: E402
import p1hold  # noqa: E402
import rcs  # noqa: E402

EXPECTED = {"p1dev": "94fe396fa35162a8ad3b88e5daf62d79ce092d1fe75e1c004637bb90ae749de8",
            "p1hold": "f747fbfa4f2537f7da464bee55ba570709daa940f57bcf38a8a635a419c9524c"}


def sha(p: Path) -> str:
    return hashlib.sha256(p.read_bytes()).hexdigest()


def code_hashes() -> dict:
    files = sorted((P2 / "evarb").glob("*.py")) + [paths.PHASE1_PROTO / f for f in ("rcs.py", "tea.py")] + \
        [paths.DEEP_SCRIPTS / f for f in ("memlab.py", "hf_client.py")] + [Path(__file__)]
    return {f.name if f.parent.name != "evarb" else "evarb/" + f.name: sha(f) for f in files}


def load_tasks(a):
    if a.split in ("p1dev", "p1hold"):
        tasks = rcs.build_p1dev() if a.split == "p1dev" else p1hold.build_p1hold()
        blob = "\n".join(json.dumps(t, sort_keys=True) for t in tasks).encode()
        h = hashlib.sha256(blob).hexdigest()
        if h != EXPECTED[a.split]:
            raise SystemExit(f"{a.split} hash {h} != {EXPECTED[a.split]}")
        return tasks, h
    path = Path(a.tasks) if a.tasks else (P2 / "data" / ("p2dev_tasks.jsonl" if a.split == "p2dev" else
                                                         f"{a.split}/{a.split}_tasks.jsonl"))
    h = sha(path)
    if a.expect_sha and h != a.expect_sha:
        raise SystemExit(f"{path} sha256 {h} != expected {a.expect_sha}")
    return [json.loads(x) for x in path.read_text(encoding="utf-8").splitlines() if x.strip()], h


def main() -> int:
    ap = argparse.ArgumentParser()
    ap.add_argument("--model", required=True)
    ap.add_argument("--run-id", required=True)
    ap.add_argument("--split", required=True)
    ap.add_argument("--tasks")
    ap.add_argument("--expect-sha")
    ap.add_argument("--configs", required=True)
    ap.add_argument("--temperature", type=float, default=0.0)
    ap.add_argument("--seed", type=int, default=20261111)
    ap.add_argument("--limit", type=int)
    ap.add_argument("--out", default=str(P2 / "raw"))
    a = ap.parse_args()
    tasks, split_sha = load_tasks(a)
    tasks.sort(key=lambda t: t["task_id"])
    if a.limit:
        tasks = tasks[:a.limit]
    configs = a.configs.split(",")
    out = Path(a.out) / a.run_id
    out.mkdir(parents=True, exist_ok=True)
    runs = out / "runs.jsonl"
    done = set()
    if runs.exists():
        for line in runs.read_text(encoding="utf-8").splitlines():
            if line.strip():
                r = json.loads(line)
                done.add((r["task_id"], r["config"]))
    client = FamilyClient(a.model, temperature=a.temperature, seed=a.seed)
    arb = LLMArbiter(client) if any(c in ("LA", "LG") for c in configs) else None
    import torch
    import transformers
    man = {"run_id": a.run_id, "split": a.split, "split_sha256": split_sha, "n_tasks": len(tasks), "configs": configs,
           "evarb_version": EVARB_VERSION, "p2_loop_version": P2_VERSION, "code_sha256": code_hashes(),
           "client": client.describe(), "temperature": a.temperature, "seed": a.seed,
           "python": platform.python_version(), "torch": torch.__version__, "transformers": transformers.__version__,
           "gpu": torch.cuda.get_device_name(0), "slurm_job_id": os.environ.get("SLURM_JOB_ID"),
           "started_utc": time.strftime("%Y-%m-%dT%H:%M:%SZ", time.gmtime()), "resumed_with_done": len(done)}
    with open(out / "manifest.jsonl", "a", encoding="utf-8") as f:
        f.write(json.dumps(man) + "\n")
    t0, n = time.monotonic(), 0
    with open(runs, "a", encoding="utf-8") as f:
        for task in tasks:
            for c in configs:
                if (task["task_id"], c) in done:
                    continue
                try:
                    run = run_any(client, task, c, harness="v2", llm_arbiter=arb)
                except Exception as e:  # recorded, scored as a failure (PREREGISTRATION.md §7)
                    run = {"record_type": "run", "task_id": task["task_id"], "config": c, "error": repr(e)[:500],
                           "final": None, "draft": None, "hit_max_steps": False, "tool_calls": [], "api_calls": [],
                           "rcs_events": [], "messages": [], "timing": {"total_s": 0.0}}
                run["model"] = a.model
                f.write(json.dumps(run, ensure_ascii=False, default=str) + "\n")
                f.flush()
                n += 1
                s = memlab.score_run(task, run) if "error" not in run else {"outcome": "harness_error"}
                ev = run.get("rcs_events") or []
                print(f"[{time.monotonic() - t0:7.0f}s] {task['task_id']} {c} -> {s['outcome']}"
                      f"{' ' + ev[0]['rule'] if ev else ''}{' reverted' if run.get('reverted') else ''}", flush=True)
    (out / "DONE").write_text(json.dumps({"finished_utc": time.strftime("%Y-%m-%dT%H:%M:%SZ", time.gmtime()),
                                          "runs": len(done) + n}))
    return 0


if __name__ == "__main__":
    raise SystemExit(main())
