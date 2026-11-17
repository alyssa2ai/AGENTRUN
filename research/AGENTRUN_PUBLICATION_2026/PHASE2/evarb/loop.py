"""Agent loop for the Phase 2 configurations.

Phase 1 configurations (A, B, E, G, R, T, RT) are dispatched to the UNCHANGED Phase 1 code
(rcs.run_task / tea.run_task). Phase 2 configurations use `run_task` below. The loop is the
Phase 1 loop (same prompts, tools, step budget, repair notice, scoring fields) with three hooks:
labels from a resolver, the basis-gated policy at the terminal action, and reversible notices.

Phase 2 configurations:
  EB         evidence-basis labels (evarb arbiter), advisory only
  EBG        EB + basis-gated enforcement (strong only) + search-before-submit + safe submission  [proposed]
  EBG-all    EBG enforcing strong and moderate resolutions                     (ablation: gating)
  EBG-unsafe EBG without reverting failed post-notice submissions              (ablation: safe submission)
  EBG-noR3   EBG without search-before-submit                                  (ablation: R3)
  LA         LLM-arbiter labels (same model as the agent), advisory            (baseline)
  LG         LLM-arbiter labels + the same gated policy and safe submission    (baseline)
"""
from __future__ import annotations

import json
import time

from . import paths  # noqa: F401
from .arbiter import arbitrate
from .policy import decide, question_intent
from .render import memory_tool_result
import memlab  # noqa: E402
import rcs  # noqa: E402
import tea  # noqa: E402

P2_VERSION = "evarb-loop-0.2"
PHASE1_CONFIGS = {"A", "B", "E", "G", "R", "T", "RT"}
CONFIGS = {
    "EB": dict(resolver="evarb", mode="none", r3=False, safe=True),
    "EBG": dict(resolver="evarb", mode="gated", r3=True, safe=True),
    "EBG-all": dict(resolver="evarb", mode="all", r3=True, safe=True),
    "EBG-unsafe": dict(resolver="evarb", mode="gated", r3=True, safe=False),
    "EBG-noR3": dict(resolver="evarb", mode="gated", r3=False, safe=True),
    "LA": dict(resolver="llm", mode="none", r3=False, safe=True),
    "LG": dict(resolver="llm", mode="gated", r3=True, safe=True),
}
ALL_CONFIGS = sorted(PHASE1_CONFIGS) + list(CONFIGS)


def run_any(client, task: dict, config: str, harness: str = "v2", llm_arbiter=None) -> dict:
    if config in ("T", "RT"):
        run = tea.run_task(client, task, config, harness=harness)
    elif config in PHASE1_CONFIGS:
        run = rcs.run_task(client, task, config, harness=harness)
    else:
        return run_task(client, task, config, harness=harness, llm_arbiter=llm_arbiter)
    run["p2_version"] = None
    return run


def run_task(client, task: dict, config: str, harness: str = "v2", llm_arbiter=None) -> dict:
    cfg = CONFIGS[config]
    store = memlab.MemoryStore(task["memory"], None)
    hv = memlab.HARNESSES[harness]
    registry = memlab.Registry(task["registry"])
    tools = [memlab.CALC_TOOL, memlab.REG_TOOL, memlab.MEM_TOOL, memlab.SUBMIT_TOOL]
    messages = [{"role": "system", "content": hv["system"]}, {"role": "user", "content": task["prompt"]}]
    intent = question_intent(task["prompt"])
    calls, api, retrieved_all = [], [], set()
    resolutions, groups, arb_log = {}, {}, []

    def resolve(group):
        key = (group[0]["entity"], group[0]["attribute"])
        if key not in resolutions:
            if cfg["resolver"] == "llm":
                res, log = llm_arbiter.arbitrate(group)
                arb_log.append(log)
            else:
                res = arbitrate(group)
            resolutions[key], groups[key] = res, group
        return resolutions[key]

    repaired, notice_used, events = False, False, []
    pre_notice, draft_text, hit_max, t_ret = None, None, False, 0.0
    t0 = time.monotonic()
    max_steps = memlab.MAX_STEPS + (1 if cfg["mode"] != "none" or cfg["r3"] else 0)
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
            parsed = memlab.parse_final(cand_text)
            if not notice_used and step < max_steps and (cfg["mode"] != "none" or cfg["r3"]):
                d = decide(task["prompt"], resolutions, groups, retrieved_all, calls, parsed, mode=cfg["mode"],
                           r3=cfg["r3"])
                events.append({"step": step, "action": d.action, "rule": d.rule, "submission": cand_text,
                               "key": list(d.key) if d.key else None})
                if d.action in ("ENFORCE", "REQUEST_EVIDENCE"):
                    notice_used = True
                    events[-1]["notice"] = d.notice
                    if (parsed or {}).get("status"):
                        pre_notice = cand_text
                    if sub is not None:
                        messages.append({"role": "assistant", "content": msg.get("content") or "", "tool_calls": [sub]})
                        messages.append({"role": "tool", "tool_call_id": sub.get("id"), "name": "submit_answer",
                                         "content": d.notice})
                    else:
                        messages.append({"role": "assistant", "content": cand_text})
                        messages.append({"role": "user", "content": d.notice})
                    continue
            draft_text = cand_text
            if sub is not None:
                try:
                    dj = json.loads(draft_text)
                    if isinstance(dj, dict) and dj.get("status") != "answer":
                        dj["value"] = None
                    draft_text = json.dumps(dj)
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
            elif name == "memory_search" and isinstance(args.get("query"), str):
                r0 = time.monotonic()
                obs, retrieved = memory_tool_result(store, args["query"], resolve, intent["intent"])
                t_ret += time.monotonic() - r0
                status = "OK"
                try:
                    retrieved_all |= {r["record_id"] for r in json.loads(obs)["results"]}
                except Exception:
                    pass
                retrieved_all |= set(retrieved)
            else:
                status, obs = "VALIDATION_ERROR", f"ERROR: unknown tool or invalid arguments for '{name}'"
            calls.append({"step": step, "name": name, "arguments": args, "status": status, "observation": obs,
                          "retrieved_ids": retrieved})
            messages.append({"role": "tool", "tool_call_id": tc.get("id"), "name": name, "content": obs})
    else:
        hit_max = True
    draft = memlab.parse_final(draft_text)
    reverted = False
    if cfg["safe"] and pre_notice is not None and (hit_max or not (draft or {}).get("status")):
        draft_text, draft, hit_max, reverted = pre_notice, memlab.parse_final(pre_notice), False, True
    wait = sum(a["wait_s"] for a in api)
    return {"record_type": "run", "task_id": task["task_id"], "config": config, "harness": harness,
            "p2_version": P2_VERSION, "repair_used": repaired, "rcs_events": [e for e in events if e.get("notice")],
            "policy_events": events, "reverted": reverted, "intent": intent,
            "resolutions": {f"{k[0]}|{k[1]}": {"kind": r.kind, "basis": r.basis, "strength": r.strength,
                                                "current_value": r.current_value,
                                                "statuses": {i: s["status"] for i, s in r.statuses.items()}}
                            for k, r in resolutions.items()},
            "llm_arbiter_log": arb_log, "messages": messages, "tool_calls": calls, "api_calls": api,
            "draft_text": draft_text, "draft": draft, "verdict": None, "final": draft, "hit_max_steps": hit_max,
            "timing": {"total_s": round(time.monotonic() - t0 - wait, 4), "rate_limit_wait_s": round(wait, 2),
                       "model_s": round(sum(a["latency_s"] for a in api), 4), "retrieval_s": round(t_ret, 6)}}
