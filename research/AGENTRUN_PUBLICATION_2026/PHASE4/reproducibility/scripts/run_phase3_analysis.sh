#!/bin/bash
# One-command Phase 3 pipeline. Run from PHASE3/ in Git Bash:  bash scripts/run_phase3_analysis.sh <stage>
#   status    cell completeness on the cluster (rows, DONE, queue); read-only
#   fetch     copy run dirs + logs + the sealed task file to PHASE3/ (gitignored), verify sha256 against the cluster
#             and the task file against FREEZE_eval3.json. Sealed content never goes into tracked files.
#   verify    freeze/prereg/evarb hash checks, per-cell completeness and missing-run report -> ANALYSIS/COMPLETENESS.md
#   analyze   frozen analyze_p2 (primary cells pooled; Holm over EBG-RT, EBG-T, EBG-LG, EBG-B), secondary cells,
#             flagged-complement sensitivity, descriptive metrics -> ANALYSIS/
#   report    independent cross-check of the headline numbers + PHASE3_* tables (build_reports.py)
#   all       fetch, verify, analyze, report
# DRY=1 runs verify+analyze on the p2val2 development runs (no cluster, no eval3) to test the pipeline.
set -euo pipefail
H=<user>@<cluster-login>
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
  ssh -o BatchMode=yes $H "squeue -a -o '%.12i %.9u %.12j %.8T %.10M %R'; cat ~/AGENTRUN_HPC/phase3_controller/status.txt; tail -5 ~/AGENTRUN_HPC/phase3_controller/events.log" ;;
fetch)
  mkdir -p logs
  scp -q $H:$S/eval3_tasks.jsonl $H:$S/eval3_PRIMARY_IDS.json SEALED_LOCAL/
  mkdir -p SEALED_LOCAL/qwen14b_only   # inputs of sensitivity set (b); checked against the seal's SHA256SUMS
  scp -q $H:$S/SHA256SUMS $H:$S/eval3_groups.jsonl $H:$S/eval3_skeleton.jsonl $H:$S/eval3_annotations_qwen14b.jsonl SEALED_LOCAL/qwen14b_only/
  (cd SEALED_LOCAL/qwen14b_only && grep -E " (eval3_groups|eval3_skeleton|eval3_annotations_qwen14b).jsonl$" SHA256SUMS | sha256sum -c --quiet) && echo "set (b) inputs match the seal"
  python - <<PY
import hashlib,json
f=json.load(open("$P2/FREEZE_eval3.json"))["sealed_files"]
for n in ("eval3_tasks.jsonl","eval3_PRIMARY_IDS.json"):
    h=hashlib.sha256(open("SEALED_LOCAL/"+n,"rb").read()).hexdigest(); print(n,"OK" if h==f[n] else "MISMATCH"); assert h==f[n]
PY
  for c in $(ssh $H "cd ~/AGENTRUN_HPC/phase3_raw && ls -d eval3_*/ | tr -d /"); do
    mkdir -p RAW_RESULTS/$c; scp -q $H:AGENTRUN_HPC/phase3_raw/$c/* RAW_RESULTS/$c/
  done
  scp -q "$H:$R/logs/phase3_*" logs/ || true
  ssh $H "cd ~/AGENTRUN_HPC/phase3_raw && sha256sum eval3_*/*" | sort -k2 > ANALYSIS/remote_raw_sums.txt
  scp -q $H:AGENTRUN_HPC/phase3_raw/SHA256SUMS ANALYSIS/controller_SHA256SUMS.txt || echo "controller SHA256SUMS not present (campaign not finished?)"
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
    # flagged complement of (a), analysed the same way (PREREGISTRATION.md section 8, item set)
    python $A/subset_tasks.py --tasks $TASKS --ids SEALED_LOCAL/eval3_PRIMARY_IDS.json --out SEALED_LOCAL/eval3_tasks_agreed.jsonl --out-flagged SEALED_LOCAL/eval3_tasks_flagged.jsonl
    python $A/analyze_p2.py --tasks SEALED_LOCAL/eval3_tasks_flagged.jsonl --runs $PRIMARY_CELLS --out $OUT/SENSITIVITY_flagged_complement --holm EBG-RT,EBG-T,EBG-LG,EBG-B
    # set (b): Qwen2.5-14B annotator agrees with gold, by the frozen agreement rule (benchmark/agreement.py) on one annotator
    python $P2/benchmark/agreement.py --split eval3 --dir SEALED_LOCAL/qwen14b_only --tags qwen14b --quiet > $OUT/SENSITIVITY_qwen14b_agreement_summary.json
    python scripts/agreed_ids_b.py --agreement SEALED_LOCAL/qwen14b_only/eval3_AGREEMENT.json --groups SEALED_LOCAL/qwen14b_only/eval3_groups.jsonl --out SEALED_LOCAL/eval3_QWEN14B_AGREED_IDS.json
    python $A/subset_tasks.py --tasks $TASKS --ids SEALED_LOCAL/eval3_QWEN14B_AGREED_IDS.json --out SEALED_LOCAL/eval3_tasks_qwen14b_agreed.jsonl
    python $A/analyze_p2.py --tasks SEALED_LOCAL/eval3_tasks_qwen14b_agreed.jsonl --runs $PRIMARY_CELLS --out $OUT/SENSITIVITY_qwen14b_agreed --holm EBG-RT,EBG-T,EBG-LG,EBG-B
  fi
  python scripts/phase3_metrics.py --tasks $TASKS --runs $PRIMARY_CELLS $SEC_CELLS --out $OUT/METRICS ;;
report)
  python scripts/crosscheck_phase3.py --tasks $TASKS --runs $PRIMARY_CELLS --analysis $OUT/CONFIRMATORY_primary_cells.json --out $OUT/CROSSCHECK
  if [ "${DRY:-0}" = 1 ]; then
    python scripts/build_reports.py --src $OUT --dest $OUT/reports --cells $PRIMARY_CELLS --dry
  else
    python scripts/build_reports.py --src $OUT --dest . --cells $PRIMARY_CELLS $SEC_CELLS --logs logs
  fi ;;
all) bash "$0" fetch; bash "$0" verify; bash "$0" analyze; bash "$0" report ;;
*) echo "usage: $0 status|fetch|verify|analyze|report|all   (DRY=1 for the p2val2 pipeline test)"; exit 1 ;;
esac
