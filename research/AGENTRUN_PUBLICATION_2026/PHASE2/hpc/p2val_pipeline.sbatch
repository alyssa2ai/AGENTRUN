#!/bin/bash
#SBATCH --job-name=agentrun-p2-val
#SBATCH --partition=gpu-nodes
#SBATCH --nodes=1
#SBATCH --ntasks=1
#SBATCH --cpus-per-task=4
#SBATCH --gres=gpu:1
#SBATCH --mem=64G
#SBATCH --time=02:30:00
#SBATCH --output=logs/p2val_pipeline_%j.out
#SBATCH --error=logs/p2val_pipeline_%j.err
# Phase 2: (1) independent writer for p2val, (2) assemble, (3) two blind annotators,
# (4) LLM evidence arbiter on all development component groups. ONE GPU, sequential, resumable.
# Submit from PHASE2/:  sbatch hpc/p2val_pipeline.sbatch
set -uo pipefail
W=$HOME/AGENTRUN_HPC/20261111
source $W/environment/venv/bin/activate
export HF_HUB_OFFLINE=1 TRANSFORMERS_OFFLINE=1 TOKENIZERS_PARALLELISM=false PYTHONUNBUFFERED=1
P2=$W/source/research/AGENTRUN_PUBLICATION_2026/PHASE2
D=$P2/data/p2val
cd $P2/benchmark
step() { echo "start $(date -Is) $*"; "$@"; echo "exit=$? $(date -Is) $1 $2"; }
step python write_and_annotate.py write --split p2val --dir $D --model Qwen/Qwen2.5-14B-Instruct
step python assemble.py --split p2val --dir $D
step python write_and_annotate.py annotate --split p2val --dir $D --model meta-llama/Llama-3.1-8B-Instruct --tag llama8b
step python write_and_annotate.py annotate --split p2val --dir $D --model Qwen/Qwen2.5-14B-Instruct --tag qwen14b
cd $P2/scripts
for M in Qwen/Qwen2.5-3B-Instruct Qwen/Qwen2.5-7B-Instruct meta-llama/Llama-3.1-8B-Instruct Qwen/Qwen2.5-14B-Instruct; do
  step python llm_arbiter_eval.py --model $M --groups ../data/dev_groups.jsonl ../data/regression_groups.jsonl $D/p2val_groups.jsonl --out ../raw/llm_arbiter
done
echo "job finished $(date -Is)"
