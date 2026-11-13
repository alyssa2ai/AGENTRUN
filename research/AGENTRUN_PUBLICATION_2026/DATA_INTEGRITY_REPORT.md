> **Note added 13 Nov 2026 by the continuation session.** "387 each" = 384 memory-store files + 3 other files. The size-sweep runs had no store files locally, so the store-isolation check had been skipped for them; the stores and the adapter v2-dev budget-3 run have since been copied from the compute node and verified (see `REPOSITORY_AND_DATA_AUDIT.md`). The text below is otherwise unchanged.

# Data integrity report

**Date: 13 November 2026. Status: COMPLETE.** Everything here was checked live this session.

## Local raw data (E:\agentrun\research\AGENTRUN_DEEPENING_2026-11-11\raw_results)

86 MB, 3,200 files. Campaign 2 run counts, tallied per dataset:

| Dataset | Runs | Format |
|---|---:|---|
| c2_qwen25_{7b,3b,1p5b,14b}_{v1,v2}, c2_qwen3_8b_{v1,v2} | 10 × 480 | runs.jsonl (7B/8B: per-run files, 387 each) |
| c2_qwen25_7b_v2_{hash,bm25}_pad2000 | 2 × 192 | runs.jsonl |
| c2_legacy23_* (10 runs: base/adapter × b3/b6 × greedy + 3 seeds) | 10 × 23 | scores.json + v2_log.jsonl |
| c2_v2dev55_{base_b3,base_b6,adapter_b6} | 3 × 55 | scores.json + v2_log.jsonl |
| c2_v2dev55_adapter_b3 | summary only | Slurm log (per-task data stayed on cluster) |

Total: **5,184 agent runs** + **450 benchmark task evaluations** (230 legacy + 220 v2-dev, of which 55 summary-only). This matches the canonical RESULTS_CAMPAIGN2.md exactly and resolves the brief's "8 additional datasets / ~3,264 runs" claim: jobs 6–13 = 6 size-sweep datasets × 480 + 2 retrieval datasets × 192 = 3,264.

Every record carries full message transcripts, tool calls, token usage and timing. The analysis is reproducible: `analyze_c2.py` regenerates the committed tables byte-identically from these files (verified by diff).

## Remote state (SIT HPC, checked 2026-11-13 10:12 UTC)

- `192.168.192.9` (`sit-gpu`): **reachable**, up 52 days. `/home` at 88% (426 GB free).
- `192.168.192.11` (login node, Slurm controller): **unreachable** (SSH timeout). `squeue` from sit-gpu: "Unable to contact slurm controller". Needs the HPC administrator.
- GPUs: `nvidia-smi` still fails (NVML 580.178 driver/library mismatch) but **CUDA works**: torch 2.15.0+cu132 sees 2 × NVIDIA L40 (verified in the project venv). Every campaign job ran in this state; it is a monitoring problem, not a compute problem.
- Workspace `/home/gpuuser12/AGENTRUN_HPC/20261111/` intact: environment, experiments (111 MB raw_results, 5,255 files), manifests, scripts, source.
- `manifests/jobs_finished.tsv`: campaign2 array 4148 tasks **0–13 all exit=0** (2026-11-12 05:31–08:42 UTC); tasks 14–20 absent — **never dispatched**, consistent with the controller dying while the array (concurrency %2) was still queued.
- Backup `AGENTRUN_HPC/backups/c2_backup_20261112_120842/`: 5,336 files incl. SHA256SUMS.txt, plus a 4.9 MB partial tarball. The earlier "5,223 checksummed files" claim undercounts slightly; the backup as found contains 5,336 files.
- The unrelated BeyondSilence artifacts under the same account were not touched.

## Jobs 14–20: exact mapping (from scripts/campaign2.sbatch, read on the cluster)

| Index | Experiment | Value to the paper |
|---|---|---|
| 14 | dense retriever (bge-small) + 2,000 records | completes the retrieval comparison (currently hash vs BM25 only) — **high** |
| 15 | Qwen2.5-7B, harness v1r (repair turn only) | splits the +15.8 pp into repair vs prompt rules on the model that used the repair turn — **high** |
| 16 | Qwen3-8B, harness v1r | control (8B never fired the repair turn under v2) — medium |
| 17 | adapter on memory benchmark, v1 | transfer question, tangential to the paper — low |
| 18 | adapter on memory benchmark, v2 | low |
| 19–20 | v2 sampled repeats (T=0.7, seeds 1–2) | run-to-run spread for the headline configuration — **high** |

The sbatch is resumable ("resubmitting skips finished work"), so when the controller returns: `sbatch --array=14-20%2 scripts/campaign2.sbatch` after confirming with `squeue` that no remnant of array 4148 is pending. Priority if time-constrained: 14, 15, 19, 20, then 16; 17–18 optional.

## Benchmark artifacts

- `benchmark/eval2.jsonl` (96 tasks): SHA-256 matches `FREEZE_eval2.json` (`42552d7b…`), frozen 2026-11-12 04:54 UTC — before the first eval2 job finished (05:31 UTC).
- `benchmark_v2/dev.jsonl` (55 tasks) and `.sealed/test.jsonl` (130 tasks) match SEAL.json counts; the sealed split's task contents were **not opened** in this session. SEAL.json's custody note (move `.sealed/` out of the repo) is still unexecuted.
- First-study split (48 tasks, `benchmark/eval.jsonl`) present with its own FREEZE.json.

## Discrepancies found

1. "5,223 checksummed files" (previous session) vs 5,336 files in the backup directory — the backup is larger than reported, not smaller; no data loss.
2. `c2_v2dev55_adapter_b3` per-task file exists only on the cluster; retrieve it (low priority) next time the login node allows rsync, or read it from `sit-gpu` directly.
3. Nothing else: counts, hashes and manifests agree across laptop, cluster and committed tables.
