#!/bin/bash
#SBATCH --job-name=agentrun-p3-ctl2
#SBATCH --partition=gpu-nodes
#SBATCH --ntasks=1
#SBATCH --cpus-per-task=1
#SBATCH --mem=1G
#SBATCH --time=7-00:00:00
#SBATCH --output=logs/phase3_ctl2_%j.out
# Phase 3 controller v2 (replaces retry controller 4243, 18 Nov 2026). No GPU. Submit from PHASE2/:
#   sbatch hpc/phase3_controller_v2.sbatch
# * Keeps at most MAX_LANES (default 2) AGENTRUN cells queued/running, one GPU each (Slurm gres assigns distinct
#   /dev/nvidia0 and /dev/nvidia1; CUDA_VISIBLE_DEVICES is set per job).
# * Drops to ONE lane whenever any non-AGENTRUN job requests a GPU (pending or running). Never preempts anything.
# * Submits a cell only if it has no DONE marker and is not already queued/running (squeue -r, array index %K);
#   if squeue fails, it submits nothing in that round (no blind submissions).
# * Resubmits only incomplete cells; the runner skips finished (task, config) pairs, so successful work is never redone.
# * Before a resubmission, a truncated trailing line in runs.jsonl (kill during a write) is moved, not deleted,
#   to runs.jsonl.partial_<UTC>.
# * A cell with no new rows over two consecutive attempts, or more than 5 attempts, is marked BLOCKED (not retried).
# * The experiment is untouched: every submission is `sbatch --array=<idx> hpc/phase3_eval3.sbatch`; only the 14B cell
#   gets a longer wall-time limit (--time=36:00:00) so it is not split by the 12 h default.
# * When all 18 cells are DONE it writes phase3_raw/SHA256SUMS and phase3_controller/ALL_DONE, then exits.
set -uo pipefail
cd "${SLURM_SUBMIT_DIR:-$(dirname "$0")/..}"
OUT=$HOME/AGENTRUN_HPC/phase3_raw
ST=$HOME/AGENTRUN_HPC/phase3_controller
MAX_LANES=${MAX_LANES:-2}
POLL=${POLL:-300}
mkdir -p "$ST"
TAGS=(qwen25_3b_greedy qwen25_3b_T07_s1 qwen25_3b_T07_s2 qwen25_3b_T07_s3
      qwen25_7b_greedy qwen25_7b_T07_s1 qwen25_7b_T07_s2 qwen25_7b_T07_s3
      llama31_8b_greedy llama31_8b_T07_s1 llama31_8b_T07_s2 llama31_8b_T07_s3
      qwen3_8b_greedy qwen3_8b_T07_s1 qwen3_8b_T07_s2 qwen3_8b_T07_s3
      qwen25_14b_greedy llama32_3b_greedy)
# Longest cell first on the free lane (minimises wall time); the rest in the pre-registered cheapest-first order.
ORDER=(16 0 1 2 3 4 5 6 7 8 9 10 11 12 13 14 15 17)
log() { echo "$(date -u +%FT%TZ) $*" | tee -a "$ST/events.log"; }

others=$(squeue -h -n agentrun-p3-ctl2 -o "%i" | grep -v "^${SLURM_JOB_ID:-none}$" | wc -l)
[ "$others" -gt 0 ] && { log "another controller is active; exiting"; exit 0; }

rows() { [ -f "$OUT/eval3_$1/runs.jsonl" ] && wc -l < "$OUT/eval3_$1/runs.jsonl" || echo 0; }

fix_tail() {  # quarantine a truncated last line; never touches complete lines
  local f="$OUT/eval3_$1/runs.jsonl"; [ -s "$f" ] || return 0
  python3 - "$f" <<'EOF'
import json, sys, time
p = sys.argv[1]; b = open(p, "rb").read()
body = b.rstrip(b"\n"); last = body.rsplit(b"\n", 1)[-1]
try:
    json.loads(last); ok = b.endswith(b"\n")
except Exception:
    ok = False
if not ok:
    cut = body.rfind(b"\n") + 1
    q = p + ".partial_" + time.strftime("%Y%m%dT%H%M%SZ", time.gmtime())
    open(q, "wb").write(b[cut:])
    with open(p, "r+b") as f:
        f.truncate(cut)
    print("quarantined", len(b) - cut, "bytes ->", q)
EOF
}

log "controller start job=${SLURM_JOB_ID:-local} lanes<=$MAX_LANES"
while true; do
  active=$(squeue -h -r -u "$USER" -n agentrun-p3-eval3 -o "%K") || { log "squeue failed; skipping round"; sleep "$POLL"; continue; }
  gpu_jobs=$(squeue -h -t PD,R,CF -o "%j|%b") || { log "squeue failed; skipping round"; sleep "$POLL"; continue; }
  foreign=$(echo "$gpu_jobs" | grep -i "gpu" | grep -vc "^agentrun-")
  lanes=$MAX_LANES; [ "$foreign" -gt 0 ] && lanes=1
  n_active=$(echo "$active" | grep -c "[0-9]")
  todo=(); ndone=0; status=""
  for i in "${ORDER[@]}"; do
    t=${TAGS[$i]}; r=$(rows "$t")
    if [ -f "$OUT/eval3_$t/DONE" ]; then s=DONE; ndone=$((ndone+1))
    elif echo "$active" | grep -qx "$i"; then s=ACTIVE
    elif [ -f "$ST/blocked_$i" ]; then s=BLOCKED
    else s=TODO; todo+=("$i"); fi
    status+=$(printf "%2d %-20s %-8s rows=%s attempts=%s\n" "$i" "$t" "$s" "$r" "$(cat "$ST/attempts_$i" 2>/dev/null || echo 0)")$'\n'
  done
  { echo "updated $(date -u +%FT%TZ)  done=$ndone/18  active=$n_active  lanes=$lanes  foreign_gpu_jobs=$foreign"; echo "$status" | sort -n; } > "$ST/status.txt"
  if [ "$ndone" -eq 18 ]; then
    ( cd "$OUT" && sha256sum eval3_*/runs.jsonl eval3_*/manifest.jsonl eval3_*/DONE > SHA256SUMS )
    date -u +%FT%TZ > "$ST/ALL_DONE"; log "all 18 cells DONE; SHA256SUMS written"; break
  fi
  if [ ${#todo[@]} -eq 0 ] && [ "$n_active" -eq 0 ]; then
    date -u +%FT%TZ > "$ST/STOPPED_BLOCKED"; log "no runnable cells left (blocked); stopping"; break
  fi
  for i in "${todo[@]}"; do
    [ "$n_active" -ge "$lanes" ] && break
    t=${TAGS[$i]}; r=$(rows "$t"); a=$(cat "$ST/attempts_$i" 2>/dev/null || echo 0)
    prev=$(cat "$ST/rows_at_submit_$i" 2>/dev/null || echo -1)
    if [ "$a" -gt 0 ] && [ "$r" -le "$prev" ]; then np=$(( $(cat "$ST/noprog_$i" 2>/dev/null || echo 0) + 1 )); else np=0; fi
    echo "$np" > "$ST/noprog_$i"
    if [ "$np" -ge 2 ] || [ "$a" -ge 5 ]; then log "cell $i $t BLOCKED (attempts=$a, no-progress=$np, rows=$r)"; touch "$ST/blocked_$i"; continue; fi
    fix_tail "$t" | while read -r l; do log "cell $i $t $l"; done
    extra=(); [ "$i" -eq 16 ] && extra=(--time=36:00:00)
    sub=$(sbatch "${extra[@]}" --array="$i" hpc/phase3_eval3.sbatch 2>&1)
    log "submit cell $i $t rows=$r attempt=$((a+1)): $sub"
    if echo "$sub" | grep -q "Submitted batch job"; then
      echo $((a+1)) > "$ST/attempts_$i"; echo "$(rows "$t")" > "$ST/rows_at_submit_$i"; n_active=$((n_active+1))
    fi
  done
  [ "${ONCE:-0}" = 1 ] && break   # test mode: one round (use with a fake sbatch on PATH)
  sleep "$POLL"
done
log "controller exit"
