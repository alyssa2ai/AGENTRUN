"""Phase 1 held-out stress split `p1hold` (development-only; NOT a confirmatory split).

Written and hashed (FREEZE_p1hold.json) BEFORE the arbiter in tea.py was written, so
that the arbiter is not tuned on these phrasings. Same author for both, which is a
stated limitation: the split tests generalisation beyond p1dev's two templates, not
independence from the arbiter's designer.

Eight scenarios x 6 tasks = 48 tasks. Names: a fourth disjoint slice of the memlab
name pool ([8000:10400]); p1dev uses [5200:8000], eval2 [1600:5200].

  H7a  same-day correction that names the corrected value, 3 lexicon-style phrasings
       and 1 phrasing outside a correction lexicon ("disregard ... confirmed")  -> answer new
  H7b  same-day correction that does NOT name the corrected value               -> answer new
  H8a  valid time in text, non-ISO dates ("Effective 3 March 2026", ...), same
       import date in metadata                                                  -> answer newer
  H9   back-filled entry: the record entered LATER states an OLDER validity date,
       so recorded_on order is the reverse of real order (misleading metadata)   -> answer newer valid date
  N1   genuine same-day conflict, both texts carry the same "As of" date         -> conflict
  N2   genuine same-day conflict, one text mentions the rival value neutrally    -> conflict
  N3   genuine conflict, one text says it does NOT replace the rival value       -> conflict
  C4   control: ordinary metadata-ordered update (S4 date_in_metadata_only)      -> answer new
"""
from __future__ import annotations

import random
import sys
from datetime import date, timedelta
from pathlib import Path

HERE = Path(__file__).resolve().parent
DEEP = HERE.parents[2] / "AGENTRUN_DEEPENING_2026-11-11"
sys.path.insert(0, str(DEEP / "scripts"))
import memlab  # noqa: E402

SPLIT = "p1hold"
SEED = 20261115
PER = 6


class HoldWorld(memlab._World):
    def __init__(self, seed: int):
        self.names = memlab._name_pool(10400)[8000:]
        self.rng = random.Random(seed)
        self.rng.shuffle(self.names)
        self._i = 0


def _long(d: str) -> str:
    x = date.fromisoformat(d)
    return f"{x.day} {x.strftime('%B')} {x.year}"


def _us(d: str) -> str:
    x = date.fromisoformat(d)
    return f"{x.strftime('%B')} {x.day}, {x.year}"


def fact(a, e, v):
    return memlab.ATTRS[a]["t"].format(e=e, v=v)


H7A = [
    lambda f, old: f"Update at 16:40: {f} This replaces the {old} noted this morning.",
    lambda f, old: f"Revised figure: {f} (the {old} given earlier today was wrong.)",
    lambda f, old: f"Erratum. {f} Please ignore the earlier {old}.",
    lambda f, old: f"Disregard the {old} from this morning; the confirmed figure is now in. {f}",
]
H8A = [
    lambda d, f: f"Effective {_long(d)}: {f}",
    lambda d, f: f"Valid from {_us(d)}. {f}",
    lambda d, f: f"Since {_long(d)}, {f[0].lower() + f[1:]}",
    lambda d, f: f"As at {_us(d)}: {f}",  # 'as at' (not 'as of')
]


def build_p1hold(seed: int = SEED, per: int = PER) -> list[dict]:
    w = HoldWorld(seed)
    attrs = list(memlab.ATTRS)
    tasks = []

    def add(scen, variant, i, **kw):
        t = {"task_id": f"{SPLIT}-{scen}-{i:02d}", "split": SPLIT, "scenario": scen, "variant": variant}
        t.update(kw)
        tasks.append(memlab._finish(w, t))

    def pair(a):
        e = w.project()
        v1 = w.value(a)
        return e, v1, w.value(a, avoid=v1)

    def q(a, e):
        return memlab.ATTRS[a]["q"].format(e=e)

    for i in range(per):  # H7a
        a = attrs[i % len(attrs)]
        e, v1, v2 = pair(a)
        d, src = w.day(), w.rng.choice(memlab._SOURCES)
        k = i % len(H7A)
        r1 = memlab._rec(e, a, v1, d, src, role="gold")
        r2 = memlab._rec(e, a, v2, d, src, role="gold")
        r2["text"] = H7A[k](fact(a, e, v2), v1)
        add("H7a_correction_named", f"phrasing{k}", i, prompt=q(a, e),
            expected=memlab._expected("answer", value=v2, stale_value=v1),
            _records=[r1, r2] + memlab._distractors(w, 5), needed_tools=["memory_search"])
    for i in range(per):  # H7b
        a = attrs[(i + 1) % len(attrs)]
        e, v1, v2 = pair(a)
        d, src = w.day(), w.rng.choice(memlab._SOURCES)
        r1 = memlab._rec(e, a, v1, d, src, role="gold")
        r2 = memlab._rec(e, a, v2, d, src, role="gold")
        r2["text"] = ("Correction, later the same day: " if i % 2 else "Corrected entry: ") + fact(a, e, v2)
        add("H7b_correction_unnamed", "late_same_day" if i % 2 else "corrected_entry", i, prompt=q(a, e),
            expected=memlab._expected("answer", value=v2, stale_value=v1),
            _records=[r1, r2] + memlab._distractors(w, 5), needed_tools=["memory_search"])
    for i in range(per):  # H8a
        a = attrs[(i + 2) % len(attrs)]
        e, old, new = pair(a)
        d_old = w.day(0, 60)
        d_new = (date.fromisoformat(d_old) + timedelta(days=w.rng.randrange(30, 120))).isoformat()
        imported = w.day(130, 140)
        k = i % len(H8A)
        r_old = memlab._rec(e, a, old, imported, "imported_doc", role="gold")
        r_new = memlab._rec(e, a, new, imported, "imported_doc", role="gold")
        r_old["text"] = H8A[k](d_old, fact(a, e, old))
        r_new["text"] = H8A[k](d_new, fact(a, e, new))
        add("H8a_valid_time_text", f"phrasing{k}", i, prompt=q(a, e),
            expected=memlab._expected("answer", value=new, stale_value=old),
            _records=[r_old, r_new] + memlab._distractors(w, 5), needed_tools=["memory_search"])
    for i in range(per):  # H9
        a = attrs[(i + 3) % len(attrs)]
        e, old, new = pair(a)
        v_old = w.day(0, 40)
        v_new = (date.fromisoformat(v_old) + timedelta(days=w.rng.randrange(20, 60))).isoformat()
        entered_new = (date.fromisoformat(v_new) + timedelta(days=w.rng.randrange(1, 10))).isoformat()
        entered_old = (date.fromisoformat(entered_new) + timedelta(days=w.rng.randrange(5, 30))).isoformat()
        r_new = memlab._rec(e, a, new, entered_new, "meeting_notes", role="gold")
        r_old = memlab._rec(e, a, old, entered_old, "imported_doc", role="gold")
        r_new["text"] = f"As of {v_new}: {fact(a, e, new)}"
        r_old["text"] = f"As of {v_old}: {fact(a, e, old)} (back-filled from an archived plan)"
        add("H9_backfilled_entry", "iso_as_of", i, prompt=q(a, e),
            expected=memlab._expected("answer", value=new, stale_value=old),
            _records=[r_new, r_old] + memlab._distractors(w, 5), needed_tools=["memory_search"])
    for i in range(per):  # N1
        a = attrs[(i + 4) % len(attrs)]
        e, v1, v2 = pair(a)
        d = w.day()
        r1 = memlab._rec(e, a, v1, d, "meeting_notes", role="gold")
        r2 = memlab._rec(e, a, v2, d, "imported_doc", role="gold")
        r1["text"] = f"As of {d}: {r1['text']}"
        r2["text"] = f"As of {d}: {r2['text']}"
        add("N1_conflict_same_text_date", "iso_as_of", i, prompt=q(a, e),
            expected=memlab._expected("conflict", conflict_values=[v1, v2]),
            _records=[r1, r2] + memlab._distractors(w, 5), needed_tools=["memory_search"])
    for i in range(per):  # N2
        a = attrs[(i + 5) % len(attrs)]
        e, v1, v2 = pair(a)
        d = w.day()
        r1 = memlab._rec(e, a, v1, d, "meeting_notes", role="gold")
        r2 = memlab._rec(e, a, v2, d, "imported_doc", role="gold")
        r2["text"] = f"{fact(a, e, v2)} The meeting notes from the same day give {v1}."
        add("N2_conflict_rival_mentioned", "neutral_mention", i, prompt=q(a, e),
            expected=memlab._expected("conflict", conflict_values=[v1, v2]),
            _records=[r1, r2] + memlab._distractors(w, 5), needed_tools=["memory_search"])
    for i in range(per):  # N3
        a = attrs[i % len(attrs)]
        e, v1, v2 = pair(a)
        d = w.day()
        r1 = memlab._rec(e, a, v1, d, "meeting_notes", role="gold")
        r2 = memlab._rec(e, a, v2, d, "imported_doc", role="gold")
        r2["text"] = (f"{fact(a, e, v2)} This does not replace the {v1} in the meeting notes; "
                      "both figures stand until they are reconciled.")
        add("N3_conflict_negated_replacement", "negated_cue", i, prompt=q(a, e),
            expected=memlab._expected("conflict", conflict_values=[v1, v2]),
            _records=[r1, r2] + memlab._distractors(w, 5), needed_tools=["memory_search"])
    for i in range(per):  # C4
        a = attrs[(i + 1) % len(attrs)]
        e, old, new = pair(a)
        d_old = w.day(0, 60)
        d_new = (date.fromisoformat(d_old) + timedelta(days=w.rng.randrange(30, 120))).isoformat()
        src = w.rng.choice(memlab._SOURCES)
        add("C4_metadata_update", "date_in_metadata_only", i, prompt=q(a, e),
            expected=memlab._expected("answer", value=new, stale_value=old),
            _records=[memlab._rec(e, a, old, d_old, src, role="gold"), memlab._rec(e, a, new, d_new, src, role="gold")]
            + memlab._distractors(w, 5), needed_tools=["memory_search"])
    return tasks


if __name__ == "__main__":
    import hashlib
    import json
    ts = build_p1hold()
    blob = "\n".join(json.dumps(t, sort_keys=True) for t in ts).encode()
    print(len(ts), hashlib.sha256(blob).hexdigest())
