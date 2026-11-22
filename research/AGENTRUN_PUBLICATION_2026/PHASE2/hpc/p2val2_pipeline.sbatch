#!/bin/bash
#SBATCH --job-name=agentrun-p2val2
#SBATCH --partition=gpu-nodes
#SBATCH --nodes=1
#SBATCH --ntasks=1
#SBATCH --cpus-per-task=4
#SBATCH --gres=gpu:1
#SBATCH --mem=64G
#SBATCH --time=02:30:00
#SBATCH --output=logs/p2val2_pipeline_%j.out
#SBATCH --error=logs/p2val2_pipeline_%j.err
# Phase 2 clean validation split p2val2 for the FROZEN evarb-0.2 (FREEZE_evarb.json).
# p2val became development data when evarb-0.2 was tuned after its look, so p2val2 (v2 semantics,
# names [21200:22400], distractors [22400:23600]) is the untouched validation set.
# (1) independent writer (no gold), (2) assemble + mechanical validation, (3) two blind annotators,
# (4) agreement, (5) split-boundary/leakage checks, (6) LLM evidence arbiter on the p2val2 groups.
# ONE GPU, sequential, resumable.  Submit from PHASE2/:  sbatch hpc/p2val2_pipeline.sbatch
set -uo pipefail
W=$HOME/AGENTRUN_HPC/20261111
source $W/environment/venv/bin/activate
export HF_HUB_OFFLINE=1 TRANSFORMERS_OFFLINE=1 TOKENIZERS_PARALLELISM=false PYTHONUNBUFFERED=1
P2=$W/source/research/AGENTRUN_PUBLICATION_2026/PHASE2
D=$P2/data/p2val2
cd $P2/benchmark
step() { echo "start $(date -Is) $*"; "$@"; echo "exit=$? $(date -Is) $1 $2"; }
echo "job=$SLURM_JOB_ID host=$(hostname) CUDA_VISIBLE_DEVICES=${CUDA_VISIBLE_DEVICES:-}"
step python write_and_annotate.py write --split p2val2 --dir $D --model Qwen/Qwen2.5-14B-Instruct
step python assemble.py --split p2val2 --dir $D
step python write_and_annotate.py annotate --split p2val2 --dir $D --model meta-llama/Llama-3.1-8B-Instruct --tag llama8b
step python write_and_annotate.py annotate --split p2val2 --dir $D --model Qwen/Qwen2.5-14B-Instruct --tag qwen14b
step python agreement.py --split p2val2 --dir $D --tags llama8b qwen14b --quiet
step python seal_checks.py --split p2val2 --dir $D
cd $P2/scripts
for M in Qwen/Qwen2.5-3B-Instruct Qwen/Qwen2.5-7B-Instruct meta-llama/Llama-3.1-8B-Instruct Qwen/Qwen2.5-14B-Instruct; do
  step python llm_arbiter_eval.py --model $M --groups $D/p2val2_groups.jsonl --out ../raw/llm_arbiter
done
echo "job finished $(date -Is)"
