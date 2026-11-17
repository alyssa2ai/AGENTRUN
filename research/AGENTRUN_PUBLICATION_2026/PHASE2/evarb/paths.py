"""Put the frozen harness and the Phase 1 prototype on sys.path (read-only use)."""
import sys
from pathlib import Path

PHASE2 = Path(__file__).resolve().parents[1]
PUB = PHASE2.parent
PHASE1_PROTO = PUB / "PHASE1" / "prototype"
DEEP_SCRIPTS = PUB.parent / "AGENTRUN_DEEPENING_2026-11-11" / "scripts"
for p in (DEEP_SCRIPTS, PHASE1_PROTO):
    if str(p) not in sys.path:
        sys.path.insert(0, str(p))
