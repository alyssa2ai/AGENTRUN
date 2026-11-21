"""Unit and adversarial tests of evidence-basis arbitration (no LLM)."""
import pytest

from evarb.arbiter import arbitrate
from evarb.cues import analyse, mentions

E, A = "Project Zalor", "team_size"


def r(i, v, d, t=None, src="imported_doc", a=A):
    return {"record_id": i, "entity": E, "attribute": a, "value": v, "recorded_on": d, "source": src,
            "text": t or f"Project Zalor has a team of {v} people."}


def res(group):
    x = arbitrate(group)
    return x.kind, x.basis, x.strength, x.current_value


# ---- the ten bases -------------------------------------------------------------------------
@pytest.mark.parametrize("group,expected", [
    ([r("a", 12, "2026-05-01"), r("b", 17, "2026-07-01")], ("resolved", "record_time", "strong", 17)),
    ([r("a", 12, "2026-09-01", "As of 2026-03-01: Project Zalor has a team of 12 people."),
      r("b", 17, "2026-09-01", "Effective 4 June 2026: Project Zalor has a team of 17 people.")],
     ("resolved", "valid_time", "strong", 17)),
    ([r("a", 12, "2026-05-01"), r("b", 17, "2026-06-01", "Project Zalor has a team of 17. This replaces the 12.")],
     ("resolved", "explicit_supersession", "strong", 17)),
    ([r("a", 12, "2026-05-01"), r("b", 17, "2026-06-01", "Project Zalor has a team of 17. The 12 was a typo.")],
     ("resolved", "explicit_correction", "strong", 17)),
    ([r("a", 12, "2026-05-01"), r("b", 17, "2026-05-01", "Project Zalor has a team of 17. The 12 was a typo.")],
     ("resolved", "same_day_correction", "strong", 17)),
    ([r("a", 12, "2026-05-01", src="meeting_notes"), r("b", 17, "2026-05-01", src="system_of_record")],
     ("resolved", "source_authority", "moderate", 17)),
    ([r("a", 12, "2026-05-01"), r("b", 17, "2026-05-01")], ("contradiction", "genuine_contradiction", "strong", None)),
    ([r("a", 12, "2026-05-01"), r("b", 17, "2026-05-01", "Project Zalor has a team of 17. This does not replace the 12; "
                                                           "both figures stand.")],
     ("contradiction", "negated_correction", "strong", None)),
    # evarb-0.2: a negated replacement WITHOUT a "both stand / disagree" marker defers to the rival (advisory)
    ([r("a", 12, "2026-05-01"), r("b", 17, "2026-05-01", "Project Zalor has a team of 17. This does not replace the 12.")],
     ("resolved", "negated_correction", "moderate", 12)),
    ([r("a", 12, "2026-05-01"), r("b", 17, "2026-05-01", 'Kim wrote: "17 replaces the 12". Project Zalor has a team of 17.')],
     ("unresolved", "quoted_or_hypothetical", "none", None)),
    ([r("a", 12, ""), r("b", 17, "2026-05-01")], ("unresolved", "insufficient_evidence", "none", None)),
])
def test_bases(group, expected):
    assert res(group) == expected


# ---- the negation / modality safeguards named in the brief ----------------------------------
@pytest.mark.parametrize("text,expected_kind,expected_value", [
    ("Project Zalor has a team of 17. This replaces the earlier value.", "resolved", 17),
    ("Project Zalor has a team of 17. This does not replace the earlier value.", "resolved", 12),
    ("Project Zalor has a team of 17. This does not replace the earlier value; the two disagree.", "contradiction", None),
    ("According to a recent statement, Project Zalor will now have 17 instead of 12.", "resolved", 12),
    ("A team of 17 is still under discussion; 12 remains the confirmed figure.", "resolved", 12),
    ("A team of 17 was proposed. The previous figure remains valid.", "resolved", 12),
    ("Project Zalor has a team of 17. The update was not confirmed.", "resolved", 12),
    ('Lee said "the 12 was a mistake". Project Zalor has a team of 17.', "unresolved", None),
    ("If funding is approved, Project Zalor would have a team of 17.", "resolved", 12),
    ("Hypothetically, a team of 17 could replace the 12.", "resolved", 12),
    ("Nobody has revised the 12. Project Zalor has a team of 17.", "resolved", 12),
])

def test_linguistic_safeguards(text, expected_kind, expected_value):
    later = "2026-05-01"
    x = arbitrate([r("a", 12, "2026-05-01"), r("b", 17, later, text)])
    assert (x.kind, x.current_value) == (expected_kind, expected_value)


def test_doubt_word_downgrades_time_order_to_advisory():
    x = arbitrate([r("a", 12, "2026-05-01"), r("b", 17, "2026-07-01", "A team of 17 was discussed for Project Zalor.")])
    assert (x.kind, x.current_value, x.strength) == ("resolved", 17, "moderate")


def test_ordinal_dates():
    x = arbitrate([r("a", 12, "2026-09-09", "As of June 4th, 2026, Project Zalor has a team of 12."),
                   r("b", 17, "2026-09-09", "Starting August 19th, 2026, Project Zalor will have a team of 17."),
                   ])
    assert (x.basis, x.current_value) == ("valid_time", 17)
    y = arbitrate([r("a", 12, "2026-09-09", "Effective 3rd of March 2026: team of 12."),
                   r("b", 17, "2026-09-09", "Effective 1st of May 2026: team of 17.")])
    assert y.current_value == 17


def test_validity_cue_starting_from():
    x = arbitrate([r("a", 12, "2026-09-01", "Starting from 2026-03-01, Project Zalor has a team of 12."),
                   r("b", 17, "2026-09-01", "From June 4, 2026, Project Zalor has a team of 17.")])
    assert (x.basis, x.current_value) == ("valid_time", 17)


def test_unreferenced_update_word_does_not_break_tie():
    x = arbitrate([r("a", 12, "2026-05-01"), r("b", 17, "2026-05-01", "Weekly status update: Project Zalor has a team of 17.")])
    assert x.kind == "contradiction"


def test_unreferenced_correction_breaks_tie_only_moderately():
    x = arbitrate([r("a", 12, "2026-05-01"), r("b", 17, "2026-05-01", "Corrected entry: Project Zalor has a team of 17.")])
    assert (x.kind, x.current_value, x.strength) == ("resolved", 17, "moderate")


def test_unreferenced_correction_does_not_override_record_time():
    x = arbitrate([r("a", 12, "2026-07-01"), r("b", 17, "2026-05-01", "Corrected entry: Project Zalor has a team of 17.")])
    assert (x.kind, x.current_value, x.basis) == ("resolved", 12, "record_time")


def test_correcting_record_older_than_corrected_is_not_strong():
    x = arbitrate([r("a", 12, "2026-07-01"), r("b", 17, "2026-05-01", "Project Zalor has 17. The 12 was a typo.")])
    assert x.current_value == 17 and x.strength == "moderate"


def test_cyclic_corrections_are_unresolved():
    x = arbitrate([r("a", 12, "2026-05-01", "Team of 12. The 17 was a typo."),
                   r("b", 17, "2026-05-01", "Team of 17. The 12 was a typo.")])
    assert x.kind == "unresolved"


def test_deadline_value_is_not_a_validity_date():
    a = "deadline"
    x = arbitrate([r("a", "2027-01-10", "2026-05-01", "The delivery deadline for Project Zalor is 2027-01-10.", a=a),
                   r("b", "2027-03-01", "2026-05-01", "The delivery deadline for Project Zalor is 2027-03-01.", a=a)])
    assert x.kind == "contradiction"


def test_same_text_validity_date_is_contradiction():
    x = arbitrate([r("a", 12, "2026-05-01", "As of 2026-05-01: team of 12."), r("b", 17, "2026-05-01", "As of 2026-05-01: team of 17.")])
    assert x.kind == "contradiction"


def test_backfilled_entry_valid_time_beats_record_time():
    x = arbitrate([r("a", 17, "2026-06-05", "As of 2026-06-01: team of 17."),
                   r("b", 12, "2026-07-20", "As of 2026-02-01: team of 12 (entered late).")])
    assert (x.current_value, x.basis) == (17, "valid_time")
    assert "differs from recorded_on" in x.statuses["a"]["note"]


def test_three_value_chain_record_time():
    x = arbitrate([r("a", 10, "2026-01-01"), r("b", 12, "2026-03-01"), r("c", 17, "2026-05-01")])
    assert x.current_value == 17 and x.statuses["a"]["status"] == "superseded"


def test_unchallenged_and_same_value_duplicates():
    assert arbitrate([r("a", 12, "2026-01-01")]).kind == "unchallenged"
    assert arbitrate([r("a", 12, "2026-01-01"), r("b", 12, "2026-05-01")]).kind == "unchallenged"


def test_value_mention_is_token_bounded():
    assert mentions("ports 13184 and 3184x", 3184) is False
    assert mentions("port 3184.", 3184) is True
    assert mentions("north-fjord-2 region", "north-fjord-2") is True
    assert mentions("dated 2026-05-01", 5) is False


def test_negation_scope_is_local():
    c = analyse(r("b", 17, "2026-05-01", "Not much changed in the meeting. Project Zalor has a team of 17. This replaces the 12."))
    sup = [x for x in c.clauses if x.kind == "supersession"]
    assert sup and not sup[0].negated
