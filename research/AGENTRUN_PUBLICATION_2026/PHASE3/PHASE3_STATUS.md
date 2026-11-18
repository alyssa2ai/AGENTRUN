# Phase 3 status

**17 November 2026, 09:00 UTC. Phase 3 is RUNNING, not complete. No confirmatory result exists and none has been looked at.**

- Preregistration frozen (sha256 `221013b3…`), Phase 2 commit `48d6e44` (local, not pushed).
- Slurm array **4233**, 18 cells (Qwen2.5-3B, Qwen2.5-7B, Llama-3.1-8B, Qwen3-8B × greedy + 3 seeds; then Qwen2.5-14B and Llama-3.2-3B greedy), `%1` = one GPU at a time. Cell 0 started 08:58:33 UTC; in-job gates passed (evarb-0.2 hashes, eval3 `sha256sum -c`, preregistration hash).
- Estimate: 128.1 GPU-h (≈ 5.3 days) from p2val2-measured timings; T=0.7 and 14B times are partly not measured.
- Other projects: queue was empty and the node idle at submission; a note was appended to the cluster `COORDINATION.md`.
- Resume rule: `sbatch --array=<idx> hpc/phase3_eval3.sbatch` re-runs only missing pairs. Raw output: `~/AGENTRUN_HPC/phase3_raw/` on the cluster.
- Remaining deliverables (execution log, model comparison, ablations, statistics, failure analysis, latency, limitations, final report) are not written; they need the completed cells.

## Update 17 Nov 2026 (afternoon, IST)
- Retry controller **4243** (`PHASE2/hpc/phase3_retry_controller.sbatch`, no GPU, 1 GB) starts after array 4233 ends and resubmits only incomplete cells, up to 5 rounds (the 14B cell needs two because of the 12 h task limit).
- Analysis pipeline ready and tested on p2val2 development data (`DRY=1`): `scripts/run_phase3_analysis.sh status|fetch|verify|analyze|all`, `scripts/verify_phase3.py`, `scripts/build_reports.py`. Sealed task file and raw eval3 runs are gitignored (`PHASE3/.gitignore`).
- `LIMITATIONS.md` written. Remaining deliverables need real results: FAILURE_ANALYSIS, PHASE3_FINAL_REPORT.
- Cluster is only reachable from campus; next on-campus step: `bash scripts/run_phase3_analysis.sh status`.

## Update 18 Nov 2026, 09:10 UTC (on campus)
- Cluster state verified: **8/18 cells DONE** (0-7: Qwen2.5-3B and Qwen2.5-7B, greedy + 3 seeds; 3216/3216 rows each, exit 0). Measured wall time per cell: Qwen2.5-3B 1.70-1.77 h, Qwen2.5-7B 3.71-3.86 h. Cell 8 (Llama-3.1-8B greedy) running, ~3.9 h.
- Fetched the 8 DONE cells (24 files, sha256 equal to the cluster) to `RAW_RESULTS/` (gitignored); `verify_phase3.py`: no missing pairs, duplicates, harness errors or hash drift (`ANALYSIS/INTERIM/COMPLETENESS_done8.md`). No outcome has been aggregated (no interim look, PREREGISTRATION.md section 10).
- GPU1 was idle and no other GPU job was queued, so the campaign now uses both L40s: retry controller 4243 and the pending (never started) tasks 4233_[9-17] were cancelled and replaced by **controller v2, job 4257** (`PHASE2/hpc/phase3_controller_v2.sbatch`): at most two cells, one per GPU, falls back to one GPU when any other project requests a GPU, never resubmits DONE or queued cells, quarantines truncated trailing lines, marks no-progress cells BLOCKED. The 14B cell (job 4259_16, `CUDA_VISIBLE_DEVICES=1`, 36 h limit) started 08:58 UTC at ~10 s/run (~9 h, not 25 h). Coordination note appended to the cluster `COORDINATION.md`.
- Remaining ≈ 40 GPU-h on two lanes; expected completion ≈ 19 Nov 2026 05:00-08:00 UTC. Status: `bash scripts/run_phase3_analysis.sh status`.
- Pipeline: the 100,000-permutation p2val2 dry run had completed on 17 Nov (p-values on the 1/100001 grid); reproducibility re-run, cross-check (`scripts/crosscheck_phase3.py`), sensitivity analyses (flagged complement, set (b) via `scripts/agreed_ids_b.py`, validated against the Phase 2 Qwen-agreed ids) and `build_reports.py` (PHASE3_* deliverables, CSVs, mechanical verdicts) added; `report` stage in `run_phase3_analysis.sh`.
- Correction 09:21 UTC: over 22 min the 14B cell runs at ~21 s/run (≈ 18.5 h for 3216 runs, consistent with the Phase 1 pilot's 27 s/run), not ~10 s. Remaining ≈ 49 GPU-h; with two lanes the expected completion is **≈ 19 Nov 2026 10:00-11:00 UTC** (lane A: cells 8-13/15, lane B: 14B then the remaining cells).

## Update 18 Nov 2026, 10:00 UTC: the cluster finishes Phase 3 without the laptop
- The repository (branch at `b7c8b7a`) was cloned on the cluster as a git bundle to `~/AGENTRUN_HPC/finalize/AGENTRUN`. The clone's frozen files are byte-identical to the tree the running cells use. evarb-0.2 and preregistration hashes verify.
- Chain, all under Slurm: controller v2 (4257) runs the cells and exits only when all 18 are DONE or the rest are BLOCKED. Then **finalization job 4270** (`--dependency=afterany:4257`, CPU only, 2 CPUs, 16 GB) runs `PHASE3/scripts/phase3_finalize.sbatch`. It re-checks every gate explicitly (`finalize_gates.py`: 18 DONE, 3216 unique pairs per cell, no duplicates or unparsable lines, last Slurm exit 0, consistent manifests). It also checks raw checksums, the eval3 seal, and the freeze and preregistration hashes, and stops on any failure. It then runs `run_phase3_analysis.sh verify/analyze/report`, writes `PHASE4/manuscript/07_results_AUTO.md`, writes `PHASE3_SHA256_MANIFEST.txt`, and commits in the HPC clone (never pushed).
- Status file: `~/AGENTRUN_HPC/PHASE3_FINAL_STATUS.md` (STATE: RUNNING, FAILED (stage) or ANALYSIS COMPLETE). No notification channel is configured.
- Validated on the cluster (CPU job 4268): Phase 3 pipeline tests pass. 88 Phase 2 tests pass; `tests/test_clients.py` cannot import `agentrun_v2`, which is untracked in git. The gates pass cells 0-7 and fail only the unfinished cells.
- Stalls: every cell has a wall-time limit (12 h; 36 h for 14B). A hung cell is killed and resubmitted. Two attempts without new rows mark it BLOCKED, with at most 5 attempts.
- Still needs a session: the interpretation (PHASE3_FAILURE_ANALYSIS.md, PHASE3_FINAL_REPORT.md), the manuscript discussion, the citation fixes and the reproducibility package. To fetch the finished work: `git fetch gpuuser12@192.168.192.11:AGENTRUN_HPC/finalize/AGENTRUN research/memory-ablation-2026-11:hpc-final`.
