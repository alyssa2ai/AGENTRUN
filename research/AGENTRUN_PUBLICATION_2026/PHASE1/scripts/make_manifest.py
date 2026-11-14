"""Write PHASE1/HASH_MANIFEST.txt: sha256 of every file under PHASE1 (except the manifest itself).

    py -3.11 PHASE1/scripts/make_manifest.py
"""
import hashlib
from pathlib import Path

P1 = Path(__file__).resolve().parents[1]
lines = []
for f in sorted(p for p in P1.rglob("*") if p.is_file() and p.name != "HASH_MANIFEST.txt"
                and "__pycache__" not in p.parts and ".pytest_cache" not in p.parts):
    lines.append(f"{hashlib.sha256(f.read_bytes()).hexdigest()}  {f.relative_to(P1).as_posix()}")
(P1 / "HASH_MANIFEST.txt").write_text("\n".join(lines) + "\n", encoding="utf-8")
print(len(lines), "files")
