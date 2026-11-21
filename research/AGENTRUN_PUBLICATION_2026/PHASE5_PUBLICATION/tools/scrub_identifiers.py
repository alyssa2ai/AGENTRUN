"""Replace cluster identifiers with placeholders in the repository's prose and scripts.

    python scrub_identifiers.py --root <repo root> [--apply] [--report <file>]

Policy (see PHASE5_PUBLICATION/PRIVACY_SCRUB_REPORT.md):

  SCRUBBED    human-readable documentation and executable scripts: .md .sh .sbatch .py .tex .txt .yml .yaml
              These are the publicly distributable parts of the repository.

  PRESERVED   integrity-bearing research artifacts: run manifests, raw results, scorer outputs, cluster job logs
              and summary tables. Their bytes are hashed in FREEZE_* / SHA256SUMS files and in the Phase 3
              manifest, so editing them would break the chain of custody of the experiment. They are already
              classified as RESTRICTED (not publicly released) in the artifact-availability policy, and the
              publication package contains none of them.

  EXEMPT      files whose purpose is redaction itself, which must keep the literal patterns to work.

The replacements are deliberately readable rather than hashed, so that a reader can still follow the operational
narrative (which host did what) without learning the real names or addresses.
"""
from __future__ import annotations

import argparse
import re
import subprocess
from pathlib import Path

import redaction  # same directory; patterns come from the gitignored local config

REPLACEMENTS, DETECT = redaction.load()

SCRUB_SUFFIXES = {".md", ".sh", ".sbatch", ".py", ".tex", ".txt", ".yml", ".yaml", ".cfg", ".toml"}

# Directory segments holding integrity-bearing artifacts that must keep their original bytes.
PRESERVE_DIR_PARTS = {"raw", "raw_pilot", "raw_results", "logs", "from_cluster", "tables", "sealed", "SEALED_LOCAL",
                      "RAW_RESULTS", "build"}
PRESERVE_SUFFIXES = {".jsonl", ".out", ".err", ".csv"}

# Files that must keep the literal identifiers to do their job.
EXEMPT: set[str] = set()  # the patterns now live in a gitignored config, so no tracked file needs an exemption

# Documentation-grade JSON that is part of the written record rather than an experiment artifact.
SCRUB_JSON_ALLOWLIST = {
    "research/AGENTRUN_PUBLICATION_2026/PHASE3/platform_evidence.json",
    "research/AGENTRUN_PUBLICATION_2026/PHASE3/ANALYSIS/PLATFORM_CONTINUITY.json",
}


def classify(rel: str) -> str:
    p = Path(rel)
    if rel in EXEMPT:
        return "exempt"
    if rel in SCRUB_JSON_ALLOWLIST:
        return "scrub"
    # Prose and executable scripts are scrubbed wherever they live: a generated .tex dossier or a markdown table
    # under build/ is still a document, not an experiment artifact.
    if p.suffix in SCRUB_SUFFIXES:
        return "scrub"
    parts = set(p.parts[:-1])
    if parts & PRESERVE_DIR_PARTS:
        return "preserve"
    if p.suffix in PRESERVE_SUFFIXES or p.suffix == ".json":
        return "preserve"
    return "preserve"


def main() -> int:
    ap = argparse.ArgumentParser()
    ap.add_argument("--root", required=True)
    ap.add_argument("--apply", action="store_true")
    ap.add_argument("--report")
    a = ap.parse_args()
    root = Path(a.root).resolve()

    out = subprocess.run(["git", "grep", "-l", "-E", DETECT.pattern, "--", "."],
                         cwd=root, capture_output=True, text=True)
    files = [x for x in out.stdout.splitlines() if x.strip()]

    scrubbed, preserved, exempt, errors = [], [], [], []
    for rel in files:
        kind = classify(rel)
        p = root / rel
        if kind == "exempt":
            exempt.append(rel)
            continue
        if kind == "preserve":
            preserved.append(rel)
            continue
        try:
            text = p.read_text(encoding="utf-8")
        except (UnicodeDecodeError, OSError) as e:
            errors.append(f"{rel}: {e}")
            continue
        new = text
        counts = {}
        for pat, rep in REPLACEMENTS:
            new, n = pat.subn(rep, new)
            if n:
                counts[pat.pattern] = counts.get(pat.pattern, 0) + n
        if new != text:
            if a.apply:
                p.write_text(new, encoding="utf-8")
            scrubbed.append((rel, sum(counts.values())))
        left = DETECT.findall(new)
        if left:
            errors.append(f"{rel}: {len(left)} identifier(s) still present after substitution")

    lines = ["# Privacy scrub report", "",
             f"Mode: {'APPLIED' if a.apply else 'DRY RUN'}", "",
             f"- files containing a cluster identifier: **{len(files)}**",
             f"- scrubbed (documentation and scripts): **{len(scrubbed)}**",
             f"- preserved (integrity-bearing research artifacts, restricted, never published): **{len(preserved)}**",
             f"- exempt (redaction tooling, must keep the literal patterns): **{len(exempt)}**",
             f"- errors: **{len(errors)}**", ""]
    lines += ["## Scrubbed", "", "| File | Replacements |", "|---|---:|"]
    lines += [f"| `{r}` | {n} |" for r, n in sorted(scrubbed)]
    lines += ["", "## Preserved (restricted artifacts; bytes unchanged so their recorded hashes still verify)", ""]
    lines += [f"- `{r}`" for r in sorted(preserved)]
    lines += ["", "## Exempt", ""] + [f"- `{r}`" for r in sorted(exempt)]
    if errors:
        lines += ["", "## Errors", ""] + [f"- {e}" for e in errors]
    text = "\n".join(lines) + "\n"
    if a.report:
        Path(a.report).write_text(text, encoding="utf-8")
    print(f"files with identifiers: {len(files)}; scrubbed: {len(scrubbed)}; preserved: {len(preserved)}; "
          f"exempt: {len(exempt)}; errors: {len(errors)}"
          + ("" if a.apply else "   (dry run; pass --apply to write)"))
    for e in errors:
        print("  ERROR " + e)
    return 1 if errors else 0


if __name__ == "__main__":
    raise SystemExit(main())
