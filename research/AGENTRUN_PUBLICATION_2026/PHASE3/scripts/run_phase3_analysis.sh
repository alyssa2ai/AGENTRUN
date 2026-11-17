#!/bin/bash
# One-command Phase 3 pipeline. Run from PHASE3/ in Git Bash:  bash scripts/run_phase3_analysis.sh <stage>
#   status    cell completeness on the cluster (rows, DONE, queue); read-only
#   fetch     copy run dirs + logs + the sealed task file to PHASE3/ (gitignored), verify sha256 against the cluster
#             and the task file against FREEZE_eval3.json. Sealed content never goes into tracked files.
#   verify    freeze/prereg/evarb hash checks, per-cell completeness and missing-run report -> ANALYSIS/COMPLETENESS.md
#   analyze   frozen analyze_p2 (primary cells pooled; Holm over EBG-RT, EBG-T, EBG-LG, EBG-B), secondary cells,
#             flagged-complement sensitivity, descriptive metrics -> ANALYSIS/
#   all       fetch, verify, analyze
# DRY=1 runs verify+analyze on the p2val2 development runs (no cluster, no eval3) to test the pipeline.
set -euo pipefail
H=gpuuser12@192.168.192.11
R=AGENTRUN_HPC/20261111/source/research/AGENTRUN_PUBLICATION_2026/PHASE2
S=AGENTRUN_HPC/sealed/eval3
cd "$(dirname "$0")/.."
P2=../PHASE2
TAGS_PRIMARY="qwen25_3b qwen25_7b llama31_8b qwen3_8b"
DECS="greedy T07_s1 T07_s2 T07_s3"
SECONDARY="qwen25_14b_greedy llama32_3b_greedy"
if [ "${DRY:-0}" = 1 ]; then
  TASKS=$P2/data/p2val2/p2val2_tasks.jsonl; RUNROOT=$P2/raw; PFX=p2val2_; OUT=ANALYSIS/DRYRUN
  PRIMARY_CELLS=$(for m in $TAGS_PRIMARY; do [ -d $RUNROOT/${PFX}${m}_greedy ] && echo $RUNROOT/${PFX}${m}_greedy; done); SEC_CELLS=""
else
  TASKS=SEALED_LOCAL/eval3_tasks.jsonl; RUNROOT=RAW_RESULTS; PFX=eval3_; OUT=ANALYSIS
  PRIMARY_CELLS=$(for m in $TAGS_PRIMARY; do for d in $DECS; do echo $RUNROOT/${PFX}${m}_$d; done; done)
  SEC_CELLS=$(for c in $SECONDARY; do echo $RUNROOT/${PFX}$c; done)
fi
mkdir -p "$OUT" RAW_RESULTS SEALED_LOCAL
stage=${1:-}
case "$stage" in
status)
  ssh -o BatchMode=yes $H "squeue -a -o '%.12i %.9u %.12j %.8T %.10M %R'; cd $R && bash hpc/phase3_resume.sh" ;;
fetch)
  mkdir -p logs
  scp -q $H:$S/eval3_tasks.jsonl $H:$S/eval3_PRIMARY_IDS.json SEALED_LOCAL/
  python - <<PY
import hashlib,json
f=json.load(open("$P2/FREEZE_eval3.json"))["sealed_files"]
for n in ("eval3_tasks.jsonl","eval3_PRIMARY_IDS.json"):
    h=hashlib.sha256(open("SEALED_LOCAL/"+n,"rb").read()).hexdigest(); print(n,"OK" if h==f[n] else "MISMATCH"); assert h==f[n]
PY
  for c in $(ssh $H "ls ~/AGENTRUN_HPC/phase3_raw"); do
    mkdir -p RAW_RESULTS/$c; scp -q $H:AGENTRUN_HPC/phase3_raw/$c/* RAW_RESULTS/$c/
  done
  scp -q "$H:$R/logs/phase3_*" logs/ || true
  ssh $H "cd ~/AGENTRUN_HPC/phase3_raw && sha256sum */*" | sort -k2 > ANALYSIS/remote_raw_sums.txt
  (cd RAW_RESULTS && sha256sum -c --quiet ../ANALYSIS/remote_raw_sums.txt) && echo "raw files match the cluster ($(wc -l < ANALYSIS/remote_raw_sums.txt) files)" ;;
verify)
  python scripts/verify_phase3.py --tasks $TASKS --cells $PRIMARY_CELLS $SEC_CELLS --out $OUT/COMPLETENESS $( [ "${DRY:-0}" = 1 ] && echo --dry ) ;;
analyze)
  A=$P2/scripts
  python $A/analyze_p2.py --tasks $TASKS --runs $PRIMARY_CELLS --out $OUT/CONFIRMATORY_primary_cells \
    --holm EBG-RT,EBG-T,EBG-LG,EBG-B --n-perm 100000
  if [ "${DRY:-0}" != 1 ]; then
    python $A/subset_tasks.py --tasks $TASKS --ids SEALED_LOCAL/eval3_PRIMARY_IDS.json --out SEALED_LOCAL/eval3_tasks_agreed.jsonl
    python $A/analyze_p2.py --tasks SEALED_LOCAL/eval3_tasks_agreed.jsonl --runs $PRIMARY_CELLS --out $OUT/SENSITIVITY_annotator_agreed --holm EBG-RT,EBG-T,EBG-LG,EBG-B
    python $A/analyze_p2.py --tasks $TASKS --runs $SEC_CELLS --out $OUT/SECONDARY_cells
  fi
  python scripts/phase3_metrics.py --tasks $TASKS --runs $PRIMARY_CELLS $SEC_CELLS --out $OUT/METRICS ;;
all) bash "$0" fetch; bash "$0" verify; bash "$0" analyze ;;
*) echo "usage: $0 status|fetch|verify|analyze|all   (DRY=1 for the p2val2 pipeline test)"; exit 1 ;;
esac
