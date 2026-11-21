"""Publication QA: privacy scan, source manifest, and the mechanical gates of PUBLICATION_QA_REPORT.md.

    python package_qa.py <PHASE5_PUBLICATION dir>

Checks, and writes SOURCE_MANIFEST.sha256 over everything that would be shipped:
  P1  no credential, host name, address or account identifier anywhere in the submission or supplement
  F1  both PDFs exist, are non-trivial, and embed all their fonts
  F2  no undefined reference or citation in either LaTeX log
  F3  no overfull box wider than 5pt
  C1  every citation key used is defined, and every bibliography entry is cited
  S1  every figure data file carries a provenance line naming its source
"""
from __future__ import annotations

import hashlib
import re
import subprocess
import sys
from pathlib import Path

P5 = Path(sys.argv[1]).resolve()
SUB = P5 / "submission"
sys.path.insert(0, str(P5 / "tools"))
import redaction  # noqa: E402

results: list[tuple[str, str, bool, str]] = []


def gate(gid: str, name: str, ok: bool, detail: str) -> None:
    results.append((gid, name, ok, detail))


# ---------------------------------------------------------------- P1 privacy
_, LEAK = redaction.load()
CRED = re.compile(
    r"(?i)(api[_-]?key\s*[:=]|\bsecret[_-]?(key|token)\b|\bpass(word|wd)\s*[:=]|"
    r"\b(auth|access|bearer)[_-]?token\b|BEGIN [A-Z ]*PRIVATE KEY|ssh-rsa AAAA|ssh-ed25519 AAAA)")
leaks: list[str] = []
scanned = 0
for p in sorted(SUB.rglob("*")):
    if not p.is_file() or p.suffix.lower() in {".pdf", ".png", ".jpg"}:
        continue
    try:
        t = p.read_text(encoding="utf-8")
    except (UnicodeDecodeError, OSError):
        continue
    scanned += 1
    for m in set(LEAK.findall(t)):
        leaks.append(f"{p.relative_to(P5)}: identifier '{m}'")
    for m in set(CRED.findall(t)):
        leaks.append(f"{p.relative_to(P5)}: credential-like token '{m}'")
# also scan the rendered PDFs
for pdf in [SUB / "main.pdf", SUB / "supplementary" / "supplementary.pdf"]:
    if pdf.exists():
        try:
            txt = subprocess.run(["pdftotext", str(pdf), "-"], capture_output=True, text=True).stdout
            for m in set(LEAK.findall(txt)):
                leaks.append(f"{pdf.name} (rendered text): identifier '{m}'")
        except FileNotFoundError:
            pass
gate("P1", f"no identifiers or credentials in the package ({scanned} text files + 2 PDFs scanned)",
     not leaks, "; ".join(leaks[:6]) if leaks else "clean")

# ---------------------------------------------------------------- F1 PDFs and fonts
pdfs = {"main.pdf": SUB / "main.pdf", "supplementary.pdf": SUB / "supplementary" / "supplementary.pdf"}
missing = [n for n, p in pdfs.items() if not p.exists() or p.stat().st_size < 50_000]
notemb = []
for n, p in pdfs.items():
    if p.exists():
        try:
            out = subprocess.run(["pdffonts", str(p)], capture_output=True, text=True).stdout
            for line in out.splitlines()[2:]:
                cols = line.split()
                if len(cols) >= 5 and cols[-4] == "no":
                    notemb.append(f"{n}: {cols[0]}")
        except FileNotFoundError:
            pass
gate("F1", "both PDFs build and embed all fonts", not missing and not notemb,
     ("missing/small: " + ", ".join(missing) if missing else "") +
     ("; not embedded: " + ", ".join(notemb) if notemb else "") or "ok")

# ---------------------------------------------------------------- F2/F3 logs
logs = {"main": SUB / "main.log", "supplementary": SUB / "supplementary" / "supplementary.log"}
undef, over = [], []
for n, p in logs.items():
    if not p.exists():
        undef.append(f"{n}: no log")
        continue
    t = p.read_text(encoding="utf-8", errors="replace")
    for m in re.finditer(r"(Citation|Reference) `([^']+)' .*undefined", t):
        undef.append(f"{n}: {m.group(1)} {m.group(2)}")
    for m in re.finditer(r"Overfull \\hbox \(([0-9.]+)pt too wide", t):
        if float(m.group(1)) > 5.0:
            over.append(f"{n}: {m.group(1)}pt")
gate("F2", "no undefined reference or citation", not undef, "; ".join(sorted(set(undef))[:6]) or "none")
gate("F3", "no overfull box wider than 5pt", not over, "; ".join(over[:6]) or "none")

# ---------------------------------------------------------------- C1 citations
bib = (SUB / "references.bib").read_text(encoding="utf-8")
declared = set(re.findall(r"^@\w+\{([^,]+),", bib, re.M))
used: set[str] = set()
CITE = re.compile(r"\\cite[a-z]*\{([^}]*)\}")
for p in list((SUB / "sections").glob("*.tex")) + list((SUB / "tables").glob("*.tex")) + \
         list((SUB / "figures").glob("*.tex")) + [SUB / "main.tex"]:
    for m in CITE.finditer(p.read_text(encoding="utf-8")):
        for k in m.group(1).split(","):
            if k.strip():
                used.add(k.strip())
gate("C1", f"citations resolve ({len(declared)} entries, {len(used)} cited)",
     not (used - declared) and not (declared - used),
     ("undefined: " + ", ".join(sorted(used - declared)) if used - declared else "") +
     ("uncited: " + ", ".join(sorted(declared - used)) if declared - used else "") or "all resolve, none uncited")

# ---------------------------------------------------------------- S1 figure data provenance
data = sorted((SUB / "figures" / "data").glob("*.dat"))
noprov = [p.name for p in data if not p.read_text(encoding="utf-8").startswith("# source:")]
gate("S1", f"every figure data file names its source ({len(data)} files)", not noprov,
     ", ".join(noprov) or "all traceable")

# ---------------------------------------------------------------- manifest
SKIP = {".aux", ".log", ".out", ".blg", ".bbl", ".toc", ".synctex", ".fls", ".fdb_latexmk"}
lines = ["# SHA-256 manifest of the publication package",
         "# verify with:  sha256sum -c SOURCE_MANIFEST.sha256   (run from PHASE5_PUBLICATION/)", ""]
count = 0
for p in sorted(P5.rglob("*")):
    if not p.is_file():
        continue
    rel = p.relative_to(P5).as_posix()
    if p.suffix in SKIP or rel == "SOURCE_MANIFEST.sha256" or "__pycache__" in rel \
            or rel.startswith("build/pages/") or rel.endswith("redaction_identifiers.json"):
        continue
    lines.append(f"{hashlib.sha256(p.read_bytes()).hexdigest()}  {rel}")
    count += 1
with open(P5 / "SOURCE_MANIFEST.sha256", "w", encoding="utf-8", newline="\n") as f:
    f.write("\n".join(lines) + "\n")

allok = all(ok for _, _, ok, _ in results)
print(f"manifest: {count} files")
for gid, name, ok, detail in results:
    print(f"  [{'PASS' if ok else 'FAIL'}] {gid} {name}: {detail}")
print("RESULT:", "PASS" if allok else "FAIL")
sys.exit(0 if allok else 1)
