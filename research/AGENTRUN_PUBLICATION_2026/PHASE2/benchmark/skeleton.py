"""Benchmark skeletons for p2val (validation) and eval3 (sealed evaluation).

A skeleton fixes everything structural and the ground truth: entity, attribute, values, record
dates and sources, category, expected behaviour, and for every record a WRITING BRIEF saying what
its text must convey. The natural-language record texts (and the wording of historical
questions) are written afterwards by a separate writer that has no access to the mechanism
(BENCHMARK_EVAL3_SPEC.md), then merged by assemble.py.

    py -3.11 skeleton.py --split p2val --out <dir>
    py -3.11 skeleton.py --split eval3 --out <sealed dir outside the repository>

Skeleton versions: v1 (p2val, as built and used) and v2 (p2val2, eval3). v2 follows the evidence
principle adopted after the p2val blind annotation: a record that only reports a claim, proposes,
conditions, or says it does not replace the other value does not establish its value, so the
established value stands; a conflict needs two asserted values with nothing ordering them, or an
explicit "both stand / disagree". v2 changes: negated_replacement [old] (was [conflict]), new
negated_both_stand [conflict], quoted_claim [old] (was [conflict]; the claimed value is never stated
as fact), and a stricter incidental_change_word brief.

Categories (v1: 22; v2: 23; ground truth in brackets, v1 shown):
  update_record_time [new]          valid_time_same_import [new]     backfilled_entry [new]
  same_day_correction_ref [new]     same_day_correction_noref [new]  supersession_later_ref [new]
  three_value_chain [latest]        single_record_control [value]    historical_question [old]
  as_of_question [old]
  retention [old]                   unconfirmed_change [old]         hypothetical_change [old]
  negated_replacement [conflict]    quoted_claim [conflict]          conflict_plain [conflict]
  conflict_same_validity [conflict] conflict_rival_neutral [conflict] authority_both [conflict]
  missing_timestamp [conflict]      incidental_change_word [conflict]
  unsupported [abstain]
Excluded on purpose: a tie broken only by source authority. Its ground truth depends on a
convention the agent's prompt does not state, so it is not a fair evaluation item (kept in the
development fixtures only).
"""
from __future__ import annotations

import argparse
import hashlib
import json
import random
import sys
from datetime import date, timedelta
from pathlib import Path

P2 = Path(__file__).resolve().parents[1]
sys.path.insert(0, str(P2))
from evarb import paths  # noqa: E402,F401
import memlab  # noqa: E402

SPLITS = {"p2val": {"seed": 20261117, "names": (12800, 14000), "per_cat": 4, "version": 1},
          "p2val2": {"seed": 20261118, "names": (21200, 22400), "per_cat": 4, "version": 2},
          "eval3": {"seed": 20261201, "names": (14000, 17600), "per_cat": 12, "version": 2}}
PLAIN = "State the fact plainly in one or two sentences, like a note or a document line. No dates, no correction words."


class W(memlab._World):
    def __init__(self, seed, lo, hi):
        self.names = memlab._name_pool(hi)[lo:]
        self.rng = random.Random(seed)
        self.rng.shuffle(self.names)
        self._i = 0


def fact(a):
    return {"budget_usd": "the approved budget in USD", "team_size": "the team size (number of people)",
            "port": "the staging server port", "lead": "the project lead", "region": "the cloud region",
            "deadline": "the delivery deadline (a date)"}[a]


def build(split: str) -> list[dict]:
    cfg = SPLITS[split]
    w = W(cfg["seed"], *cfg["names"])
    attrs = list(memlab.ATTRS)
    items = []
    k = 0

    def pair(a):
        e = w.project()
        v1 = w.value(a)
        return e, v1, w.value(a, avoid=v1)

    def later(d, lo=20, hi=90):
        return (date.fromisoformat(d) + timedelta(days=w.rng.randrange(lo, hi))).isoformat()

    def R(v, d, src, brief):
        return {"value": v, "recorded_on": d, "source": src, "brief": brief}

    def add(cat, a, e, recs, gold, question_brief=None, as_of=None):
        nonlocal k
        k += 1
        items.append({"item_id": f"{split}-{k:04d}", "category": cat, "entity": e, "attribute": a,
                      "fact": fact(a), "records": recs, "gold": gold,
                      "question": None if question_brief else memlab.ATTRS[a]["q"].format(e=e),
                      "question_brief": question_brief, "as_of": as_of})

    semv2 = cfg["version"] == 2
    cats = ["update_record_time", "valid_time_same_import", "backfilled_entry", "same_day_correction_ref",
            "same_day_correction_noref", "supersession_later_ref", "three_value_chain", "single_record_control",
            "historical_question", "as_of_question", "retention", "unconfirmed_change", "hypothetical_change",
            "negated_replacement"] + (["negated_both_stand"] if semv2 else []) + ["quoted_claim", "conflict_plain", "conflict_same_validity",
            "conflict_rival_neutral", "authority_both", "missing_timestamp", "incidental_change_word", "unsupported"]
    for i in range(cfg["per_cat"]):
        for c in cats:
            a = attrs[(i + cats.index(c)) % len(attrs)]
            src = w.rng.choice(memlab._SOURCES)
            e, v1, v2 = pair(a)
            d1 = w.day(0, 60)
            if c == "update_record_time":
                add(c, a, e, [R(v1, d1, src, PLAIN), R(v2, later(d1), src, PLAIN)], {"kind": "answer", "value": v2, "stale": v1})
            elif c == "valid_time_same_import":
                imp, d2 = w.day(130, 140), later(d1, 30, 80)
                add(c, a, e, [R(v1, imp, "imported_doc", f"State the fact and that it applies from {d1} (write the date in any natural format)."),
                              R(v2, imp, "imported_doc", f"State the fact and that it applies from {d2} (any natural date format).")],
                    {"kind": "answer", "value": v2, "stale": v1})
            elif c == "backfilled_entry":
                d2 = later(d1, 20, 60)
                e_new = later(d2, 1, 5)
                e_old = later(e_new, 5, 25)
                add(c, a, e, [R(v2, e_new, "meeting_notes", f"State the fact and that it applies from {d2} (any natural date format)."),
                              R(v1, e_old, "imported_doc", f"State the fact and that it applied from {d1} (any natural date format); "
                                "mention that the note was entered late from an older source.")],
                    {"kind": "answer", "value": v2, "stale": v1})
            elif c == "same_day_correction_ref":
                add(c, a, e, [R(v1, d1, src, PLAIN), R(v2, d1, src, f"State the fact, and say explicitly that it corrects, replaces or "
                              f"invalidates the earlier entry of {v1}, naming {v1}. Vary the wording.")],
                    {"kind": "answer", "value": v2, "stale": v1})
            elif c == "same_day_correction_noref":
                add(c, a, e, [R(v1, d1, src, PLAIN), R(v2, d1, src, "State the fact and make clear this entry is a correction of an earlier "
                              "entry made the same day, WITHOUT stating the earlier value.")],
                    {"kind": "answer", "value": v2, "stale": v1})
            elif c == "supersession_later_ref":
                add(c, a, e, [R(v1, d1, src, PLAIN), R(v2, later(d1), src, f"State the new fact and say it supersedes or replaces {v1}, naming {v1}.")],
                    {"kind": "answer", "value": v2, "stale": v1})
            elif c == "three_value_chain":
                v3 = w.value(a, avoid=v2)
                if v3 == v1:
                    v3 = w.value(a, avoid=v1)
                d2 = later(d1)
                add(c, a, e, [R(v1, d1, src, PLAIN), R(v2, d2, src, PLAIN), R(v3, later(d2), src, PLAIN)],
                    {"kind": "answer", "value": v3, "stale": v2})
            elif c == "single_record_control":
                add(c, a, e, [R(v1, d1, src, PLAIN)], {"kind": "answer", "value": v1})
            elif c == "historical_question":
                add(c, a, e, [R(v1, d1, src, PLAIN), R(v2, later(d1), src, PLAIN)], {"kind": "answer", "value": v1, "stale": v2},
                    question_brief=f"Ask for {fact(a)} of {e} as it was BEFORE it was changed (the earlier value), in natural wording. "
                    "Do not mention any value." + (" Ask for the date as YYYY-MM-DD." if a == "deadline" else ""))
            elif c == "as_of_question":
                d2 = later(d1, 40, 90)
                mid = (date.fromisoformat(d1) + timedelta(days=(date.fromisoformat(d2) - date.fromisoformat(d1)).days // 2)).isoformat()
                imp = w.day(130, 140)
                add(c, a, e, [R(v1, imp, "imported_doc", f"State the fact and that it applies from {d1} (ISO date YYYY-MM-DD)."),
                              R(v2, imp, "imported_doc", f"State the fact and that it applies from {d2} (ISO date YYYY-MM-DD).")],
                    {"kind": "answer", "value": v1, "stale": v2},
                    question_brief=f"Ask for {fact(a)} of {e} as of {mid}, writing the date exactly as {mid}. Do not mention any value.",
                    as_of=mid)
            elif c == "retention":
                add(c, a, e, [R(v1, d1, src, PLAIN), R(v2, later(d1, 5, 20), "meeting_notes",
                              f"Mention that {v2} was suggested or discussed, but say clearly that {v1} (name it) remains the valid figure.")],
                    {"kind": "answer", "value": v1, "stale": v2})
            elif c == "unconfirmed_change":
                add(c, a, e, [R(v1, d1, src, PLAIN), R(v2, later(d1, 5, 20), "meeting_notes",
                              f"Present {v2} as a proposed, pending or draft change that has NOT been approved or confirmed.")],
                    {"kind": "answer", "value": v1, "stale": v2})
            elif c == "hypothetical_change":
                add(c, a, e, [R(v1, d1, src, PLAIN), R(v2, later(d1, 5, 20), "meeting_notes",
                              f"Say that the value would or could become {v2} only if some condition happens (conditional, not a decision).")],
                    {"kind": "answer", "value": v1, "stale": v2})
            elif c == "negated_replacement" and not semv2:
                add(c, a, e, [R(v1, d1, "meeting_notes", PLAIN), R(v2, d1, "imported_doc",
                              f"State the fact with value {v2}, and say explicitly that it does NOT replace, correct or override {v1} "
                              f"(name {v1}); the two figures disagree. Vary the negation wording.")],
                    {"kind": "conflict"})
            elif c == "negated_replacement":
                add(c, a, e, [R(v1, d1, "meeting_notes", PLAIN), R(v2, d1, "imported_doc",
                              f"Mention the value {v2}, and say explicitly that it does NOT replace, correct or override {v1} "
                              f"(name {v1}). Do NOT say that both figures stand or that they disagree. Vary the negation wording.")],
                    {"kind": "answer", "value": v1, "stale": v2})
            elif c == "negated_both_stand":
                add(c, a, e, [R(v1, d1, "meeting_notes", PLAIN), R(v2, d1, "imported_doc",
                              f"State the fact with value {v2}, say it does NOT replace {v1} (name {v1}), AND say that both "
                              "figures stand / disagree until they are reconciled.")],
                    {"kind": "conflict"})
            elif c == "quoted_claim":
                add(c, a, e, [R(v1, d1, "meeting_notes", PLAIN), R(v2, d1, "user_statement",
                              f"Report that a person or a message CLAIMED that {v2} replaces {v1} (quote or reported speech), "
                              "without the record itself confirming it. Mention the project."
                              + (f" Never state {v2} as a fact outside the reported claim." if semv2 else ""))],
                    {"kind": "answer", "value": v1, "stale": v2} if semv2 else {"kind": "conflict"})
            elif c == "conflict_plain":
                add(c, a, e, [R(v1, d1, "meeting_notes", PLAIN), R(v2, d1, "imported_doc", PLAIN)], {"kind": "conflict"})
            elif c == "conflict_same_validity":
                add(c, a, e, [R(v1, d1, "meeting_notes", f"State the fact and that it applies from {d1} (any natural date format)."),
                              R(v2, d1, "imported_doc", f"State the fact and that it applies from {d1} (any natural date format).")],
                    {"kind": "conflict"})
            elif c == "conflict_rival_neutral":
                add(c, a, e, [R(v1, d1, "meeting_notes", PLAIN), R(v2, d1, "imported_doc",
                              f"State the fact with {v2}, and neutrally note that another source lists {v1}; no correction or "
                              "replacement language.")], {"kind": "conflict"})
            elif c == "authority_both":
                add(c, a, e, [R(v1, d1, "system_of_record", PLAIN), R(v2, d1, "system_of_record", PLAIN)], {"kind": "conflict"})
            elif c == "missing_timestamp":
                add(c, a, e, [R(v1, "", src, PLAIN), R(v2, d1, src, PLAIN)], {"kind": "conflict"})
            elif c == "incidental_change_word":
                add(c, a, e, [R(v1, d1, "meeting_notes", PLAIN), R(v2, d1, "imported_doc",
                              "State the fact inside a line that uses a word like 'update', 'revised' or 'new' about something "
                              "else (a status report, an agenda, a page). It must NOT say the fact corrects or replaces anything."
                              + (" Begin with an unrelated header such as 'Weekly status update:' or 'Revised agenda, item 3:' and "
                                 "then state the fact as a plain present-tense statement. Do not use 'now', 'new', 'changed', "
                                 "'moved', 'switched' or 'will' about the fact itself." if semv2 else ""))],
                    {"kind": "conflict"})
            elif c == "unsupported":
                others = [x for x in attrs if x != a]
                recs = [R(w.value(x), w.day(), w.rng.choice(memlab._SOURCES), PLAIN) | {"attribute": x}
                        for x in w.rng.sample(others, 2)]
                add(c, a, e, recs, {"kind": "abstain"})
    for it in items:
        for j, r in enumerate(it["records"], 1):
            r["slot"] = j
            r.setdefault("attribute", it["attribute"])
        it["distractor_seed"] = w.rng.randrange(10 ** 9)
    return items


def main():
    ap = argparse.ArgumentParser()
    ap.add_argument("--split", choices=list(SPLITS), required=True)
    ap.add_argument("--out", required=True)
    a = ap.parse_args()
    items = build(a.split)
    out = Path(a.out)
    out.mkdir(parents=True, exist_ok=True)
    blob = "\n".join(json.dumps(x, sort_keys=True, ensure_ascii=False) for x in items) + "\n"
    (out / f"{a.split}_skeleton.jsonl").write_bytes(blob.encode("utf-8"))
    # the writer's input: briefs only, no gold
    wi = [{"item_id": x["item_id"], "entity": x["entity"], "fact": x["fact"],
           "records": [{"slot": r["slot"], "value": r["value"], "attribute_fact": fact(r["attribute"]), "brief": r["brief"]}
                       for r in x["records"]],
           "question_brief": x["question_brief"]} for x in items]
    (out / f"{a.split}_writer_input.jsonl").write_bytes(
        ("\n".join(json.dumps(x, ensure_ascii=False) for x in wi) + "\n").encode("utf-8"))
    print(json.dumps({"split": a.split, "n_items": len(items), "skeleton_sha256": hashlib.sha256(blob.encode()).hexdigest(),
                      "categories": len({x["category"] for x in items})}))


if __name__ == "__main__":
    main()
