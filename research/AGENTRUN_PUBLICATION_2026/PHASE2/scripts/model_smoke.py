"""Second-model-family readiness: load + inference + tool-call parse test (development data only).

    python model_smoke.py --model meta-llama/Llama-3.2-3B-Instruct --n-tasks 10 --out ../raw/smoke

For each model: load from the local HF cache (no download), record load time and peak VRAM,
run the first n p1dev tasks (Phase 1 development split) under configs B and G with the
unchanged Phase 1 loop (rcs.run_task), and count, over all model turns:
  tool_call     the turn produced at least one parsed tool call
  submission    the turn ended the run with a parsable submit_answer / final JSON
  malformed     the client reported a malformed tool call (error)
  other_text    plain text that is neither (repair notice or format error follows)
Readiness criterion (Phase 1 design step 2.5): >= 95% of turns are tool_call or submission.
Also runs the frozen parser alone on every raw generation, to show what the adapter changes.
"""
from __future__ import annotations

import argparse
import json
import sys
import time
from collections import Counter
from pathlib import Path

sys.path.insert(0, str(Path(__file__).resolve().parents[1]))
from evarb import paths  # noqa: E402,F401
from evarb.clients import FamilyClient  # noqa: E402
import rcs  # noqa: E402
from agentrun_v2.parser import parse_model_output  # noqa: E402

memlab = rcs.memlab


def main():
    p = argparse.ArgumentParser()
    p.add_argument("--model", required=True)
    p.add_argument("--n-tasks", type=int, default=10)
    p.add_argument("--out", required=True)
    a = p.parse_args()
    import torch
    out = Path(a.out)
    out.mkdir(parents=True, exist_ok=True)
    tag = a.model.split("/")[-1]
    t0 = time.monotonic()
    torch.cuda.reset_peak_memory_stats()
    client = FamilyClient(a.model)
    load_s = time.monotonic() - t0
    tasks = rcs.build_p1dev()
    tasks.sort(key=lambda t: (int(t["task_id"].rsplit("-", 1)[1]), t["scenario"]))
    tasks = tasks[:a.n_tasks]
    turns = Counter()
    frozen_only = Counter()
    rows = []
    for t in tasks:
        for c in ("B", "G"):
            run = rcs.run_task(client, t, c, harness="v2")
            run["model"] = a.model
            s = memlab.score_run(t, run)
            for i, api in enumerate(run["api_calls"]):
                raw = api.get("raw_text") or ""
                fp = parse_model_output(raw)
                frozen_only["tool_call" if fp["tool_calls"] else "none"] += 1
                if api.get("error"):
                    turns["malformed"] += 1
                elif api.get("parse_path") in ("closed", "open_fallback", "client_bare_json", "family_llama_json"):
                    turns["tool_call"] += 1
                elif (memlab.parse_final(raw) or {}).get("status"):
                    turns["submission"] += 1
                else:
                    turns["other_text"] += 1
                turns["path:" + str(api.get("parse_path"))] += 1
            rows.append({"task_id": t["task_id"], "config": c, "outcome": s["outcome"], "n_turns": len(run["api_calls"]),
                         "raw_texts": [x.get("raw_text") for x in run["api_calls"]]})
    n = sum(turns[k] for k in ("tool_call", "submission", "malformed", "other_text"))
    res = {"model": a.model, "client": client.describe(), "load_s": round(load_s, 1),
           "peak_vram_gib": round(torch.cuda.max_memory_allocated() / 2 ** 30, 2), "n_runs": len(rows), "turns": n,
           "turn_counts": dict(turns), "frozen_parser_only": dict(frozen_only),
           "parsable_rate": round((turns["tool_call"] + turns["submission"]) / max(1, n), 4),
           "family_reparses": client.n_family_reparse}
    res["outcomes"] = {f"{k[0]}:{k[1]}": v for k, v in Counter((r["config"], r["outcome"]) for r in rows).items()}
    (out / f"smoke_{tag}.json").write_text(json.dumps(res, indent=1), encoding="utf-8")
    with open(out / f"smoke_{tag}_runs.jsonl", "w", encoding="utf-8") as f:
        for r in rows:
            f.write(json.dumps(r, ensure_ascii=False) + "\n")
    print(json.dumps({k: v for k, v in res.items() if k != "client"}, indent=1))


if __name__ == "__main__":
    main()
