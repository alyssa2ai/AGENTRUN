"""Evidence-basis arbitration for one (entity, attribute) group of memory records.

Output per record: status in {current, superseded, contradictory, unresolved, unchallenged},
plus the evidence `basis` and its `strength` (strong | moderate | none). "historical" is not an
arbiter status: the renderer shows a superseded record as historical when the question asks
about the past (policy.question_intent), because history is a property of the question.

Bases (the ten classes of the Phase 2 brief):
  explicit_correction     a record asserts a correction / dismissal of the rival and refers to it
  explicit_supersession   a record asserts it replaces / revises the rival and refers to it
  valid_time              every competing record states a validity date in its text
  record_time             a unique latest `recorded_on`
  source_authority        a tie broken only by an authoritative source (advisory only)
  same_day_correction     an asserted correction/supersession between records of the same date
  genuine_contradiction   same time, different values, no ordering evidence; or the text says both stand
  negated_correction      a correction/supersession cue under negation, or an explicit retention /
                          non-confirmation of the change
  quoted_or_hypothetical  the only ordering cue is reported speech or a conditional
  insufficient_evidence   the evidence cannot establish an order (missing dates, cyclic or
                          contradictory cues, text against metadata)

Precedence: non-established records (proposals, conditionals, retained-against) are set aside;
then asserted text edges; then validity dates; then record time; then source authority; else
contradiction or unresolved. Strength:
  strong    record_time; valid_time; explicit_* / same_day_correction that refer to the rival;
            genuine_contradiction with no cue of any kind, or with an explicit "both stand"
  moderate  an asserted correction that does not refer to the rival (single rival); source_authority;
            retention / non-confirmation / hypothetical set-asides
  none      unresolved
Deterministic, no LLM, never sees the expected answer.
"""
from __future__ import annotations

from dataclasses import dataclass, field

from .cues import RecordCues, analyse, refers_to

AUTHORITATIVE = {"system_of_record", "tool:registry_lookup", "official_registry", "signed_contract", "registry"}
EDGE_KINDS = ("correction", "supersession", "dismissal")
STRONG, MODERATE, NONE = "strong", "moderate", "none"


@dataclass
class Resolution:
    key: tuple
    kind: str  # unchallenged | resolved | contradiction | unresolved
    basis: str | None
    strength: str
    current_value: object = None
    statuses: dict = field(default_factory=dict)
    note: str = ""

    def status(self, rid: str) -> dict:
        return self.statuses[rid]


def _v(r):
    return str(r.get("value"))


def _edge_basis(clause, same_time: bool) -> str:
    if same_time:
        return "same_day_correction"
    return "explicit_supersession" if clause.kind == "supersession" else "explicit_correction"


def arbitrate(group: list[dict]) -> Resolution:
    key = (group[0].get("entity"), group[0].get("attribute")) if group else (None, None)
    ids = [g["record_id"] for g in group]
    values = {_v(g) for g in group}
    if len(values) <= 1:
        return Resolution(key, "unchallenged", None, STRONG, group[0].get("value") if group else None,
                          {i: {"status": "unchallenged"} for i in ids})
    cues: dict[str, RecordCues] = {g["record_id"]: analyse(g) for g in group}
    by_id = {g["record_id"]: g for g in group}
    statuses: dict[str, dict] = {}
    notes = []

    # 1. Set aside records that do not establish their own value.
    set_aside = {}
    for g in group:
        c = cues[g["record_id"]]
        own_unconf = [x for x in c.of("unconfirmed") if not x.negated]
        own_hypo = [x for x in c.clauses if x.hypothetical and x.kind in EDGE_KINDS + ("unconfirmed", "hypothetical_value")]
        if own_unconf:
            set_aside[g["record_id"]] = ("negated_correction", "the record says its value is not confirmed / proposed")
        elif own_hypo and not c.of(*EDGE_KINDS, asserted=True):
            set_aside[g["record_id"]] = ("quoted_or_hypothetical", "the record's change is conditional or hypothetical")
    # explicit retention: r says the rival's value remains valid -> r set aside, rival kept
    contra_marker = any(cl.kind == "contradiction" and not cl.negated for c in cues.values() for cl in c.clauses)
    for g in group:
        c = cues[g["record_id"]]
        rivals = [q for q in group if _v(q) != _v(g)]
        n_rv = len({_v(q) for q in rivals})
        for cl in c.of("retention"):
            if not cl.negated and any(refers_to(cl, q, n_rv) for q in rivals):
                set_aside.setdefault(g["record_id"], ("negated_correction", "the record says the other value remains valid"))
        # evarb-0.2: "does not replace <rival>" without any "both stand / disagree" marker -> the record defers
        if not contra_marker:
            for cl in c.of(*EDGE_KINDS):
                if cl.negated and any(refers_to(cl, q, n_rv) or n_rv == 1 for q in rivals):
                    set_aside.setdefault(g["record_id"], ("negated_correction",
                                                          "the record says it does not replace the other value"))
        # evarb-0.2: own value only reported, conditional or inside a negated replacement -> not established
        if not c.own_value_asserted and g["record_id"] not in set_aside:
            basis = "negated_correction" if any(cl.negated for cl in c.of(*EDGE_KINDS)) else "quoted_or_hypothetical"
            set_aside[g["record_id"]] = (basis, "the record does not assert its own value as a fact")
    established = [g for g in group if g["record_id"] not in set_aside]
    for rid, (basis, why) in set_aside.items():
        statuses[rid] = {"status": "unresolved", "basis": basis, "strength": MODERATE, "note": why}
    if not established:
        for g in group:
            statuses[g["record_id"]]["strength"] = NONE
        return Resolution(key, "unresolved", "insufficient_evidence", NONE, None, statuses,
                          "no record establishes a value")
    est_values = {_v(g) for g in established}
    if len(est_values) == 1:
        cv = established[0]
        basis = next(iter(set_aside.values()))[0] if set_aside else None
        for g in established:
            statuses[g["record_id"]] = {"status": "current", "basis": basis, "strength": MODERATE,
                                        "note": "the competing record does not establish its value"}
        return Resolution(key, "resolved", basis, MODERATE, cv.get("value"), statuses)

    # 2. Asserted text edges among established records (r supersedes q).
    edges, weak, negated_pairs, contra_text = [], {}, set(), False
    for g in established:
        c = cues[g["record_id"]]
        rivals = [q for q in established if _v(q) != _v(g)]
        n_rv = len({_v(q) for q in rivals})
        for cl in c.clauses:
            if cl.kind == "contradiction" and not cl.negated:
                contra_text = True
            if cl.kind not in EDGE_KINDS:
                continue
            for q in rivals:
                ref = refers_to(cl, q, n_rv)
                same = g.get("recorded_on") == q.get("recorded_on")
                if cl.negated and (ref or n_rv == 1):
                    negated_pairs.add(frozenset((g["record_id"], q["record_id"])))
                elif cl.quoted or cl.hypothetical:
                    notes.append(f"{g['record_id']}: reported or hypothetical cue ignored")
                elif ref:
                    edges.append((g, q, _edge_basis(cl, same), STRONG))
                elif n_rv == 1 and cl.kind != "supersession":  # unreferenced correction/dismissal: tie-break only
                    weak.setdefault(g["record_id"], set()).add(q["record_id"])
    if negated_pairs or contra_text:
        involved = {rid for p in negated_pairs for rid in p} or {g["record_id"] for g in established}
        for g in established:
            if g["record_id"] in involved:
                statuses[g["record_id"]] = {"status": "contradictory", "basis": "negated_correction" if negated_pairs
                                            else "genuine_contradiction", "strength": STRONG,
                                            "conflicts_with": sorted(r["record_id"] for r in established
                                                                     if _v(r) != _v(g) and r["record_id"] in involved),
                                            "note": "the record text says the values are not a replacement of each other"}
        if all(g["record_id"] in statuses for g in established):
            return Resolution(key, "contradiction", "negated_correction" if negated_pairs else "genuine_contradiction",
                              STRONG, None, statuses, "; ".join(notes))
    if edges:
        winners = {_v(e[0]) for e in edges}
        losers = {_v(e[1]) for e in edges}
        sinks = winners - losers
        if len(sinks) == 1 and (est_values - sinks) <= losers and not (winners & losers):
            cv = sinks.pop()
            strength = STRONG if all(e[3] == STRONG for e in edges if _v(e[0]) == cv) else MODERATE
            basis = sorted({e[2] for e in edges if _v(e[0]) == cv})[0]
            # text edge against metadata order (winner recorded strictly earlier) -> not enforced
            if any(e[0].get("recorded_on") and e[1].get("recorded_on") and e[0]["recorded_on"] < e[1]["recorded_on"]
                   for e in edges if _v(e[0]) == cv):
                strength = MODERATE
                notes.append("the correcting record is older than the corrected one by recorded_on")
            cur = sorted(g["record_id"] for g in established if _v(g) == cv)
            for g in established:
                statuses[g["record_id"]] = ({"status": "current", "basis": basis, "strength": strength}
                                            if _v(g) == cv else
                                            {"status": "superseded", "basis": basis, "strength": strength,
                                             "superseded_by": cur})
            return Resolution(key, "resolved", basis, strength, by_id[cur[0]].get("value"), statuses, "; ".join(notes))
        for g in established:
            statuses[g["record_id"]] = {"status": "unresolved", "basis": "insufficient_evidence", "strength": NONE,
                                        "note": "the records' correction cues are inconsistent"}
        return Resolution(key, "unresolved", "insufficient_evidence", NONE, None, statuses)

    # 3. Validity dates in every established record's text.
    vf = {g["record_id"]: cues[g["record_id"]].valid_from for g in established}
    if all(vf.values()):
        return _order(key, established, lambda g: vf[g["record_id"]], "valid_time", statuses, notes, cues, weak)
    # 4. Record time.
    if all(g.get("recorded_on") for g in established):
        return _order(key, established, lambda g: g["recorded_on"], "record_time", statuses, notes, cues, weak)
    for g in established:
        statuses[g["record_id"]] = {"status": "unresolved", "basis": "insufficient_evidence", "strength": NONE,
                                    "note": "some records have no date in metadata or text"}
    return Resolution(key, "unresolved", "insufficient_evidence", NONE, None, statuses)


def _order(key, established, timef, basis, statuses, notes, cues, weak=None) -> Resolution:
    top = max(timef(g) for g in established)
    tied = [g for g in established if timef(g) == top]
    weak = weak or {}
    if len({_v(g) for g in tied}) > 1:  # unreferenced correction cue breaks a same-time tie (moderate)
        tied_ids = {g["record_id"] for g in tied}
        claimers = [g for g in tied if (weak.get(g["record_id"], set()) & tied_ids)]
        cv_set = {_v(g) for g in claimers}
        if len(cv_set) == 1 and not any(weak.get(q["record_id"], set()) & {c["record_id"] for c in claimers}
                                        for q in tied):
            cv = cv_set.pop()
            cur = sorted(g["record_id"] for g in established if _v(g) == cv)
            for g in established:
                statuses[g["record_id"]] = ({"status": "current", "basis": "same_day_correction", "strength": MODERATE,
                                             "note": "same date; this record says it corrects, without naming the old value"}
                                            if _v(g) == cv else
                                            {"status": "superseded", "basis": "same_day_correction",
                                             "strength": MODERATE, "superseded_by": cur})
            return Resolution(key, "resolved", "same_day_correction", MODERATE, claimers[0].get("value"), statuses)
    if len({_v(g) for g in tied}) == 1:
        cv = _v(tied[0])
        cur = sorted(g["record_id"] for g in established if _v(g) == cv)
        rec_latest = max((g.get("recorded_on") or "") for g in established)
        disagrees = basis == "valid_time" and any(g.get("recorded_on") == rec_latest and _v(g) != cv for g in established)
        # evarb-0.2: a winner by time order whose text signals deliberation or doubt is advised, not enforced
        doubt = any(cues[g["record_id"]].doubt for g in established if _v(g) == cv)
        sv = MODERATE if doubt else STRONG
        for g in established:
            st = ({"status": "current", "basis": basis, "strength": sv} if _v(g) == cv else
                  {"status": "superseded", "basis": basis, "strength": sv, "superseded_by": cur})
            if doubt:
                st["note"] = "the newer record's wording signals deliberation or doubt"
            if basis == "valid_time":
                st["valid_from"] = cues[g["record_id"]].valid_from
                if disagrees:
                    st["note"] = "order from the validity dates stated in the texts; it differs from recorded_on"
            statuses[g["record_id"]] = st
        return Resolution(key, "resolved", basis, sv, tied[0].get("value"), statuses, "; ".join(notes))
    # tie at the top: source authority (advisory), else contradiction
    auth = [g for g in tied if str(g.get("source", "")).lower() in AUTHORITATIVE]
    if len({_v(g) for g in auth}) == 1 and len(auth) < len(tied):
        cv = _v(auth[0])
        cur = sorted(g["record_id"] for g in established if _v(g) == cv)
        for g in established:
            statuses[g["record_id"]] = ({"status": "current", "basis": "source_authority", "strength": MODERATE}
                                        if _v(g) == cv else
                                        {"status": "superseded", "basis": "source_authority", "strength": MODERATE,
                                         "superseded_by": cur})
        return Resolution(key, "resolved", "source_authority", MODERATE, auth[0].get("value"), statuses)
    reported = [g for g in tied if any((c.quoted or c.hypothetical) and c.kind in EDGE_KINDS
                                       for c in cues[g["record_id"]].clauses)]
    if reported:
        for g in established:
            statuses[g["record_id"]] = ({"status": "unresolved", "basis": "quoted_or_hypothetical", "strength": NONE,
                                         "note": "a change is only reported or hypothetical; the order is not established"}
                                        if g in tied else
                                        {"status": "superseded", "basis": basis, "strength": STRONG,
                                         "superseded_by": sorted(r["record_id"] for r in tied)})
        return Resolution(key, "unresolved", "quoted_or_hypothetical", NONE, None, statuses)
    any_cue = any(cues[g["record_id"]].clauses for g in tied)
    strength = MODERATE if any_cue else STRONG
    for g in established:
        if g in tied:
            statuses[g["record_id"]] = {"status": "contradictory", "basis": "genuine_contradiction", "strength": strength,
                                        "conflicts_with": sorted(r["record_id"] for r in tied if _v(r) != _v(g)),
                                        "note": f"same {'stated validity date' if basis == 'valid_time' else 'recorded_on date'}"
                                                ", different values, no evidence which is current"}
        else:
            statuses[g["record_id"]] = {"status": "superseded", "basis": basis, "strength": STRONG,
                                        "superseded_by": sorted(r["record_id"] for r in tied)}
    return Resolution(key, "contradiction", "genuine_contradiction", strength, None, statuses, "; ".join(notes))


def arbitrate_store(records: list[dict]) -> dict[tuple, Resolution]:
    groups: dict[tuple, list] = {}
    for r in records:
        groups.setdefault((r.get("entity"), r.get("attribute")), []).append(r)
    return {k: arbitrate(v) for k, v in groups.items()}
