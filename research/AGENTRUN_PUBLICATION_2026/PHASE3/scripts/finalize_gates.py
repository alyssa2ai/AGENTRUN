"""Integrity gates before the Phase 3 confirmatory analysis (run inside the HPC finalization job; no outcomes read).

    python finalize_gates.py --raw <phase3_raw> --logs <PHASE2/logs> --tasks <sealed eval3_tasks.jsonl> --out <gates.json>

Gates (G1-G4 must pass; exit 1 otherwise):
  G1 all 18 pre-registered cells have a DONE marker
  G2 every cell has rows == n_tasks x 12 configurations, no duplicate (task, config) pair, no unparsable line
  G3 the last Slurm segment of every cell ended with exit=0 (start/exit lines only)
  G4 every manifest line of a cell agrees on the pre-registered run identity: temperature, seed, split hash,
     code hashes, configs, and every CLIENT IDENTITY field (see the policy below)
Reads task ids only to count them; reads runs.jsonl only for task_id / config / error keys.

G4 policy version g4-v2 (2026-11-21)
------------------------------------
g4-v1 (preserved verbatim as `finalize_gates_v1_frozen.py`, sha256
8c1870f0725131c12ee4a4b3b67687426c3490b9d6967643b41f1364dc9e704d) compared the whole `client` object as one opaque
JSON blob. That made read-only host telemetry indistinguishable from a change of client implementation, and the
failure message named neither the subfield nor the values. See PHASE3_G4_FORENSIC_REPORT.md.

g4-v2 splits `client` into two explicitly declared sets and is CLOSED BY DEFAULT:

  CLIENT_IDENTITY       every field that can determine what was executed. Must be PRESENT in every start and EQUAL
                        across starts. Any difference, or any absence, is a hard failure that prints the exact field
                        path and the differing values.
  CLIENT_OBSERVATIONAL  read-only observations of the host that cannot influence execution. Excluded from the
                        identity comparison ONLY. Every start's original value is retained and reported in
                        gates.json (`client_observational_diffs`) and on stdout. Manifests are never rewritten.
  anything else         a `client` key in neither set is a HARD FAILURE until it is explicitly classified here.

The single declared observational field is `gpu_mem_gib`. Justification: hf_client.py:58 computes it as
round(torch.cuda.get_device_properties(0).total_memory / 2**30, 1) and stores it in `_versions`, which is consumed
only by HFClient.describe() to build the manifest. The model is loaded with device_map={"": 0} and no `max_memory`
(hf_client.py:45), so the reported device total has no path to placement, offloading, batching or generation.
"""
import argparse, json, re, sys
from pathlib import Path

GATE_POLICY_VERSION = "g4-v2 (2026-11-21)"

CELLS = ["qwen25_3b_greedy", "qwen25_3b_T07_s1", "qwen25_3b_T07_s2", "qwen25_3b_T07_s3",
         "qwen25_7b_greedy", "qwen25_7b_T07_s1", "qwen25_7b_T07_s2", "qwen25_7b_T07_s3",
         "llama31_8b_greedy", "llama31_8b_T07_s1", "llama31_8b_T07_s2", "llama31_8b_T07_s3",
         "qwen3_8b_greedy", "qwen3_8b_T07_s1", "qwen3_8b_T07_s2", "qwen3_8b_T07_s3",
         "qwen25_14b_greedy", "llama32_3b_greedy"]
N_CONFIGS = 12
START = re.compile(r"^start (\S+) job=(\S+) model=(\S+) decoding=(\S+)")
EXIT = re.compile(r"^exit=(\d+) (\S+) (\S+) (\S+)")

# --- G4 client policy -------------------------------------------------------------------------------------------
CLIENT_IDENTITY = (
    "backend",          # client implementation family
    "family",           # per-family prompt/tool handling
    "family_adapter",   # evarb.clients.FamilyClient/<n>
    "model",            # model identity
    "model_path",       # resolved HF snapshot (pins the weights)
    "adapter",          # PEFT adapter, if any
    "adapter_sha256",   # adapter weights hash
    "temperature",      # decoding
    "seed",
    "decoding",
    "max_new_tokens",
    "dtype",
    "thinking",
    "parser_version",   # agentrun_v2.parser version
    "torch",            # framework identities
    "transformers",
    "cuda",
    "gpu",              # device model
)
CLIENT_OBSERVATIONAL = ("gpu_mem_gib",)
_MISSING = object()

# Top-level manifest fields compared strictly across starts (unchanged from g4-v1).
TOP_IDENTITY = ("temperature", "seed", "split_sha256", "code_sha256", "configs")


def check_client_identity(cell, manifests):
    """Return (failures, observational_diffs) for one cell's manifest lines. Pure; used by the tests."""
    fails, obs = [], {}
    if not manifests:
        return [f"G4 {cell}: no manifest"], obs
    clients = []
    for i, m in enumerate(manifests):
        c = m.get("client")
        if not isinstance(c, dict) or not c:
            fails.append(f"G4 {cell}: start {i} has no client metadata")
        clients.append(c if isinstance(c, dict) else {})
    if fails:
        return fails, obs
    # fail closed: every key present in any start must be classified
    unknown = sorted(set().union(*[set(c) for c in clients]) - set(CLIENT_IDENTITY) - set(CLIENT_OBSERVATIONAL))
    if unknown:
        fails.append(f"G4 {cell}: unclassified client field(s) {unknown}: classify in CLIENT_IDENTITY or "
                     f"CLIENT_OBSERVATIONAL before this cell can pass")
    for k in CLIENT_IDENTITY:
        missing = [i for i, c in enumerate(clients) if c.get(k, _MISSING) is _MISSING]
        if missing:
            fails.append(f"G4 {cell}: client.{k} missing in start(s) {missing}")
            continue
        vals = [c[k] for c in clients]
        if len({json.dumps(v, sort_keys=True) for v in vals}) > 1:
            fails.append(f"G4 {cell}: client.{k} differs between starts: "
                         + " vs ".join(f"start {i}={json.dumps(v)}" for i, v in enumerate(vals)))
    for k in CLIENT_OBSERVATIONAL:
        vals = [c.get(k) for c in clients]
        if len({json.dumps(v, sort_keys=True) for v in vals}) > 1:
            obs[k] = vals  # retained verbatim, reported, never a failure and never written back
    return fails, obs


def check_top_identity(cell, manifests):
    fails = []
    for k in TOP_IDENTITY:
        if len({json.dumps(m.get(k), sort_keys=True) for m in manifests}) > 1:
            fails.append(f"G4 {cell}: manifest field {k} differs between starts")
    return fails


def main():
    ap = argparse.ArgumentParser()
    ap.add_argument("--raw", required=True); ap.add_argument("--logs", required=True)
    ap.add_argument("--tasks", required=True); ap.add_argument("--out", required=True)
    a = ap.parse_args()
    n_tasks = sum(1 for x in open(a.tasks, encoding="utf-8") if x.strip())
    expected = n_tasks * N_CONFIGS
    last = {}  # (model, decoding) -> (start time, exit code or None, log name)
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
    cells, fails, notes = [], [], []
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
            fails.extend(check_top_identity(c, man))
            cf, obs = check_client_identity(c, man)
            fails.extend(cf)
            if obs:
                r["client_observational_diffs"] = obs
                for k, vals in obs.items():
                    note = (f"{c}: observational client.{k} differs between starts "
                            + " vs ".join(f"start {i}={json.dumps(v)}" for i, v in enumerate(vals))
                            + " (declared observational; excluded from identity comparison only)")
                    notes.append(note)
            if isinstance(man[0].get("client"), dict) and "model" in man[0]["client"]:
                dec = "greedy" if man[0]["temperature"] == 0 else f"T07_s{man[0]['seed']}"
                seg = last.get((man[0]["client"]["model"], dec))
                r["last_segment"] = seg
                if not seg or seg[1] != 0:
                    fails.append(f"G3 {c}: last Slurm segment exit {seg[1] if seg else 'not found'}")
        else:
            fails.append(f"G4 {c}: no manifest")
        cells.append(r)
    out = {"gate_policy_version": GATE_POLICY_VERSION, "client_identity_fields": list(CLIENT_IDENTITY),
           "client_observational_fields": list(CLIENT_OBSERVATIONAL),
           "n_tasks": n_tasks, "expected_rows_per_cell": expected, "cells": cells,
           "observational_notes": notes, "failures": fails, "pass": not fails}
    Path(a.out).write_text(json.dumps(out, indent=1) + "\n", encoding="utf-8")
    print(f"gates: {'PASS' if not fails else 'FAIL'} ({GATE_POLICY_VERSION}); cells DONE {sum(c['done'] for c in cells)}/18")
    for x in notes:
        print("  NOTE " + x)
    for x in fails:
        print("  " + x)
    sys.exit(0 if not fails else 1)


if __name__ == "__main__":
    main()
