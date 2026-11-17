"""Component-level comparison of the four arbitration methods on a validation split (CPU, no GPU).

    python component_report.py --split p2val2 [--primary ../data/p2val2/p2val2_PRIMARY_IDS.json] --out ../data/BASELINE_p2val2

Methods: legacy (memlab labels), TEA (Phase 1), evarb (frozen evarb-0.2), and the LLM evidence
arbiter (one row per model; predictions from raw/llm_arbiter/<model>__<split>_groups.jsonl, produced on
the GPU by llm_arbiter_eval.py with the same prompt for every model).
Scoring is the frozen scripts/component_eval.py `score` function, unchanged. Only groups whose gold is
`resolved` or `no_current` are scored (single-record and unsupported items need no arbitration).

Inference: items are clustered in families (category x attribute). Paired evarb-minus-baseline
differences use a family-level bootstrap (10,000 resamples of families) for the 95% CI and an exact
sign-flip test over family-level differences for p; Holm over the baselines of one split.
"""
from __future__ import annotations

import argparse
import glob
import itertools
import json
import random
import sys
from collections import Counter, defaultdict
from pathlib import Path

HERE = Path(__file__).resolve().parent
P2 = HERE.parent
sys.path.insert(0, str(HERE))
import component_eval as ce  # noqa: E402  (frozen; imported, not modified)

ERRS = ["false_resolution", "incorrect_supersession", "incorrect_conflict", "unnecessary_unresolved", "overconfident",
        "format_failure"]


def wilson(k, n, z=1.96):
    if n == 0:
        return [None, None]
    p = k / n
    d = 1 + z * z / n
    c = p + z * z / (2 * n)
    r = z * ((p * (1 - p) + z * z / (4 * n)) / n) ** 0.5
    return [round((c - r) / d, 4), round((c + r) / d, 4)]


def family(f):
    return f"{f['category']}|{f['records'][0]['attribute']}"


def paired(ok_a, ok_b, fams, n_boot=10000, seed=1):
    by = defaultdict(list)
    for i, fam in fams.items():
        if i in ok_a and i in ok_b:
            by[fam].append(ok_a[i] - ok_b[i])
    keys = sorted(by)
    n = sum(len(v) for v in by.values())
    diff = sum(sum(v) for v in by.values()) / n
    rng = random.Random(seed)
    boots = []
    for _ in range(n_boot):
        s = [by[k] for k in (rng.choice(keys) for _ in keys)]
        m = sum(len(v) for v in s)
        boots.append(sum(sum(v) for v in s) / m)
    boots.sort()
    sums = [sum(by[k]) for k in keys]
    obs = abs(sum(sums))
    nz = [s for s in sums if s != 0]
    if len(nz) <= 20:
        cnt = sum(abs(sum(x * s for x, s in zip(signs, nz))) >= obs - 1e-12
                  for signs in itertools.product((1, -1), repeat=len(nz)))
        p = cnt / 2 ** len(nz)
    else:
        cnt = sum(abs(sum(rng.choice((1, -1)) * s for s in nz)) >= obs - 1e-12 for _ in range(100000))
        p = (cnt + 1) / 100001
    return {"n_items": n, "n_families": len(keys), "diff": round(diff, 4),
            "ci95": [round(boots[int(0.025 * n_boot)], 4), round(boots[int(0.975 * n_boot) - 1], 4)], "p_signflip": round(p, 5)}


def holm(ps):
    order = sorted(range(len(ps)), key=lambda i: ps[i])
    adj, run = [0.0] * len(ps), 0.0
    for r, i in enumerate(order):
        run = max(run, min(1.0, (len(ps) - r) * ps[i]))
        adj[i] = round(run, 5)
    return adj


def main():
    ap = argparse.ArgumentParser()
    ap.add_argument("--split", required=True)
    ap.add_argument("--groups")
    ap.add_argument("--primary", nargs="*", default=[], help="primary id files; their INTERSECTION is used")
    ap.add_argument("--llm-dir", default=str(P2 / "raw" / "llm_arbiter"))
    ap.add_argument("--out", required=True)
    a = ap.parse_args()
    gpath = Path(a.groups) if a.groups else P2 / "data" / a.split / f"{a.split}_groups.jsonl"
    fixtures = [f for f in ce.load(gpath) if f["gold"]["kind"] in ("resolved", "no_current")]
    subsets = {"all_valid": {f["fixture_id"] for f in fixtures},
               # component scoring asks for the CURRENT value; historical / as-of intent is resolved by the
               # agent loop (intent routing), so those items are only meaningful at agent level
               "current_intent": {f["fixture_id"] for f in fixtures if f.get("intent_gold", "current") == "current"}}
    if a.primary:
        keep = None
        for p in a.primary:
            s = set(json.loads(Path(p).read_text()))
            keep = s if keep is None else keep & s
        subsets["annotator_agreed_current"] = keep & subsets["current_intent"]
    preds = {"legacy": {f["fixture_id"]: ce.legacy(f["records"]) for f in fixtures},
             "TEA": {f["fixture_id"]: ce.tea_(f["records"]) for f in fixtures},
             "evarb": {f["fixture_id"]: ce.evarb_(f["records"]) for f in fixtures}}
    cost = {}
    for path in sorted(glob.glob(str(Path(a.llm_dir) / f"*__{gpath.stem}.jsonl"))):
        model = Path(path).name.split("__")[0]
        rows = {r["fixture_id"]: r for r in ce.load(path)}
        pm, lat, tok = {}, [], []
        for f in fixtures:
            r = rows.get(f["fixture_id"])
            if r is None:
                continue
            key = (f["records"][0]["entity"], f["records"][0]["attribute"])
            res = ce.parse_response(key, f["records"], r["raw"])
            pm[f["fixture_id"]] = ce.from_resolution(res) if res else {"kind": "unresolved", "strength": "none",
                                                                       "format_failure": True}
            lat.append(r.get("latency_s") or 0.0)
            tok.append((r.get("usage") or {}).get("total_tokens") or 0)
        preds[f"LLM:{model}"] = pm
        cost[f"LLM:{model}"] = {"n": len(lat), "mean_latency_s": round(sum(lat) / max(1, len(lat)), 3),
                                "mean_total_tokens": round(sum(tok) / max(1, len(tok)), 1)}
    fams = {f["fixture_id"]: family(f) for f in fixtures}
    byid = {f["fixture_id"]: f for f in fixtures}
    out = {"split": a.split, "groups_file": str(gpath.name), "n_scored": len(fixtures), "llm_cost": cost, "subsets": {}}
    md = [f"# Arbitration methods on {a.split} (component level)\n",
          f"Generated by `scripts/component_report.py`. Scored with the frozen `component_eval.score`. "
          f"Groups needing arbitration: {len(fixtures)}. Families = category x attribute.\n"]
    for sname, ids in subsets.items():
        res, oks = {}, {}
        for m, pm in preds.items():
            c, ok = Counter(), {}
            cats = defaultdict(lambda: [0, 0])
            for i in sorted(ids):
                if i not in pm:
                    continue
                good, errs, enforceable, _ = ce.score(pm[i], byid[i]["gold"])
                ok[i] = int(good)
                c["n"] += 1
                c["ok"] += good
                c["enforceable_errors"] += bool(enforceable)
                for e in errs:
                    c[e] += 1
                cats[byid[i]["category"]][0] += good
                cats[byid[i]["category"]][1] += 1
            oks[m] = ok
            res[m] = {"accuracy": [c["ok"], c["n"]], "accuracy_wilson95": wilson(c["ok"], c["n"]),
                      **{e: c[e] for e in ERRS}, "enforceable_errors": c["enforceable_errors"],
                      "by_category": dict(sorted(cats.items()))}
        comps = {}
        base = [m for m in preds if m != "evarb"]
        for m in base:
            comps[f"evarb-{m}"] = paired(oks["evarb"], oks[m], fams)
        adj = holm([comps[k]["p_signflip"] for k in comps])
        for k, h in zip(comps, adj):
            comps[k]["p_holm"] = h
        out["subsets"][sname] = {"n_items": len(ids), "n_families": len({fams[i] for i in ids}), "methods": res,
                                 "paired_vs_evarb": comps}
        md.append(f"## Subset `{sname}`: {len(ids)} items, {len({fams[i] for i in ids})} families\n")
        md.append("| Method | correct | 95% CI | false resolution | incorrect supersession | incorrect conflict | "
                  "unnecessary unresolved | overconfident | enforceable errors | format failures |")
        md.append("|---|---|---|---|---|---|---|---|---|---|")
        for m, x in res.items():
            ci = x["accuracy_wilson95"]
            md.append(f"| {m} | {x['accuracy'][0]}/{x['accuracy'][1]} | {ci[0]:.2f}-{ci[1]:.2f} | " +
                      " | ".join(str(x[e]) for e in ERRS[:5]) + f" | {x['enforceable_errors']} | {x['format_failure']} |")
        md.append("\nPaired, family-clustered (evarb minus baseline, proportion correct):\n")
        md.append("| Contrast | items | families | diff | 95% CI (family bootstrap) | p (sign-flip) | p (Holm) |")
        md.append("|---|---|---|---|---|---|---|")
        for k, v in comps.items():
            md.append(f"| {k} | {v['n_items']} | {v['n_families']} | {v['diff']:+.3f} | {v['ci95'][0]:+.3f} to "
                      f"{v['ci95'][1]:+.3f} | {v['p_signflip']} | {v['p_holm']} |")
        md.append("\nPer category (correct / n):\n")
        names = list(res)
        md.append("| Category | " + " | ".join(names) + " |")
        md.append("|---|" + "---|" * len(names))
        for cat in sorted({byid[i]["category"] for i in ids}):
            md.append(f"| {cat} | " + " | ".join("{}/{}".format(*res[m]["by_category"].get(cat, ["-", "-"])) for m in names) + " |")
        md.append("")
    if cost:
        md.append("LLM arbiter cost per group: " + "; ".join(f"{k}: {v['mean_latency_s']} s, {v['mean_total_tokens']} tokens"
                                                         for k, v in cost.items()) + "\n")
    Path(a.out + ".json").write_text(json.dumps(out, indent=1) + "\n", encoding="utf-8")
    Path(a.out + ".md").write_text("\n".join(md) + "\n", encoding="utf-8")
    print("\n".join(md))


if __name__ == "__main__":
    main()
