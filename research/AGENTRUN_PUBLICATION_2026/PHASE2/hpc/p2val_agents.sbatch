#!/bin/bash
#SBATCH --job-name=agentrun-p2-agents
#SBATCH --partition=gpu-nodes
#SBATCH --nodes=1
#SBATCH --ntasks=1
#SBATCH --cpus-per-task=4
#SBATCH --gres=gpu:1
#SBATCH --mem=48G
#SBATCH --time=05:00:00
#SBATCH --array=0-2%1
#SBATCH --output=logs/p2val_agents_%A_%a.out
#SBATCH --error=logs/p2val_agents_%A_%a.err
# Phase 2 agent-level VALIDATION with the FROZEN mechanism evarb-0.2 (FREEZE_evarb.json).
# Per model: p2val (development after the evarb-0.2 look) and p2val2 (untouched validation).
# Array tasks run one at a time (%1): AGENTRUN never holds more than one GPU. Resumable.
# Submit from PHASE2/ (after p2val2 exists):  sbatch hpc/p2val_agents.sbatch
set -uo pipefail
W=$HOME/AGENTRUN_HPC/20261111
source $W/environment/venv/bin/activate
export HF_HUB_OFFLINE=1 TRANSFORMERS_OFFLINE=1 TOKENIZERS_PARALLELISM=false PYTHONUNBUFFERED=1
cd $W/source/research/AGENTRUN_PUBLICATION_2026/PHASE2/scripts
case $SLURM_ARRAY_TASK_ID in
  0) M=Qwen/Qwen2.5-3B-Instruct; T=qwen25_3b ;;
  1) M=Qwen/Qwen2.5-7B-Instruct; T=qwen25_7b ;;
  2) M=meta-llama/Llama-3.1-8B-Instruct; T=llama31_8b ;;
esac
C=B,G,R,T,RT,EB,EBG,LA,LG,EBG-all,EBG-unsafe,EBG-noR3
for S in p2val2 p2val; do
  echo "start $(date -Is) job=${SLURM_ARRAY_JOB_ID}_${SLURM_ARRAY_TASK_ID} model=$M split=$S CUDA_VISIBLE_DEVICES=${CUDA_VISIBLE_DEVICES:-}"
  python run_p2.py --model $M --split $S --configs $C --run-id ${S}_${T}_greedy
  echo "exit=$? $(date -Is) $M $S"
done
