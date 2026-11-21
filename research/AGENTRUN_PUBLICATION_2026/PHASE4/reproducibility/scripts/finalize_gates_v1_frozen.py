"""Integrity gates before the Phase 3 confirmatory analysis (run inside the HPC finalization job; no outcomes read).

    python finalize_gates.py --raw <phase3_raw> --logs <PHASE2/logs> --tasks <sealed eval3_tasks.jsonl> --out <gates.json>

Gates (all must pass; exit 1 otherwise):
  G1 all 18 pre-registered cells have a DONE marker
  G2 every cell has rows == n_tasks x 12 configurations, no duplicate (task, config) pair, no unparsable line
  G3 the last Slurm segment of every cell ended with exit=0 (start/exit lines only)
  G4 every manifest line of a cell agrees on model, temperature, seed, split hash, code hashes and configs
Reads task ids only to count them; reads runs.jsonl only for task_id / config / error keys.
"""
import argparse, json, re, sys
from pathlib import Path

CELLS = ["qwen25_3b_greedy", "qwen25_3b_T07_s1", "qwen25_3b_T07_s2", "qwen25_3b_T07_s3",
         "qwen25_7b_greedy", "qwen25_7b_T07_s1", "qwen25_7b_T07_s2", "qwen25_7b_T07_s3",
         "llama31_8b_greedy", "llama31_8b_T07_s1", "llama31_8b_T07_s2", "llama31_8b_T07_s3",
         "qwen3_8b_greedy", "qwen3_8b_T07_s1", "qwen3_8b_T07_s2", "qwen3_8b_T07_s3",
         "qwen25_14b_greedy", "llama32_3b_greedy"]
N_CONFIGS = 12
START = re.compile(r"^start (\S+) job=(\S+) model=(\S+) decoding=(\S+)")
EXIT = re.compile(r"^exit=(\d+) (\S+) (\S+) (\S+)")


def main():
    ap = argparse.ArgumentParser()
    ap.add_argument("--raw", required=True); ap.add_argument("--logs", required=True)
    ap.add_argument("--tasks", required=True); ap.add_argument("--out", required=True)
    a = ap.parse_args()
    n_tasks = sum(1 for x in open(a.tasks, encoding="utf-8") if x.strip())
    expected = n_tasks * N_CONFIGS
    last = {}  # (model, decoding) -> (start time, exit code or None)
    for f in sorted(Path(a.logs).glob("phase3_*_*.out")):
        st = ex = None
        for line in open(f, encoding="utf-8", errors="replace"):
            if line.startswith("start "):
                st = START.match(line)
            elif line.startswith("exit="):
                ex = EXIT.match(line)
        if st:
            k = (st.group(3), st.group(4))
            if k not in last or st.group(1) > last[k][0]:
                last[k] = (st.group(1), int(ex.group(1)) if ex else None, f.name)
    cells, fails = [], []
    for c in CELLS:
        d = Path(a.raw) / f"eval3_{c}"
        r = {"cell": c, "done": (d / "DONE").exists()}
        if not r["done"]:
            fails.append(f"G1 {c}: no DONE marker")
        seen, dup, bad, err = set(), 0, 0, 0
        if (d / "runs.jsonl").exists():
            for line in open(d / "runs.jsonl", encoding="utf-8"):
                if not line.strip():
                    continue
                try:
                    x = json.loads(line)
                except Exception:
                    bad += 1; continue
                k = (x["task_id"], x["config"]); dup += k in seen; seen.add(k); err += "error" in x
        r.update(rows=len(seen) + dup, expected=expected, duplicates=dup, unparsable=bad, harness_errors=err)
        if len(seen) != expected or dup or bad:
            fails.append(f"G2 {c}: unique pairs {len(seen)}/{expected}, duplicates {dup}, unparsable {bad}")
        man = [json.loads(x) for x in open(d / "manifest.jsonl", encoding="utf-8") if x.strip()] if (d / "manifest.jsonl").exists() else []
        r["starts"] = len(man)
        if man:
            for k in ("client", "temperature", "seed", "split_sha256", "code_sha256", "configs"):
                if len({json.dumps(m.get(k), sort_keys=True) for m in man}) > 1:
                    fails.append(f"G4 {c}: manifest field {k} differs between starts")
            dec = "greedy" if man[0]["temperature"] == 0 else f"T07_s{man[0]['seed']}"
            seg = last.get((man[0]["client"]["model"], dec))
            r["last_segment"] = seg
            if not seg or seg[1] != 0:
                fails.append(f"G3 {c}: last Slurm segment exit {seg[1] if seg else 'not found'}")
        else:
            fails.append(f"G4 {c}: no manifest")
        cells.append(r)
    out = {"n_tasks": n_tasks, "expected_rows_per_cell": expected, "cells": cells, "failures": fails, "pass": not fails}
    Path(a.out).write_text(json.dumps(out, indent=1) + "\n", encoding="utf-8")
    print(f"gates: {'PASS' if not fails else 'FAIL'}; cells DONE {sum(c['done'] for c in cells)}/18")
    for x in fails:
        print("  " + x)
    sys.exit(0 if not fails else 1)


if __name__ == "__main__":
    main()
