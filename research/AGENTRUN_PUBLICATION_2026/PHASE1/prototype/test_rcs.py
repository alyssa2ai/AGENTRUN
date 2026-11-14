"""Deterministic fixture tests for the RCS decision logic (no LLM).

    py -3.11 -m pytest PHASE1/prototype/test_rcs.py -q
"""
import sys
from pathlib import Path

sys.path.insert(0, str(Path(__file__).resolve().parent))
import rcs  # noqa: E402

memlab = rcs.memlab


def rec(rid, e, a, v, d, text=None):
    return {"record_id": rid, "entity": e, "attribute": a, "value": v, "recorded_on": d, "source": "user_statement",
            "text": text or memlab.ATTRS[a]["t"].format(e=e, v=v)}


Q = "How many people are on the team for Project Zalor?"
STALE = [rec("m-01", "Project Zalor", "team_size", 12, "2026-05-01"),
         rec("m-02", "Project Zalor", "team_size", 17, "2026-07-01"),
         rec("m-03", "Project Other", "team_size", 9, "2026-06-01")]
CONFL = [rec("m-01", "Project Zalor", "team_size", 12, "2026-05-01"),
         rec("m-02", "Project Zalor", "team_size", 17, "2026-05-01")]
SEARCH = [{"name": "memory_search", "status": "OK"}]


def store(r):
    return memlab.MemoryStore(r, None)


def test_r1_stale_value_flagged():
    rule, _ = rcs.check_submission(Q, store(STALE), {"m-01", "m-02"}, SEARCH, {"status": "answer", "value": "12"})
    assert rule == "R1"


def test_current_value_passes():
    assert rcs.check_submission(Q, store(STALE), {"m-01", "m-02"}, SEARCH, {"status": "answer", "value": "17"}) \
        == (None, None)


def test_r2_false_conflict_flagged():
    rule, notice = rcs.check_submission(Q, store(STALE), {"m-01", "m-02"}, SEARCH, {"status": "conflict"})
    assert rule == "R2" and "m-02" in notice


def test_real_conflict_passes():
    assert rcs.check_submission(Q, store(CONFL), {"m-01", "m-02"}, SEARCH, {"status": "conflict"}) == (None, None)


def test_r3_no_search():
    rule, _ = rcs.check_submission(Q, store(STALE), set(), [], {"status": "abstain"})
    assert rule == "R3"


def test_registry_success_counts_as_evidence():
    calls = [{"name": "registry_lookup", "status": "OK"}]
    assert rcs.check_submission(Q, store(STALE), set(), calls, {"status": "answer", "value": "5"}) == (None, None)


def test_unanchored_records_ignored():
    # retrieved only another project's record: nothing to check
    assert rcs.check_submission(Q, store(STALE), {"m-03"}, SEARCH, {"status": "conflict"}) == (None, None)


def test_abstain_after_search_never_flagged():
    # RCS does not second-guess abstentions once memory was searched (unsupported-premise tasks)
    assert rcs.check_submission(Q, store(STALE), {"m-01", "m-02"}, SEARCH, {"status": "abstain"}) == (None, None)


def test_cost_case_same_day_correction_is_not_flagged_as_stale():
    # same-date records are "conflicting"; answering the correction is not flagged by R1 (no superseded record)
    assert rcs.check_submission(Q, store(CONFL), {"m-01", "m-02"}, SEARCH, {"status": "answer", "value": "17"}) \
        == (None, None)


def test_dev_split_builds_and_is_disjoint():
    tasks = rcs.build_p1dev()
    assert len(tasks) == 64 and len({t["task_id"] for t in tasks}) == 64
    deep = rcs.DEEP / "benchmark"
    import json
    ents = set()
    for f in ("dev.jsonl", "eval.jsonl", "eval2.jsonl"):
        for x in (deep / f).read_text(encoding="utf-8").splitlines():
            if x.strip():
                ents |= {m["entity"] for m in json.loads(x)["memory"]}
    mine = {m["entity"] for t in tasks for m in t["memory"]}
    assert not (mine & ents)
