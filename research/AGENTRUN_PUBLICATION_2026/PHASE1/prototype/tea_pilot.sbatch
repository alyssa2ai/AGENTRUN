#!/bin/bash
#SBATCH --job-name=agentrun-p1-tea
#SBATCH --partition=gpu-nodes
#SBATCH --nodes=1
#SBATCH --ntasks=1
#SBATCH --cpus-per-task=8
#SBATCH --gres=gpu:1
#SBATCH --mem=48G
#SBATCH --time=03:00:00
#SBATCH --output=logs/tea_pilot_%j.out
#SBATCH --error=logs/tea_pilot_%j.err
# Phase 1 TEA follow-up pilot. ONE GPU, models run one after another (shared node with Veriflow:
# see HPC_RESOURCE_SHARING.md). Resumable: finished (task, config) pairs are skipped on resubmission.
# Submit from PHASE1/:  sbatch prototype/tea_pilot.sbatch
set -uo pipefail
W=$HOME/AGENTRUN_HPC/20261111
source $W/environment/venv/bin/activate
export HF_HUB_OFFLINE=1 TRANSFORMERS_OFFLINE=1 TOKENIZERS_PARALLELISM=false PYTHONUNBUFFERED=1
cd $W/source/research/AGENTRUN_PUBLICATION_2026/PHASE1/prototype
echo "start $(date -Is) job=$SLURM_JOB_ID host=$(hostname) CUDA_VISIBLE_DEVICES=${CUDA_VISIBLE_DEVICES:-}"
run() { echo "start $(date -Is) $*"; python run_tea.py "$@"; echo "exit=$? $(date -Is) $*"; }
for spec in "Qwen/Qwen2.5-3B-Instruct qwen25_3b" "Qwen/Qwen2.5-7B-Instruct qwen25_7b" "Qwen/Qwen3-8B qwen3_8b"; do
  set -- $spec
  run --model $1 --split p1dev  --configs T,RT       --run-id p1_${2}_greedy_tea
  run --model $1 --split p1hold --configs B,G,R,T,RT --run-id p1h_${2}_greedy
done
echo "job finished $(date -Is)"
