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
