# Execution under Slurm

All commands run from `research/AGENTRUN_PUBLICATION_2026/PHASE2/` on the cluster login node. Jobs run on the GPU node.

## 1. One cell
```bash
sbatch --array=<idx> hpc/phase3_eval3.sbatch          # idx 0-17, mapping in CELLS
```
Before any model call, each job:
1. checks every evarb-0.2 file against `FREEZE_evarb.json`;
2. runs `sha256sum -c` on the sealed eval3 directory;
3. checks the preregistration hash against `FREEZE_eval3.json` (status SEALED).

It then runs `scripts/run_p2.py` with the 12 configurations. Output goes to `$HOME/AGENTRUN_HPC/phase3_raw/eval3_<tag>_<decoding>/`: `runs.jsonl` gets one line per (task, configuration), flushed after each run; `manifest.jsonl` gets one line per start; `DONE` is written only on normal completion. The runner skips (task, configuration) pairs already present, so a resubmitted cell resumes.

## 2. Campaign controller (`hpc/phase3_controller_v2.sbatch`)
CPU-only job that keeps at most two cells running, one per GPU. It falls back to one GPU whenever a job from another project requests a GPU, and it never preempts. It submits a cell only if the cell has no `DONE` marker and is not already queued or running (`squeue -r`, array index). If `squeue` fails, it submits nothing that round. Before a resubmission it moves a truncated trailing line of `runs.jsonl` to `runs.jsonl.partial_<UTC>` (nothing is deleted). A cell with no new rows over two consecutive attempts, or with more than 5 attempts, is marked BLOCKED. Cell wall-time limits are 12 h, or 36 h for Qwen2.5-14B, so a hung cell is killed and retried. When all 18 cells are DONE, the controller writes `phase3_raw/SHA256SUMS` and `phase3_controller/ALL_DONE`. Status is in `$HOME/AGENTRUN_HPC/phase3_controller/status.txt` and `events.log`.

## 3. Finalization (`PHASE3/scripts/phase3_finalize.sbatch`, copy in `slurm/`)
```bash
sbatch --dependency=afterany:<controller job id> phase3_finalize.sbatch
```
CPU-only job. It does not take the controller's exit as proof: it re-checks every gate itself (`finalize_gates.py` and hash checks):
- 18 DONE markers;
- 3,216 unique pairs per cell, no duplicates and no unparsable lines;
- the last Slurm segment of each cell exited with 0;
- manifests consistent across starts;
- raw-file checksums;
- the eval3 seal;
- evarb-0.2, preregistration and seal-manifest hashes.

It stops on the first failure. It then stages copies of the raw cells and verifies them, runs `run_phase3_analysis.sh verify / analyze / report`, writes the results draft and the SHA-256 manifest, and commits in a repository clone on the cluster. Nothing is pushed. Status goes to `$HOME/AGENTRUN_HPC/PHASE3_FINAL_STATUS.md`.

## 4. Campaign record (Phase 3, Nov 2026)
Slurm array 4233 ran cells 0–8 on one GPU. Controller v2 (job 4257) ran cells 9–17, two at a time from 18 Nov 08:58 UTC. Finalization was job 4270. Per-cell job ids, GPU index, start and end times, wall hours and exit codes are in `PHASE3/PHASE3_EXECUTION_LOG.md` and `PHASE3/results/execution.csv`.
