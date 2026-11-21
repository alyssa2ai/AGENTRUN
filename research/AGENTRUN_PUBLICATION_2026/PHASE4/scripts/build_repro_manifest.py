"""Refresh the reproducibility package's script/config copies and write its SHA-256 manifests.

    python build_repro_manifest.py <PHASE4 dir>

configs/   byte-identical copies of the frozen originals (verified, never redacted)
scripts/   copies of the Phase 3 analysis scripts with host identifiers redacted
slurm/     copies of the Slurm scripts with host identifiers redacted
SHA256SUMS          every file in the package
SHA256SUMS_SOURCES  the originals the copies were taken from, at their repository paths
"""
import hashlib
import re
import sys
from pathlib import Path

P4 = Path(sys.argv[1]).resolve()
PUB = P4.parent
P3 = PUB / "PHASE3"
P2 = PUB / "PHASE2"
R = P4 / "reproducibility"

REDACTIONS = [
    (re.compile(r"gpuuser12@192\.168\.192\.11"), "<user>@<cluster-login>"),
    (re.compile(r"gpuuser12@192\.168\.192\.9"), "<user>@<compute-node>"),
    (re.compile(r"192\.168\.192\.11"), "<cluster-login>"),
    (re.compile(r"192\.168\.192\.9"), "<compute-node>"),
    (re.compile(r"/home/gpuuser12"), "$HOME"),
    (re.compile(r"\bgpuuser12\b"), "<user>"),
    (re.compile(r"\bsitgpumaster\b"), "<cluster-login>"),
    (re.compile(r"\bsit-gpu\b"), "<compute-node>"),
    (re.compile(r"\bgpu-nodes\b"), "<partition>"),
]

BYTE_COPIES = {  # package path -> source path (must stay byte-identical)
    "configs/FREEZE_evarb.json": P2 / "FREEZE_evarb.json",
    "configs/FREEZE_eval3.json": P2 / "FREEZE_eval3.json",
    "configs/PREREGISTRATION.md": P2 / "PREREGISTRATION.md",
    "configs/PRIMARY_RULE_DECISION.md": P2 / "data/p2val2/PRIMARY_RULE_DECISION.md",
}
REDACTED_COPIES = {
    "scripts/finalize_gates.py": P3 / "scripts/finalize_gates.py",
    "scripts/finalize_gates_v1_frozen.py": P3 / "scripts/finalize_gates_v1_frozen.py",
    "scripts/platform_continuity.py": P3 / "scripts/platform_continuity.py",
    "scripts/verify_phase3.py": P3 / "scripts/verify_phase3.py",
    "scripts/crosscheck_phase3.py": P3 / "scripts/crosscheck_phase3.py",
    "scripts/phase3_metrics.py": P3 / "scripts/phase3_metrics.py",
    "scripts/build_reports.py": P3 / "scripts/build_reports.py",
    "scripts/write_results_section.py": P3 / "scripts/write_results_section.py",
    "scripts/agreed_ids_b.py": P3 / "scripts/agreed_ids_b.py",
    "scripts/run_phase3_analysis.sh": P3 / "scripts/run_phase3_analysis.sh",
    "scripts/assemble_manuscript.py": P4 / "scripts/assemble_manuscript.py",
    "slurm/phase3_finalize.sbatch": P3 / "scripts/phase3_finalize.sbatch",
}


def sha(p):
    return hashlib.sha256(Path(p).read_bytes()).hexdigest()


def redact(text):
    for pat, rep in REDACTIONS:
        text = pat.sub(rep, text)
    return text


problems = []

for rel, src in BYTE_COPIES.items():
    dst = R / rel
    if not src.exists():
        problems.append(f"missing source for {rel}: {src}")
        continue
    dst.parent.mkdir(parents=True, exist_ok=True)
    dst.write_bytes(src.read_bytes())
    if sha(dst) != sha(src):
        problems.append(f"byte copy mismatch: {rel}")

for rel, src in REDACTED_COPIES.items():
    dst = R / rel
    if not src.exists():
        problems.append(f"missing source for {rel}: {src}")
        continue
    dst.parent.mkdir(parents=True, exist_ok=True)
    dst.write_text(redact(src.read_text(encoding="utf-8")), encoding="utf-8")

# leftover copies whose source no longer exists (e.g. the old controller/eval3 sbatch files) are kept as they are,
# but they must still be free of host identifiers.
leak = re.compile(r"gpuuser12|192\.168\.192\.|sitgpumaster|sit-gpu")
for p in sorted(R.rglob("*")):
    if p.is_file() and p.name not in ("SHA256SUMS", "SHA256SUMS_SOURCES"):
        try:
            t = p.read_text(encoding="utf-8")
        except UnicodeDecodeError:
            continue
        if p.relative_to(R).as_posix().startswith("configs/"):
            continue  # frozen byte copies: never altered; checked separately below
        for m in set(leak.findall(t)):
            problems.append(f"host identifier '{m}' still present in {p.relative_to(R).as_posix()}")

# frozen config copies are byte-identical by definition; report (do not alter) any identifier they contain
for rel in BYTE_COPIES:
    t = (R / rel).read_text(encoding="utf-8", errors="replace")
    for m in sorted(set(leak.findall(t))):
        problems.append(f"NOTE frozen byte copy {rel} contains '{m}' (not altered: it must match the original)")

files = sorted(p for p in R.rglob("*") if p.is_file() and p.name not in ("SHA256SUMS", "SHA256SUMS_SOURCES"))
(R / "SHA256SUMS").write_text(
    "".join(f"{sha(p)}  {p.relative_to(R).as_posix()}\n" for p in files), encoding="utf-8")

lines = ["# Hashes of the repository originals from which this package's copies were made.",
         "# configs/ are byte-identical to these; scripts/ and slurm/ are the same files with host identifiers redacted.",
         ""]
for rel, src in list(BYTE_COPIES.items()) + list(REDACTED_COPIES.items()):
    if src.exists():
        lines.append(f"{sha(src)}  {src.relative_to(PUB).as_posix()}   -> {rel}")
(R / "SHA256SUMS_SOURCES").write_text("\n".join(lines) + "\n", encoding="utf-8")

print(f"package files hashed: {len(files)}")
print(f"byte copies verified: {len(BYTE_COPIES)}; redacted copies refreshed: {len(REDACTED_COPIES)}")
for x in problems:
    print("  " + x)
print("RESULT:", "PASS" if not [x for x in problems if not x.startswith("NOTE")] else "ATTENTION")
