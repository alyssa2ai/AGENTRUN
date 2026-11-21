"""G5 - platform-continuity report for Phase 3. REPORTING ONLY: it never fails the finalization and nothing it
writes is read by any statistical computation.

    python platform_continuity.py --raw <phase3_raw> --evidence <platform_evidence.json> \
                                  --out-json <ANALYSIS/PLATFORM_CONTINUITY.json> --out-md <PHASE3_PLATFORM_CONTINUITY.md>

What it does:
  * derives, from the frozen manifests alone, which cells have more than one start and which of those straddle the
    recorded node boot, with the per-start row split and the configuration balance of the post-boot segment;
  * joins that with the recorded host evidence (platform_evidence.json), keeping each fact's epistemic status:
      verified  read directly from a named system source
      inferred  deduced from verified facts, with the reasoning carried through
      unknown   could not be established, with what would settle it
  * always exits 0. A cell that straddles a boot is reported, not failed: PREREGISTRATION.md section 7 provides for
    resume, and section 10 restricts restarts to a freeze mismatch, a seal mismatch or a runner defect.

It reads only manifest.jsonl and the (task_id, config) keys of runs.jsonl. No outcome, task text or label is read.
"""
import argparse, json, sys
from collections import Counter
from pathlib import Path

G5_VERSION = "g5-v1 (2026-11-21)"
STATUS_ORDER = {"verified": 0, "inferred": 1, "unknown": 2}


def cell_segments(d: Path, manifests):
    """Split a cell's rows into one segment per start, using resumed_with_done. Keys only."""
    seq = []
    runs = d / "runs.jsonl"
    if runs.exists():
        with open(runs, encoding="utf-8") as f:
            for line in f:
                if line.strip():
                    x = json.loads(line)
                    seq.append((x["task_id"], x["config"]))
    bounds = [m.get("resumed_with_done", 0) for m in manifests] + [len(seq)]
    segs = []
    for i, m in enumerate(manifests):
        lo, hi = bounds[i], bounds[i + 1]
        rows = seq[lo:hi]
        segs.append({"start": i, "slurm_job_id": m.get("slurm_job_id"), "started_utc": m.get("started_utc"),
                     "resumed_with_done": m.get("resumed_with_done"), "rows": len(rows),
                     "tasks": len(set(t for t, _ in rows)),
                     "config_counts": dict(sorted(Counter(c for _, c in rows).items())),
                     "gpu_mem_gib": (m.get("client") or {}).get("gpu_mem_gib")})
    split_tasks = []
    if len(segs) > 1:
        task_sets = []
        for i in range(len(segs)):
            lo, hi = bounds[i], bounds[i + 1]
            task_sets.append(set(t for t, _ in seq[lo:hi]))
        for i in range(len(task_sets) - 1):
            for t in sorted(task_sets[i] & task_sets[i + 1]):
                counts = [sum(1 for x, _ in seq[bounds[j]:bounds[j + 1]] if x == t) for j in range(len(segs))]
                split_tasks.append({"task_id": t, "rows_per_start": counts})
    return segs, split_tasks, len(seq)


def main():
    ap = argparse.ArgumentParser()
    ap.add_argument("--raw", required=True)
    ap.add_argument("--evidence", required=True)
    ap.add_argument("--out-json", required=True)
    ap.add_argument("--out-md", required=True)
    a = ap.parse_args()
    ev = json.loads(Path(a.evidence).read_text(encoding="utf-8"))
    boot = ev["boot_event"]["node_boot_utc"].rstrip("Z")
    raw = Path(a.raw)

    cells, total_rows, post_rows = [], 0, 0
    for d in sorted(raw.glob("eval3_*")):
        if not d.is_dir():
            continue
        mp = d / "manifest.jsonl"
        if not mp.exists():
            continue
        man = [json.loads(x) for x in open(mp, encoding="utf-8") if x.strip()]
        segs, split_tasks, n = cell_segments(d, man)
        straddles = len(man) > 1 and any((s["started_utc"] or "").rstrip("Z") > boot for s in segs) \
            and any((s["started_utc"] or "").rstrip("Z") < boot for s in segs)
        after = sum(s["rows"] for s in segs if (s["started_utc"] or "").rstrip("Z") > boot)
        total_rows += n
        post_rows += after
        quarantine = sorted(p.name for p in d.glob("runs.jsonl.partial_*"))
        cells.append({"cell": d.name.replace("eval3_", ""), "starts": len(man), "rows": n,
                      "straddles_node_boot": straddles, "rows_after_boot": after,
                      "segments": segs, "tasks_split_across_starts": split_tasks,
                      "quarantined_fragments": quarantine})

    affected = [c for c in cells if c["straddles_node_boot"]]
    facts = []
    for key, val in ev.items():
        if isinstance(val, dict) and "status" in val:
            facts.append({"fact": key, **val})
    facts.sort(key=lambda f: (STATUS_ORDER.get(f["status"], 9), f["fact"]))

    out = {"g5_version": G5_VERSION, "reporting_only": True,
           "node_boot_utc": ev["boot_event"]["node_boot_utc"],
           "cells_total": len(cells), "cells_straddling_boot": len(affected),
           "rows_total": total_rows, "rows_after_boot": post_rows,
           "rows_after_boot_pct": round(100.0 * post_rows / total_rows, 3) if total_rows else None,
           "affected_cells": [c["cell"] for c in affected], "cells": cells,
           "facts_by_status": {s: [f["fact"] for f in facts if f["status"] == s]
                               for s in ("verified", "inferred", "unknown")},
           "facts": facts}
    Path(a.out_json).write_text(json.dumps(out, indent=1) + "\n", encoding="utf-8")

    L = []
    L.append("# Phase 3 - G5 platform-continuity report")
    L.append("")
    L.append(f"Generated by `scripts/platform_continuity.py` ({G5_VERSION}). **Reporting only**: this check never "
             "fails the finalization, and nothing in it is read by any statistical computation. It records a host "
             "platform transition that occurred during the campaign so that it can be disclosed, not corrected.")
    L.append("")
    L.append(f"- Node boot recorded at **{ev['boot_event']['node_boot_utc']}**")
    L.append(f"- Cells whose starts straddle that boot: **{len(affected)} of {len(cells)}** "
             f"({', '.join(c['cell'] for c in affected) if affected else 'none'})")
    L.append(f"- Rows produced after the boot: **{post_rows} of {total_rows}** "
             f"({out['rows_after_boot_pct']}%)")
    L.append("")
    L.append("## 1. Per-cell continuity")
    L.append("")
    L.append("| Cell | Starts | Rows | Straddles boot | Rows after boot | gpu_mem_gib per start |")
    L.append("|---|---|---|---|---|---|")
    for c in cells:
        mem = " / ".join(str(s["gpu_mem_gib"]) for s in c["segments"])
        L.append(f"| `{c['cell']}` | {c['starts']} | {c['rows']} | {'yes' if c['straddles_node_boot'] else 'no'} "
                 f"| {c['rows_after_boot']} | {mem} |")
    L.append("")
    if affected:
        L.append("## 2. Segment detail for the affected cells")
        L.append("")
        for c in affected:
            L.append(f"### `{c['cell']}`")
            L.append("")
            L.append("| Start | Slurm job | Started (UTC) | resumed_with_done | Rows | Whole tasks | gpu_mem_gib |")
            L.append("|---|---|---|---|---|---|---|")
            for s in c["segments"]:
                L.append(f"| {s['start']} | {s['slurm_job_id']} | {s['started_utc']} | {s['resumed_with_done']} "
                         f"| {s['rows']} | {s['tasks']} | {s['gpu_mem_gib']} |")
            L.append("")
            post = [s for s in c["segments"] if (s["started_utc"] or "").rstrip("Z") > boot]
            for s in post:
                cc = s["config_counts"]
                L.append(f"Post-boot segment configuration balance (start {s['start']}): "
                         f"min {min(cc.values())}, max {max(cc.values())} rows per configuration over "
                         f"{len(cc)} configurations - `{json.dumps(cc)}`.")
            if c["tasks_split_across_starts"]:
                for t in c["tasks_split_across_starts"]:
                    L.append(f"Task split across starts: `{t['task_id']}` with {t['rows_per_start']} rows per start.")
            else:
                L.append("No task is split across starts in this cell.")
            L.append(f"Quarantined fragments retained: {c['quarantined_fragments'] or 'none'}.")
            L.append("")
        L.append("The runner iterates tasks in sorted `task_id` order (outer) and the 12 frozen configurations "
                 "(inner), so a resumed segment is a contiguous suffix in task order carrying all 12 configurations "
                 "for every whole task it contains. The platform transition is therefore balanced across "
                 "configurations to within one row per configuration, and the residual within-task confound is "
                 "limited to the tasks listed above.")
        L.append("")
    L.append("## 3. Facts by epistemic status")
    L.append("")
    for status, heading in (("verified", "Directly verified"), ("inferred", "Inferred from historical records"),
                            ("unknown", "Not established")):
        sel = [f for f in facts if f["status"] == status]
        L.append(f"### {heading} ({len(sel)})")
        L.append("")
        if not sel:
            L.append("_none_")
            L.append("")
            continue
        for f in sel:
            bits = [f"**`{f['fact']}`**"]
            for k in ("what", "version", "release", "field", "before", "after", "node_boot_utc", "count", "model"):
                if k in f:
                    bits.append(f"{k}: `{f[k]}`")
            L.append("- " + "; ".join(bits))
            if f.get("reasoning"):
                L.append(f"  - reasoning: {f['reasoning']}")
            if f.get("source"):
                L.append(f"  - source: `{f['source']}`")
            if f.get("caveat"):
                L.append(f"  - caveat: {f['caveat']}")
            if f.get("would_settle"):
                L.append(f"  - would settle it: `{f['would_settle']}`")
        L.append("")
    L.append("## 4. Standing of this report")
    L.append("")
    L.append("This report changes nothing about the experiment's validity, the pre-registered analysis, the "
             "denominators or any statistical calculation. `PREREGISTRATION.md` section 7 provides for a resumed "
             "cell; section 10 restricts a restart to a freeze mismatch, a seal mismatch or a runner defect, none "
             "of which occurred. The disclosure obligation this report creates is discharged in "
             "`PHASE3_DEVIATIONS.md` and in the manuscript's limitations.")
    Path(a.out_md).write_text("\n".join(L) + "\n", encoding="utf-8")
    print(f"G5 {G5_VERSION}: {len(affected)}/{len(cells)} cells straddle the node boot; "
          f"{post_rows}/{total_rows} rows after it ({out['rows_after_boot_pct']}%); reporting only")
    return 0


if __name__ == "__main__":
    sys.exit(main())
