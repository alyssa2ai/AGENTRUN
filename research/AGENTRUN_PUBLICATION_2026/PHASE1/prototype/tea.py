"""Phase 1 candidate: Temporal Evidence Arbitration (TEA).

The reliability gate in memlab (and in RCS) orders records only by `recorded_on`,
i.e. transaction time. When that metadata cannot order the records (same-day
corrections; bulk imports) or orders them wrongly (back-filled entries), the gate
asserts "conflicting" or "superseded" with full confidence, and the Phase 1 pilot
shows that models up to 8B follow the wrong label (S7/S8, G - B = -23 to -50 pp).

TEA replaces only the status function. For every (entity, attribute) group it
decides the order from the strongest available evidence and reports which
evidence it used (`basis`):

  1. text_valid_date  every competing record states a validity date in its text
                      ("as of", "effective", "valid from", "since", "dated", "updated on" + a date);
                      valid time outranks transaction time, also when they disagree
  2. recorded_on      otherwise, a unique latest `recorded_on` (the memlab rule)
  3. explicit_correction  on a tie, a record that carries a correction cue AND names
                      the rival's value supersedes the rival
  4. no_ordering_evidence  otherwise the tie is reported as "conflicting", with that basis
  (metadata_missing)  a record without `recorded_on` and no text date -> "unordered"

It is deterministic, uses no LLM and never sees the expected answer. The lexicons
below were fixed before the held-out split p1hold was run against them (p1hold.py
was frozen first; see FREEZE_p1hold.json). Known blind spots by design: negation
("does not replace"), corrections that do not name the old value, date cues
outside the list ("as at"), relative dates ("this morning").

Configurations: T = G with TEA labels (advisory); RT = R with TEA labels (the same
RCS rules R1-R3, now evaluated on TEA's state). The only code difference between
G/T and R/RT is the status function, swapped in for the duration of one run.
"""
from __future__ import annotations

import re
from contextlib import contextmanager
from datetime import date

import rcs

memlab = rcs.memlab
TEA_VERSION = "tea-0.1"

_MONTHS = {m: i for i, m in enumerate(["january", "february", "march", "april", "may", "june", "july", "august",
                                       "september", "october", "november", "december"], 1)}
_MON = r"(january|february|march|april|may|june|july|august|september|october|november|december)"
_DATE = (r"(?P<iso>\d{4}-\d{2}-\d{2})|(?P<dmy>\d{1,2} " + _MON + r" \d{4})|(?P<mdy>" + _MON
         + r" \d{1,2},? \d{4})")
_CUE = r"\b(as of|effective(?: from| on)?|valid from|since|dated|updated on)\b[\s:,]*"
VALID_DATE_RE = re.compile(_CUE + r"(?:" + _DATE + r")", re.I)
CORRECTION_RE = re.compile(r"\b(correct(?:ion|ed|s)?|erratum|was (?:a )?(?:mistake|wrong|incorrect|an error)|"
                           r"replace[sd]?|supersede[sd]?|instead of|no longer|revised|amended|update[sd]?)\b", re.I)


def _parse_date(m: re.Match) -> str | None:
    try:
        if m.group("iso"):
            return date.fromisoformat(m.group("iso")).isoformat()
        s = (m.group("dmy") or m.group("mdy")).lower().replace(",", "")
        parts = s.split()
        if m.group("dmy"):
            d, mon, y = int(parts[0]), _MONTHS[parts[1]], int(parts[2])
        else:
            mon, d, y = _MONTHS[parts[0]], int(parts[1]), int(parts[2])
        return date(y, mon, d).isoformat()
    except (ValueError, KeyError, IndexError):
        return None


def valid_date(rec: dict) -> str | None:
    """Validity date stated in the record text, if exactly one distinct one is found.
    A date equal to the record's own value (e.g. a deadline) is not a validity date."""
    own = str(rec.get("value"))
    found = {d for m in VALID_DATE_RE.finditer(rec.get("text") or "") if (d := _parse_date(m)) and d != own}
    return found.pop() if len(found) == 1 else None


def _mentions(text: str, value) -> bool:
    if isinstance(value, (int, float)) and not isinstance(value, bool):
        nums = re.findall(r"(?<![\d.])-?\d[\d,]*(?:\.\d+)?(?![\d])", text)
        return any(abs(float(n.replace(",", "")) - float(value)) < 1e-9 for n in nums)
    v = memlab._norm(value)
    return bool(v) and re.search(r"(?<![a-z0-9])" + re.escape(v) + r"(?![a-z0-9])", memlab._norm(text)) is not None


def corrects(rec: dict, rival: dict) -> bool:
    text = rec.get("text") or ""
    return (str(rec["value"]) != str(rival["value"]) and CORRECTION_RE.search(text) is not None
            and _mentions(text, rival["value"]))


def _resolve_tie(tied: list[dict], basis_if_none: str):
    """Records tied on the ordering key with >1 value: explicit correction or conflict."""
    vals = {str(g["value"]) for g in tied}
    winners = [g for g in tied if any(corrects(g, r) for r in tied if str(r["value"]) != str(g["value"]))]
    wv = {str(g["value"]) for g in winners}
    if len(wv) == 1 and not any(corrects(r, w) for w in winners for r in tied if str(r["value"]) not in wv):
        return wv.pop(), "explicit_correction"
    return None, basis_if_none if len(vals) > 1 else None


def arbitrate(group: list[dict]) -> dict[str, dict]:
    """Status for every record of one (entity, attribute) group."""
    ids = [g["record_id"] for g in group]
    if len({str(g["value"]) for g in group}) <= 1:
        return {i: {"status": "unchallenged"} for i in ids}
    vd = {g["record_id"]: valid_date(g) for g in group}
    if all(vd.values()):
        key, basis = (lambda g: vd[g["record_id"]]), "text_valid_date"
    elif all(g.get("recorded_on") for g in group):
        key, basis = (lambda g: g["recorded_on"]), "recorded_on"
    else:
        return {i: {"status": "unordered", "basis": "metadata_missing",
                    "note": "some records have no date in metadata or text; order unknown"} for i in ids}
    top = max(key(g) for g in group)
    tied = [g for g in group if key(g) == top]
    if len({str(g["value"]) for g in tied}) == 1:
        cur_val = str(tied[0]["value"])
    else:
        cur_val, tie_basis = _resolve_tie(tied, "no_ordering_evidence")
        if cur_val is None:
            out = {}
            for g in group:
                if g in tied:
                    out[g["record_id"]] = {"status": "conflicting", "basis": tie_basis,
                                           "conflicts_with": sorted(r["record_id"] for r in tied
                                                                    if str(r["value"]) != str(g["value"])),
                                           "note": f"same {'stated validity date' if basis == 'text_valid_date' else 'recorded_on date'}"
                                                   " and no explicit correction between them"}
                else:
                    out[g["record_id"]] = {"status": "superseded", "basis": basis,
                                           "superseded_by": sorted(r["record_id"] for r in tied)}
            return out
        basis = tie_basis
    current = sorted(g["record_id"] for g in tied if str(g["value"]) == cur_val)
    latest_rec = max((r.get("recorded_on") or "") for r in group)
    disagrees = basis == "text_valid_date" and any(
        g.get("recorded_on") == latest_rec and str(g["value"]) != cur_val for g in group)
    out = {}
    for g in group:
        if str(g["value"]) == cur_val:
            st = {"status": "current", "basis": basis}
        else:
            st = {"status": "superseded", "basis": basis, "superseded_by": current}
        if basis == "text_valid_date":
            st["valid_from"] = vd[g["record_id"]]
            if disagrees:
                st["note"] = "order taken from the validity dates in the record texts; it differs from recorded_on"
        elif basis == "explicit_correction":
            st["note"] = "same date; the current record states that it corrects the other value"
        out[g["record_id"]] = st
    return out


def reliability_status(rec: dict, group: list[dict]) -> dict:
    """Drop-in replacement for memlab.reliability_status."""
    return arbitrate(group)[rec["record_id"]]


CONFIGS = {
    "T": dict(rcs.CONFIGS["G"], label="T: G with TEA labels (advisory)", tea=True),
    "RT": dict(rcs.CONFIGS["R"], label="RT: R with TEA labels (RCS rules on TEA state)", tea=True),
}


@contextmanager
def tea_labels():
    orig = memlab.reliability_status
    memlab.reliability_status = reliability_status
    try:
        yield
    finally:
        memlab.reliability_status = orig


def run_task(client, task: dict, config: str, harness: str = "v2") -> dict:
    if config not in CONFIGS:
        run = rcs.run_task(client, task, config, harness=harness)
        run["tea_version"] = None
        return run
    base = "G" if config == "T" else "R"
    with tea_labels():
        run = rcs.run_task(client, task, base, harness=harness)
    run["config"] = config
    run["tea_version"] = TEA_VERSION
    return run
