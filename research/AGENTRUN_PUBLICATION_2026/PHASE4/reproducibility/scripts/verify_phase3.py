"""Per-cell completeness and provenance report for Phase 3 (CPU, no outcomes printed).

    python verify_phase3.py --tasks <tasks.jsonl> --cells <run dirs...> --out <prefix> [--dry]

For every cell: present?, DONE marker, rows, expected rows (tasks x configs), missing and duplicate (task, config)
pairs, harness-error rows, manifest consistency (all manifest lines: same model, temperature, seed, split hash,
code hashes), code hashes equal to FREEZE_evarb.json, task-file hash equal to the manifest's split_sha256.
Writes <prefix>.md/.json. Exit 1 if any integrity problem (hash drift) is found; incompleteness is reported, not fatal.
"""
import argparse, hashlib, json, sys
from pathlib import Path

P2 = Path(__file__).resolve().parents[2] / "PHASE2"


def jl(p):
    return [json.loads(l) for l in open(p, encoding="utf-8") if l.strip()]


def main():
    ap = argparse.ArgumentParser()
    ap.add_argument("--tasks", required=True); ap.add_argument("--cells", nargs="+", required=True)
    ap.add_argument("--out", required=True); ap.add_argument("--dry", action="store_true")
    a = ap.parse_args()
    tasks = {t["task_id"] for t in jl(a.tasks)}
    task_sha = hashlib.sha256(Path(a.tasks).read_bytes()).hexdigest()
    freeze = json.load(open(P2 / "FREEZE_evarb.json"))["files"]
    rows, problems = [], []
    for c in a.cells:
        d = Path(c); r = {"cell": d.name, "present": d.is_dir()}
        if not r["present"]:
            rows.append(r); continue
        man = jl(d / "manifest.jsonl") if (d / "manifest.jsonl").exists() else []
        runs = jl(d / "runs.jsonl") if (d / "runs.jsonl").exists() else []
        cfgs = man[0]["configs"] if man else []
        seen, dup, err = set(), 0, 0
        for x in runs:
            k = (x["task_id"], x["config"]); dup += k in seen; seen.add(k); err += "error" in x
        exp = {(t, g) for t in tasks for g in cfgs}
        r.update(done=(d / "DONE").exists(), starts=len(man), rows=len(runs), expected=len(exp),
                 missing=len(exp - seen), duplicates=dup, error_rows=err)
        probs = []
        if man:
            for k in ("client", "temperature", "seed", "split_sha256", "code_sha256", "configs"):
                if len({json.dumps(m.get(k), sort_keys=True) for m in man}) > 1:
                    probs.append(f"manifest field {k} differs between starts")
            cs = man[0]["code_sha256"]
            bad = [k for k, v in freeze.items() if k in cs and cs[k] != v]
            if bad: probs.append(f"code hash differs from FREEZE_evarb: {bad}")
            if not a.dry and man[0]["split_sha256"] != task_sha: probs.append("task-file hash differs from manifest")
            r["model"] = man[0]["client"]["model"]; r["temperature"] = man[0]["temperature"]; r["seed"] = man[0]["seed"]
        r["problems"] = probs; problems += [f"{d.name}: {p}" for p in probs]
        rows.append(r)
    Path(a.out).parent.mkdir(parents=True, exist_ok=True)
    json.dump({"tasks": len(tasks), "task_sha256": task_sha, "cells": rows, "problems": problems},
              open(a.out + ".json", "w"), indent=1)
    L = [f"# Completeness ({'DRY RUN on development data' if a.dry else 'eval3'})", "",
         f"Tasks {len(tasks)}; task file sha256 `{task_sha[:16]}…`.", "",
         "| Cell | present | DONE | rows / expected | missing | duplicates | error rows | starts |", "|---|---|---|---|---|---|---|---|"]
    for r in rows:
        L.append(f"| {r['cell']} | {r['present']} | {r.get('done','-')} | {r.get('rows','-')} / {r.get('expected','-')} | "
                 f"{r.get('missing','-')} | {r.get('duplicates','-')} | {r.get('error_rows','-')} | {r.get('starts','-')} |")
    L += ["", "Integrity problems: " + ("none" if not problems else "; ".join(problems))]
    Path(a.out + ".md").write_text("\n".join(L) + "\n", encoding="utf-8")
    print("\n".join(L)); sys.exit(1 if problems else 0)


if __name__ == "__main__":
    main()
