# Campaign 2 — HPC Recovery

## Current infrastructure state (as of 2026-11-12 12:08 UTC)

| Component | Status | Details |
|---|---|---|
| Login node (192.168.192.11) | DOWN | SSH: "Connection timed out" / "No route to host" |
| Compute node (192.168.192.9) | UP | SSH connects, uptime >51 days, load ≈ 0 |
| Slurm controller | UNREACHABLE | `Unable to contact slurm controller (connect failure)` from compute node |
| nvidia-smi | BROKEN | `Failed to initialize NVML: Driver/library version mismatch (NVML library version: 580.178)` |
| User processes | NONE | No AGENTRUN processes under gpuuser12 (BeyondSilence service running — do not touch) |

## What happened

1. Campaign 2 was submitted as Slurm array 4148, indices 0–20, max 2 concurrent.
2. Jobs 0–13 completed successfully between 04:58 and 08:42 UTC on 2026-11-12.
3. After job 13 completed, the login node (which runs the Slurm controller) became unreachable.
4. Jobs 14–20 were queued but never dispatched because the scheduler was gone.
5. The compute node is still up but cannot submit or query jobs without the controller.

## What needs to happen (requires SIT administrator)

1. **Restore the login node** (192.168.192.11) or the Slurm controller daemon.
2. **Fix the NVML driver mismatch.** The nvidia-smi failure may be unrelated to the Slurm outage but would prevent any GPU workload from running even if Slurm is restored. This likely requires `sudo` access to update the NVIDIA driver.
3. **Verify GPU functionality** with `nvidia-smi` and a test CUDA program.

## Recovery procedure once infrastructure is restored

```bash
# 1. Connect to the login node
ssh gpuuser12@192.168.192.11

# 2. Verify Slurm is back
squeue -u gpuuser12
scontrol show partition gpu-nodes

# 3. Check if original array 4148 is still active
scontrol show job 4148

# 4a. If array is dead (COMPLETED or FAILED), submit only missing indices:
cd /home/gpuuser12/AGENTRUN_HPC/20261111
sbatch --array=14-20%2 scripts/campaign2.sbatch

# 4b. If array is still pending, check which tasks are pending:
squeue -u gpuuser12 --array

# 5. Monitor progress
watch -n 30 'squeue -u gpuuser12; tail -3 manifests/jobs_finished.tsv'

# 6. Verify completions
for i in 14 15 16 17 18 19 20; do
  grep "4148_${i}" manifests/jobs_finished.tsv
done
```

## What the 7 missing jobs would produce

| Index | Run ID | Est. wall time | What it adds |
|---|---|---|---|
| 14 | c2_qwen25_7b_v2_dense_pad2000 | ~15 min | Completes retrieval comparison (hash vs BM25 vs dense) |
| 15 | c2_qwen25_7b_v1r | ~33 min | Isolates repair turn effect (v1r = v1 + repair, no rules) |
| 16 | c2_qwen3_8b_v1r | ~38 min | Same for Qwen3-8B |
| 17 | c2_qwen25_7b_lora_v1 | ~33 min | QLoRA adapter effect on eval2 tasks (v1 harness) |
| 18 | c2_qwen25_7b_lora_v2 | ~33 min | QLoRA adapter effect on eval2 tasks (v2 harness) |
| 19 | c2_qwen25_7b_v2_T07_s1 | ~33 min | Run-to-run variance under sampling (seed 1) |
| 20 | c2_qwen25_7b_v2_T07_s2 | ~33 min | Run-to-run variance under sampling (seed 2) |

**Estimated total time with 2 concurrent:** ~2 hours.

## Data collection after recovery

```bash
# From local machine, after jobs complete:
RBASE=research/AGENTRUN_DEEPENING_2026-11-11/raw_results
REMOTE=/home/gpuuser12/AGENTRUN_HPC/20261111/experiments/raw_results

for exp in c2_qwen25_7b_v2_dense_pad2000 c2_qwen25_7b_v1r c2_qwen3_8b_v1r c2_qwen25_7b_lora_v1 c2_qwen25_7b_lora_v2 c2_qwen25_7b_v2_T07_s1 c2_qwen25_7b_v2_T07_s2; do
  mkdir -p "$RBASE/$exp"
  scp "gpuuser12@192.168.192.9:$REMOTE/$exp/runs.jsonl" "$RBASE/$exp/"
  scp "gpuuser12@192.168.192.9:$REMOTE/$exp/DONE" "$RBASE/$exp/"
  scp "gpuuser12@192.168.192.9:$REMOTE/$exp/manifest.jsonl" "$RBASE/$exp/"
done

# Re-run analysis
cd research/AGENTRUN_DEEPENING_2026-11-11/scripts
py -3.11 analyze_c2.py
```

## Fallback if HPC is never restored

The 14 completed jobs provide sufficient evidence for:
- Memory component ablation (main finding)
- Model-size effects (1.5B–14B)
- Harness variant comparison
- BM25 vs hash retrieval at scale
- Legacy benchmark validation

What would remain unknown:
- Dense retrieval performance
- Whether v1r (repair only) accounts for most of v2's improvement
- QLoRA adapter effect on fresh tasks
- Run-to-run variance estimates
