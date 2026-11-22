"""Client-matched re-run of AGENTRUN's own benchmarks on a local GPU.

Runs the repository's existing v2 runner (agentrun_v2.runner: training system
prompt, the four MCP tool schemas, deterministic frozen tool environment, raw
generation logged, client-side two-pass parser) with a locally served model,
and scores with the repository's existing scorers:

  --tasks legacy   the 23 original tasks, scored by the frozen eval/harness.py (R0)
  --tasks dev      the 55-task dev split of benchmark v2, scored by scorer_v2 (R2, R0-rule)

The sealed v2 test split is never used here.

    python run_v2_hpc.py --model Qwen/Qwen2.5-7B-Instruct --tasks legacy --max-steps 3 --run-id legacy_base_b3
"""

from __future__ import annotations

import argparse
import hashlib
import json
import time
from pathlib import Path

import memlab
from agentrun_v2 import scorer_v2
from agentrun_v2.legacy import legacy_tasks, score_legacy
from agentrun_v2.runner import RunConfig, read_log, run_benchmark
from hf_client import HFClient

HERE = Path(__file__).resolve().parent.parent
REPO = memlab.REPO


class RawClient:
    """Adapter from HFClient.chat() to the v2 runner's generate() contract."""

    def __init__(self, hf: HFClient):
        self.hf = hf

    def describe(self) -> dict:
        return self.hf.describe()

    def generate(self, messages, tools):
        r = self.hf.chat(messages, tools)
        return {"raw_text": r["raw_text"], "meta": {"usage": r["usage"], "latency_s": r["latency_s"]}}


def main() -> int:
    p = argparse.ArgumentParser()
    p.add_argument("--model", required=True)
    p.add_argument("--adapter")
    p.add_argument("--tasks", choices=["legacy", "dev"], required=True)
    p.add_argument("--max-steps", type=int, choices=[3, 6], required=True)
    p.add_argument("--run-id", required=True)
    p.add_argument("--temperature", type=float, default=0.0)
    p.add_argument("--seed", type=int, default=20261111)
    a = p.parse_args()

    out = HERE / "raw_results" / a.run_id
    out.mkdir(parents=True, exist_ok=True)
    log = out / "v2_log.jsonl"
    if (out / "DONE").exists():
        print("already done")
        return 0
    if a.tasks == "legacy":
        tasks, bench_id, bpath = legacy_tasks(), "legacy-23", REPO / "eval" / "tasks.py"
    else:
        bpath = REPO / "benchmark_v2" / "dev.jsonl"
        tasks = [json.loads(x) for x in bpath.read_text(encoding="utf-8").splitlines() if x.strip()]
        bench_id = "bench-v2:dev.jsonl"
    hf = HFClient(a.model, adapter=a.adapter, temperature=a.temperature, seed=a.seed)
    cond = ("adapter" if a.adapter else "base") + ("" if a.temperature == 0 else f"_T{a.temperature}_s{a.seed}")
    cfg = RunConfig(run_id=a.run_id, condition=cond, max_steps=a.max_steps, benchmark_id=bench_id,
                    benchmark_sha256=hashlib.sha256(bpath.read_bytes()).hexdigest(), seed=a.seed,
                    adapter=a.adapter, adapter_sha256=hf.adapter_sha, base_model=a.model,
                    notes="SIT HPC, local GPU, frozen tool environment (legacy fixture for legacy tasks)")
    t0 = time.monotonic()
    run_benchmark(RawClient(hf), tasks, cfg, log)
    manifest, recs = read_log(log)
    if a.tasks == "legacy":
        scores = score_legacy(recs)
        summary = {"scorer": "eval/harness.py (frozen R0)", "n": len(scores), "r0_pass": sum(s["r0"] for s in scores)}
    else:
        scores = scorer_v2.score_log(tasks, recs)
        summary = scorer_v2.summarize(scores)
    res = {"run_id": a.run_id, "model": a.model, "adapter_sha256": hf.adapter_sha, "condition": cond,
           "tasks": a.tasks, "max_steps": a.max_steps, "client": hf.describe(), "summary": summary,
           "per_task": scores, "wall_s": round(time.monotonic() - t0, 1)}
    (out / "scores.json").write_text(json.dumps(res, indent=1, default=str), encoding="utf-8")
    (out / "DONE").write_text(time.strftime("%Y-%m-%dT%H:%M:%SZ", time.gmtime()))
    print(json.dumps(summary, indent=1, default=str), flush=True)
    print("exit 0", flush=True)
    return 0


if __name__ == "__main__":
    raise SystemExit(main())
