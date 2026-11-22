"""CPU-only tests for the memlab ablation harness (no network)."""
import json
import sys
from pathlib import Path

sys.path.insert(0, str(Path(__file__).resolve().parent.parent / "scripts"))
import memlab  # noqa: E402


def _tasks(split="eval", seed=20261112, per=8):
    return memlab.build_split(split, seed, per)


def test_build_is_deterministic_and_sized():
    a, b = _tasks(), _tasks()
    assert a == b and len(a) == 48
    assert len({t["task_id"] for t in a}) == 48 and len({t["prompt"] for t in a}) == 48


def test_dev_and_eval_entities_are_disjoint():
    def ents(ts):
        return {r["entity"] for t in ts for r in t["memory"]} | {f["entity"] for t in ts for f in t["registry"]["facts"]}
    assert not ents(_tasks()) & ents(_tasks("dev", 101, 2))


def test_expected_value_never_in_prompt():
    for t in _tasks():
        e = t["expected"]
        for v in [e.get("value"), e.get("stale_value"), *e.get("conflict_values", [])]:
            if v is not None and e.get("value_kind") != "num" or isinstance(v, str):
                assert memlab._norm(v) not in memlab._norm(t["prompt"])
            elif v is not None:
                assert str(v) not in t["prompt"]


def test_unsupported_tasks_have_no_supporting_record():
    for t in _tasks():
        if t["scenario"] == "S5_unsupported":
            ent = t["prompt"].split("Project ")[1].split("?")[0].split(" ")[0]
            attr = next(a for a, s in memlab.ATTRS.items() if s["q"].split("{e}")[0] in t["prompt"])
            assert not [r for r in t["memory"] if ent in r["entity"] and r["attribute"] == attr]
            assert not t["gold_record_ids"] and not t["registry"]["facts"]


def test_reliability_status():
    g = [{"record_id": "a", "value": 1, "recorded_on": "2026-05-01"},
         {"record_id": "b", "value": 2, "recorded_on": "2026-06-01"}]
    assert memlab.reliability_status(g[0], g) == {"status": "superseded", "superseded_by": ["b"]}
    assert memlab.reliability_status(g[1], g) == {"status": "current"}
    g[0]["recorded_on"] = "2026-06-01"
    assert memlab.reliability_status(g[0], g) == {"status": "conflicting", "conflicts_with": ["b"]}
    assert memlab.reliability_status(g[0], g[:1]) == {"status": "unchallenged"}


def test_classify_table():
    ans = {"kind": "answer", "value": 10.5, "value_kind": "num", "tol": 0.011, "stale_value": 7}
    c = memlab.classify
    assert c(ans, {"status": "answer", "value": "10.50 USD"}) == "correct"
    assert c(ans, {"status": "answer", "value": 7}) == "stale_value"
    assert c(ans, {"status": "answer", "value": 3}) == "wrong_value"
    assert c(ans, {"status": "abstain"}) == "over_abstain"
    assert c(ans, {"status": "conflict"}) == "false_conflict"
    assert c({"kind": "abstain"}, {"status": "answer", "value": 1}) == "unsupported_claim"
    assert c({"kind": "abstain"}, {"status": "abstain"}) == "correct"
    assert c({"kind": "conflict"}, {"status": "answer", "value": 1}) == "arbitrary_pick"
    assert c({"kind": "conflict"}, {"status": "conflict"}) == "correct"
    assert c(ans, None) == "format_error" and c(ans, {"status": "answer"}, True) == "max_steps"
    txt = {"kind": "answer", "value": "Mira Tolvane", "value_kind": "text"}
    assert c(txt, {"status": "answer", "value": "mira tolvane (lead)"}) == "correct"


def test_parse_final_takes_last_status_object():
    assert memlab.parse_final('x {"a":1} {"status":"abstain","value":null} tail')["status"] == "abstain"
    assert memlab.parse_final("no json") is None


class Scripted:
    """Ideal-behaviour stand-in model: searches memory with the prompt, calls
    the registry for S6, then answers from what the tools returned."""
    def __init__(self, task):
        self.task, self.n = task, 0

    def chat(self, messages, tools=None):
        self.n += 1
        base = {"usage": {}, "latency_s": 0.0, "wait_s": 0.0, "error": None, "finish_reason": "stop"}
        if tools is None:
            return {"message": {"content": '{"verdict":"SUPPORTED","reason":"ok"}'}, **base}
        names = [t["function"]["name"] for t in tools]
        if self.n == 1 and "memory_search" in names:
            call = {"id": "c1", "function": {"name": "memory_search",
                                             "arguments": json.dumps({"query": self.task["prompt"]})}}
            return {"message": {"tool_calls": [call]}, **base}
        e = self.task["expected"]
        ans = {"status": e["kind"], "value": str(e.get("value", ""))}
        if self.task["task_id"].endswith(("1", "3")):  # plain-text finals are accepted too
            return {"message": {"content": json.dumps(ans)}, **base}
        call = {"id": "c2", "function": {"name": "submit_answer", "arguments": json.dumps(ans)}}
        return {"message": {"tool_calls": [call]}, **base}


def test_end_to_end_with_scripted_model_and_provenance_isolation(tmp_path):
    for t in _tasks():
        for cfg in memlab.CONFIGS:
            run = memlab.run_task(Scripted(t), t, cfg, tmp_path)
            s = memlab.score_run(t, run)
            assert s["outcome"] == "correct"
            blob = json.dumps(run["messages"])
            assert "gold_record_ids" not in blob and '"expected"' not in blob and '"role": "gold"' not in blob
            mem = [c for c in run["tool_calls"] if c["name"] == "memory_search"]
            assert bool(mem) == memlab.CONFIGS[cfg]["memory"]
            for c in mem:
                assert ("recorded_on" in c["observation"]) == memlab.CONFIGS[cfg]["provenance"]
                assert ("reliability" in c["observation"]) == memlab.CONFIGS[cfg]["reliability"]


def test_registry_failure_plans():
    t = next(x for x in _tasks() if x["variant"] == "transient_timeout")
    f = t["registry"]["facts"][0]
    r = memlab.Registry(t["registry"])
    assert r.call(f["entity"], f["attribute"])[0] == "TIMEOUT"
    assert r.call(f["entity"], f["attribute"])[0] == "OK"
    assert r.call("Project Nowhere", f["attribute"])[0] == "NOT_FOUND"
