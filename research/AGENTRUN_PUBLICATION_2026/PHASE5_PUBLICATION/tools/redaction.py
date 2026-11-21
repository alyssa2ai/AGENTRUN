"""Shared redaction patterns, loaded from a local config so that no tracked file holds a real identifier.

Copy `redaction_identifiers.example.json` to `redaction_identifiers.json`, fill in the real host names, addresses
and account names, and keep that copy out of version control (`.gitignore` already excludes it).
"""
from __future__ import annotations

import json
import re
from pathlib import Path

CONFIG = Path(__file__).resolve().parent / "redaction_identifiers.json"
EXAMPLE = Path(__file__).resolve().parent / "redaction_identifiers.example.json"


def load(required: bool = True):
    """Return (replacements, detect_regex). replacements is a list of (compiled pattern, replacement)."""
    if not CONFIG.exists():
        if required:
            raise SystemExit(
                f"redaction config not found: {CONFIG}\n"
                f"Copy {EXAMPLE.name} to {CONFIG.name}, fill in the real identifiers, and re-run. "
                f"The filled copy is gitignored on purpose.")
        return [], re.compile(r"(?!x)x")  # matches nothing
    cfg = json.loads(CONFIG.read_text(encoding="utf-8"))
    reps = [(re.compile(p), r) for p, r in cfg["replacements"]]
    return reps, re.compile(cfg["detect"])


def redact(text: str, reps=None) -> str:
    if reps is None:
        reps, _ = load()
    for pat, rep in reps:
        text = pat.sub(rep, text)
    return text
