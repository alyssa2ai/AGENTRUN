"""Write FREEZE_eval3.json from the sealed build job's LOG (counts, statistics and hashes only; no content).

    python write_freeze_eval3.py --log ../logs/eval3_build_<job>.out --remote-check <seal-check output> \
        --prereg ../PREREGISTRATION.md --out ../FREEZE_eval3.json

The eval3 build log (hpc/eval3_build.sbatch) contains only: the skeleton summary, assemble.py --quiet output
(counts and file hashes), agreement.py --quiet (kappa, exact agreement, primary counts per category, primary-ids
hash), seal_checks.py output (counts), the provenance record, and the SHA256SUMS lines. This script collects
them; it never opens a sealed file. `--remote-check` is the captured output of
`cd ~/AGENTRUN_HPC/sealed/eval3 && sha256sum -c SHA256SUMS && stat -c '%A %n' *` run at freeze time.
The pre-registration's sha256 is recorded so that the pre-registration is fixed together with eval3.
"""
from __future__ import annotations

import argparse
import hashlib
import json
import re
import time
from pathlib import Path


def json_objects(text):
    dec, out, i = json.JSONDecoder(), [], 0
    while True:
        j = text.find("{", i)
        if j < 0:
            return out
        try:
            obj, end = dec.raw_decode(text, j)
            out.append(obj)
            i = end
        except json.JSONDecodeError:
            i = j + 1


def main():
    ap = argparse.ArgumentParser()
    ap.add_argument("--log", required=True)
    ap.add_argument("--remote-check", required=True)
    ap.add_argument("--prereg", required=True)
    ap.add_argument("--out", required=True)
    a = ap.parse_args()
    log = Path(a.log).read_text(encoding="utf-8", errors="replace")
    objs = json_objects(log)
    pick = lambda pred: next((o for o in objs if pred(o)), None)  # noqa: E731
    assemble = pick(lambda o: o.get("split") == "eval3" and "n_valid" in o and "tasks.jsonl" in o)
    agreement = pick(lambda o: "annotators" in o and "n_primary" in o)
    seal_checks = pick(lambda o: "hard_checks_pass" in o)
    prov = pick(lambda o: o.get("human_validation") is not None)
    sums = dict((n, h) for h, n in re.findall(r"^([0-9a-f]{64})  (eval3_\S+)$", log, re.M))
    sums_self = re.search(r"SHA256SUMS itself: ([0-9a-f]{64})", log)
    remote = Path(a.remote_check).read_text(encoding="utf-8", errors="replace")
    ok_lines = re.findall(r"^(eval3_\S+): OK$", remote, re.M)
    writable = re.findall(r"^\S*w\S* (eval3_\S+|SHA256SUMS)$", remote, re.M)
    problems = []
    if not assemble:
        problems.append("assemble summary missing from log")
    if not sums:
        problems.append("SHA256SUMS lines missing from log")
    if set(ok_lines) != set(sums):
        problems.append(f"remote sha256sum -c: {len(ok_lines)} OK of {len(sums)}")
    if writable:
        problems.append(f"{len(writable)} sealed files are writable")
    if seal_checks and not seal_checks.get("hard_checks_pass"):
        problems.append("seal_checks hard checks failed")
    if "seal verified" not in log:
        problems.append("job log lacks 'seal verified'")
    pre = Path(a.prereg).read_bytes().replace(b"\r\n", b"\n")
    out = {"split": "eval3", "status": "SEALED" if not problems else "PROBLEM", "problems": problems,
           "written_utc": time.strftime("%Y-%m-%dT%H:%M:%SZ", time.gmtime()),
           "sealed_dir": "~/AGENTRUN_HPC/sealed/eval3 (cluster only)", "sealed_files": sums,
           "sha256sums_file_sha256": sums_self.group(1) if sums_self else None,
           "n_skeleton": assemble and assemble.get("n_skeleton"), "n_valid": assemble and assemble.get("n_valid"),
           "n_excluded": assemble and assemble.get("excluded_ids"),
           "agreement": agreement and {k: v for k, v in agreement.items() if k != "flags"},
           "seal_checks": seal_checks, "provenance": prov,
           "preregistration_sha256": hashlib.sha256(pre).hexdigest(),
           "rule": "Nobody connected to the mechanism reads eval3 contents before Phase 3 scoring. Only this record "
                   "(counts, statistics, hashes) is in the repository.",
           "human_validation": "none"}
    Path(a.out).write_text(json.dumps(out, indent=1) + "\n", encoding="utf-8")
    print(json.dumps({k: out[k] for k in ("status", "problems", "n_skeleton", "n_valid", "n_excluded")}, indent=1))
    return 0 if not problems else 4


if __name__ == "__main__":
    raise SystemExit(main())
