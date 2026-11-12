#!/bin/bash
#SBATCH --job-name=agentrun-abl
#SBATCH --partition=gpu-nodes
#SBATCH --nodes=1
#SBATCH --ntasks=1
#SBATCH --cpus-per-task=8
#SBATCH --gres=gpu:1
#SBATCH --mem=48G
#SBATCH --time=16:00:00
#SBATCH --array=0-5%2
#SBATCH --output=experiments/logs/abl-%A_%a.out
#SBATCH --error=experiments/logs/abl-%A_%a.err
# Frozen 48-task x 5-configuration memlab ablation on locally served models.
# Resumable: finished (task, config) pairs in runs.jsonl are skipped, so resubmitting is safe.
set -uo pipefail
W=$HOME/AGENTRUN_HPC/20261111
ADAPTER=$W/source/adapters/repo_root_adapter
case $SLURM_ARRAY_TASK_ID in
  0) MODEL=Qwen/Qwen2.5-7B-Instruct; RID=hpc_qwen25_7b_greedy_t1;       EXTRA="" ;;
  1) MODEL=Qwen/Qwen3-8B;            RID=hpc_qwen3_8b_greedy_t1;        EXTRA="" ;;
  2) MODEL=Qwen/Qwen2.5-7B-Instruct; RID=hpc_qwen25_7b_lora_greedy_t1;  EXTRA="--adapter $ADAPTER" ;;
  3) MODEL=Qwen/Qwen2.5-7B-Instruct; RID=hpc_qwen25_7b_temp07_seed1;    EXTRA="--temperature 0.7 --seed 1" ;;
  4) MODEL=Qwen/Qwen2.5-7B-Instruct; RID=hpc_qwen25_7b_temp07_seed2;    EXTRA="--temperature 0.7 --seed 2" ;;
  5) MODEL=Qwen/Qwen3-8B;            RID=hpc_qwen3_8b_temp07_seed1;     EXTRA="--temperature 0.7 --seed 1" ;;
esac
echo "Start: $(date -Is) job=${SLURM_ARRAY_JOB_ID}_${SLURM_ARRAY_TASK_ID} host=$(hostname) CUDA_VISIBLE_DEVICES=${CUDA_VISIBLE_DEVICES:-} model=$MODEL run=$RID extra=$EXTRA"
free -h | head -n 2
source $W/environment/venv/bin/activate
export HF_HUB_OFFLINE=1 TRANSFORMERS_OFFLINE=1 TOKENIZERS_PARALLELISM=false PYTHONUNBUFFERED=1
cd $W/source/research/AGENTRUN_DEEPENING_2026-11-11/scripts
python run_ablation.py --backend hf --model $MODEL --split eval --run-id $RID $EXTRA
rc=$?
echo "End: $(date -Is) exit=$rc"
echo -e "${SLURM_ARRAY_JOB_ID}_${SLURM_ARRAY_TASK_ID}\t$RID\t$(date -Is)\texit=$rc" >> $W/manifests/jobs_finished.tsv
exit $rc
