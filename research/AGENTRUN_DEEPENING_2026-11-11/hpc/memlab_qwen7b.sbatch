#!/bin/bash
# PREPARED, NOT EXECUTED. Verify partition, gres syntax, modules and paths on the cluster first.
#SBATCH --job-name=memlab-qwen7b
#SBATCH --partition=gpu-nodes
#SBATCH --nodelist=sit-gpu
#SBATCH --gres=gpu:1
#SBATCH --cpus-per-task=8
#SBATCH --mem=48G
#SBATCH --time=03:00:00
#SBATCH --output=logs/slurm-%j.out
#SBATCH --error=logs/slurm-%j.err

set -euo pipefail
AGENTRUN_DIR=${AGENTRUN_DIR:?set AGENTRUN_DIR to the repository path on the cluster}
MODEL=${MODEL:-Qwen/Qwen2.5-7B-Instruct}
cd "$AGENTRUN_DIR/research/AGENTRUN_DEEPENING_2026-11-11"

echo "job $SLURM_JOB_ID on $(hostname) started $(date -u +%FT%TZ)"
nvidia-smi --query-gpu=name,memory.total,memory.used --format=csv
python -c "import torch; print(torch.__version__, torch.cuda.is_available(), torch.cuda.get_device_name(0))"

# OpenAI-compatible server on the node (requires vllm in the active environment).
python -m vllm.entrypoints.openai.api_server --model "$MODEL" --port 8000 \
    --enable-auto-tool-choice --tool-call-parser hermes --seed 20261111 > logs/vllm-$SLURM_JOB_ID.log 2>&1 &
SERVER=$!
trap 'kill $SERVER' EXIT
until curl -sf http://127.0.0.1:8000/v1/models > /dev/null; do sleep 5; done

cd scripts
GROQ_API_KEY=unused python run_ablation.py --model "$MODEL" --split eval \
    --run-id "eval_qwen25_7b_base_slurm$SLURM_JOB_ID" --base-url http://127.0.0.1:8000/v1
echo "finished $(date -u +%FT%TZ)"
