#!/bin/bash
# Phase 3 recovery: list cells that are incomplete and NOT queued/running, and (with --submit) resubmit only those.
# Never resubmits a finished cell (DONE present) or one that is already in the queue. Run on the login node from PHASE2/.
#   bash hpc/phase3_resume.sh            # report only
#   bash hpc/phase3_resume.sh --submit   # resubmit the missing cells as one %1 array (one GPU)
set -uo pipefail
OUT=$HOME/AGENTRUN_HPC/phase3_raw
TAGS=(qwen25_3b_greedy qwen25_3b_T07_s1 qwen25_3b_T07_s2 qwen25_3b_T07_s3
      qwen25_7b_greedy qwen25_7b_T07_s1 qwen25_7b_T07_s2 qwen25_7b_T07_s3
      llama31_8b_greedy llama31_8b_T07_s1 llama31_8b_T07_s2 llama31_8b_T07_s3
      qwen3_8b_greedy qwen3_8b_T07_s1 qwen3_8b_T07_s2 qwen3_8b_T07_s3
      qwen25_14b_greedy llama32_3b_greedy)
queued=$(squeue -h -u "$USER" -n agentrun-p3-eval3 -o "%i" | tr '\n' ' ')
todo=()
for i in "${!TAGS[@]}"; do
  d=$OUT/eval3_${TAGS[$i]}
  n=$( [ -f $d/runs.jsonl ] && wc -l < $d/runs.jsonl || echo 0 )
  if [ -f $d/DONE ]; then st=DONE; else st=INCOMPLETE; todo+=($i); fi
  printf "%2d %-22s %-10s rows=%s\n" $i ${TAGS[$i]} $st $n
done
echo "queued array jobs: ${queued:-none}"
if [ "${1:-}" = "--submit" ] && [ ${#todo[@]} -gt 0 ]; then
  if [ -n "$queued" ]; then echo "an agentrun-p3-eval3 job is still queued/running; not submitting (avoid duplicates)"; exit 0; fi
  idx=$(IFS=,; echo "${todo[*]}")
  sbatch --array="${idx}%1" hpc/phase3_eval3.sbatch
fi
