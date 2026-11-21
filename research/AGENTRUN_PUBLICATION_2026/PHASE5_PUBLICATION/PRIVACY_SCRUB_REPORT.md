# Privacy scrub report

**Date:** 2026-11-21. **Tool:** `PHASE5_PUBLICATION/tools/scrub_identifiers.py` (patterns loaded from a gitignored
local config, so no tracked file contains a real identifier).

## Correction to an earlier figure

`FINAL_COMPLETION_REPORT.md` §9 estimated "approximately nineteen pre-existing files" carrying cluster identifiers.
That figure came from a restricted search and was **wrong**. A full `git grep` across the repository found
**160 tracked files** containing at least one of: the cluster login address, the compute-node address, the account
name `<user>`, or the host names `<cluster-login>` / `<compute-node>`. Occurrences before the scrub: 249 account
names, 93 compute-host names, 29 login addresses, 21 login host names, 17 compute addresses.

## Policy

Two different things were conflated in the original instruction, and they are treated differently here.

| Class | Count | Action | Why |
|---|---|---|---|
| **Documentation and scripts** (`.md`, `.sh`, `.sbatch`, `.py`, `.tex`, `.txt`, plus two documentation-grade JSON files) | **42** | **Scrubbed** — identifiers replaced with `<user>`, `<cluster-login>`, `<compute-node>`, `<partition>` | These are the publicly distributable parts of the repository. The placeholders keep the operational narrative readable without disclosing real names or addresses. |
| **Integrity-bearing research artifacts** (run manifests, raw results, scorer outputs, cluster job logs, summary tables) | **117** | **Preserved byte-for-byte** | Their exact bytes are hashed in `FREEZE_*.json`, in the controller's `SHA256SUMS` and in `PHASE3_SHA256_MANIFEST.txt`. Editing them would break the experiment's chain of custody and invalidate every integrity gate. They are already classified **RESTRICTED** in the artifact-availability policy and are **not** part of any public release. |
| **Redaction tooling** | 0 | n/a | The patterns moved to a gitignored config (`tools/redaction_identifiers.json`, with `redaction_identifiers.example.json` tracked), so no tool needs an exemption any more. |

This follows the instruction in Part 10 to preserve original internal research archives rather than destructively
editing historical records, while still removing every identifier from everything that can reach a reader.

## Result

| Check | Result |
|---|---|
| Identifiers in `PHASE3/`, `PHASE4/`, `PHASE5_PUBLICATION/` (the published areas) | **none** |
| Identifiers in any `.md`, `.sh`, `.sbatch`, `.py`, `.tex`, `.txt` anywhere in the repository | **none** |
| Identifiers in the reproducibility package | **none** (checked by `build_repro_manifest.py`, which fails the build on a leak) |
| Identifiers in the submission package | **none** (checked in `PUBLICATION_QA_REPORT.md`) |
| Restricted artifacts still containing identifiers | 117 files, all `RESTRICTED`, none published |

Dependent manifests were regenerated after the scrub: `PHASE4/reproducibility/SHA256SUMS` (29/29 verified) and
`PHASE3/PHASE3_SHA256_MANIFEST.txt` (155 hashed files).

## Two limits the reader should know

1. **Git history still contains the originals.** The scrub changes the working tree, not the commit history, so a
   public clone with full history would still expose the identifiers in earlier revisions of the 42 scrubbed files.
   Rewriting history was not done, consistent with the project's earlier decision not to rewrite history. **Before a
   public release the repository must either be published as a squashed or filtered export, or the history must be
   rewritten.** This is listed as an open item.
2. **The 117 preserved artifacts must stay restricted.** They are already withheld (cluster logs and per-run
   transcripts are restricted until publication in any case), but if that policy ever changes they must be scrubbed
   first, and that will invalidate the hashes recorded for them — so they should be released as a separately hashed
   sanitized export rather than edited in place.

## Scrubbed files

Full list with per-file replacement counts: run
`python PHASE5_PUBLICATION/tools/scrub_identifiers.py --root . --report <file>` (a dry run after the scrub now
reports zero remaining). The 42 files are, by area:

- `research/AGENTRUN_DEEPENING_2026-11-11/` — 9 (execution log, overnight status, reproducibility, results ×2,
  hpc README, sbatch, summarize script, retrieval table)
- `research/AGENTRUN_DEEPENING_2026-11-12/` — 5 (campaign status, executive summary, HPC recovery, reproducibility,
  research audit)
- `research/AGENTRUN_MITACS_INTERVIEW_2026-11-12/` — 3 (dossier and its two build outputs)
- `research/AGENTRUN_PUBLICATION_2026/` root — 6 (continuation status, data-integrity report, roadmap, open issues,
  project audit, repository/data audit, stage-1 audit)
- `PHASE1/` — 7 (architecture and failure analysis, HPC resource sharing, final report, pilot results, README,
  selected direction, launch script)
- `PHASE2/` — 4 (status, execution plan, coordination, finish script)
- `PHASE3/` — 6 (deviations, forensic report, platform continuity ×2, finalize sbatch, analysis driver,
  `platform_evidence.json`)
- `PHASE4/` — 1 (`scripts/build_repro_manifest.py`, now config-driven)
