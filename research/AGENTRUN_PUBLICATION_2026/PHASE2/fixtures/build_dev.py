"""Phase 2 DEVELOPMENT fixtures (not an evaluation set; the mechanism is tuned against these).

    py -3.11 PHASE2/fixtures/build_dev.py

Writes
  PHASE2/data/dev_groups.jsonl      component fixtures: one (entity, attribute) group + question + gold
  PHASE2/data/p2dev_tasks.jsonl     agent-level tasks (memlab task format) built from the same categories
  PHASE2/data/regression_groups.jsonl  exact Phase 1 failure groups (p1dev S7/S8, p1hold H7b/H9/N3)
  PHASE2/data/DEV_MANIFEST.json     counts and sha256

Gold for a group:  {"kind": "resolved", "current_value": v, "basis": b, "strength": s}  or
                   {"kind": "no_current", "acceptable": ["contradiction", "unresolved"], "basis": b}
`strength` in gold is the strongest the evidence justifies (strong / moderate). For agent tasks the
expected behaviour follows memlab: answer <value>, conflict (no current value), or abstain.
Missing timestamps are recorded_on = "" (the legacy gate sorts them as oldest).
Names: memlab name pool slice [10400:12800] (p1dev [5200:8000], p1hold [8000:10400]; eval3 will use
[12800:]). Seed 20261116.
"""
from __future__ import annotations

import hashlib
import json
import random
import sys
from datetime import date, timedelta
from pathlib import Path

HERE = Path(__file__).resolve().parent
P2 = HERE.parent
sys.path.insert(0, str(P2))
from evarb import paths  # noqa: E402,F401
import memlab  # noqa: E402
import p1hold  # noqa: E402
import rcs  # noqa: E402

SEED = 20261116
N_GROUP = 6   # component fixtures per category
N_TASK = 4    # agent tasks per category (subset of the same construction, fresh names)


class DevWorld(memlab._World):
    def __init__(self, seed):
        self.names = memlab._name_pool(12800)[10400:]
        self.rng = random.Random(seed)
        self.rng.shuffle(self.names)
        self._i = 0


def F(a, e, v):
    return memlab.ATTRS[a]["t"].format(e=e, v=v)


def longd(d):
    x = date.fromisoformat(d)
    return f"{x.day} {x.strftime('%B')} {x.year}"


def rec(e, a, v, d, src, text=None):
    return {"entity": e, "attribute": a, "value": v, "recorded_on": d, "source": src, "text": text or F(a, e, v)}


# Each category: builder(w, a, i) -> (records, question, gold, expected_task_kind)
def _pair(w, a):
    e = w.project()
    v1 = w.value(a)
    return e, v1, w.value(a, avoid=v1)


def c_temporal_update(w, a, i):
    e, old, new = _pair(w, a)
    d1 = w.day(0, 60)
    d2 = (date.fromisoformat(d1) + timedelta(days=w.rng.randrange(20, 90))).isoformat()
    s = w.rng.choice(memlab._SOURCES)
    return ([rec(e, a, old, d1, s), rec(e, a, new, d2, s)], memlab.ATTRS[a]["q"].format(e=e),
            {"kind": "resolved", "current_value": new, "basis": "record_time", "strength": "strong"}, ("answer", new, old))


def c_backfilled(w, a, i):
    e, old, new = _pair(w, a)
    v_old = w.day(0, 30)
    v_new = (date.fromisoformat(v_old) + timedelta(days=w.rng.randrange(20, 60))).isoformat()
    ent_new = (date.fromisoformat(v_new) + timedelta(days=3)).isoformat()
    ent_old = (date.fromisoformat(ent_new) + timedelta(days=w.rng.randrange(5, 25))).isoformat()
    fmt = (lambda d: d) if i % 2 == 0 else longd
    return ([rec(e, a, new, ent_new, "meeting_notes", f"Valid from {fmt(v_new)}: {F(a, e, new)}"),
             rec(e, a, old, ent_old, "imported_doc", f"Effective {fmt(v_old)}, {F(a, e, old)[0].lower()}{F(a, e, old)[1:]} "
                 "(entered late from an old spreadsheet)")],
            memlab.ATTRS[a]["q"].format(e=e),
            {"kind": "resolved", "current_value": new, "basis": "valid_time", "strength": "strong"}, ("answer", new, old))


def c_valid_time_same_import(w, a, i):
    e, old, new = _pair(w, a)
    d_old = w.day(0, 50)
    d_new = (date.fromisoformat(d_old) + timedelta(days=w.rng.randrange(30, 80))).isoformat()
    imp = w.day(130, 140)
    cue = ["Valid from", "Effective from", "Dated", "Updated on"][i % 4]
    return ([rec(e, a, old, imp, "imported_doc", f"{cue} {d_old}: {F(a, e, old)}"),
             rec(e, a, new, imp, "imported_doc", f"{cue} {d_new}: {F(a, e, new)}")],
            memlab.ATTRS[a]["q"].format(e=e),
            {"kind": "resolved", "current_value": new, "basis": "valid_time", "strength": "strong"}, ("answer", new, old))


SDC = [lambda f, o: f"{f} This corrects the figure of {o} entered earlier today.",
       lambda f, o: f"Amended entry: {f} The {o} recorded this morning is withdrawn.",
       lambda f, o: f"{f} (The previous value, {o}, was a typo.)",
       lambda f, o: f"Please discard the {o} noted at the start of the meeting. {f}",
       lambda f, o: f"Revision: {f} It supersedes {o}.",
       lambda f, o: f"{f} Ignore the earlier entry of {o}; it was incorrect."]


def c_same_day_named(w, a, i):
    e, old, new = _pair(w, a)
    d = w.day()
    s = w.rng.choice(memlab._SOURCES)
    return ([rec(e, a, old, d, s), rec(e, a, new, d, s, SDC[i % len(SDC)](F(a, e, new), old))],
            memlab.ATTRS[a]["q"].format(e=e),
            {"kind": "resolved", "current_value": new, "basis": "same_day_correction", "strength": "strong"},
            ("answer", new, old))


def c_same_day_unnamed(w, a, i):
    e, old, new = _pair(w, a)
    d = w.day()
    s = w.rng.choice(memlab._SOURCES)
    pre = ["Corrected:", "Erratum.", "Correction to today's entry:", "Amended:"][i % 4]
    return ([rec(e, a, old, d, s), rec(e, a, new, d, s, f"{pre} {F(a, e, new)}")], memlab.ATTRS[a]["q"].format(e=e),
            {"kind": "resolved", "current_value": new, "basis": "same_day_correction", "strength": "moderate"},
            ("answer", new, old))


def c_conflict_plain(w, a, i):
    e, v1, v2 = _pair(w, a)
    d = w.day()
    return ([rec(e, a, v1, d, "meeting_notes"), rec(e, a, v2, d, "imported_doc")], memlab.ATTRS[a]["q"].format(e=e),
            {"kind": "no_current", "acceptable": ["contradiction"], "basis": "genuine_contradiction"}, ("conflict",))


def c_conflict_same_text_date(w, a, i):
    e, v1, v2 = _pair(w, a)
    d = w.day()
    return ([rec(e, a, v1, d, "meeting_notes", f"Effective {d}: {F(a, e, v1)}"),
             rec(e, a, v2, d, "imported_doc", f"Effective {d}: {F(a, e, v2)}")], memlab.ATTRS[a]["q"].format(e=e),
            {"kind": "no_current", "acceptable": ["contradiction"], "basis": "genuine_contradiction"}, ("conflict",))


def c_conflict_rival_mentioned(w, a, i):
    e, v1, v2 = _pair(w, a)
    d = w.day()
    t = [f"{F(a, e, v2)} Finance lists {v1} instead.", f"{F(a, e, v2)} The other spreadsheet says {v1}.",
         f"{F(a, e, v2)} (Notes from the same call give {v1}.)"][i % 3]
    return ([rec(e, a, v1, d, "meeting_notes"), rec(e, a, v2, d, "imported_doc", t)], memlab.ATTRS[a]["q"].format(e=e),
            {"kind": "no_current", "acceptable": ["contradiction"], "basis": "genuine_contradiction"}, ("conflict",))


NEG = [lambda f, o: f"{f} This does not replace the {o} in the planning sheet; both figures stand until reconciled.",
       lambda f, o: f"{f} Note: this is not a correction of the {o} reported by finance.",
       lambda f, o: f"{f} It should not be read as superseding the {o} on file.",
       lambda f, o: f"{f} The {o} from the other team was not withdrawn, so the two values disagree.",
       lambda f, o: f"{f} Nobody has revised the {o} in the contract.",
       lambda f, o: f"{f} This doesn't override the {o} agreed earlier."]


def c_negated(w, a, i):
    """evarb-0.2 semantics (after the p2val annotation): a record that says it does not replace the other
    value defers to it, UNLESS the text says the values disagree / both stand (variants 0 and 3)."""
    e, v1, v2 = _pair(w, a)
    d = w.day()
    recs = [rec(e, a, v1, d, "meeting_notes"), rec(e, a, v2, d, "imported_doc", NEG[i % len(NEG)](F(a, e, v2), v1))]
    if i % len(NEG) in (0, 3):
        return (recs, memlab.ATTRS[a]["q"].format(e=e),
                {"kind": "no_current", "acceptable": ["contradiction"], "basis": "negated_correction"}, ("conflict",))
    return (recs, memlab.ATTRS[a]["q"].format(e=e),
            {"kind": "resolved", "current_value": v1, "basis": "negated_correction", "strength": "moderate"},
            ("answer", v1, v2))


def c_retention(w, a, i):
    e, old, new = _pair(w, a)
    d1 = w.day(0, 60)
    d2 = (date.fromisoformat(d1) + timedelta(days=10)).isoformat()
    t = [f"A value of {new} was floated for {e}, but the previous figure of {old} remains valid.",
         f"Someone suggested {new} for {e}; {old} still stands.",
         f"{e}: {new} was discussed. The existing value {old} is unchanged."][i % 3]
    return ([rec(e, a, old, d1, "meeting_notes"), rec(e, a, new, d2, "meeting_notes", t)],
            memlab.ATTRS[a]["q"].format(e=e),
            {"kind": "resolved", "current_value": old, "basis": "negated_correction", "strength": "moderate"},
            ("answer", old, new))


def c_unconfirmed(w, a, i):
    e, old, new = _pair(w, a)
    d1 = w.day(0, 60)
    d2 = (date.fromisoformat(d1) + timedelta(days=12)).isoformat()
    t = [f"Proposed change: {F(a, e, new)} Not yet approved.", f"Draft: {F(a, e, new)} Pending sign-off.",
         f"{F(a, e, new)} This update has not been confirmed."][i % 3]
    return ([rec(e, a, old, d1, "imported_doc"), rec(e, a, new, d2, "meeting_notes", t)],
            memlab.ATTRS[a]["q"].format(e=e),
            {"kind": "resolved", "current_value": old, "basis": "negated_correction", "strength": "moderate"},
            ("answer", old, new))


def c_quoted(w, a, i):
    e, v1, v2 = _pair(w, a)
    d = w.day()
    t = [f'A forwarded email said "the {v2} replaces the {v1}". {F(a, e, v2)}',
         f"According to a hallway conversation, {v2} supersedes {v1}. {F(a, e, v2)}",
         f'Sam claimed that the {v1} was a mistake. {F(a, e, v2)}'][i % 3]
    return ([rec(e, a, v1, d, "meeting_notes"), rec(e, a, v2, d, "user_statement", t)], memlab.ATTRS[a]["q"].format(e=e),
            {"kind": "no_current", "acceptable": ["unresolved", "contradiction"], "basis": "quoted_or_hypothetical"},
            ("conflict",))


def c_hypothetical(w, a, i):
    e, old, new = _pair(w, a)
    d1 = w.day(0, 60)
    d2 = (date.fromisoformat(d1) + timedelta(days=8)).isoformat()
    t = [f"If the extension is granted, {F(a, e, new)[0].lower()}{F(a, e, new)[1:]}",
         f"Were the merger to go ahead, the value for {e} would become {new} instead of {old}.",
         f"In case the review fails, {e} might move to {new}."][i % 3]
    return ([rec(e, a, old, d1, "imported_doc"), rec(e, a, new, d2, "meeting_notes", t)],
            memlab.ATTRS[a]["q"].format(e=e),
            {"kind": "resolved", "current_value": old, "basis": "quoted_or_hypothetical", "strength": "moderate"},
            ("answer", old, new))


def c_missing_ts(w, a, i):
    e, v1, v2 = _pair(w, a)
    d = w.day()
    r1, r2 = rec(e, a, v1, "", "imported_doc"), rec(e, a, v2, d, "meeting_notes")
    return ([r1, r2], memlab.ATTRS[a]["q"].format(e=e),
            {"kind": "no_current", "acceptable": ["unresolved"], "basis": "insufficient_evidence"}, ("conflict",))


def c_missing_ts_text_dated(w, a, i):
    e, old, new = _pair(w, a)
    d_old = w.day(0, 50)
    d_new = (date.fromisoformat(d_old) + timedelta(days=40)).isoformat()
    return ([rec(e, a, old, "", "imported_doc", f"As of {d_old}: {F(a, e, old)}"),
             rec(e, a, new, "", "imported_doc", f"As of {d_new}: {F(a, e, new)}")],
            memlab.ATTRS[a]["q"].format(e=e),
            {"kind": "resolved", "current_value": new, "basis": "valid_time", "strength": "strong"}, ("answer", new, old))


def c_authority_one(w, a, i):
    e, v1, v2 = _pair(w, a)
    d = w.day()
    return ([rec(e, a, v1, d, "meeting_notes"), rec(e, a, v2, d, "system_of_record")], memlab.ATTRS[a]["q"].format(e=e),
            {"kind": "resolved", "current_value": v2, "basis": "source_authority", "strength": "moderate"},
            ("answer", v2, v1))


def c_authority_both(w, a, i):
    e, v1, v2 = _pair(w, a)
    d = w.day()
    return ([rec(e, a, v1, d, "system_of_record"), rec(e, a, v2, d, "system_of_record")],
            memlab.ATTRS[a]["q"].format(e=e),
            {"kind": "no_current", "acceptable": ["contradiction"], "basis": "genuine_contradiction"}, ("conflict",))


HQ = {"budget_usd": "What was the approved budget, in USD, for {e} before it was changed?",
      "team_size": "How many people were originally on the team for {e}?",
      "port": "Which port did the staging server for {e} previously listen on?",
      "lead": "Who was the original lead of {e}?",
      "region": "In which cloud region was {e} previously hosted?",
      "deadline": "What was the delivery deadline for {e} before the change? Give the date as YYYY-MM-DD."}


def c_historical(w, a, i):
    recs, _, gold, _ = c_temporal_update(w, a, i)
    e = recs[0]["entity"]
    return (recs, HQ[a].format(e=e), dict(gold, intent="historical"), ("answer", recs[0]["value"], recs[1]["value"]))


def c_incidental_cue(w, a, i):
    """Adversarial: an incidental 'update' word, no correction meaning, same date -> still a contradiction."""
    e, v1, v2 = _pair(w, a)
    d = w.day()
    t = [f"Weekly status update: {F(a, e, v2)}", f"Updated project card: {F(a, e, v2)}",
         f"Revised meeting agenda attached. {F(a, e, v2)}"][i % 3]
    return ([rec(e, a, v1, d, "meeting_notes"), rec(e, a, v2, d, "imported_doc", t)], memlab.ATTRS[a]["q"].format(e=e),
            {"kind": "no_current", "acceptable": ["contradiction", "unresolved"], "basis": "genuine_contradiction"},
            ("conflict",))


CATEGORIES = {
    "temporal_update": c_temporal_update, "backfilled": c_backfilled, "valid_time_same_import": c_valid_time_same_import,
    "same_day_correction_named": c_same_day_named, "same_day_correction_unnamed": c_same_day_unnamed,
    "conflict_plain": c_conflict_plain, "conflict_same_text_date": c_conflict_same_text_date,
    "conflict_rival_mentioned": c_conflict_rival_mentioned, "negated_correction": c_negated,
    "retention": c_retention, "unconfirmed_update": c_unconfirmed, "quoted_correction": c_quoted,
    "hypothetical_change": c_hypothetical, "missing_timestamp": c_missing_ts,
    "missing_timestamp_text_dated": c_missing_ts_text_dated, "authority_one": c_authority_one,
    "authority_both": c_authority_both, "historical_question": c_historical, "incidental_update_word": c_incidental_cue,
}


def _ids(recs, prefix="g"):
    for k, r in enumerate(recs, 1):
        r["record_id"] = f"{prefix}-{k:02d}"
    return recs


def build():
    w = DevWorld(SEED)
    attrs = list(memlab.ATTRS)
    groups, tasks = [], []
    for cat, fn in CATEGORIES.items():
        for i in range(N_GROUP):
            a = attrs[(i + len(groups)) % len(attrs)]
            recs, q, gold, _ = fn(w, a, i)
            groups.append({"fixture_id": f"dev-{cat}-{i:02d}", "category": cat, "question": q,
                           "records": _ids(recs), "gold": gold})
        for i in range(N_TASK):
            a = attrs[(i + 3 + len(tasks)) % len(attrs)]
            recs, q, gold, exp = fn(w, a, i)
            for r in recs:
                r["role"] = "gold"
            if exp[0] == "answer":
                expected = memlab._expected("answer", value=exp[1], stale_value=exp[2])
            else:
                expected = memlab._expected("conflict", conflict_values=[r["value"] for r in recs])
            t = {"task_id": f"p2dev-{cat}-{i:02d}", "split": "p2dev", "scenario": cat, "variant": f"v{i % 3}",
                 "prompt": q, "expected": expected, "_records": recs + memlab._distractors(w, 5),
                 "needed_tools": ["memory_search"], "gold_resolution": gold}
            tasks.append(memlab._finish(w, t))
    for i in range(N_TASK):  # unsupported questions: the asked fact is nowhere
        a = attrs[i % len(attrs)]
        e = w.project()
        others = [x for x in attrs if x != a]
        recs = [rec(e, x, w.value(x), w.day(), w.rng.choice(memlab._SOURCES)) for x in w.rng.sample(others, 2)]
        for r in recs:
            r["role"] = "distractor"
        recs += memlab._distractors(w, 4)
        t = {"task_id": f"p2dev-unsupported-{i:02d}", "split": "p2dev", "scenario": "unsupported", "variant": "plain",
             "prompt": memlab.ATTRS[a]["q"].format(e=e), "expected": memlab._expected("abstain"), "_records": recs,
             "needed_tools": ["memory_search"], "gold_resolution": None}
        tasks.append(memlab._finish(w, t))
    return groups, tasks


def regression_groups():
    """Exact Phase 1 failure groups, with gold from the Phase 1 task expectations."""
    out = []
    sources = [("p1dev", rcs.build_p1dev(), ("S7", "S8")), ("p1hold", p1hold.build_p1hold(), ("H7b", "H9", "N3", "H7a", "H8a"))]
    for split, ts, prefixes in sources:
        for t in ts:
            if not t["scenario"].startswith(prefixes):
                continue
            mem = {r["record_id"]: r for r in t["memory"]}
            gold_recs = [mem[i] for i in t["gold_record_ids"]]
            grp = [r for r in t["memory"] if (r["entity"], r["attribute"]) == (gold_recs[0]["entity"], gold_recs[0]["attribute"])]
            exp = t["expected"]
            gold = ({"kind": "resolved", "current_value": exp["value"]} if exp["kind"] == "answer"
                    else {"kind": "no_current", "acceptable": ["contradiction", "unresolved"]})
            out.append({"fixture_id": f"reg-{t['task_id']}", "category": f"regression_{split}_{t['scenario'].split('_')[0]}",
                        "question": t["prompt"], "records": grp, "gold": gold, "source_task": t["task_id"]})
    return out


def main():
    groups, tasks = build()
    reg = regression_groups()
    d = P2 / "data"
    d.mkdir(exist_ok=True)
    man = {"seed": SEED, "name_slice": [10400, 12800], "status": "DEVELOPMENT - tuned against",
           "n_groups": len(groups), "n_tasks": len(tasks), "n_regression": len(reg),
           "categories": list(CATEGORIES) + ["unsupported (tasks only)"]}
    for name, rows in (("dev_groups.jsonl", groups), ("p2dev_tasks.jsonl", tasks), ("regression_groups.jsonl", reg)):
        blob = "\n".join(json.dumps(r, sort_keys=True, ensure_ascii=False) for r in rows) + "\n"
        (d / name).write_bytes(blob.encode("utf-8"))
        man[name] = hashlib.sha256(blob.encode("utf-8")).hexdigest()
    (d / "DEV_MANIFEST.json").write_text(json.dumps(man, indent=1) + "\n", encoding="utf-8")
    print(json.dumps(man, indent=1))


if __name__ == "__main__":
    main()
