# Phase 3 status

**COMPLETE — 2026-11-21.** Campaign executed, integrity gates passed, preregistered analysis run, reports written,
deviations disclosed, manuscript results and discussion written from the verified outputs.

| | |
|---|---|
| Cells | 18 / 18 DONE |
| Rows | 3216 per cell, **57,888** total; 0 missing, 0 duplicates, 0 harness errors, 0 unparsable |
| Integrity gates | G1–G4 **PASS** under policy `g4-v2`; 2 observational notes (`client.gpu_mem_gib` 44.6 → 44.4) |
| G5 platform continuity | reporting only: 2/18 cells straddle the node boot; 980/57,888 rows (1.693%) |
| Checksums | raw 54/54 OK; eval3 seal OK; `FREEZE_evarb` OK; preregistration hash `221013b3cee87c00` OK |
| Confirmatory analysis | 268 tasks, 135 families, 51,456 runs, 100,000 permutations, Holm over 4 contrasts |
| Cross-check | independent recomputation agrees exactly (60/60 counts, 4/4 differences) |
| Tests | Phase 2: 92 passed (campaign tree) / 88 passed + 1 documented import error (clone); Phase 3: 28 passed |
| Finalization job | Slurm **4359**, 2026-11-21 04:52–05:03 UTC, CPU-only (2 CPUs, 6 GB) |
| HPC commit | `39d69b0` (analysis), on `research/memory-ablation-2026-11`, local only |

## Verdicts

| Hypothesis | Contrast | Difference | Holm p | Verdict |
|---|---|---|---|---|
| H-primary | EBG − RT | +17.1 pp [12.2, 22.1] | 4 × 10⁻⁵ | SUPPORTED |
| S1 | EBG − T | +14.5 pp [10.5, 18.6] | 4 × 10⁻⁵ | SUPPORTED |
| S2 | EBG − LG | +15.9 pp [10.4, 21.2] | 4 × 10⁻⁵ | SUPPORTED |
| S3 | EBG − B | +15.3 pp [10.3, 20.5] | 4 × 10⁻⁵ | SUPPORTED |
| S4 | EBG − RT harmful | −19.4 pp [−24.6, −14.6] | — | NOT FALSIFIED |

The most important exploratory result cuts the other way: ungated enforcement (EBG-all) scored **9.7 pp higher**
than EBG while more than doubling the harmful rate. See `PHASE3_FINAL_REPORT.md` §3.1 and §7.

## History

| Date | Event |
|---|---|
| 2026-11-17 | preregistration frozen (`221013b3cee87c00`); campaign starts as Slurm array 4233 |
| 2026-11-18 → 11-19 | controller v2 (job 4257) runs the remaining cells, two lanes |
| 2026-11-20 10:11:58 | **unplanned node reboot**; kernel and NVIDIA driver change; two cells interrupted |
| 2026-11-20 10:17 | controller quarantines the truncated tails and resubmits (jobs 4326, 4327) |
| 2026-11-20 11:22 | all 18 cells DONE; raw SHA256SUMS written |
| 2026-11-20 11:22 | finalization job **4270** fails: `STATE: FAILED (gates)` on two G4 `client` mismatches |
| 2026-11-21 | forensic investigation; G4 corrected to `g4-v2`; G5 added; deviations documented |
| 2026-11-21 04:51 | job 4358 passes gates and G5, fails at `verify` (same blob comparison in `verify_phase3.py`) |
| 2026-11-21 04:52–05:03 | job **4359** completes every stage; analysis, reports, results draft, seal, commit |

## Deliverables

`PHASE3_FINAL_REPORT.md` §8 lists them all, with the generated and hand-written ones distinguished. Everything is
hashed in `PHASE3_SHA256_MANIFEST.txt`.

## What is not done

- The eval3 items, annotations and per-run transcripts stay sealed until publication, so no transcript-level failure
  study exists (`PHASE3_FAILURE_ANALYSIS.md` §6).
- The pre-reboot kernel and driver versions are inferred, not read; one privileged command on the node would settle
  it (`PHASE3_DEVIATIONS.md` D1).
- Whether the driver change altered generation cannot be established from this campaign
  (`PHASE3_FINAL_REPORT.md` §7.1).
