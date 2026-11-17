# Phase 3 execution plan

**16 November 2026. Prepared, not launched.** Script: `hpc/phase3_eval3.sbatch`. Pre-registration: `PREREGISTRATION.md` (draft until its ⏳ items are filled). Do not submit before eval3 is sealed and the pre-registration commit exists.

## 1. Run matrix

| Cell idx | Model | Decoding | Role |
|---|---|---|---|
| 0–3 | Qwen2.5-3B | greedy, T0.7 s1–s3 | primary |
| 4–7 | Qwen2.5-7B | greedy, T0.7 s1–s3 | primary |
| 8–11 | Llama-3.1-8B | greedy, T0.7 s1–s3 | primary (second family) |
| 12 | Qwen2.5-14B | greedy | secondary |
| 13 | Llama-3.2-3B | greedy | format-limited, separate |

Each cell: eval3 valid tasks (≤ 276) × 12 configurations = **≤ 3,312 runs**. Whole campaign: **≤ 46,368 runs**.

## 2. GPU budget

**Recalculated 16 November from measured, model-specific per-run times** (`scripts/budget_phase3.py` → `data/BUDGET_phase3.md|json`; ≤ 276 tasks × 12 configurations per cell; LA/LG add 1.5 arbiter calls per run at the latency measured for that model in Slurm job 4189):

| Model | s/run greedy | s/run T0.7 | Source | Cells | GPU-h |
|---|---|---|---|---|---|
| Qwen2.5-3B | 2.1 | 3.2 | Phase 1 pilot, measured (3 and 2 run sets) | 4 | 11.4 |
| Qwen2.5-7B | 4.0 | 8.2 | Phase 1 pilot, measured | 4 | 27.4 |
| Llama-3.1-8B | **4.8** | 9.8 | greedy **measured** in Slurm job 4183 (incl. process start); T0.7 = greedy × 2.05, the Qwen2.5-7B ratio (**not measured** for Llama) | 4 | 32.7 |
| Qwen2.5-14B | 27.1 | — | Phase 1 pilot, one run set outside Slurm (6.8 s per call). Scaling the 7B agent time by the 14B/7B arbiter-latency ratio measured in job 4189 gives ≈ 9 s instead | 1 | 25.6 |
| Llama-3.2-3B | **2.2** | — | **measured** in job 4183 | 1 | 2.2 |
| **Subtotal** | | | | 14 | **99.3** (primary cells 71.5) |
| **Total with 10% contingency** | | | | | **109.2 GPU-h ≈ 4.5 days on one GPU** |

Sensitivity: with 14B at the scaled 9.1 s/run the total is 91.0 GPU-h. The earlier 130 GPU-h estimate assumed 240 tasks × 9 configs × 4 decodings for every model, including 14B.

⏳ **Final figure:** `bash scripts/finish_phase2.sh analyze` reruns `budget_phase3.py --runs raw/p2val2_*_greedy`, which replaces the per-run times of Qwen2.5-3B/7B and Llama-3.1-8B with times measured on p2val2 for **every configuration** (EB/EBG and LA/LG included, so no arbiter-call assumption). 14B and Llama-3.2-3B keep the values above (not run in Phase 2).

**Per-model GPU requirement:** one L40; peak VRAM (measured, bf16): Qwen2.5-3B 5.9 GiB, Llama-3.1-8B 15.5 GiB, Qwen2.5-7B ≈ 16 GiB and Qwen2.5-14B ≈ 30 GiB (bf16 weight size, not measured as peak). **Concurrent GPUs: 1** (array `%1`).

**Wall time:** ≈ 109 h of continuous single-GPU use ≈ **4.5 days** if the queue is free; each array task has a 12 h limit (the largest cell, 14B greedy, ≈ 25 h, needs two re-submissions; the runner resumes).

**Disk:** 7.2 KB per run record measured in Phase 1 (LLM-arbiter configs log more) → ≈ 0.35–0.5 GB of raw output under `~/AGENTRUN_HPC/phase3_raw/`. `/home` had 397 GB free on 16 November. No model download is needed (all snapshots cached).

## 3. Order and checkpointing

- Cells run cheapest-first: the 12 primary cells finish (≈ 71.5 GPU-h) before the secondary ones start. If the campaign is stopped, the confirmatory analysis can run on complete primary cells.
- `run_p2.py` appends one line per (task, config) and skips finished pairs: a killed, pre-empted or timed-out cell is re-submitted unchanged (`sbatch --array=<idx> hpc/phase3_eval3.sbatch`). Each run directory has `manifest.jsonl` (one line per start, with code hashes) and `DONE`.
- Integrity gates at the start of every cell: `FREEZE_evarb.json` hashes, `sha256sum -c` of the sealed eval3, and `--expect-sha` on the task file.

## 4. Sharing the node

- Node `sit-gpu`: 2 × L40, 96 CPUs, 515 GB RAM. Shared with Veriflow, ErrorEcho (same Unix account, separate projects) and other users.
- AGENTRUN rule (`PHASE1/HPC_RESOURCE_SHARING.md`): at most one GPU, always through Slurm, `--time` set, `squeue` checked immediately before each submission, never touch other projects' processes or files.
- Veriflow submits one-GPU arrays (`%1`, up to ≈ 42 GB VRAM). With AGENTRUN also at one GPU, both fit at the same time. A 4.5-day campaign should be announced to the Veriflow and ErrorEcho owners in advance; ErrorEcho's queued jobs on 16 November were CPU-only.
- **Observed on 16 November:** job 4196 (`vne_compare`, another user) requested `--mem=0`, i.e. all 515 GB, with a 365-day limit, and uses no GPU. While it runs, Slurm cannot start any other job on the node (scheduler's projected start for AGENTRUN's queued job: 2027-11-16). Phase 3 cannot start until this is resolved by its owner or the administrator.
