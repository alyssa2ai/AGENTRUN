"""End-to-end CPU dry run of the Phase 2/3 analysis pipeline with SIMULATED agents (no GPU, no real model).

    python dryrun_pipeline.py --tasks ../data/p2val/p2val_tasks.jsonl --out <scratch dir>

Purpose: verify, before any real run exists, that the frozen loop (all 12 configurations, including LA/LG),
the run-file format written by run_p2.py, the frozen analysis (analyze_p2.py: pairing, family sign-flip,
bootstrap, Holm over the pre-registered set, missing-run handling) and power_phase3.py work together exactly
as PREREGISTRATION.md §7–§9 describe. The numbers it produces are MEANINGLESS (simulated agents) and
must never be reported as results.

Simulated agent: searches memory once, then submits; with probability `follow` it answers with the record
the labels call current (or `conflict` for contradictory / unresolved), otherwise a uniformly random retrieved
value; after a notice it complies with probability `comply`. Three simulated "models" differ in these
probabilities. The LLM arbiter's client returns a fixed valid JSON ("every record unresolved").
A configurable share of (task, config) rows is deleted to exercise missing-run handling.
"""
from __future__ import annotations

import argparse
import json
import random
import subprocess
import sys
from pathlib import Path

HERE = Path(__file__).resolve().parent
P2 = HERE.parent
sys.path.insert(0, str(P2))
from evarb import paths  # noqa: E402,F401
from evarb.llm_arbiter import LLMArbiter  # noqa: E402
from evarb.loop import run_any  # noqa: E402

CONFIGS = "B,G,R,T,RT,EB,EBG,LA,LG,EBG-all,EBG-unsafe,EBG-noR3".split(",")
SIMS = {"sim/agent-small": (0.45, 0.6), "sim/agent-mid": (0.65, 0.8), "sim/agent-family2": (0.55, 0.7)}


class SimAgent:
    def __init__(self, follow, comply, seed):
        self.follow, self.comply, self.rng = follow, comply, random.Random(seed)
        self.vals = {}

    def set_task(self, task):
        # the harness shows record texts, not values; the simulator reads the value off its own copy of the task
        self.vals = {m["text"]: m["value"] for m in task["memory"]}

    def _msg(self, name, args):
        return {"message": {"role": "assistant", "content": "", "tool_calls": [
            {"id": f"c{self.rng.randrange(10**6)}", "type": "function", "function": {"name": name, "arguments": json.dumps(args)}}]},
            "usage": {"prompt_tokens": 0, "completion_tokens": 0}, "latency_s": 0.0, "wait_s": 0.0, "raw_text": "",
            "parse_path": None, "finish_reason": "stop", "error": None}

    def chat(self, messages, tools=None):
        if tools is None:  # LLM-arbiter call: fixed, valid, uninformative output
            return {"message": {"role": "assistant", "content": json.dumps({"records": {}})}, "raw_text": "", "usage": {},
                    "latency_s": 0.0, "finish_reason": "stop", "error": None}
        tool_msgs = [m for m in messages if m.get("role") == "tool"]
        if not tool_msgs:
            q = next((m["content"] for m in messages if m.get("role") == "user"), "")
            return self._msg("memory_search", {"query": q[:120]})
        last_user = [m for m in messages if m.get("role") == "user"][-1]["content"]
        notice = len([m for m in messages if m.get("role") == "user"]) > 1
        try:
            res = json.loads(tool_msgs[-1]["content"]).get("results", [])
        except Exception:
            res = []
        res = [dict(r, value=self.vals.get(r.get("text"))) for r in res if self.vals.get(r.get("text")) is not None]
        if not res:
            return self._msg("submit_answer", {"status": "abstain", "value": "", "evidence": [], "note": ""})
        cur = [r for r in res if (r.get("reliability") or {}).get("status") in ("current", "unchallenged")]
        bad = any((r.get("reliability") or {}).get("status") in ("contradictory", "conflicting") for r in res)
        if notice and self.rng.random() < self.comply and "conflict" in last_user.lower():
            return self._msg("submit_answer", {"status": "conflict", "value": "", "evidence": [], "note": ""})
        if self.rng.random() < self.follow:
            if cur:
                return self._msg("submit_answer", {"status": "answer", "value": str(cur[0]["value"]), "evidence": [], "note": ""})
            if bad:
                return self._msg("submit_answer", {"status": "conflict", "value": "", "evidence": [], "note": ""})
        r = self.rng.choice(res)
        return self._msg("submit_answer", {"status": "answer", "value": str(r["value"]), "evidence": [], "note": ""})


def main():
    ap = argparse.ArgumentParser()
    ap.add_argument("--tasks", required=True)
    ap.add_argument("--out", required=True)
    ap.add_argument("--limit", type=int, help="use only the first N tasks (for the unit test)")
    ap.add_argument("--n-perm", default="20000")
    ap.add_argument("--drop", type=float, default=0.01, help="share of rows deleted to test missing-run handling")
    a = ap.parse_args()
    tasks = [json.loads(x) for x in Path(a.tasks).read_text(encoding="utf-8").splitlines() if x.strip()]
    if a.limit:
        tasks = tasks[:a.limit]
        a.tasks = str(Path(a.out) / "tasks_subset.jsonl")
        Path(a.out).mkdir(parents=True, exist_ok=True)
        Path(a.tasks).write_text("\n".join(json.dumps(t) for t in tasks) + "\n", encoding="utf-8")
    out = Path(a.out)
    dirs = []
    rng = random.Random(7)
    errors = 0
    for m, (fol, com) in SIMS.items():
        d = out / f"dryrun_{m.split('/')[-1]}"
        d.mkdir(parents=True, exist_ok=True)
        agent = SimAgent(fol, com, hash(m) % 1000)
        arb = LLMArbiter(agent)
        with open(d / "manifest.jsonl", "w", encoding="utf-8") as f:
            f.write(json.dumps({"run_id": d.name, "split": "dryrun", "configs": CONFIGS, "client": {"model": m},
                                "temperature": 0.0, "seed": 0, "SIMULATED": True}) + "\n")
        with open(d / "runs.jsonl", "w", encoding="utf-8") as f:
            for t in tasks:
                agent.set_task(t)
                for c in CONFIGS:
                    if rng.random() < a.drop:
                        continue
                    try:
                        run = run_any(agent, t, c, harness="v2", llm_arbiter=arb)
                    except Exception as e:  # recorded like run_p2.py does
                        errors += 1
                        run = {"task_id": t["task_id"], "config": c, "error": repr(e)[:300]}
                    run["model"] = m
                    f.write(json.dumps(run, default=str) + "\n")
        dirs.append(str(d))
    print(json.dumps({"simulated_models": len(SIMS), "tasks": len(tasks), "configs": len(CONFIGS), "loop_exceptions": errors}))
    r1 = subprocess.run([sys.executable, str(HERE / "analyze_p2.py"), "--tasks", a.tasks, "--runs", *dirs,
                         "--out", str(out / "dryrun_analysis"), "--holm", "EBG-RT,EBG-T,EBG-LG,EBG-B", "--n-perm", a.n_perm],
                        capture_output=True, text=True)
    print("analyze_p2 exit", r1.returncode, r1.stderr[-800:])
    r2 = subprocess.run([sys.executable, str(HERE / "power_phase3.py"), "--tasks", a.tasks, "--runs", *dirs,
                         "--models", ",".join(SIMS), "--eval3-families", "138", "--n-sim", "400",
                         "--out", str(out / "dryrun_power")], capture_output=True, text=True)
    print("power_phase3 exit", r2.returncode, r2.stderr[-800:])
    return r1.returncode or r2.returncode


if __name__ == "__main__":
    raise SystemExit(main())
