#!/bin/bash
# Phase 1 pilot launcher for <compute-node> (<compute-node>), run directly on the compute node because the
# Slurm controller is down (13 Nov 2026). One queue per GPU; each queue runs its models sequentially.
# Usage (on the node):  bash launch_pilot.sh 0   # GPU 0 queue
#                       bash launch_pilot.sh 1   # GPU 1 queue
set -uo pipefail
W=$HOME/AGENTRUN_HPC/20261111
source $W/environment/venv/bin/activate
export HF_HUB_OFFLINE=1 TRANSFORMERS_OFFLINE=1 TOKENIZERS_PARALLELISM=false PYTHONUNBUFFERED=1
export CUDA_VISIBLE_DEVICES=$1
cd $W/source/research/AGENTRUN_PUBLICATION_2026/PHASE1/prototype
mkdir -p ../logs
run() { echo "start $(date -Is) $*"; python run_pilot.py "$@"; echo "exit=$? $(date -Is) $*"; }
if [ "$1" = "0" ]; then
  M=Qwen/Qwen2.5-3B-Instruct
  run --model $M --run-id p1_qwen25_3b_greedy
  run --model $M --temperature 0.7 --seed 1 --run-id p1_qwen25_3b_T07_s1
  run --model $M --temperature 0.7 --seed 2 --run-id p1_qwen25_3b_T07_s2
  run --model Qwen/Qwen2.5-14B-Instruct --run-id p1_qwen25_14b_greedy
else
  M=Qwen/Qwen2.5-7B-Instruct
  run --model $M --run-id p1_qwen25_7b_greedy
  run --model $M --temperature 0.7 --seed 1 --run-id p1_qwen25_7b_T07_s1
  run --model $M --temperature 0.7 --seed 2 --run-id p1_qwen25_7b_T07_s2
  run --model Qwen/Qwen3-8B --run-id p1_qwen3_8b_greedy
fi
echo "queue $1 finished $(date -Is)"
