#!/bin/bash
#SBATCH --job-name=agentrun-p3-eval3
#SBATCH --partition=gpu-nodes
#SBATCH --nodes=1
#SBATCH --ntasks=1
#SBATCH --cpus-per-task=4
#SBATCH --gres=gpu:1
#SBATCH --mem=48G
#SBATCH --time=12:00:00
#SBATCH --array=0-17%1
#SBATCH --output=logs/phase3_%A_%a.out
#SBATCH --error=logs/phase3_%A_%a.err
# PHASE 3 CONFIRMATORY RUNS ON THE SEALED eval3 (PREREGISTRATION.md). NOT TO BE SUBMITTED IN PHASE 2.
# One array task = one (model, decoding) cell; %1 keeps AGENTRUN at ONE GPU. Every task is resumable:
# run_p2.py skips finished (task, config) pairs, so a pre-empted or timed-out cell is resubmitted as is:
#   sbatch --array=<idx> hpc/phase3_eval3.sbatch
# The runner refuses the task file unless its sha256 equals FREEZE_eval3.json's eval3_tasks.jsonl hash,
# and the job refuses to start unless the mechanism matches FREEZE_evarb.json.
# Order: cheapest first, so a stopped campaign still has complete primary cells (PHASE3_EXECUTION_PLAN.md §3).
# Submit from PHASE2/ after recording the pre-registration commit:  sbatch hpc/phase3_eval3.sbatch
set -uo pipefail
W=$HOME/AGENTRUN_HPC/20261111
source $W/environment/venv/bin/activate
export HF_HUB_OFFLINE=1 TRANSFORMERS_OFFLINE=1 TOKENIZERS_PARALLELISM=false PYTHONUNBUFFERED=1
P2=$W/source/research/AGENTRUN_PUBLICATION_2026/PHASE2
SEALED=$HOME/AGENTRUN_HPC/sealed/eval3
OUT=$HOME/AGENTRUN_HPC/phase3_raw
mkdir -p $OUT
# primary cells (Qwen2.5-3B, Qwen2.5-7B, Llama-3.1-8B, Qwen3-8B) x (greedy + 3 seeds), then secondary cells (greedy only)
CELLS=(
 "Qwen/Qwen2.5-3B-Instruct qwen25_3b 0.0 20261111"  "Qwen/Qwen2.5-3B-Instruct qwen25_3b 0.7 1"
 "Qwen/Qwen2.5-3B-Instruct qwen25_3b 0.7 2"         "Qwen/Qwen2.5-3B-Instruct qwen25_3b 0.7 3"
 "Qwen/Qwen2.5-7B-Instruct qwen25_7b 0.0 20261111"  "Qwen/Qwen2.5-7B-Instruct qwen25_7b 0.7 1"
 "Qwen/Qwen2.5-7B-Instruct qwen25_7b 0.7 2"         "Qwen/Qwen2.5-7B-Instruct qwen25_7b 0.7 3"
 "meta-llama/Llama-3.1-8B-Instruct llama31_8b 0.0 20261111" "meta-llama/Llama-3.1-8B-Instruct llama31_8b 0.7 1"
 "meta-llama/Llama-3.1-8B-Instruct llama31_8b 0.7 2"        "meta-llama/Llama-3.1-8B-Instruct llama31_8b 0.7 3"
 "Qwen/Qwen3-8B qwen3_8b 0.0 20261111"              "Qwen/Qwen3-8B qwen3_8b 0.7 1"
 "Qwen/Qwen3-8B qwen3_8b 0.7 2"                     "Qwen/Qwen3-8B qwen3_8b 0.7 3"
 "Qwen/Qwen2.5-14B-Instruct qwen25_14b 0.0 20261111"
 "meta-llama/Llama-3.2-3B-Instruct llama32_3b 0.0 20261111"
)
read -r M T TEMP SEED <<< "${CELLS[$SLURM_ARRAY_TASK_ID]}"
DEC=$([ "$TEMP" = "0.0" ] && echo greedy || echo T07_s$SEED)
python - "$P2" <<'EOF' || { echo "FREEZE CHECK FAILED"; exit 2; }
import hashlib, json, sys, pathlib
p2 = pathlib.Path(sys.argv[1]); f = json.loads((p2 / "FREEZE_evarb.json").read_text())
bad = [k for k, v in f["files"].items() if hashlib.sha256((p2 / k).read_bytes().replace(b"\r\n", b"\n")).hexdigest() != v]
print("freeze", f["version"], "mismatches", bad); sys.exit(1 if bad else 0)
EOF
( cd $SEALED && sha256sum -c --quiet SHA256SUMS ) || { echo "SEAL CHECK FAILED"; exit 3; }
python - "$P2" <<'EOF' || { echo "PREREGISTRATION CHECK FAILED"; exit 4; }
import hashlib, json, sys, pathlib
p2 = pathlib.Path(sys.argv[1]); f = json.loads((p2 / "FREEZE_eval3.json").read_text())
h = hashlib.sha256((p2 / "PREREGISTRATION.md").read_bytes().replace(b"\r\n", b"\n")).hexdigest()
print("prereg", h[:16], "frozen", (f.get("preregistration_sha256") or "")[:16], "status", f.get("status"))
sys.exit(0 if h == f.get("preregistration_sha256") and f.get("status") == "SEALED" else 1)
EOF
SHA=$(python -c "import json;print(json.load(open('$P2/FREEZE_eval3.json'))['sealed_files']['eval3_tasks.jsonl'])")
C=B,G,R,T,RT,EB,EBG,LA,LG,EBG-all,EBG-unsafe,EBG-noR3
echo "start $(date -Is) job=${SLURM_ARRAY_JOB_ID}_${SLURM_ARRAY_TASK_ID} model=$M decoding=$DEC CUDA_VISIBLE_DEVICES=${CUDA_VISIBLE_DEVICES:-}"
cd $P2/scripts
python run_p2.py --model $M --split eval3 --tasks $SEALED/eval3_tasks.jsonl --expect-sha $SHA --configs $C \
  --temperature $TEMP --seed $SEED --run-id eval3_${T}_${DEC} --out $OUT
echo "exit=$? $(date -Is) $M $DEC"
