# Phase 2 status

**17 November 2026 update: Phase 2 gates pass; see `PHASE2_COMPLETION_REPORT.md`. Everything below this line is the 16 November record of the blocked state (superseded).**

**16 November 2026, updated 09:45 UTC. Phase 2 is NOT complete.** The GPU-dependent steps are submitted to Slurm but cannot start (§2). Everything that does not need a GPU is done and verified.

## 1. State when this session resumed (recovered, not redone)

| Item | State found | Verification |
|---|---|---|
| Branch / commits | `research/memory-ablation-2026-11`, HEAD `d3cdb95` (Phase 1: `fc3224c`, `d3cdb95`) | `git log` |
| Working tree | Phase 2 directory and many unrelated files untracked/modified (`README.md`, `.gitignore`, `agentrun_v2/`, …) | preserved; nothing reset or cleaned |
| Job 4189 (`hpc/p2val_pipeline.sbatch`) | **completed successfully** on 14 Nov 05:09–05:44 UTC: writer, assembly, 2 annotators, LLM arbiter × 4 models, every step exit 0 | log `logs/p2val_pipeline_4189.out`; not in queue; `sacct` unavailable (accounting disabled) |
| p2val | 88 skeleton items (22 categories), **77 valid**, 11 excluded by mechanical validation (ids and reasons in `p2val_MANIFEST.json`) | local files sha256-identical to the cluster |
| LLM-arbiter outputs of job 4189 | existed only on the cluster | copied, 16/16 sha256-identical |
| evarb | **already frozen as evarb-0.2** (2026-11-14T08:14:16Z) after one look at p2val with 0.1 | 12/12 file hashes + 3 dependencies match locally and on the cluster |
| Tests | 82 passing | re-run |
| p2val2 | skeleton (92 items, 23 categories, v2 semantics) and writer input built; texts not written | writer input contains no gold (checked) |
| eval3 | not built | `~/AGENTRUN_HPC/sealed/` did not exist |

Corrections to the resume brief: job 4189 wrote all 88 p2val items (11 failed validation, not "3 of 32"); evarb was already frozen; p2val had become development data, so the planned validation split for the frozen mechanism is p2val2.

## 2. Blocker

Job **4196** (`vne_compare`, user `gpuuser16`, not an AGENTRUN, Veriflow or ErrorEcho job) requested `--mem=0`, i.e. **all 515,705 MB** of the node's memory, with a **365-day** time limit. It uses no GPU and 2 CPUs, but while it runs Slurm cannot place any other job on `sit-gpu`. The scheduler's projected start for AGENTRUN's next job is **2027-11-16**. Both L40s are idle. ErrorEcho's jobs were blocked the same way.

AGENTRUN does not bypass Slurm and does not touch other users' jobs. **Resolution needs the job's owner or the cluster administrator** (re-submit 4196 with a real `--mem`, or cancel it). The AGENTRUN owner emailed the administrators on 16 November. Queue and sharing details: `hpc/COORDINATION.md`.

Queued AGENTRUN chain (one GPU at a time, all start automatically when memory is free):

| Job | Script | Depends on | Does | Est. GPU time |
|---|---|---|---|---|
| 4199 | `hpc/p2val2_pipeline.sbatch` | — | p2val2 writer, assembly, 2 blind annotators, agreement, seal checks, LLM arbiter × 4 | ≈ 0.6 h (job 4189 took 35 min for the same steps on p2val) |
| 4200 | `hpc/eval3_build.sbatch` | afterany 4199 | freeze check, eval3 skeleton → writer → assembly → annotators → agreement → seal checks → provenance → seal + verify | ≈ 1 h |
| 4201 (array 0–2 %1) | `hpc/p2val_agents.sbatch` | afterok 4199, afterany 4200 | 12 configs × (p2val2, p2val) × Qwen2.5-3B / 7B, Llama-3.1-8B | ≈ 6 h |

## 3. Completion checklist (brief §13)

| # | Criterion | Status |
|---|---|---|
| 1 | Job 4189 status recovered | **done** — completed, outputs recovered and hash-verified |
| 2 | p2val generation and quality checks | **done for p2val** (77 valid; 3 blind annotators; split checks pass; the 11 exclusions re-reviewed: `data/p2val/P2VAL_EXCLUSION_REVIEW.md`). **p2val2 texts not generated** (blocked); its generator audited (`data/GENERATOR_AUDIT.json`) |
| 3 | Evarb evaluated against the baselines | **component level done** on dev, regression, p2val (`BASELINE_COMPARISON.md`); **p2val2 and agent level blocked** |
| 4 | Evarb frozen on a documented decision | **done** — evarb-0.2, `FREEZE_evarb.json` history; not changed in this session |
| 5 | Agent-level p2val results | **blocked** (job 4201) |
| 6 | Llama-3.1-8B integration reproducible | **partly** — adapter, unit tests, 20-run smoke (96% parsable, job 4183) and 230-group LLM-arbiter run (0 format failures) exist; the agent-level runs are in job 4201 |
| 7 | eval3 generated, verified, sealed | **blocked** (job 4200); build, split checks and seal are scripted and gated on the freeze |
| 8 | Pre-registration complete | **draft** — every element fixed and the procedures verified end to end with a CPU dry run (§14); power and the eval3 hashes still need p2val2 runs and the sealed build |
| 9 | Phase 3 scripts and budget | **scripts ready** (`hpc/phase3_eval3.sbatch`); budget recalculated from measured model-specific times: **109.2 GPU-h** (`data/BUDGET_phase3.md`); final figure from p2val2 timings |
| 10 | Tests, manifests, documentation | **92/92 tests pass**; `PHASE2_HASH_MANIFEST.txt` refreshed; documents written from observed evidence |

## 4. Housekeeping: BeyondSilence cold storage (done)

Read-only check on 16 November (`~/claude_ops/beyondsilence_verify_20261116/VERIFY_REPORT.txt` on the cluster). Archive sha256 `e0a8a2f467988f07772c4ac9c47208d4ac84b3d83547a9c10678578f5f77237f` (28,261,660,777 bytes); zstd and tar both exit 0; decompressed 72,104,960,000 bytes as expected; 62,420 regular files, 35,581 hard links, 1,155 symlinks, 6,449 directories; all 98,001 file paths and all regular-file sizes match `~/beyondsilence-work`. Original project untouched; service not restarted.

## 5. Done while the queue was blocked (16 November, CPU only)

- Excluded p2val items re-reviewed: 6 validator false negatives (long-form dates), 5 genuine writer failures; all stay excluded; deadline items under-represented (5/14 kept).
- Long-range negation failure pinned as a regression case (`tests/test_known_limitations.py`) and listed in `PREREGISTRATION.md` §12.
- p2val2 and eval3 generators audited before any text exists (`benchmark/audit_generators.py`; also run on the cluster copy).
- Pre-registration procedures verified end to end with simulated agents (`scripts/dryrun_pipeline.py`, `PREREGISTRATION.md` §14).
- Phase 3 budget recalculated (`scripts/budget_phase3.py`): 109.2 GPU-h.
- Post-HPC automation: `scripts/finish_phase2.sh` (status / fetch / freeze / analyze), `scripts/write_freeze_eval3.py`, `scripts/subset_tasks.py`.
- Code synced to the cluster; evarb-0.2 hashes re-verified there; the queued jobs are unchanged (no duplicates submitted).

## 6. What to do when the queue frees

Nothing needs to be re-submitted: 4199 → 4200 → 4201 run in order. Then, in `PHASE2/`:
1. `bash scripts/finish_phase2.sh status` until all three show their final `exit=` lines.
2. `bash scripts/finish_phase2.sh fetch` — copies p2val2, arbiter outputs, agent runs and logs; verifies every sha256 against the cluster.
3. Audit every p2val2 item (text vs. brief and gold: meaning, values, negation/quotation, ambiguity, entities) **before** looking at any evarb output; write `data/p2val2/P2VAL2_ITEM_AUDIT.md` and list exclusions.
4. `bash scripts/finish_phase2.sh freeze` — `FREEZE_eval3.json` from the eval3 job log and a remote `sha256sum -c` (no sealed content read).
5. `bash scripts/finish_phase2.sh analyze` — component comparison on p2val2, agent-level analysis (p2val2 all/primary, p2val), power, final budget.
6. Fill the ⏳ items in `PREREGISTRATION.md`, update the documents, re-run tests and the hash manifest, commit, then freeze the pre-registration (its sha256 goes into `FREEZE_eval3.json` via step 4, so run step 4 again after the final edit).
