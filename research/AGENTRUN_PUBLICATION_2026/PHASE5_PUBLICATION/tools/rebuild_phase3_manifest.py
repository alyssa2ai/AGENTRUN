"""Rebuild PHASE3_SHA256_MANIFEST.txt from a local checkout.

    python rebuild_phase3_manifest.py <PUBLICATION dir>

Mirrors the seal stage of `PHASE3/scripts/phase3_finalize.sbatch`, with two differences: the raw-cell and sealed
eval3 sections are carried over verbatim from the existing manifest (those files live only on the cluster), and the
output is written with LF endings so `sha256sum -c` works on a Windows checkout too.
"""
from __future__ import annotations

import hashlib
import sys
from pathlib import Path

PUB = Path(sys.argv[1]).resolve()
P3 = PUB / "PHASE3"
MAN = P3 / "PHASE3_SHA256_MANIFEST.txt"


def sha(p: Path) -> str:
    return hashlib.sha256(p.read_bytes()).hexdigest()


old = MAN.read_text(encoding="utf-8").splitlines() if MAN.exists() else []
carried: list[str] = []
section = None
for line in old:
    if line.startswith("## "):
        section = line
    if section is not None and section.startswith(("## raw cells", "## sealed eval3")):
        carried.append(line)
    if line.startswith("## outputs"):
        break

out: list[str] = ["# Phase 3 SHA-256 manifest (rebuilt from the local checkout after the privacy scrub; "
                  "analysis outputs unchanged since finalization job 4359)"]
out += carried
out.append("## outputs")

for d in ("ANALYSIS", "results", "scripts", "tests"):
    root = P3 / d
    if not root.exists():
        continue
    for p in sorted(root.rglob("*")):
        if p.is_file() and "DRYRUN" not in p.parts and p.suffix != ".pyc" and "__pycache__" not in p.parts:
            out.append(f"{sha(p)}  {p.relative_to(P3).as_posix()}")

for p in sorted(P3.glob("PHASE3_*.md")) + [P3 / "PHASE3_DECISIONS.json", P3 / "platform_evidence.json",
                                           P3 / "LIMITATIONS.md"]:
    if p.exists():
        out.append(f"{sha(p)}  {p.relative_to(P3).as_posix()}")

for sub in ("PHASE4/manuscript", "PHASE4/scripts", "PHASE5_PUBLICATION/tools"):
    root = PUB / sub
    if not root.exists():
        continue
    for p in sorted(root.rglob("*")):
        if p.is_file() and p.suffix != ".pyc" and "__pycache__" not in p.parts and p.name != "redaction_identifiers.json":
            out.append(f"{sha(p)}  {p.relative_to(PUB).as_posix()}")

rs = PUB / "PHASE4/reproducibility/SHA256SUMS"
if rs.exists():
    out.append(f"{sha(rs)}  PHASE4/reproducibility/SHA256SUMS")

with open(MAN, "w", encoding="utf-8", newline="\n") as f:
    f.write("\n".join(out) + "\n")
print(f"wrote {MAN.name}: {len(out)} lines")
