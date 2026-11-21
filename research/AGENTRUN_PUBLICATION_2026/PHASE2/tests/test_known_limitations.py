"""Known failures of the FROZEN evarb-0.2, kept as regression cases (NEGATION_AND_CONFLICT_TESTS.md §4).

These tests assert the CURRENT (wrong) behaviour, so that:
  * the suite stays green while evarb-0.2 is frozen and the failure stays documented, and
  * any change to the behaviour (i.e. a new development version) makes the test fail and forces the
    limitation to be re-assessed and the documents updated.
The intended behaviour is stated in each test. evarb-0.2 must not be modified to fix them; a fix is a new
development version (evarb-0.3) evaluated on fresh data.
"""
from evarb import EVARB_VERSION
from evarb.arbiter import arbitrate


def _pair(text_b, date_b="2026-05-01"):
    return [{"record_id": "a", "entity": "Project X", "attribute": "team_size", "value": 40,
             "text": "Project X has a team of 40.", "source": "meeting_notes", "recorded_on": "2026-05-01"},
            {"record_id": "b", "entity": "Project X", "attribute": "team_size", "value": 60,
             "text": text_b, "source": "meeting_notes", "recorded_on": date_b}]


def test_version_is_frozen_evarb_02():
    assert EVARB_VERSION == "evarb-0.2"


def test_LIMITATION_long_range_negation_read_as_strong_correction():
    # Intended: the negation scopes over "revised", so record b does not establish 60 -> 40 stands (or unresolved),
    # never a STRONG resolution to 60. Actual (evarb-0.2): negation window is 4 tokens before the cue, so the cue
    # "revised ... from 40 to 60" is read as an asserted same-day correction.
    r = arbitrate(_pair("It is not the case that, after the long review in the spring, the team of Project X "
                        "was revised from 40 to 60."))
    assert (r.kind, r.basis, r.strength, r.current_value) == ("resolved", "same_day_correction", "strong", 60)


def test_short_range_negation_is_handled_contrast():
    # The same content with the negator inside the window behaves as intended (rival stands, not strong 60).
    r = arbitrate(_pair("The team of Project X was not revised from 40 to 60."))
    assert not (r.current_value == 60 and r.strength == "strong")


def test_LIMITATION_negated_both_stand_resolved_to_rival_p2val2():
    # Found on p2val2 (validation of the frozen 0.2), category negated_both_stand: 0/4.
    # Intended: "does not replace X" + "both figures stand until reconciled" -> contradiction.
    # Actual: the contradiction marker is detected, but the 0.2 rule "own value asserted only inside a negated
    # replacement -> set aside" ignores it, so the rival stands (moderate, advisory only).
    g = [{"record_id": "a", "entity": "Project R", "attribute": "lead", "value": "Pavel Teralt", "recorded_on": "2026-05-26",
          "source": "meeting_notes", "text": "Project R's project lead is Pavel Teralt."},
         {"record_id": "b", "entity": "Project R", "attribute": "lead", "value": "Elif Thioquux", "recorded_on": "2026-05-26",
          "source": "imported_doc", "text": "Project R has Elif Thioquux as the project lead, but this does not replace "
                                            "Pavel Teralt. Both figures stand until they are reconciled."}]
    r = arbitrate(g)
    assert (r.kind, r.strength, r.current_value) == ("resolved", "moderate", "Pavel Teralt")


def test_LIMITATION_correcting_not_a_correction_cue_p2val2():
    # Found on p2val2-0005 (same_day_correction_noref). Intended: the same-day "correcting ... to Y" record wins.
    # Actual: "correcting" is not in the correction cue list, so the tie is a STRONG genuine contradiction (enforceable).
    g = [{"record_id": "a", "entity": "Project T", "attribute": "region", "value": "east-mesa-1", "recorded_on": "2026-05-02",
          "source": "user_statement", "text": "For Project T, the cloud region is east-mesa-1."},
         {"record_id": "b", "entity": "Project T", "attribute": "region", "value": "south-delta-3", "recorded_on": "2026-05-02",
          "source": "user_statement", "text": "For Project T, correcting the cloud region to south-delta-3."}]
    r = arbitrate(g)
    assert (r.kind, r.strength) == ("contradiction", "strong")
