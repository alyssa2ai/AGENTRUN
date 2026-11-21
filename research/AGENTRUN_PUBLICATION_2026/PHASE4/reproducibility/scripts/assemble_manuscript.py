"""Assemble the manuscript and check its citations.

    python assemble_manuscript.py --manuscript <PHASE4/manuscript> --out MANUSCRIPT.md --report CITATION_CHECK.md

Concatenates the section files in reading order into one document, then checks:
  * every pandoc citation key [@key] used in the text has an entry in references.bib;
  * every entry in references.bib is either cited or listed below as intentionally uncited;
  * no [CITATION NEEDED] or [RESULTS PENDING] placeholder survives.
Exits 1 if any check fails.
"""
import argparse
import re
import sys
from pathlib import Path

ORDER = [
    "00_title_and_abstract.md",
    "01_introduction.md",
    "02_related_work.md",
    "03_method_evarb.md",
    "04_experimental_design.md",
    "05_dataset.md",
    "06_implementation.md",
    "07_results.md",
    "08_statistical_analysis.md",
    "09_ablation_studies.md",
    "10_failure_analysis.md",
    "11_platform_and_resume_deviation.md",
    "12_discussion.md",
    "13_threats_and_limitations.md",
    "14_reproducibility.md",
    "15_conclusion.md",
]
# Entries kept in the bibliography although nothing cites them, with the reason.
INTENTIONALLY_UNCITED: dict[str, str] = {}

CITE = re.compile(r"\[@([^\]]+)\]|(?<![\w@])@([A-Za-z][A-Za-z0-9_:.-]*\d{4}[A-Za-z0-9_:.-]*)")
BIBKEY = re.compile(r"^@\w+\{([^,]+),", re.M)
PLACEHOLDER = re.compile(r"\[(CITATION NEEDED|RESULTS PENDING)[^\]]*\]")


def main():
    ap = argparse.ArgumentParser()
    ap.add_argument("--manuscript", required=True)
    ap.add_argument("--out", required=True)
    ap.add_argument("--report", required=True)
    a = ap.parse_args()
    M = Path(a.manuscript)

    missing_files = [f for f in ORDER if not (M / f).exists()]
    parts, used = [], {}
    for f in ORDER:
        p = M / f
        if not p.exists():
            continue
        text = p.read_text(encoding="utf-8")
        parts.append(text.rstrip() + "\n")
        for m in CITE.finditer(text):
            group = m.group(1) or m.group(2)
            for key in re.split(r"[;,]", group):
                key = key.strip().lstrip("@").split(" ")[0].strip(" .,;")
                if key:
                    used.setdefault(key, set()).add(f)

    bib = M / "references.bib"
    declared = set(BIBKEY.findall(bib.read_text(encoding="utf-8"))) if bib.exists() else set()

    body = "\n\n".join(parts)
    Path(a.out).write_text(body + "\n", encoding="utf-8")

    undefined = sorted(set(used) - declared)
    uncited = sorted(declared - set(used) - set(INTENTIONALLY_UNCITED))
    placeholders = []
    for f in ORDER:
        p = M / f
        if p.exists():
            for i, line in enumerate(p.read_text(encoding="utf-8").splitlines(), 1):
                for m in PLACEHOLDER.finditer(line):
                    placeholders.append(f"{f}:{i}: {m.group(0)}")

    ok = not (undefined or uncited or placeholders or missing_files)
    L = ["# Citation and placeholder check", "",
         f"- section files assembled: **{len(parts)} of {len(ORDER)}**",
         f"- bibliography entries: **{len(declared)}**",
         f"- distinct citation keys used in the text: **{len(used)}**",
         f"- undefined citation keys (used but not in references.bib): **{len(undefined)}**",
         f"- uncited bibliography entries: **{len(uncited)}**",
         f"- surviving placeholders: **{len(placeholders)}**", ""]
    if missing_files:
        L += ["## Missing section files", ""] + [f"- `{f}`" for f in missing_files] + [""]
    if undefined:
        L += ["## Undefined citation keys", ""] + [f"- `{k}` (used in {', '.join(sorted(used[k]))})" for k in undefined] + [""]
    if uncited:
        L += ["## Uncited bibliography entries", ""] + [f"- `{k}`" for k in uncited] + [""]
    if INTENTIONALLY_UNCITED:
        L += ["## Intentionally listed but uncited", ""] + [f"- `{k}`: {v}" for k, v in INTENTIONALLY_UNCITED.items()] + [""]
    if placeholders:
        L += ["## Surviving placeholders", ""] + [f"- {x}" for x in placeholders] + [""]
    L += ["## Citation usage", "", "| key | sections |", "|---|---|"]
    for k in sorted(used):
        L.append(f"| `{k}` | {', '.join(sorted(s.split('_')[0] for s in used[k]))} |")
    L += ["", f"**Result: {'PASS' if ok else 'FAIL'}**"]
    Path(a.report).write_text("\n".join(L) + "\n", encoding="utf-8")
    print(f"assembled {len(parts)}/{len(ORDER)} sections -> {a.out}; "
          f"{len(declared)} bib entries, {len(used)} cited, {len(undefined)} undefined, "
          f"{len(uncited)} uncited, {len(placeholders)} placeholders: {'PASS' if ok else 'FAIL'}")
    for x in undefined:
        print("  UNDEFINED " + x)
    for x in uncited:
        print("  UNCITED " + x)
    for x in placeholders:
        print("  PLACEHOLDER " + x)
    for x in missing_files:
        print("  MISSING SECTION " + x)
    return 0 if ok else 1


if __name__ == "__main__":
    sys.exit(main())
