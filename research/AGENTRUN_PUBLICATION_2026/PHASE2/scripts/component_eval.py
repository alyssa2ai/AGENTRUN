"""Component-level comparison of resolution mechanisms on development fixtures (no agent).

    py -3.11 PHASE2/scripts/component_eval.py [--llm PHASE2/raw/llm_arbiter/<model>.jsonl ...]

Mechanisms: legacy (memlab.reliability_status, = labels of G and R), TEA (Phase 1 tea.arbitrate,
= T and RT), evarb (this phase), and LLM arbiters (predictions produced on the GPU by
scripts/llm_arbiter_eval.py, scored here with the same code).

Each mechanism's output on a group is reduced to a decision:
  resolved(v, strength) | contradiction(strength) | unresolved
Legacy and TEA have no strength: every resolution they show is asserted, so it is scored as strong.
Errors (on the gold of the fixture):
  false_resolution        gold has no current value, mechanism resolves one
  incorrect_supersession  gold resolved v, mechanism resolves another value
  incorrect_conflict      gold resolved, mechanism says contradiction
  unnecessary_unresolved  gold resolved, mechanism says unresolved (the arbiter "abstains")
  overconfident           mechanism asserts a STRONG resolution where gold allows only moderate or none
  format_failure          LLM arbiter output unparsable (scored as unresolved)
"Enforceable error" = an error made with strength strong: the gated policy would act on it.
Writes PHASE2/data/component_eval.json and component_eval.md.
"""
from __future__ import annotations

import argparse
import json
import sys
from collections import Counter, defaultdict
from pathlib import Path

P2 = Path(__file__).resolve().parents[1]
sys.path.insert(0, str(P2))
from evarb import paths  # noqa: E402,F401
from evarb.arbiter import arbitrate  # noqa: E402
from evarb.llm_arbiter import parse_response  # noqa: E402
import memlab  # noqa: E402
import tea  # noqa: E402


def _same(a, b):
    if a is None or b is None:
        return False
    if isinstance(a, (int, float)) or isinstance(b, (int, float)):
        na, nb = memlab._num(a), memlab._num(b)
        return na is not None and nb is not None and abs(na - nb) < 0.011
    return memlab._norm(a) == memlab._norm(b)


def from_status_map(group, st):
    """st: rid -> status string (legacy / TEA vocabulary)."""
    by = {g["record_id"]: g for g in group}
    cur = {str(by[r]["value"]) for r, s in st.items() if s == "current"}
    if len(cur) == 1:
        rid = next(r for r, s in st.items() if s == "current")
        return {"kind": "resolved", "value": by[rid]["value"], "strength": "strong"}
    if any(s in ("conflicting", "contradictory") for s in st.values()):
        return {"kind": "contradiction", "strength": "strong"}
    if any(s in ("unordered", "unresolved") for s in st.values()):
        return {"kind": "unresolved", "strength": "none"}
    return {"kind": "unchallenged", "strength": "strong"}


def legacy(group):
    return from_status_map(group, {g["record_id"]: memlab.reliability_status(g, group)["status"] for g in group})


def tea_(group):
    return from_status_map(group, {g["record_id"]: s["status"] for g, s in
                                   ((g, tea.arbitrate(group)[g["record_id"]]) for g in group)})


def from_resolution(res):
    if res.kind == "resolved":
        return {"kind": "resolved", "value": res.current_value, "strength": res.strength, "basis": res.basis}
    if res.kind == "contradiction":
        return {"kind": "contradiction", "strength": res.strength, "basis": res.basis}
    return {"kind": res.kind, "strength": res.strength, "basis": res.basis}


def evarb_(group):
    return from_resolution(arbitrate(group))


def score(pred, gold):
    errs = []
    if gold["kind"] == "resolved":
        if pred["kind"] == "resolved":
            ok = _same(pred["value"], gold["current_value"])
            if not ok:
                errs.append("incorrect_supersession")
        elif pred["kind"] == "contradiction":
            ok, errs = False, ["incorrect_conflict"]
        else:
            ok, errs = False, ["unnecessary_unresolved"]
        if ok and pred.get("strength") == "strong" and gold.get("strength") == "moderate":
            errs.append("overconfident")
    else:
        if pred["kind"] == "resolved":
            ok, errs = False, ["false_resolution"]
            if pred.get("strength") == "strong":
                errs.append("overconfident")
        else:
            ok = True
            if pred["kind"] not in gold.get("acceptable", ["contradiction", "unresolved"]):
                errs.append("wrong_no_current_kind")
    if pred.get("format_failure"):
        errs.append("format_failure")
    enforceable = (not ok) and pred.get("strength") == "strong"
    basis_ok = (pred.get("basis") == gold.get("basis")) if gold.get("basis") and pred.get("basis") else None
    return ok, errs, enforceable, basis_ok


def load(path):
    return [json.loads(x) for x in Path(path).read_text(encoding="utf-8").splitlines() if x.strip()]


def main():
    ap = argparse.ArgumentParser()
    ap.add_argument("--llm", nargs="*", default=[])
    ap.add_argument("--groups", nargs="*", help="group files (default: dev + regression)")
    ap.add_argument("--only-ids", help="JSON list of fixture ids to keep (e.g. a primary item set)")
    ap.add_argument("--tag", default="component_eval")
    a = ap.parse_args()
    files = a.groups or [P2 / "data" / "dev_groups.jsonl", P2 / "data" / "regression_groups.jsonl"]
    fixtures = [f for p in files for f in load(p) if f["gold"]["kind"] in ("resolved", "no_current")]
    if a.only_ids:
        keep = set(json.loads(Path(a.only_ids).read_text()))
        fixtures = [f for f in fixtures if f["fixture_id"] in keep]
    mechs = {"legacy": legacy, "TEA": tea_, "evarb": evarb_}
    preds = {m: {f["fixture_id"]: fn(f["records"]) for f in fixtures} for m, fn in mechs.items()}
    for path in a.llm:
        name = "LLM:" + Path(path).stem
        rows = {r["fixture_id"]: r for r in load(path)}
        pm = {}
        for f in fixtures:
            r = rows.get(f["fixture_id"])
            if r is None:
                continue
            key = (f["records"][0]["entity"], f["records"][0]["attribute"])
            res = parse_response(key, f["records"], r["raw"])
            pm[f["fixture_id"]] = (from_resolution(res) if res else
                                   {"kind": "unresolved", "strength": "none", "format_failure": True})
        preds[name] = pm
    out = {"n_fixtures": len(fixtures), "mechanisms": {}}
    md = ["# Component evaluation (development fixtures; exploratory)\n",
          f"{len(fixtures)} groups: {sum(1 for f in fixtures if not f['category'].startswith('regression'))} dev "
          f"fixtures + {sum(1 for f in fixtures if f['category'].startswith('regression'))} Phase 1 regression groups. "
          "Generated by `scripts/component_eval.py`.\n"]
    cats = sorted({f["category"] for f in fixtures})
    for m, pm in preds.items():
        tot, err, enf, bas = Counter(), Counter(), Counter(), Counter()
        by_cat = defaultdict(lambda: [0, 0])
        fails = []
        for f in fixtures:
            if f["fixture_id"] not in pm:
                continue
            ok, errs, enforceable, basis_ok = score(pm[f["fixture_id"]], f["gold"])
            tot["n"] += 1
            tot["ok"] += ok
            by_cat[f["category"]][0] += ok
            by_cat[f["category"]][1] += 1
            for e in errs:
                err[e] += 1
            if enforceable:
                enf["enforceable_errors"] += 1
            if basis_ok is not None:
                bas["n"] += 1
                bas["ok"] += basis_ok
            if not ok:
                fails.append(f"{f['fixture_id']}: {pm[f['fixture_id']]}")
        out["mechanisms"][m] = {"accuracy": [tot["ok"], tot["n"]], "errors": dict(err), **dict(enf),
                                "basis_accuracy": [bas["ok"], bas["n"]] if bas["n"] else None,
                                "by_category": {c: by_cat[c] for c in cats if by_cat[c][1]}, "failures": fails}
    md.append("| Mechanism | correct | false resolution | incorrect supersession | incorrect conflict | "
              "unnecessary unresolved | overconfident | enforceable errors | format failures | basis correct |")
    md.append("|---|---|---|---|---|---|---|---|---|---|")
    for m, x in out["mechanisms"].items():
        e = x["errors"]
        ba = x["basis_accuracy"]
        basis_cell = f"{ba[0]}/{ba[1]}" if ba else "-"
        md.append(f"| {m} | {x['accuracy'][0]}/{x['accuracy'][1]} | {e.get('false_resolution', 0)} | "
                  f"{e.get('incorrect_supersession', 0)} | {e.get('incorrect_conflict', 0)} | "
                  f"{e.get('unnecessary_unresolved', 0)} | {e.get('overconfident', 0)} | "
                  f"{x.get('enforceable_errors', 0)} | {e.get('format_failure', 0)} | {basis_cell} |")
    md.append("\nPer category (correct / n):\n")
    names = list(out["mechanisms"])
    md.append("| Category | " + " | ".join(names) + " |")
    md.append("|---|" + "---|" * len(names))
    for c in cats:
        md.append(f"| {c} | " + " | ".join(f"{out['mechanisms'][m]['by_category'].get(c, ['-', '-'])[0]}/"
                                           f"{out['mechanisms'][m]['by_category'].get(c, ['-', '-'])[1]}"
                                           for m in names) + " |")
    (P2 / "data" / f"{a.tag}.json").write_text(json.dumps(out, indent=1), encoding="utf-8")
    (P2 / "data" / f"{a.tag}.md").write_text("\n".join(md) + "\n", encoding="utf-8")
    print("\n".join(md))


if __name__ == "__main__":
    main()
