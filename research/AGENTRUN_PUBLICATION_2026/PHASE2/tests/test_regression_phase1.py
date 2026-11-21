"""Regression tests: every Phase 1 failure that a resolution mechanism made, as an explicit case.

Groups are rebuilt from the frozen Phase 1 split builders (p1dev hash 94fe396f..., p1hold
f747fbfa...), not copied, so these tests also fail if those builders drift.
"""
import json
from pathlib import Path

import pytest

from evarb import paths  # noqa: F401
from evarb.arbiter import arbitrate
import p1hold
import rcs

P2 = Path(__file__).resolve().parents[1]


def groups(tasks, prefix):
    out = []
    for t in tasks:
        if not t["scenario"].startswith(prefix):
            continue
        mem = {r["record_id"]: r for r in t["memory"]}
        g0 = mem[t["gold_record_ids"][0]]
        out.append((t, [r for r in t["memory"] if (r["entity"], r["attribute"]) == (g0["entity"], g0["attribute"])]))
    return out


HOLD = p1hold.build_p1hold()
DEV = rcs.build_p1dev()


def test_split_hashes_unchanged():
    frozen = json.loads((paths.PHASE1_PROTO / "FREEZE_p1hold.json").read_text())
    import hashlib
    blob = "\n".join(json.dumps(t, sort_keys=True) for t in HOLD).encode()
    assert hashlib.sha256(blob).hexdigest() == frozen["split_sha256"]


@pytest.mark.parametrize("t,grp", groups(HOLD, "N3"), ids=lambda x: x["task_id"] if isinstance(x, dict) else "")
def test_p1hold_N3_negated_cue_is_not_resolved(t, grp):
    """The six Phase 1 false resolutions (TEA labelled N3 current/superseded; RT then forced arbitrary picks)."""
    x = arbitrate(grp)
    assert x.kind == "contradiction" and x.current_value is None


@pytest.mark.parametrize("prefix,tasks", [("S7", DEV), ("S8", DEV), ("H7a", HOLD), ("H8a", HOLD), ("H9", HOLD), ("H7b", HOLD)])
def test_metadata_insufficient_groups_resolve_to_expected(prefix, tasks):
    for t, grp in groups(tasks, prefix):
        x = arbitrate(grp)
        assert x.kind == "resolved", t["task_id"]
        assert str(x.current_value) == str(t["expected"]["value"]), t["task_id"]


def test_H7b_unreferenced_corrections_are_not_enforceable():
    for t, grp in groups(HOLD, "H7b"):
        assert arbitrate(grp).strength == "moderate", t["task_id"]


@pytest.mark.parametrize("prefix", ["S3", "N1", "N2"])
def test_genuine_conflicts_stay_conflicts(prefix):
    tasks = DEV if prefix == "S3" else HOLD
    for t, grp in groups(tasks, prefix):
        assert arbitrate(grp).kind == "contradiction", t["task_id"]


def test_S4_and_C4_metadata_order_unchanged():
    for tasks, prefix in ((DEV, "S4"), (HOLD, "C4")):
        for t, grp in groups(tasks, prefix):
            x = arbitrate(grp)
            assert x.kind == "resolved" and str(x.current_value) == str(t["expected"]["value"]), t["task_id"]
