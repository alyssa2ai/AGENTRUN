#!/bin/bash
#SBATCH --job-name=agentrun-c2
#SBATCH --partition=gpu-nodes
#SBATCH --nodes=1
#SBATCH --ntasks=1
#SBATCH --cpus-per-task=8
#SBATCH --gres=gpu:1
#SBATCH --mem=64G
#SBATCH --time=12:00:00
#SBATCH --array=0-20%2
#SBATCH --output=experiments/logs/c2-%A_%a.out
#SBATCH --error=experiments/logs/c2-%A_%a.err
# Campaign 2 (2026-11-12): fresh 96-task split "eval2", frozen in benchmark/FREEZE_eval2.json.
# Array indices are in priority order. Every run is resumable; resubmitting skips finished work.
set -uo pipefail
W=$HOME/AGENTRUN_HPC/20261111
ADAPTER=$W/source/adapters/repo_root_adapter
Q25=Qwen/Qwen2.5-7B-Instruct
Q3=Qwen/Qwen3-8B
MEMSC="--scenarios S1,S2,S3,S4 --configs B,D,E"
source $W/environment/venv/bin/activate
export HF_HUB_OFFLINE=1 TRANSFORMERS_OFFLINE=1 TOKENIZERS_PARALLELISM=false PYTHONUNBUFFERED=1
cd $W/source/research/AGENTRUN_DEEPENING_2026-11-11/scripts
abl() { python run_ablation.py --backend hf --split eval2 "$@"; }
v2r() { python run_v2_hpc.py "$@"; }
echo "Start: $(date -Is) job=${SLURM_ARRAY_JOB_ID}_${SLURM_ARRAY_TASK_ID} host=$(hostname) CUDA_VISIBLE_DEVICES=${CUDA_VISIBLE_DEVICES:-}"
rc=0
case $SLURM_ARRAY_TASK_ID in
  # --- main comparison: frozen v1 harness (control) vs v2 harness, two base models
  0) abl --model $Q25 --harness v1 --run-id c2_qwen25_7b_v1 ;;
  1) abl --model $Q3  --harness v1 --run-id c2_qwen3_8b_v1 ;;
  2) abl --model $Q25 --harness v2 --run-id c2_qwen25_7b_v2 ;;
  3) abl --model $Q3  --harness v2 --run-id c2_qwen3_8b_v2 ;;
  # --- AGENTRUN's own benchmarks, client-matched, frozen environment: base, then adapter
  4) v2r --model $Q25 --tasks legacy --max-steps 3 --run-id c2_legacy23_base_b3 \
     && v2r --model $Q25 --tasks legacy --max-steps 6 --run-id c2_legacy23_base_b6 \
     && v2r --model $Q25 --tasks dev --max-steps 3 --run-id c2_v2dev55_base_b3 \
     && v2r --model $Q25 --tasks dev --max-steps 6 --run-id c2_v2dev55_base_b6 \
     && for s in 1 2 3; do v2r --model $Q25 --tasks legacy --max-steps 3 --temperature 0.7 --seed $s --run-id c2_legacy23_base_b3_T07_s$s || exit 1; done ;;
  5) v2r --model $Q25 --adapter $ADAPTER --tasks legacy --max-steps 3 --run-id c2_legacy23_adapter_b3 \
     && v2r --model $Q25 --adapter $ADAPTER --tasks legacy --max-steps 6 --run-id c2_legacy23_adapter_b6 \
     && v2r --model $Q25 --adapter $ADAPTER --tasks dev --max-steps 3 --run-id c2_v2dev55_adapter_b3 \
     && v2r --model $Q25 --adapter $ADAPTER --tasks dev --max-steps 6 --run-id c2_v2dev55_adapter_b6 \
     && for s in 1 2 3; do v2r --model $Q25 --adapter $ADAPTER --tasks legacy --max-steps 3 --temperature 0.7 --seed $s --run-id c2_legacy23_adapter_b3_T07_s$s || exit 1; done ;;
  # --- model-size sweep within Qwen2.5 (7B is index 0 and 2)
  6) abl --model Qwen/Qwen2.5-14B-Instruct  --harness v1 --run-id c2_qwen25_14b_v1 ;;
  7) abl --model Qwen/Qwen2.5-3B-Instruct   --harness v1 --run-id c2_qwen25_3b_v1 ;;
  8) abl --model Qwen/Qwen2.5-1.5B-Instruct --harness v1 --run-id c2_qwen25_1p5b_v1 ;;
  9) abl --model Qwen/Qwen2.5-14B-Instruct  --harness v2 --run-id c2_qwen25_14b_v2 ;;
  10) abl --model Qwen/Qwen2.5-3B-Instruct   --harness v2 --run-id c2_qwen25_3b_v2 ;;
  11) abl --model Qwen/Qwen2.5-1.5B-Instruct --harness v2 --run-id c2_qwen25_1p5b_v2 ;;
  # --- retriever x store size, end to end: 2,000 background records per store, memory scenarios only
  12) abl --model $Q25 --harness v2 --retriever hash  --pad 2000 $MEMSC --run-id c2_qwen25_7b_v2_hash_pad2000 ;;
  13) abl --model $Q25 --harness v2 --retriever bm25  --pad 2000 $MEMSC --run-id c2_qwen25_7b_v2_bm25_pad2000 ;;
  14) abl --model $Q25 --harness v2 --retriever dense --pad 2000 $MEMSC --run-id c2_qwen25_7b_v2_dense_pad2000 ;;
  # --- which part of v2 matters: repair turn only
  15) abl --model $Q25 --harness v1r --run-id c2_qwen25_7b_v1r ;;
  16) abl --model $Q3  --harness v1r --run-id c2_qwen3_8b_v1r ;;
  # --- the repository adapter, and run-to-run spread
  17) abl --model $Q25 --adapter $ADAPTER --harness v1 --run-id c2_qwen25_7b_lora_v1 ;;
  18) abl --model $Q25 --adapter $ADAPTER --harness v2 --run-id c2_qwen25_7b_lora_v2 ;;
  19) abl --model $Q25 --harness v2 --temperature 0.7 --seed 1 --run-id c2_qwen25_7b_v2_T07_s1 ;;
  20) abl --model $Q25 --harness v2 --temperature 0.7 --seed 2 --run-id c2_qwen25_7b_v2_T07_s2 ;;
esac
rc=$?
echo "End: $(date -Is) exit=$rc"
echo -e "${SLURM_ARRAY_JOB_ID}_${SLURM_ARRAY_TASK_ID}\tcampaign2\t$(date -Is)\texit=$rc" >> $W/manifests/jobs_finished.tsv
exit $rc
