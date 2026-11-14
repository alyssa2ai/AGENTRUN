"""Deterministic fixture tests for TEA (no LLM).

    py -3.11 -m pytest PHASE1/prototype/test_tea.py -q
"""
import sys
from pathlib import Path

sys.path.insert(0, str(Path(__file__).resolve().parent))
import rcs  # noqa: E402
import tea  # noqa: E402

memlab = rcs.memlab
E, A = "Project Zalor", "team_size"


def rec(rid, v, d, text=None, a=A):
    return {"record_id": rid, "entity": E, "attribute": a, "value": v, "recorded_on": d, "source": "imported_doc",
            "text": text or memlab.ATTRS[a]["t"].format(e=E, v=v)}


def st(group):
    return {k: v["status"] for k, v in tea.arbitrate(group).items()}


def test_metadata_order_unchanged():
    g = [rec("m-01", 12, "2026-05-01"), rec("m-02", 17, "2026-07-01")]
    assert st(g) == {"m-01": "superseded", "m-02": "current"}
    assert all(tea.reliability_status(r, g)["status"] == memlab.reliability_status(r, g)["status"] for r in g)


def test_true_conflict_stays_conflict():
    g = [rec("m-01", 12, "2026-05-01"), rec("m-02", 17, "2026-05-01")]
    out = tea.arbitrate(g)
    assert {v["status"] for v in out.values()} == {"conflicting"}
    assert out["m-01"]["basis"] == "no_ordering_evidence"


def test_same_day_correction_naming_old_value():
    g = [rec("m-01", 12, "2026-05-01"),
         rec("m-02", 17, "2026-05-01", "Correction: Project Zalor has a team of 17 people. The 12 was a mistake.")]
    out = tea.arbitrate(g)
    assert out["m-02"]["status"] == "current" and out["m-01"]["status"] == "superseded"
    assert out["m-01"]["basis"] == "explicit_correction"


def test_correction_without_old_value_is_not_resolved():
    g = [rec("m-01", 12, "2026-05-01"), rec("m-02", 17, "2026-05-01", "Correction: Project Zalor has a team of 17.")]
    assert set(st(g).values()) == {"conflicting"}


def test_text_valid_dates_order_same_import_day():
    g = [rec("m-01", 12, "2026-09-01", "As of 2026-03-01: Project Zalor has a team of 12 people."),
         rec("m-02", 17, "2026-09-01", "Effective 4 June 2026: Project Zalor has a team of 17 people.")]
    assert st(g) == {"m-01": "superseded", "m-02": "current"}


def test_text_valid_date_overrides_backfilled_metadata():
    g = [rec("m-01", 17, "2026-06-05", "As of 2026-06-01: Project Zalor has a team of 17 people."),
         rec("m-02", 12, "2026-07-20", "As of 2026-02-01: Project Zalor has a team of 12 people.")]
    out = tea.arbitrate(g)
    assert out["m-01"]["status"] == "current" and out["m-02"]["status"] == "superseded"
    assert "differs from recorded_on" in out["m-01"]["note"]


def test_partial_text_dates_fall_back_to_metadata():
    g = [rec("m-01", 12, "2026-05-01", "As of 2026-09-01: Project Zalor has a team of 12 people."),
         rec("m-02", 17, "2026-07-01")]
    assert st(g) == {"m-01": "superseded", "m-02": "current"}


def test_deadline_value_is_not_a_validity_date():
    a = "deadline"
    g = [rec("m-01", "2027-01-10", "2026-05-01", a=a), rec("m-02", "2027-03-01", "2026-05-01", a=a)]
    assert set(st(g).values()) == {"conflicting"}


def test_same_text_date_is_conflict():
    g = [rec("m-01", 12, "2026-05-01", "As of 2026-05-01: Project Zalor has a team of 12 people."),
         rec("m-02", 17, "2026-05-01", "As of 2026-05-01: Project Zalor has a team of 17 people.")]
    assert set(st(g).values()) == {"conflicting"}


def test_known_blind_spot_negation():
    """Documented limitation: a negated cue that names the rival value is read as a correction."""
    g = [rec("m-01", 12, "2026-05-01"),
         rec("m-02", 17, "2026-05-01", "Project Zalor has a team of 17 people. This does not replace the 12.")]
    assert st(g)["m-02"] == "current"


def test_tea_swap_is_restored():
    orig = memlab.reliability_status
    with tea.tea_labels():
        assert memlab.reliability_status is tea.reliability_status
    assert memlab.reliability_status is orig
