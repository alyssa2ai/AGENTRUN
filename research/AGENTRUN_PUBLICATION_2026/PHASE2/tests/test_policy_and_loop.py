"""Policy decisions and end-to-end loop behaviour with a scripted (mock) model client.

The mock client replays a fixed list of model outputs, so the agent loop, the labels, the gated
policy and the safe-submission revert are exercised without a GPU.
"""
import json

import pytest

from evarb import paths  # noqa: F401
from evarb.arbiter import arbitrate
from evarb.loop import run_any, run_task
from evarb.policy import decide, question_intent
import memlab
import rcs

E, A = "Project Zalor", "team_size"
Q = "How many people are on the team for Project Zalor?"


def rec(i, v, d, t=None):
    return {"record_id": i, "entity": E, "attribute": A, "value": v, "recorded_on": d, "source": "imported_doc",
            "text": t or f"Project Zalor has a team of {v} people."}


SEARCH = [{"name": "memory_search", "status": "OK"}]


def dec(group, sub, mode="gated", q=Q, calls=SEARCH):
    res = arbitrate(group)
    key = (E, A)
    return decide(q, {key: res}, {key: group}, {g["record_id"] for g in group}, calls, sub, mode=mode)


def test_intent():
    assert question_intent(Q)["intent"] == "current"
    assert question_intent("How many people were originally on the team for Project Zalor?")["intent"] == "historical"
    assert question_intent("What was the budget as of 2026-05-01?")["as_of"] == "2026-05-01"


def test_stale_answer_enforced_when_strong():
    g = [rec("a", 12, "2026-05-01"), rec("b", 17, "2026-07-01")]
    d = dec(g, {"status": "answer", "value": "12"})
    assert (d.action, d.rule) == ("ENFORCE", "P1") and "newer" in d.notice


def test_stale_answer_on_historical_question_not_enforced():
    g = [rec("a", 12, "2026-05-01"), rec("b", 17, "2026-07-01")]
    d = dec(g, {"status": "answer", "value": "12"}, q="How many people were originally on the team for Project Zalor?")
    assert d.action == "NO_ACTION"


def test_moderate_resolution_only_advised():
    g = [rec("a", 12, "2026-05-01"), rec("b", 17, "2026-05-01", "Corrected entry: Project Zalor has a team of 17.")]
    assert dec(g, {"status": "conflict"}).action == "ADVISE"
    assert dec(g, {"status": "conflict"}, mode="all").action == "ENFORCE"


def test_false_conflict_enforced_with_truthful_notice_for_same_day_correction():
    g = [rec("a", 12, "2026-05-01"), rec("b", 17, "2026-05-01", "Team of 17. The 12 was a typo.")]
    d = dec(g, {"status": "conflict"})
    assert d.action == "ENFORCE" and "corrects or replaces" in d.notice and "same latest date" not in d.notice


def test_negated_cue_never_enforced_toward_a_value():
    # without a "both stand" marker the negating record defers (moderate): advised, never enforced
    g = [rec("a", 12, "2026-05-01"), rec("b", 17, "2026-05-01", "Team of 17. This does not replace the 12.")]
    assert dec(g, {"status": "conflict"}).action == "ADVISE"
    assert dec(g, {"status": "answer", "value": "17"}).action == "NO_ACTION"
    # with the marker it is a strong contradiction: picking a value is challenged toward conflict (P4)
    g2 = [rec("a", 12, "2026-05-01"), rec("b", 17, "2026-05-01", "Team of 17. This does not replace the 12; both stand.")]
    assert dec(g2, {"status": "conflict"}).action == "NO_ACTION"
    assert dec(g2, {"status": "answer", "value": "17"}).rule == "P4"


def test_unresolved_never_enforced():
    g = [rec("a", 12, ""), rec("b", 17, "2026-05-01")]
    for sub in ({"status": "answer", "value": "17"}, {"status": "conflict"}, {"status": "answer", "value": "12"}):
        assert dec(g, sub).action == "NO_ACTION"


def test_no_search_requests_evidence():
    g = [rec("a", 12, "2026-05-01")]
    d = dec(g, {"status": "abstain"}, calls=[{"name": "registry_lookup", "status": "UNAVAILABLE"}])
    assert d.action == "REQUEST_EVIDENCE"


# ---- loop integration with a scripted client --------------------------------------------------
class Script:
    """Replays model outputs. Each item: ("call", name, args) or ("text", str)."""

    def __init__(self, steps):
        self.steps, self.i = list(steps), 0

    def chat(self, messages, tools=None):
        kind, *rest = self.steps[min(self.i, len(self.steps) - 1)]
        self.i += 1
        base = {"usage": {}, "latency_s": 0.0, "wait_s": 0.0, "raw_text": "", "parse_path": None, "finish_reason": "stop",
                "error": None}
        if kind == "call":
            name, args = rest
            return {**base, "message": {"role": "assistant", "content": "", "tool_calls": [
                {"id": f"c{self.i}", "type": "function", "function": {"name": name, "arguments": json.dumps(args)}}]}}
        return {**base, "message": {"role": "assistant", "content": rest[0]}}


def task(records, expected, prompt=Q, registry=None):
    for k, x in enumerate(records, 1):
        x["record_id"] = f"m-{k:02d}"
    return {"task_id": "t", "split": "test", "scenario": "x", "variant": "x", "prompt": prompt, "expected": expected,
            "memory": records, "gold_record_ids": [x["record_id"] for x in records], "needed_tools": ["memory_search"],
            "registry": registry or {"facts": [], "plan": ["NOT_FOUND"]}}


def test_phase1_M10_R3_break_is_reverted_not_a_format_error():
    """Phase 1 p1dev-S6_tool_failure-02 (3B, R): correct abstain -> R3 notice -> plain text -> format_error.
    Under EBG the notice is reversible, so the correct abstention stands."""
    t = task([rec("x", 5, "2026-05-01")], memlab._expected("abstain"), prompt="Who is the lead of Project Zalor?",
             registry={"facts": [], "plan": ["UNAVAILABLE"]})
    steps = [("call", "registry_lookup", {"entity": E, "attribute": "lead"})] * 3 + [
        ("call", "submit_answer", {"status": "abstain", "value": "", "evidence": [], "note": ""}),
        ("call", "memory_search", {"query": "lead Project Zalor"}),
        ("text", "Status: abstain\nExplanation: nothing found.")]
    run = run_task(Script(steps), t, "EBG")
    assert run["reverted"] is True and run["final"]["status"] == "abstain"
    assert memlab.score_run(t, run)["outcome"] == "correct"
    unsafe = run_task(Script(steps), t, "EBG-unsafe")
    assert memlab.score_run(t, unsafe)["outcome"] == "format_error"


def test_same_day_correction_false_conflict_fixed_in_loop():
    recs = [rec("a", 12, "2026-05-01"), rec("b", 17, "2026-05-01", "Team of 17 for Project Zalor. The 12 was a typo.")]
    t = task(recs, memlab._expected("answer", value=17, stale_value=12))
    steps = [("call", "memory_search", {"query": "team Project Zalor"}),
             ("call", "submit_answer", {"status": "conflict", "value": "", "evidence": [], "note": ""}),
             ("call", "submit_answer", {"status": "answer", "value": "17", "evidence": [], "note": ""})]
    run = run_task(Script(steps), t, "EBG")
    assert run["rcs_events"][0]["rule"] == "P2" and memlab.score_run(t, run)["outcome"] == "correct"
    obs = json.loads(run["tool_calls"][0]["observation"])["results"]
    lab = {x["record_id"]: x["reliability"]["status"] for x in obs if x["record_id"] in ("m-01", "m-02")}
    assert lab == {"m-01": "superseded", "m-02": "current"}


def test_labels_say_unresolved_not_conflicting_when_order_unknown():
    recs = [rec("a", 12, ""), rec("b", 17, "2026-05-01")]
    t = task(recs, memlab._expected("conflict", conflict_values=[12, 17]))
    steps = [("call", "memory_search", {"query": "team Project Zalor"}),
             ("call", "submit_answer", {"status": "conflict", "value": "", "evidence": [], "note": ""})]
    run = run_task(Script(steps), t, "EB")
    rel = [x["reliability"] for x in json.loads(run["tool_calls"][0]["observation"])["results"]
           if x["record_id"] in ("m-01", "m-02")]
    assert {x["status"] for x in rel} == {"unresolved"} and all("conflict" not in json.dumps(x) for x in rel)


def test_historical_label_and_no_enforcement():
    recs = [rec("a", 12, "2026-05-01"), rec("b", 17, "2026-07-01")]
    q = "How many people were originally on the team for Project Zalor?"
    t = task(recs, memlab._expected("answer", value=12), prompt=q)
    steps = [("call", "memory_search", {"query": "team Project Zalor"}),
             ("call", "submit_answer", {"status": "answer", "value": "12", "evidence": [], "note": ""})]
    run = run_task(Script(steps), t, "EBG")
    assert not run["rcs_events"] and memlab.score_run(t, run)["outcome"] == "correct"
    rel = {x["record_id"]: x["reliability"]["status"] for x in json.loads(run["tool_calls"][0]["observation"])["results"]}
    assert rel["m-01"] == "historical"


@pytest.mark.parametrize("config", ["B", "G", "R", "T", "RT"])
def test_phase1_configs_dispatch_to_unchanged_code(config):
    recs = [rec("a", 12, "2026-05-01"), rec("b", 17, "2026-07-01")]
    t = task(recs, memlab._expected("answer", value=17, stale_value=12))
    steps = [("call", "memory_search", {"query": "team Project Zalor"}),
             ("call", "submit_answer", {"status": "answer", "value": "17", "evidence": [], "note": ""})]
    run = run_any(Script(steps), t, config)
    assert run.get("p2_version") is None and run["p1_version"] == rcs.P1_VERSION
    assert memlab.score_run(t, run)["outcome"] == "correct"
