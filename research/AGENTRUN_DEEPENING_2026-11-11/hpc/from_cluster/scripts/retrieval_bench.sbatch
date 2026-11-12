#!/bin/bash
#SBATCH --job-name=agentrun-retr
#SBATCH --partition=gpu-nodes
#SBATCH --nodes=1
#SBATCH --ntasks=1
#SBATCH --cpus-per-task=16
#SBATCH --gres=gpu:1
#SBATCH --mem=64G
#SBATCH --time=03:00:00
#SBATCH --output=experiments/logs/retr-%j.out
#SBATCH --error=experiments/logs/retr-%j.err
# Retrieval at scale: hash256 (AGENTRUN default) vs BM25 vs dense embeddings. Resumable (skips finished rows).
set -uo pipefail
W=$HOME/AGENTRUN_HPC/20261111
echo "Start: $(date -Is) job=$SLURM_JOB_ID host=$(hostname) CUDA_VISIBLE_DEVICES=${CUDA_VISIBLE_DEVICES:-}"
source $W/environment/venv/bin/activate
export HF_HUB_OFFLINE=1 TRANSFORMERS_OFFLINE=1 TOKENIZERS_PARALLELISM=false PYTHONUNBUFFERED=1 OMP_NUM_THREADS=16
cd $W/source/research/AGENTRUN_DEEPENING_2026-11-11/scripts
python retrieval_bench.py --out ../raw_results/hpc_retrieval_bench --sizes 2000,10000,100000 --seeds 1,2,3
rc=$?
echo "End: $(date -Is) exit=$rc"
echo -e "$SLURM_JOB_ID\tretrieval_bench\t$(date -Is)\texit=$rc" >> $W/manifests/jobs_finished.tsv
exit $rc
