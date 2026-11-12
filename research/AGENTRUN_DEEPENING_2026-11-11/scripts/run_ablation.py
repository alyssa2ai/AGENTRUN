"""Run the ablation: every task of a split under every configuration.

    py -3.11 scripts/run_ablation.py --model qwen/qwen3.8-27b --split eval --run-id qwen_eval_t1

Appends one JSON line per (task, config) to raw_results/<run-id>/runs.jsonl and
resumes if interrupted (finished pairs are skipped). The first line of
manifest.json records model, hashes and settings. GROQ_API_KEY is read from
the environment and never written anywhere.
"""

from __future__ import annotations

import argparse
import hashlib
import json
import platform
import subprocess
import time
from pathlib import Path

import memlab

HERE = Path(__file__).resolve().parent.parent
MODEL_EXTRA = {"openai/gpt-oss-120b": {"reasoning_effort": "low"}, "openai/gpt-oss-20b": {"reasoning_effort": "low"}}


def main() -> int:
    p = argparse.ArgumentParser()
    p.add_argument("--model", required=True)
    p.add_argument("--split", choices=["dev", "eval"], required=True)
    p.add_argument("--run-id", required=True)
    p.add_argument("--configs", default="A,B,C,D,E")
    p.add_argument("--limit", type=int, help="first N tasks only (smoke tests)")
    p.add_argument("--scenarios", help="comma-separated scenario prefixes, e.g. S3,S4")
    p.add_argument("--backend", choices=["api", "hf"], default="api",
                   help="api: OpenAI-compatible endpoint; hf: local GPU model through hf_client.py")
    p.add_argument("--adapter", help="hf backend: path to a LoRA adapter directory")
    p.add_argument("--temperature", type=float, default=0.0, help="hf backend only (api backend is fixed at 0)")
    p.add_argument("--seed", type=int, default=20261111)
    p.add_argument("--base-url", default="https://api.groq.com/openai/v1",
                   help="any OpenAI-compatible endpoint, e.g. a local vLLM server on an HPC node")
    p.add_argument("--key-env", default="GROQ_API_KEY", help="environment variable holding the API key")
    a = p.parse_args()

    bench = HERE / "benchmark" / f"{a.split}.jsonl"
    freeze = json.loads((HERE / "benchmark" / "FREEZE.json").read_text(encoding="utf-8"))
    sha = hashlib.sha256(bench.read_bytes()).hexdigest()
    if sha != freeze[a.split]["sha256"]:
        raise SystemExit("benchmark file does not match FREEZE.json")
    if memlab.prompts_sha256() != freeze["prompts_sha256"] and a.split == "eval":
        raise SystemExit("prompts/configs changed since the freeze; rebuild or revert before an eval run")
    tasks = [json.loads(x) for x in bench.read_text(encoding="utf-8").splitlines() if x.strip()]
    if a.scenarios:
        pre = tuple(a.scenarios.split(","))
        tasks = [t for t in tasks if t["scenario"].startswith(pre)]
    # Round-robin over scenarios, so an interrupted run is still balanced.
    tasks.sort(key=lambda t: (int(t["task_id"].rsplit("-", 1)[1]), t["scenario"]))
    if a.limit:
        tasks = tasks[:a.limit]
    configs = a.configs.split(",")

    out = HERE / "raw_results" / a.run_id
    out.mkdir(parents=True, exist_ok=True)
    runs = out / "runs.jsonl"
    done = set()
    if runs.exists():
        for line in runs.read_text(encoding="utf-8").splitlines():
            if line.strip():
                r = json.loads(line)
                done.add((r["task_id"], r["config"]))
    if a.backend == "hf":
        from hf_client import HFClient
        client = HFClient(a.model, adapter=a.adapter, temperature=a.temperature, seed=a.seed)
    else:
        client = memlab.ChatClient(a.model, MODEL_EXTRA.get(a.model), base_url=a.base_url, key_env=a.key_env,
                                   seed=a.seed)
    try:
        commit = subprocess.check_output(["git", "rev-parse", "HEAD"], cwd=HERE, text=True).strip()
    except Exception:
        commit = None
    man = {"run_id": a.run_id, "split": a.split, "benchmark_sha256": sha, "prompts_sha256": memlab.prompts_sha256(),
           "memlab_version": memlab.MEMLAB_VERSION,
           "memlab_py_sha256": hashlib.sha256((HERE / "scripts" / "memlab.py").read_bytes()).hexdigest(),
           "client": client.describe(), "configs": configs, "n_tasks": len(tasks), "top_k": memlab.TOP_K,
           "min_similarity": memlab.MIN_SIM, "max_steps": memlab.MAX_STEPS, "trials": 1,
           "python": platform.python_version(), "platform": platform.platform(), "git_commit": commit,
           "started_utc": time.strftime("%Y-%m-%dT%H:%M:%SZ", time.gmtime()), "resumed_with_done": len(done)}
    with open(out / "manifest.jsonl", "a", encoding="utf-8") as f:
        f.write(json.dumps(man) + "\n")

    t0 = time.monotonic()
    n = 0
    with open(runs, "a", encoding="utf-8") as f:
        for task in tasks:
            for c in configs:
                if (task["task_id"], c) in done:
                    continue
                run = memlab.run_task(client, task, c, out / "stores")
                run["model"] = a.model
                f.write(json.dumps(run, ensure_ascii=False) + "\n")
                f.flush()
                n += 1
                s = memlab.score_run(task, run)
                print(f"[{time.monotonic() - t0:7.0f}s req={client.n_requests:4d}] {task['task_id']} {c} "
                      f"-> {s['outcome']}", flush=True)
    (out / "DONE").write_text(json.dumps({"finished_utc": time.strftime("%Y-%m-%dT%H:%M:%SZ", time.gmtime()),
                                          "runs_in_file": len(done) + n, "expected": len(tasks) * len(configs)}))
    print(f"done: {n} new runs, {client.n_requests} API requests, exit 0", flush=True)
    return 0


if __name__ == "__main__":
    raise SystemExit(main())
