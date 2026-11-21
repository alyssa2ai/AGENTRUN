# Phase 2 completion report (17 November 2026)

## Gates

| Gate | Result | Evidence |
|---|---|---|
| Jobs 4199, 4200, 4213 (0-2), 4222 | all `exit=0`; queue empty | `logs/*`, remote `squeue`; Slurm accounting is disabled, so exit lines and `DONE` markers were used |
| Outputs fetched | all sha256-identical to the cluster (incl. the Qwen3-8B run dir, fetched separately) | `sha256sum -c` |
| eval3 sealed | yes: `seal verified` (job 4200, 16 Nov 10:46 UTC); `sha256sum -c SHA256SUMS` passes on all 13 files today; hard seal checks pass | `FREEZE_eval3.json` |
| eval3 contents unseen | no task text, label or outcome read. Two metadata reads of `eval3_tasks.jsonl`: the key names of the first row, and a count of tasks and distinct (scenario, variant) pairs (268 and 135) | disclosed |
| p2val2 | 92 skeleton, 90 valid, 2 mechanical exclusions; annotators Llama κ 0.49 (58/90 exact), Qwen-14B κ 0.63 (71/90) | `data/p2val2/*` |
| Audit chronology | audit file hash matches the record; mtime 10:03:05 UTC predates all mechanism outputs (≥10:05:03); the hash record itself was written at 10:15 UTC. Not blind or independent (same author as the mechanism) | `PREREGISTRATION.md` §16 |
| 69/74 vs 69/82 | reconciled (`BASELINE_COMPARISON.md` §6) | |
| Agent-level p2val2, 4 models | complete: 4 × 1,080 runs, 0 missing; Llama 9 format failures per config | `data/AGENT_p2val2*.md` |
| Qwen2.5-3B/7B, Llama p2val | complete | `data/AGENT_p2val.md` |
| Power | recomputed with 135 families and 4 models; H-primary power at half effect 0.961 | `data/POWER_phase3.md` |
| Budget | 116.5 GPU-h + 10% = **128.1 GPU-h** (≈ 5.3 days one GPU) for 268 tasks × 12 configs × 18 cells | `data/BUDGET_phase3.md` |
| Preregistration | filled and frozen; sha256 in `FREEZE_eval3.json` | |
| evarb-0.2 | unchanged | `FREEZE_evarb.json` |
| Tests | all pass | pytest |

## Caveats
- T=0.7 per-run times are not measured on p2val2 (greedy × 2.05 ratio); Qwen2.5-14B timing is from Phase 1.
- Power treats p2val2 effects as truth; EBG−LG is under-powered at half effect (0.53).
- p2val2 shows EBG−RT ≈ 0 on Llama-3.1-8B and ungated enforcement beating the gate; both are visible before the freeze (`PREREGISTRATION.md` §15).
- No human validation of eval3.
