# Deviations affecting reproduction

The authoritative ledger is `research/AGENTRUN_PUBLICATION_2026/PHASE3/PHASE3_DEVIATIONS.md` (D1-D7). It is kept
there, with the Phase 3 artefacts it describes, rather than duplicated here. This file lists what a reproducer needs
to know before starting.

| What | Where to read it |
|---|---|
| Host platform transition on 2026-11-20 (kernel and NVIDIA driver), and the 980 rows it affects | `PHASE3/PHASE3_DEVIATIONS.md` D1; `PHASE3/PHASE3_PLATFORM_CONTINUITY.md` |
| Slurm requeue, truncated write, quarantine recovery, two console logs lost | `PHASE3/PHASE3_DEVIATIONS.md` D2 |
| Re-seeding of the sampling stream in the one resumed sampled cell | `PHASE3/PHASE3_DEVIATIONS.md` D3; `ENVIRONMENT.md` |
| Integrity-gate correction `g4-v1` to `g4-v2`, and why | `PHASE3/PHASE3_DEVIATIONS.md` D4; `PHASE3/PHASE3_G4_FORENSIC_REPORT.md` |
| The reporting-only platform-continuity check | `PHASE3/PHASE3_DEVIATIONS.md` D5 |
| `pytest` installed after the campaign | `PHASE3/PHASE3_DEVIATIONS.md` D6; `ENVIRONMENT.md` |
| The two post-hoc exploratory sensitivity analyses, and what they cannot establish | `PHASE3/PHASE3_DEVIATIONS.md` D7; manuscript Section 8.4 |

**Three consequences for a reproduction attempt.**

1. `qwen3_8b_T07_s3` and `llama32_3b_greedy` were not produced on a single platform, so they cannot be reproduced
   row for row on one driver version. The other sixteen cells were.
2. `qwen3_8b_T07_s3` additionally re-seeded its sampler at row 2345, so reproducing it byte for byte requires
   reproducing the interruption at that row.
3. The analysis is reproducible byte for byte from the archived raw outputs regardless, with seeded permutations and
   seeded bootstraps; the two points above concern regenerating the raw outputs, not re-analysing them.
