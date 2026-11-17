# Phase 3 status

**17 November 2026, 09:00 UTC. Phase 3 is RUNNING, not complete. No confirmatory result exists and none has been looked at.**

- Preregistration frozen (sha256 `221013b3…`), Phase 2 commit `48d6e44` (local, not pushed).
- Slurm array **4233**, 18 cells (Qwen2.5-3B, Qwen2.5-7B, Llama-3.1-8B, Qwen3-8B × greedy + 3 seeds; then Qwen2.5-14B and Llama-3.2-3B greedy), `%1` = one GPU at a time. Cell 0 started 08:58:33 UTC; in-job gates passed (evarb-0.2 hashes, eval3 `sha256sum -c`, preregistration hash).
- Estimate: 128.1 GPU-h (≈ 5.3 days) from p2val2-measured timings; T=0.7 and 14B times are partly not measured.
- Other projects: queue was empty and the node idle at submission; a note was appended to the cluster `COORDINATION.md`.
- Resume rule: `sbatch --array=<idx> hpc/phase3_eval3.sbatch` re-runs only missing pairs. Raw output: `~/AGENTRUN_HPC/phase3_raw/` on the cluster.
- Remaining deliverables (execution log, model comparison, ablations, statistics, failure analysis, latency, limitations, final report) are not written; they need the completed cells.
