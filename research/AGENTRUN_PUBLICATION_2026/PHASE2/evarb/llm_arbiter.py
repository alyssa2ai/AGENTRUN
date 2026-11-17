"""LLM evidence arbiter (baseline): the same Resolution schema, decided by a language model.

This is the DISCERN/CUPMem-style alternative to a deterministic arbiter: the model reads the
records of one (entity, attribute) group (text, recorded_on, source) and returns, as JSON, a
status and an evidence basis for every record. Its output is mapped onto evarb.arbiter.Resolution,
so the same renderer and the same gated policy can be used with it (configs LA, LG).

Strength of an LLM resolution is derived from the basis it reports, exactly as for the
deterministic arbiter (strong: record_time, valid_time, explicit_*, same_day_correction,
genuine_contradiction, negated_correction; moderate: source_authority; none: insufficient_evidence,
quoted_or_hypothetical). An unparsable or inconsistent answer becomes "unresolved"
(basis insufficient_evidence, strength none) and is counted as an arbiter format failure.
"""
from __future__ import annotations

import json
import re

from .arbiter import MODERATE, NONE, STRONG, Resolution

BASES = ["explicit_correction", "explicit_supersession", "valid_time", "record_time", "source_authority",
         "same_day_correction", "genuine_contradiction", "negated_correction", "quoted_or_hypothetical",
         "insufficient_evidence"]
STRENGTH = {b: STRONG for b in BASES}
STRENGTH.update({"source_authority": MODERATE, "insufficient_evidence": NONE, "quoted_or_hypothetical": NONE})

PROMPT = """You audit memory records about one fact of one project. Decide, for every record, whether its value is
current, superseded, contradictory (records really disagree and nothing shows which is current) or unresolved
(the evidence cannot establish the order). Use only the records below. Rules:
- A later recorded_on date makes a record newer, unless the record texts state validity dates ("as of", "effective",
  "valid from"); stated validity dates take precedence over recorded_on.
- A record that explicitly corrects, replaces or dismisses the other value supersedes it. A record that says it does
  NOT replace the other value, that a change is not confirmed, proposed, conditional ("if", "would") or only reported
  ("X wrote ...") does not supersede anything.
- Same date, different values and no such evidence: contradictory.
Also give the evidence basis, one of: """ + ", ".join(BASES) + """.
Answer with JSON only, in this form:
{"records": {"<record_id>": {"status": "current|superseded|contradictory|unresolved", "basis": "<basis>"}}}

RECORDS:
"""


class LLMArbiter:
    def __init__(self, client, max_new_tokens: int = 300):
        self.client = client
        self.n_calls = 0
        self.n_parse_fail = 0

    def describe(self) -> dict:
        return {"arbiter": "llm", "model": getattr(self.client, "model_id", None), "prompt_chars": len(PROMPT)}

    def arbitrate(self, group: list[dict]) -> tuple[Resolution, dict]:
        key = (group[0].get("entity"), group[0].get("attribute"))
        ids = [g["record_id"] for g in group]
        if len({str(g.get("value")) for g in group}) <= 1:
            return (Resolution(key, "unchallenged", None, STRONG, group[0].get("value"),
                               {i: {"status": "unchallenged"} for i in ids}), {"key": list(key), "called": False})
        recs = [{"record_id": g["record_id"], "text": g.get("text"), "recorded_on": g.get("recorded_on"),
                 "source": g.get("source")} for g in group]
        resp = self.client.chat([{"role": "user", "content": PROMPT + json.dumps(recs, ensure_ascii=False)}])
        self.n_calls += 1
        raw = (resp.get("message") or {}).get("content") or resp.get("raw_text") or ""
        log = {"key": list(key), "called": True, "raw": raw[:2000], "latency_s": resp.get("latency_s"),
               "usage": resp.get("usage")}
        res = parse_response(key, group, raw)
        log["parsed"] = res is not None
        if res is None:
            self.n_parse_fail += 1
            res = Resolution(key, "unresolved", "insufficient_evidence", NONE, None,
                             {i: {"status": "unresolved", "basis": "insufficient_evidence", "strength": NONE,
                                  "note": "arbiter output unparsable"} for i in ids})
        return res, log


def parse_response(key, group, raw: str) -> Resolution | None:
    m = re.search(r"\{.*\}", raw or "", re.S)
    if not m:
        return None
    try:
        data = json.loads(m.group(0))
        recs = data["records"]
    except (json.JSONDecodeError, KeyError, TypeError):
        return None
    by_id = {g["record_id"]: g for g in group}
    statuses = {}
    for rid in by_id:
        x = recs.get(rid) if isinstance(recs, dict) else None
        if not isinstance(x, dict):
            return None
        st = str(x.get("status", "")).lower()
        basis = str(x.get("basis", "")).lower()
        if st not in ("current", "superseded", "contradictory", "unresolved") or basis not in BASES:
            return None
        statuses[rid] = {"status": st, "basis": basis, "strength": STRENGTH[basis]}
    cur_vals = {str(by_id[r]["value"]) for r, s in statuses.items() if s["status"] == "current"}
    sts = {s["status"] for s in statuses.values()}
    if len(cur_vals) == 1:
        cv = cur_vals.pop()
        cur = sorted(r for r, s in statuses.items() if s["status"] == "current")
        for r, s in statuses.items():
            if s["status"] == "superseded":
                s["superseded_by"] = cur
        basis = statuses[cur[0]]["basis"]
        return Resolution(key, "resolved", basis, STRENGTH[basis], by_id[cur[0]]["value"], statuses)
    if len(cur_vals) > 1:
        return None  # inconsistent: two different current values
    if "contradictory" in sts:
        b = next(s["basis"] for s in statuses.values() if s["status"] == "contradictory")
        return Resolution(key, "contradiction", b, STRENGTH.get(b, NONE), None, statuses)
    return Resolution(key, "unresolved", "insufficient_evidence", NONE, None, statuses)
