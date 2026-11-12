# Campaign 2 — Reproducibility

## Prerequisites

- SSH access to SIT HPC (`gpuuser12@192.168.192.11` or `gpuuser12@192.168.192.9`)
- Working Slurm controller on the login node
- Two NVIDIA L40 GPUs (functional `nvidia-smi`)
- Pre-downloaded models in the HuggingFace cache

## Repository state

| Ref | Hash | Description |
|---|---|---|
| Branch | `research/memory-ablation-2026-11` | Working branch (unpushed) |
| Base commit | `998e42e` | Initial HPC ablation study |
| Campaign 2 commit | `ca664fa` | Campaign 2 design, frozen eval2, harness variants |
| Analysis commit | TBD | This report and updated analysis |

## Reproducing the full campaign

### Step 1: Verify environment

```bash
ssh gpuuser12@192.168.192.11
cd /home/gpuuser12/AGENTRUN_HPC/20261111
source environment/venv/bin/activate
python -c "import torch; print(torch.cuda.is_available(), torch.cuda.device_count())"
squeue -u gpuuser12
```

### Step 2: Submit all 21 jobs

```bash
cd /home/gpuuser12/AGENTRUN_HPC/20261111
sbatch scripts/campaign2.sbatch
```

This submits a 21-job Slurm array with max 2 concurrent. Jobs are resumable: resubmitting after partial completion skips jobs with existing DONE markers.

### Step 3: Monitor

```bash
watch -n 30 'squeue -u gpuuser12; wc -l manifests/jobs_finished.tsv'
```

Expected wall time: ~8 hours with 2 concurrent jobs.

### Step 4: Collect results

```bash
# On local machine
RBASE=research/AGENTRUN_DEEPENING_2026-11-11/raw_results
REMOTE=/home/gpuuser12/AGENTRUN_HPC/20261111/experiments/raw_results
for d in $(ssh gpuuser12@192.168.192.9 "ls $REMOTE"); do
  mkdir -p "$RBASE/$d"
  scp "gpuuser12@192.168.192.9:$REMOTE/$d/runs.jsonl" "$RBASE/$d/" 2>/dev/null
  scp "gpuuser12@192.168.192.9:$REMOTE/$d/DONE" "$RBASE/$d/" 2>/dev/null
  scp "gpuuser12@192.168.192.9:$REMOTE/$d/manifest.jsonl" "$RBASE/$d/" 2>/dev/null
  scp "gpuuser12@192.168.192.9:$REMOTE/$d/scores.json" "$RBASE/$d/" 2>/dev/null
done
```

### Step 5: Re-run analysis

```bash
cd research/AGENTRUN_DEEPENING_2026-11-11/scripts
py -3.11 analyze_c2.py
```

This regenerates `tables/c2/C2_TABLES.md` and `tables/c2/c2_summary.json`.

### Step 6: Re-run leakage audit

```bash
cd research/AGENTRUN_DEEPENING_2026-11-11/scripts
py -3.11 leakage_audit.py
```

## Reproducing only the 7 missing jobs

```bash
ssh gpuuser12@192.168.192.11
cd /home/gpuuser12/AGENTRUN_HPC/20261111

# Verify Slurm is operational
squeue -u gpuuser12

# Submit only missing indices
sbatch --array=14-20%2 scripts/campaign2.sbatch

# Expected experiments:
# 14: dense retrieval + 2000 padding (~15 min)
# 15: Qwen2.5-7B v1r harness (~33 min)
# 16: Qwen3-8B v1r harness (~38 min)
# 17: Qwen2.5-7B + adapter v1 (~33 min)
# 18: Qwen2.5-7B + adapter v2 (~33 min)
# 19: Qwen2.5-7B T=0.7 seed 1 (~33 min)
# 20: Qwen2.5-7B T=0.7 seed 2 (~33 min)

# Estimated total wall time with 2 concurrent: ~2 hours
```

## Key file locations on HPC

| Path | Contents |
|---|---|
| `/home/gpuuser12/AGENTRUN_HPC/20261111/scripts/campaign2.sbatch` | Job array definition |
| `/home/gpuuser12/AGENTRUN_HPC/20261111/source/` | All source code |
| `/home/gpuuser12/AGENTRUN_HPC/20261111/experiments/raw_results/` | Run outputs |
| `/home/gpuuser12/AGENTRUN_HPC/20261111/experiments/logs/` | Slurm stdout/stderr |
| `/home/gpuuser12/AGENTRUN_HPC/20261111/manifests/jobs_finished.tsv` | Completion log |
| `/home/gpuuser12/AGENTRUN_HPC/backups/c2_backup_20261112_120842/` | Timestamped backup |

## Key file locations locally

| Path | Contents |
|---|---|
| `research/AGENTRUN_DEEPENING_2026-11-11/benchmark/FREEZE_eval2.json` | Frozen benchmark |
| `research/AGENTRUN_DEEPENING_2026-11-11/raw_results/c2_*/` | Downloaded run results |
| `research/AGENTRUN_DEEPENING_2026-11-11/tables/c2/C2_TABLES.md` | Generated analysis tables |
| `research/AGENTRUN_DEEPENING_2026-11-11/tables/leakage_audit_eval2.json` | Audit results |
| `research/AGENTRUN_DEEPENING_2026-11-11/scripts/analyze_c2.py` | Analysis script |
| `research/AGENTRUN_DEEPENING_2026-11-11/scripts/memlab.py` | Scoring module |

## Software versions

- Python 3.11
- PyTorch (CUDA-enabled, L40-compatible)
- HuggingFace Transformers (offline mode)
- NumPy (for bootstrap)
- Matplotlib (for figures)
