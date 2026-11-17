"""Basis-gated enforcement and safe submission.

At the agent's terminal action the policy compares the submission with the arbiter's resolution of
the groups the agent itself retrieved whose entity is named in the question ("anchored"), and
returns one of four actions:

  ENFORCE           send one corrective notice (the next submission is final)
  REQUEST_EVIDENCE  send one notice asking for the missing search (search-before-submit)
  ADVISE            no notice; the labels already shown are the only intervention
  NO_ACTION         nothing to say

Gating (mode="gated", the proposed policy): a resolution is enforced only if its strength is
"strong" (record_time, valid_time, explicit_* or same_day_correction that refers to the rival,
genuine_contradiction / negated_correction without any competing cue). Moderate resolutions
(source authority, unreferenced corrections, retention/proposal set-asides) are ADVISE only;
unresolved groups are never enforced. mode="all" enforces strong and moderate (ablation);
mode="none" never enforces (labels only).

Rules (first match):
  P3  no memory_search and no successful registry result                     -> REQUEST_EVIDENCE
  P1  current-state question, answer = a superseded value, not the current one -> ENFORCE
  P2  status conflict, every anchored multi-value group resolved               -> ENFORCE
  P4  answer = one of the values of a contradictory group, no registry result  -> ENFORCE
Historical questions ("before the correction", "originally", "as of <date>") are never enforced
by P1/P2: there the superseded value can be the right answer.

Safe submission: every notice is reversible. If the submission after a notice is unparsable,
missing, or the step budget runs out, the run's final answer reverts to the pre-notice
submission (`reverted=True`). A notice can therefore change a wrong answer but cannot turn a
well-formed submission into a format error or a step-limit failure (Phase 1 M10).

Model capability is NOT an input. Whether enforcement helps a given model is measured, not
assumed (PREREGISTRATION.md H3).
"""
from __future__ import annotations

import re
from dataclasses import dataclass

from . import paths  # noqa: F401
from .arbiter import MODERATE, STRONG, Resolution
from .cues import DATE, mentions, parse_date
import memlab  # noqa: E402

PREFIX = "[harness check] "
HIST_RE = re.compile(r"\b(?:before (?:the |it was |its )?(?:correction|change|update|revision|amendment)|"
                     r"previous(?:ly)?|original(?:ly)?|initial(?:ly)?|used to|formerly|at first|prior to|"
                     r"earlier (?:value|figure)|first recorded|at the time|was (?:it|the \w+) (?:on|in))\b", re.I)
ASOF_RE = re.compile(r"\b(?:as of|on|at)\s+" + DATE, re.I)


@dataclass
class Decision:
    action: str
    rule: str | None = None
    notice: str | None = None
    key: tuple | None = None


def question_intent(question: str) -> dict:
    m = ASOF_RE.search(question or "")
    as_of = parse_date(m) if m else None
    hist = bool(HIST_RE.search(question or "")) or as_of is not None
    return {"intent": "historical" if hist else "current", "as_of": as_of}


def _matches(v, got) -> bool:
    if got is None or str(got).strip() == "":
        return False
    if isinstance(v, (int, float)) and not isinstance(v, bool):
        g = memlab._num(got)
        return g is not None and abs(g - float(v)) <= 0.011
    return memlab._norm(v) != "" and memlab._norm(v) in memlab._norm(got)


def _enforceable(res: Resolution, mode: str) -> bool:
    if mode == "none":
        return False
    if mode == "all":
        return res.strength in (STRONG, MODERATE)
    return res.strength == STRONG


def _why(res: Resolution, group: list[dict]) -> str:
    st = res.statuses
    by = {g["record_id"]: g for g in group}
    cur = sorted(r for r, s in st.items() if s["status"] == "current")
    old = sorted(r for r, s in st.items() if s["status"] == "superseded")
    if not cur:
        return ""
    c, o = by[cur[0]], (by[old[0]] if old else None)
    if res.basis == "record_time" and o:
        return (f"record {c['record_id']} (recorded {c.get('recorded_on')}) is newer than record {o['record_id']} "
                f"(recorded {o.get('recorded_on')}) and gives a different value")
    if res.basis == "valid_time" and o:
        return (f"record {c['record_id']} states it is valid from {st[c['record_id']].get('valid_from')}, later than "
                f"record {o['record_id']} ({st[o['record_id']].get('valid_from')})")
    if res.basis in ("explicit_correction", "explicit_supersession", "same_day_correction") and o:
        return f"record {c['record_id']} states that it corrects or replaces the value in record {o['record_id']}"
    return f"the evidence supports record {c['record_id']} as current ({res.basis})"


def decide(question: str, resolutions: dict, groups: dict, retrieved_ids: set[str], calls: list[dict],
           sub: dict | None, mode: str = "gated", r3: bool = True) -> Decision:
    if not isinstance(sub, dict):
        return Decision("NO_ACTION")
    status = sub.get("status")
    searched = any(c["name"] == "memory_search" for c in calls)
    registry_ok = any(c["name"] == "registry_lookup" and c["status"] == "OK" for c in calls)
    if r3 and not searched and not registry_ok:
        return Decision("REQUEST_EVIDENCE", "P3", PREFIX + "You submitted without searching memory. Facts from earlier "
                        "sessions are stored there: call memory_search, then submit again. If memory has nothing "
                        "relevant, your previous submission stands.")
    qn = memlab._norm(question)
    intent = question_intent(question)
    anchored = {k: r for k, r in resolutions.items()
                if k[0] and memlab._norm(k[0]) in qn and any(i in retrieved_ids for i in r.statuses)}
    if not anchored:
        return Decision("NO_ACTION")
    advise = False
    if status == "answer" and intent["intent"] == "current":
        v = sub.get("value")
        for k, res in anchored.items():
            if res.kind != "resolved":
                continue
            grp = groups[k]
            st = res.statuses
            stale = [g for g in grp if st[g["record_id"]]["status"] == "superseded" and _matches(g["value"], v)]
            if stale and not _matches(res.current_value, v):
                if _enforceable(res, mode):
                    return Decision("ENFORCE", "P1", PREFIX + f"Your value matches record {stale[0]['record_id']}, but "
                                    f"{_why(res, grp)}. Re-check and submit again.", k)
                advise = True
    if status == "conflict" and intent["intent"] == "current":
        multi = {k: r for k, r in anchored.items() if r.kind != "unchallenged"}
        if multi and all(r.kind == "resolved" for r in multi.values()):
            if all(_enforceable(r, mode) for r in multi.values()):
                why = "; ".join(_why(r, groups[k]) for k, r in multi.items())
                return Decision("ENFORCE", "P2", PREFIX + f"The retrieved records about this fact are ordered by the "
                                f"evidence: {why}. They are not an unresolved conflict. Submit again.", next(iter(multi)))
            advise = True
    if status == "answer" and not registry_ok:
        v = sub.get("value")
        for k, res in anchored.items():
            if res.kind == "contradiction":
                vals = [g for g in groups[k] if res.statuses[g["record_id"]]["status"] == "contradictory"]
                if any(_matches(g["value"], v) for g in vals):
                    if _enforceable(res, mode):
                        ids = ", ".join(sorted(g["record_id"] for g in vals))
                        return Decision("ENFORCE", "P4", PREFIX + f"Records {ids} give different values for this fact "
                                        "and nothing in the evidence shows which one is current. If no other source "
                                        "settles it, submit status \"conflict\". Submit again.", k)
                    advise = True
    return Decision("ADVISE" if advise else "NO_ACTION")
