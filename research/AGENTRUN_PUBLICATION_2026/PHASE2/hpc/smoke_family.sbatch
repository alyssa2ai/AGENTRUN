#!/bin/bash
#SBATCH --job-name=agentrun-p2-smoke
#SBATCH --partition=gpu-nodes
#SBATCH --nodes=1
#SBATCH --ntasks=1
#SBATCH --cpus-per-task=4
#SBATCH --gres=gpu:1
#SBATCH --mem=48G
#SBATCH --time=00:45:00
#SBATCH --output=logs/smoke_family_%j.out
#SBATCH --error=logs/smoke_family_%j.err
# Phase 2 second-family readiness: load + 10 dev tasks x {B,G} per model. ONE GPU, sequential.
# Submit from PHASE2/:  sbatch hpc/smoke_family.sbatch
set -uo pipefail
W=$HOME/AGENTRUN_HPC/20261111
source $W/environment/venv/bin/activate
export HF_HUB_OFFLINE=1 TRANSFORMERS_OFFLINE=1 TOKENIZERS_PARALLELISM=false PYTHONUNBUFFERED=1
cd $W/source/research/AGENTRUN_PUBLICATION_2026/PHASE2/scripts
echo "start $(date -Is) job=$SLURM_JOB_ID host=$(hostname) CUDA_VISIBLE_DEVICES=${CUDA_VISIBLE_DEVICES:-}"
for M in meta-llama/Llama-3.2-3B-Instruct meta-llama/Llama-3.1-8B-Instruct Qwen/Qwen2.5-3B-Instruct; do
  echo "start $(date -Is) $M"; python model_smoke.py --model $M --n-tasks 10 --out ../raw/smoke; echo "exit=$? $(date -Is) $M"
done
echo "job finished $(date -Is)"
