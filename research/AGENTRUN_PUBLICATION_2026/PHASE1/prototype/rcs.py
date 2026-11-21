"""Phase 1 prototype: Resolution-Checked Submission (RCS).

Isolated from the frozen harness: imports memlab (unchanged) and re-implements
only the agent loop, adding one hook at the terminal action.

Configurations (all use harness v2 prompts):
  A  stateless                                  (memlab A)
  B  memory                                     (memlab B)
  E  memory + same-model verifier + provenance + advisory gate   (memlab E)
  G  memory + provenance + advisory gate, no verifier            (new: isolates the gate)
  R  G + resolution-checked submission                           (new: the mechanism)

RCS: when the agent submits, deterministic code compares the submission with
the reliability state of the memory records the agent itself retrieved
(never with ground truth). If they disagree, the harness sends ONE corrective
notice naming the records, and the agent may resubmit. The second submission
is final. Rules (each only applies to records whose entity is named in the
user question, "anchored" records):
  R1 stale value:   answer value equals a superseded record's value and no
                    current record's value  -> notice
  R2 false conflict: status "conflict" while no anchored key is in a
                    same-date conflict                       -> notice
  R3 no search:     submission without any memory_search call and without a
                    successful registry result               -> notice
RCS never changes an answer itself and never sees the expected answer.
"""
from __future__ import annotations

import json
import re
import sys
import time
from datetime import date, timedelta
from pathlib import Path

HERE = Path(__file__).resolve().parent
DEEP = HERE.parents[2] / "AGENTRUN_DEEPENING_2026-11-11"
sys.path.insert(0, str(DEEP / "scripts"))
import memlab  # noqa: E402

P1_VERSION = "rcs-0.1"
CONFIGS = {
    "A": dict(memlab.CONFIGS["A"], rcs=False),
    "B": dict(memlab.CONFIGS["B"], rcs=False),
    "E": dict(memlab.CONFIGS["E"], rcs=False),
    "G": {"label": "G: advisory gate, no verifier", "memory": True, "verify": False, "provenance": True,
          "reliability": True, "rcs": False},
    "R": {"label": "R: G + resolution-checked submission", "memory": True, "verify": False, "provenance": True,
          "reliability": True, "rcs": True},
}

RCS_PREFIX = "[harness check] "


# ----------------------------------------------------------------------------
# Development-only stress split (disjoint names; new scenarios S7, S8)
# ----------------------------------------------------------------------------
class P1World(memlab._World):
    def __init__(self, seed: int):
        self.names = memlab._name_pool(8000)[5200:]  # disjoint from dev, eval and eval2 slices
        self.rng = __import__("random").Random(seed)
        self.rng.shuffle(self.names)
        self._i = 0


def build_p1dev(seed: int = 20261114, per_scenario: int = 8) -> list[dict]:
    """S1-S6 from the memlab generator logic (same templates) plus two stress
    scenarios where the structured metadata is insufficient:
      S7 same-day correction: same date, the later record says it corrects the earlier one -> answer the correction
      S8 date only in text:  both records share recorded_on; the text dates show which is newer -> answer the newer
    In S7 and S8 the gate's metadata says "conflicting"; the record text resolves it. They measure the cost
    of trusting metadata."""
    w = P1World(seed)
    tasks = []
    orig_world = memlab._World
    try:  # reuse memlab.build_split's S1-S6 logic with our world
        memlab._World = lambda split, s: w
        tasks = memlab.build_split("p1dev", seed, per_scenario)
    finally:
        memlab._World = orig_world
    attrs = list(memlab.ATTRS)

    def add(scenario, variant, i, **kw):
        t = {"task_id": f"p1dev-{scenario}-{i:02d}", "split": "p1dev", "scenario": scenario, "variant": variant}
        t.update(kw)
        tasks.append(memlab._finish(w, t))

    for i in range(per_scenario):
        a = attrs[i % len(attrs)]
        e = w.project()
        v1 = w.value(a)
        v2 = w.value(a, avoid=v1)
        d = w.day()
        src = w.rng.choice(memlab._SOURCES)
        r1 = memlab._rec(e, a, v1, d, src, role="gold")
        r2 = memlab._rec(e, a, v2, d, src, role="gold")
        r2["text"] = (f"Correction (later the same day): " + memlab.ATTRS[a]["t"].format(e=e, v=v2)
                      + f" The earlier figure of {v1} was a mistake.")
        add("S7_same_day_correction", a, i, prompt=memlab.ATTRS[a]["q"].format(e=e),
            expected=memlab._expected("answer", value=v2, stale_value=v1),
            _records=[r1, r2] + memlab._distractors(w, 5), needed_tools=["memory_search"])
    for i in range(per_scenario):
        a = attrs[(i + 2) % len(attrs)]
        e = w.project()
        old = w.value(a)
        new = w.value(a, avoid=old)
        d_old = w.day(0, 60)
        d_new = (date.fromisoformat(d_old) + timedelta(days=w.rng.randrange(30, 120))).isoformat()
        imported = w.day(130, 140)  # both imported on the same day: metadata date carries no order
        r_old = memlab._rec(e, a, old, imported, "imported_doc", role="gold")
        r_new = memlab._rec(e, a, new, imported, "imported_doc", role="gold")
        r_old["text"] = f"As of {d_old}: " + r_old["text"]
        r_new["text"] = f"As of {d_new}: " + r_new["text"]
        add("S8_date_in_text_only", a, i, prompt=memlab.ATTRS[a]["q"].format(e=e),
            expected=memlab._expected("answer", value=new, stale_value=old),
            _records=[r_old, r_new] + memlab._distractors(w, 5), needed_tools=["memory_search"])
    return tasks


# ----------------------------------------------------------------------------
# The check
# ----------------------------------------------------------------------------
def _matches(v, got) -> bool:
    if got is None or str(got).strip() == "":
        return False
    if isinstance(v, (int, float)):
        g = memlab._num(got)
        return g is not None and abs(g - float(v)) <= 0.011
    return memlab._norm(v) != "" and memlab._norm(v) in memlab._norm(got)


def check_submission(question: str, store, retrieved_ids: set[str], calls: list[dict], sub: dict | None):
    """Return (rule, notice) or (None, None). Uses only the question text, the store
    metadata of records the agent retrieved, and the agent's own tool calls."""
    if not isinstance(sub, dict) or store is None:
        return None, None
    status = sub.get("status")
    searched = any(c["name"] == "memory_search" for c in calls)
    registry_ok = any(c["name"] == "registry_lookup" and c["status"] == "OK" for c in calls)
    if not searched and not registry_ok:
        return "R3", (RCS_PREFIX + "You submitted without searching memory. Facts from earlier sessions are "
                      "stored there: call memory_search, then submit again.")
    qn = memlab._norm(question)
    by_id = {e["record_id"]: e for e in store.entries}
    anchored = [by_id[i] for i in retrieved_ids if i in by_id and memlab._norm(by_id[i]["entity"]) in qn]
    if not anchored:
        return None, None
    keys = {(r["entity"], r["attribute"]) for r in anchored}
    groups = {k: store.same_key({"entity": k[0], "attribute": k[1]}) for k in keys}
    state = {k: {g["record_id"]: memlab.reliability_status(g, grp)["status"] for g in grp}
             for k, grp in groups.items()}
    if status == "answer":
        v = sub.get("value")
        for k, grp in groups.items():
            stale = [g for g in grp if state[k][g["record_id"]] == "superseded" and _matches(g["value"], v)]
            current = [g for g in grp if state[k][g["record_id"]] == "current"]
            if stale and current and not any(_matches(g["value"], v) for g in current):
                c = current[0]
                return "R1", (RCS_PREFIX + f"Your value matches record {stale[0]['record_id']} "
                              f"(recorded {stale[0]['recorded_on']}), which is superseded by record "
                              f"{c['record_id']} (recorded {c['recorded_on']}). Re-check and submit again.")
    if status == "conflict":
        if not any(s == "conflicting" for st in state.values() for s in st.values()):
            cur = sorted({rid for st in state.values() for rid, s in st.items() if s == "current"})
            return "R2", (RCS_PREFIX + "None of the retrieved facts about the project in the question has two "
                          "different values on the same latest date: older records are superseded by newer ones"
                          + (f" (current: {', '.join(cur)})" if cur else "") + ". Submit again.")
    return None, None


# ----------------------------------------------------------------------------
# Agent loop: memlab.run_task with the RCS hook (otherwise identical policy)
# ----------------------------------------------------------------------------
def run_task(client, task: dict, config: str, harness: str = "v2") -> dict:
    cfg = CONFIGS[config]
    store = memlab.MemoryStore(task["memory"], None) if cfg["memory"] else None
    hv = memlab.HARNESSES[harness]
    repaired, rcs_used, rcs_events = False, False, []
    registry = memlab.Registry(task["registry"])
    tools = [memlab.CALC_TOOL, memlab.REG_TOOL] + ([memlab.MEM_TOOL] if cfg["memory"] else []) + [memlab.SUBMIT_TOOL]
    messages = [{"role": "system", "content": hv["system"]}, {"role": "user", "content": task["prompt"]}]
    calls, api, evidence = [], [], []
    retrieved_all: set[str] = set()
    draft_text, hit_max, t_ret = None, False, 0.0
    t0 = time.monotonic()
    max_steps = memlab.MAX_STEPS + (1 if cfg["rcs"] else 0)  # the corrective turn gets its own step
    for step in range(1, max_steps + 1):
        resp = client.chat(messages, tools)
        api.append({"role": "agent", "step": step, **{k: resp.get(k) for k in memlab.API_KEYS}})
        msg = resp["message"]
        if resp["error"]:
            messages.append({"role": "user", "content": memlab.MALFORMED_NOTICE})
            continue
        tcs = msg.get("tool_calls") or []
        if not tcs and not (msg.get("content") or "").strip() and step < max_steps:
            messages.append({"role": "user", "content": memlab.MALFORMED_NOTICE})
            continue
        if not tcs and hv["repair"] and not repaired and step < max_steps \
                and not (memlab.parse_final(msg.get("content")) or {}).get("status"):
            repaired = True
            messages.append({"role": "assistant", "content": msg.get("content") or ""})
            messages.append({"role": "user", "content": memlab.REPAIR_NOTICE})
            continue
        sub = next((tc for tc in tcs if tc["function"]["name"] == "submit_answer"), None)
        cand_text = (sub["function"]["arguments"] or "") if sub is not None else (msg.get("content") or "")
        if sub is not None or not tcs:
            if cfg["rcs"] and not rcs_used and step < max_steps:
                rule, notice = check_submission(task["prompt"], store, retrieved_all, calls,
                                                memlab.parse_final(cand_text))
                if rule:
                    rcs_used = True
                    rcs_events.append({"step": step, "rule": rule, "submission": cand_text, "notice": notice})
                    if sub is not None:
                        messages.append({"role": "assistant", "content": msg.get("content") or "",
                                         "tool_calls": [sub]})
                        messages.append({"role": "tool", "tool_call_id": sub.get("id"), "name": "submit_answer",
                                         "content": notice})
                    else:
                        messages.append({"role": "assistant", "content": cand_text})
                        messages.append({"role": "user", "content": notice})
                    continue
            draft_text = cand_text
            if sub is not None:
                try:
                    d = json.loads(draft_text)
                    if isinstance(d, dict) and d.get("status") != "answer":
                        d["value"] = None
                    draft_text = json.dumps(d)
                except Exception:
                    pass
            messages.append({"role": "assistant", "content": draft_text})
            break
        messages.append({"role": "assistant", "content": msg.get("content") or "", "tool_calls": tcs})
        for tc in tcs:
            name = tc["function"]["name"]
            try:
                args = json.loads(tc["function"]["arguments"] or "{}")
                assert isinstance(args, dict)
            except Exception:
                args = None
            retrieved = None
            if args is None:
                status, obs = "VALIDATION_ERROR", f"ERROR: arguments for '{name}' are not a JSON object"
            elif name == "calculator" and isinstance(args.get("expression"), str):
                try:
                    obs = memlab._calculator(args["expression"])
                    status = "OK" if obs != "Invalid characters in expression." else "TOOL_ERROR"
                except Exception as e:
                    status, obs = "TOOL_ERROR", f"ERROR running tool 'calculator': {e}"
            elif name == "registry_lookup" and isinstance(args.get("entity"), str) and "attribute" in args:
                status, obs = registry.call(args["entity"], args["attribute"])
            elif name == "memory_search" and store is not None and isinstance(args.get("query"), str):
                r0 = time.monotonic()
                obs, retrieved = memlab.memory_tool_result(store, args["query"], cfg)
                t_ret += time.monotonic() - r0
                status = "OK"
                try:  # records actually shown (including ones added by the reliability check)
                    retrieved_all |= {r["record_id"] for r in json.loads(obs)["results"] if "record_id" in r}
                except Exception:
                    pass
                retrieved_all |= set(retrieved)
            else:
                status, obs = "VALIDATION_ERROR", f"ERROR: unknown tool or invalid arguments for '{name}'"
            calls.append({"step": step, "name": name, "arguments": args, "status": status, "observation": obs,
                          "retrieved_ids": retrieved})
            evidence.append({"tool": name, "arguments": args, "result": obs})
            messages.append({"role": "tool", "tool_call_id": tc.get("id"), "name": name, "content": obs})
    else:
        hit_max = True
    draft = memlab.parse_final(draft_text)
    final, verdict = draft, None
    if cfg["verify"] and draft and draft.get("status") == "answer":
        vmsg = [{"role": "system", "content": memlab.VERIFIER_PROMPT},
                {"role": "user", "content": "QUESTION:\n" + task["prompt"] + "\n\nEVIDENCE:\n"
                 + json.dumps(evidence, ensure_ascii=False) + "\n\nDRAFT ANSWER:\n"
                 + json.dumps(draft, ensure_ascii=False)}]
        vresp = client.chat(vmsg)
        api.append({"role": "verifier", "step": 0, **{k: vresp.get(k) for k in memlab.API_KEYS}})
        vraw = vresp["message"].get("content") or ""
        vparsed = memlab.parse_final(vraw) or {}
        v = str(vparsed.get("verdict", "")).upper()
        verdict = {"raw": vraw, "verdict": v if v in ("SUPPORTED", "UNSUPPORTED", "CONFLICT") else "UNPARSED",
                   "reason": vparsed.get("reason")}
        if v == "UNSUPPORTED":
            final = {"status": "abstain", "value": None, "evidence": [], "note": "verifier: unsupported"}
        elif v == "CONFLICT":
            final = {"status": "conflict", "value": None, "evidence": [], "note": "verifier: conflict"}
    wait = sum(a["wait_s"] for a in api)
    return {"record_type": "run", "task_id": task["task_id"], "config": config, "harness": harness,
            "p1_version": P1_VERSION, "repair_used": repaired, "rcs_events": rcs_events, "messages": messages,
            "tool_calls": calls, "api_calls": api, "draft_text": draft_text, "draft": draft, "verdict": verdict,
            "final": final, "hit_max_steps": hit_max,
            "timing": {"total_s": round(time.monotonic() - t0 - wait, 4), "rate_limit_wait_s": round(wait, 2),
                       "model_s": round(sum(a["latency_s"] for a in api), 4), "retrieval_s": round(t_ret, 6)}}
