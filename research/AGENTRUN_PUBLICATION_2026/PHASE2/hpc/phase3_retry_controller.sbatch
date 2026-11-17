#!/bin/bash
#SBATCH --job-name=agentrun-p3-retry
#SBATCH --partition=gpu-nodes
#SBATCH --ntasks=1
#SBATCH --cpus-per-task=1
#SBATCH --mem=1G
#SBATCH --time=7-00:00:00
#SBATCH --output=logs/phase3_retry_%j.out
# No GPU. Starts after the main Phase 3 array ends (--dependency=afterany:<array>), then up to 5 rounds:
# resubmit only INCOMPLETE cells (hpc/phase3_resume.sh --submit; resumable runner skips finished pairs),
# wait for that array to end. Needed because the 14B cell (~25 h) exceeds the 12 h task limit.
# Never touches finished cells; one GPU at a time (%1). Preregistration section 7: cells are resubmitted, not changed.
set -uo pipefail
cd "${SLURM_SUBMIT_DIR}"
for round in 1 2 3 4 5; do
  echo "round $round $(date -Is)"
  out=$(bash hpc/phase3_resume.sh --submit 2>&1); echo "$out"
  echo "$out" | grep -q "Submitted batch job" || { echo "nothing to submit; done"; break; }
  jid=$(echo "$out" | sed -n 's/.*Submitted batch job \([0-9]*\).*/\1/p' | tail -1)
  while squeue -h -j "$jid" 2>/dev/null | grep -q .; do sleep 120; done
done
echo "final state $(date -Is)"; bash hpc/phase3_resume.sh
