"""Run the LLM evidence arbiter on component groups (GPU). Scored offline by component_eval.py.

    python llm_arbiter_eval.py --model Qwen/Qwen2.5-7B-Instruct --groups ../data/dev_groups.jsonl \
        ../data/regression_groups.jsonl --out ../raw/llm_arbiter

Writes <out>/<model-tag>__<groups-stem>.jsonl: {fixture_id, raw, latency_s, usage}. Resumable.
Only groups with two or more distinct values are sent (others are trivially unchallenged).
"""
from __future__ import annotations

import argparse
import json
import sys
from pathlib import Path

sys.path.insert(0, str(Path(__file__).resolve().parents[1]))
from evarb.clients import FamilyClient  # noqa: E402
from evarb.llm_arbiter import LLMArbiter  # noqa: E402


def main():
    ap = argparse.ArgumentParser()
    ap.add_argument("--model", required=True)
    ap.add_argument("--groups", nargs="+", required=True)
    ap.add_argument("--out", required=True)
    a = ap.parse_args()
    client = FamilyClient(a.model, max_new_tokens=400)
    arb = LLMArbiter(client)
    out = Path(a.out)
    out.mkdir(parents=True, exist_ok=True)
    tag = a.model.split("/")[-1]
    for gp in a.groups:
        dest = out / f"{tag}__{Path(gp).stem}.jsonl"
        done = {json.loads(x)["fixture_id"] for x in dest.read_text(encoding="utf-8").splitlines()} if dest.exists() else set()
        rows = [json.loads(x) for x in Path(gp).read_text(encoding="utf-8").splitlines() if x.strip()]
        with open(dest, "a", encoding="utf-8") as f:
            for r in rows:
                if r["fixture_id"] in done or len({str(x["value"]) for x in r["records"]}) < 2:
                    continue
                _, log = arb.arbitrate(r["records"])
                f.write(json.dumps({"fixture_id": r["fixture_id"], "raw": log.get("raw", ""), "latency_s": log.get("latency_s"),
                                    "usage": log.get("usage"), "model": a.model}, ensure_ascii=False) + "\n")
                f.flush()
        print(f"{dest.name}: done; parse failures so far {arb.n_parse_fail}/{arb.n_calls}", flush=True)
    (out / f"{tag}__client.json").write_text(json.dumps(client.describe(), indent=1), encoding="utf-8")


if __name__ == "__main__":
    main()
