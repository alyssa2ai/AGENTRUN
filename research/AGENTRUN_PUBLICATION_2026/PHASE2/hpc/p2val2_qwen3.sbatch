#!/bin/bash
#SBATCH --job-name=agentrun-p2-qwen3
#SBATCH --partition=gpu-nodes
#SBATCH --nodes=1
#SBATCH --ntasks=1
#SBATCH --cpus-per-task=4
#SBATCH --gres=gpu:1
#SBATCH --mem=48G
#SBATCH --time=04:00:00
#SBATCH --array=0
#SBATCH --output=logs/p2val2_qwen3_%A_%a.out
#SBATCH --error=logs/p2val2_qwen3_%A_%a.err
# Phase 2 agent-level VALIDATION with the FROZEN mechanism evarb-0.2 (FREEZE_evarb.json).
# Qwen3-8B readiness + timing on p2val2 only (added 16 Nov for Phase 3; thinking disabled by the frozen client).
# Array tasks run one at a time (%1): AGENTRUN never holds more than one GPU. Resumable.
# Submit from PHASE2/ after the agents array:  sbatch --dependency=afterany:<agents job> hpc/p2val2_qwen3.sbatch
set -uo pipefail
W=$HOME/AGENTRUN_HPC/20261111
source $W/environment/venv/bin/activate
export HF_HUB_OFFLINE=1 TRANSFORMERS_OFFLINE=1 TOKENIZERS_PARALLELISM=false PYTHONUNBUFFERED=1
cd $W/source/research/AGENTRUN_PUBLICATION_2026/PHASE2/scripts
case $SLURM_ARRAY_TASK_ID in
  0) M=Qwen/Qwen3-8B; T=qwen3_8b ;;
esac
C=B,G,R,T,RT,EB,EBG,LA,LG,EBG-all,EBG-unsafe,EBG-noR3
for S in p2val2; do
  echo "start $(date -Is) job=${SLURM_ARRAY_JOB_ID}_${SLURM_ARRAY_TASK_ID} model=$M split=$S CUDA_VISIBLE_DEVICES=${CUDA_VISIBLE_DEVICES:-}"
  python run_p2.py --model $M --split $S --configs $C --run-id ${S}_${T}_greedy
  echo "exit=$? $(date -Is) $M $S"
done
