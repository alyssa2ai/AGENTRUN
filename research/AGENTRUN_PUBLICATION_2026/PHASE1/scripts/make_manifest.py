"""Write PHASE1/HASH_MANIFEST.txt: sha256 of every file under PHASE1 (except the manifest itself).

    py -3.11 PHASE1/scripts/make_manifest.py          # write
    py -3.11 PHASE1/scripts/make_manifest.py --check  # verify the working tree against it

Hashes are checkout-independent and equal to the sha256 of the git blob content:
  *.jsonl   raw bytes (these are `-text` in .gitattributes, never converted)
  others    content with CRLF normalised to LF (git stores them with LF; Windows
            checkouts with core.autocrlf=true have CRLF in the working tree)
The manifest is written with LF line endings.
"""
import hashlib
import sys
from pathlib import Path

P1 = Path(__file__).resolve().parents[1]


def digest(p: Path) -> str:
    b = p.read_bytes()
    if p.suffix != ".jsonl":
        b = b.replace(b"\r\n", b"\n")
    return hashlib.sha256(b).hexdigest()


def files():
    return sorted(p for p in P1.rglob("*") if p.is_file() and p.name != "HASH_MANIFEST.txt"
                  and "__pycache__" not in p.parts and ".pytest_cache" not in p.parts)


if __name__ == "__main__":
    man = P1 / "HASH_MANIFEST.txt"
    if "--check" in sys.argv:
        want = dict(reversed(line.split("  ", 1)) for line in man.read_text(encoding="utf-8").splitlines() if line)
        have = {f.relative_to(P1).as_posix(): digest(f) for f in files()}
        bad = sorted(k for k in set(want) | set(have) if want.get(k) != have.get(k))
        print(f"{len(have) - len(bad)} ok, {len(bad)} differ", *bad, sep="\n")
        sys.exit(1 if bad else 0)
    lines = [f"{digest(f)}  {f.relative_to(P1).as_posix()}" for f in files()]
    man.write_bytes(("\n".join(lines) + "\n").encode("utf-8"))
    print(len(lines), "files")
