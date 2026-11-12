#!/bin/bash
#SBATCH --job-name=agentrun-pilot
#SBATCH --partition=gpu-nodes
#SBATCH --nodes=1
#SBATCH --ntasks=1
#SBATCH --cpus-per-task=8
#SBATCH --gres=gpu:1
#SBATCH --mem=48G
#SBATCH --time=00:45:00
#SBATCH --output=experiments/logs/pilot-%j.out
#SBATCH --error=experiments/logs/pilot-%j.err
set -uo pipefail
W=$HOME/AGENTRUN_HPC/20261111
echo "Start: $(date -Is) job=$SLURM_JOB_ID host=$(hostname) CUDA_VISIBLE_DEVICES=${CUDA_VISIBLE_DEVICES:-}"
free -h | head -n 2
source $W/environment/venv/bin/activate
export HF_HUB_OFFLINE=1 TRANSFORMERS_OFFLINE=1 TOKENIZERS_PARALLELISM=false PYTHONUNBUFFERED=1
cd $W/source/research/AGENTRUN_DEEPENING_2026-11-11/scripts
python -c "import torch,transformers; print(torch.__version__, transformers.__version__, torch.cuda.is_available(), torch.cuda.get_device_name(0))"
python run_ablation.py --backend hf --model Qwen/Qwen2.5-7B-Instruct --split dev --run-id hpc_pilot_dev_qwen25_7b_greedy
rc=$?
echo "End: $(date -Is) exit=$rc"
echo -e "$SLURM_JOB_ID\tpilot_dev_qwen25_7b\t$(date -Is)\texit=$rc" >> $W/manifests/jobs_finished.tsv
exit $rc
