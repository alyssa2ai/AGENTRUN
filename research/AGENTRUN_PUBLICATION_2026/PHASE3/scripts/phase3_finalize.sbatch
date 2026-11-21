#!/bin/bash
#SBATCH --job-name=agentrun-p3-final
#SBATCH --partition=gpu-nodes
#SBATCH --ntasks=1
#SBATCH --cpus-per-task=2
#SBATCH --mem=6G
#SBATCH --time=04:00:00
#SBATCH --output=/home/%u/AGENTRUN_HPC/finalize/finalize_%j.out
# Phase 3 finalization on the cluster (no GPU, no laptop, no SSH session). Submitted with
#   sbatch --dependency=afterany:<controller v2 job> phase3_finalize.sbatch
# The controller only exits when all 18 cells are DONE, or when every remaining cell is BLOCKED, so `afterany` on it
# is not trusted by itself: every gate below re-checks the cells explicitly and stops the job on any failure.
# Stages (status in ~/AGENTRUN_HPC/PHASE3_FINAL_STATUS.md):
#   gates  -> 18 DONE, rows = tasks x 12, no duplicates / unparsable lines, last Slurm exit 0, manifests consistent,
#             controller SHA256SUMS, eval3 seal (sha256sum -c, without reading contents), evarb-0.2 + prereg hashes
#   stage  -> copy raw cells, Slurm logs and sealed inputs into the gitignored PHASE3 dirs of the HPC clone; re-verify
#   verify / analyze / report  -> scripts/run_phase3_analysis.sh (frozen analyze_p2, 100,000 permutations; Holm;
#             sensitivity sets; independent cross-check must agree; PHASE3_* tables, CSVs, verdicts)
#   draft  -> PHASE4/manuscript/07_results_AUTO.md (numbers only)
#   seal   -> SHA-256 manifest of every output; local commit in the HPC clone (never pushed)
set -uo pipefail
H=$HOME/AGENTRUN_HPC
REPO=$H/finalize/AGENTRUN
PUB=$REPO/research/AGENTRUN_PUBLICATION_2026
P2=$PUB/PHASE2; P3=$PUB/PHASE3
RAW=$H/phase3_raw; SEAL=$H/sealed/eval3; CTL=$H/phase3_controller
LOGS=$H/20261111/source/research/AGENTRUN_PUBLICATION_2026/PHASE2/logs
STATUS=$H/PHASE3_FINAL_STATUS.md
source $H/20261111/environment/venv/bin/activate
export PYTHONUNBUFFERED=1 PYTHONHASHSEED=0
stage=start
note() { echo "- $(date -u +%FT%TZ) $*" >> "$STATUS"; echo "$*"; }
fail() { note "**FAILED at stage \`$stage\`**: $*"; sed -i "s/^STATE: .*/STATE: FAILED ($stage)/" "$STATUS"; exit 1; }
cat > "$STATUS" <<EOF
# AGENTRUN Phase 3 finalization status (written by Slurm job ${SLURM_JOB_ID:-local})

STATE: RUNNING

Controller: $(head -1 $CTL/status.txt 2>/dev/null)
Repository clone: $REPO (branch research/memory-ablation-2026-11, local commits only)

## Events
EOF

stage=gates
[ -f $CTL/ALL_DONE ] || fail "controller did not write ALL_DONE (STOPPED_BLOCKED: $(cat $CTL/STOPPED_BLOCKED 2>/dev/null || echo no)); blocked cells: $(ls $CTL | grep blocked_ | tr '\n' ' ')"
python $P3/scripts/finalize_gates.py --raw $RAW --logs $LOGS --tasks $SEAL/eval3_tasks.jsonl --out $H/finalize/gates.json || fail "cell gates: $(python -c "import json;print('; '.join(json.load(open('$H/finalize/gates.json'))['failures'])[:900])")"
( cd $RAW && sha256sum -c --quiet SHA256SUMS ) || fail "raw files differ from the controller's SHA256SUMS"
( cd $SEAL && sha256sum -c --quiet SHA256SUMS ) || fail "eval3 seal check"
python - "$P2" "$SEAL" <<'EOF' || fail "freeze / preregistration / seal-manifest hash"
import hashlib, json, sys, pathlib
p2, seal = pathlib.Path(sys.argv[1]), pathlib.Path(sys.argv[2])
f = json.loads((p2 / "FREEZE_evarb.json").read_text())
bad = [k for k, v in f["files"].items() if hashlib.sha256((p2 / k).read_bytes().replace(b"\r\n", b"\n")).hexdigest() != v]
e = json.loads((p2 / "FREEZE_eval3.json").read_text())
pre = hashlib.sha256((p2 / "PREREGISTRATION.md").read_bytes().replace(b"\r\n", b"\n")).hexdigest() == e["preregistration_sha256"]
sums = hashlib.sha256((seal / "SHA256SUMS").read_bytes()).hexdigest() == e["sha256sums_file_sha256"]
print("evarb mismatches", bad, "prereg", pre, "seal manifest", sums); sys.exit(0 if not bad and pre and sums else 1)
EOF
note "gates passed: 18/18 cells DONE, rows/duplicates/exit codes/manifests OK, raw checksums OK, seal OK, evarb-0.2 and preregistration hashes OK"

stage=stage
cd $P3 || fail "no PHASE3 dir"
mkdir -p RAW_RESULTS SEALED_LOCAL/qwen14b_only logs ANALYSIS
for d in $RAW/eval3_*/; do c=$(basename $d); mkdir -p RAW_RESULTS/$c; cp -p $d/runs.jsonl $d/manifest.jsonl $d/DONE RAW_RESULTS/$c/; done
cp -p $RAW/SHA256SUMS ANALYSIS/controller_SHA256SUMS.txt
( cd RAW_RESULTS && sha256sum -c --quiet ../ANALYSIS/controller_SHA256SUMS.txt ) || fail "staged raw copies differ"
cp -p $SEAL/eval3_tasks.jsonl $SEAL/eval3_PRIMARY_IDS.json SEALED_LOCAL/
cp -p $SEAL/SHA256SUMS $SEAL/eval3_groups.jsonl $SEAL/eval3_skeleton.jsonl $SEAL/eval3_annotations_qwen14b.jsonl SEALED_LOCAL/qwen14b_only/
( cd SEALED_LOCAL/qwen14b_only && grep -E " (eval3_groups|eval3_skeleton|eval3_annotations_qwen14b).jsonl$" SHA256SUMS | sha256sum -c --quiet ) || fail "staged sealed inputs differ"
cp -p $LOGS/phase3_* logs/ 2>/dev/null
cp -p $H/finalize/gates.json ANALYSIS/FINALIZE_GATES.json
note "staged 18 cells, logs and sealed inputs into the clone (gitignored); copies re-verified"

stage=platform_report
python $P3/scripts/platform_continuity.py --raw $RAW --evidence $P3/platform_evidence.json \
  --out-json ANALYSIS/PLATFORM_CONTINUITY.json --out-md PHASE3_PLATFORM_CONTINUITY.md \
  > ANALYSIS/finalize_platform.log 2>&1 || fail "G5 platform-continuity report could not be generated"
note "G5 platform-continuity report written (reporting only): $(tail -1 ANALYSIS/finalize_platform.log)"
[ -s PHASE3_DEVIATIONS.md ] || fail "PHASE3_DEVIATIONS.md is missing: the G5 disclosure has no home"

stage=verify
bash scripts/run_phase3_analysis.sh verify > ANALYSIS/finalize_verify.log 2>&1 || fail "verify_phase3.py reported integrity problems (ANALYSIS/finalize_verify.log)"
note "verify_phase3: no integrity problems"
stage=analyze
bash scripts/run_phase3_analysis.sh analyze > ANALYSIS/finalize_analyze.log 2>&1 || fail "analysis failed (ANALYSIS/finalize_analyze.log)"
note "analysis done: primary (100,000 permutations, Holm), sensitivity (a), flagged complement, set (b), secondary, metrics"
stage=exploratory
bash scripts/run_phase3_analysis.sh exploratory > ANALYSIS/finalize_exploratory.log 2>&1 || fail "exploratory sensitivity analyses failed (ANALYSIS/finalize_exploratory.log)"
note "exploratory (post-hoc, NOT confirmatory): primary contrasts without the straddling cell; Qwen3-8B pre-reboot decodings only"
stage=report
bash scripts/run_phase3_analysis.sh report > ANALYSIS/finalize_report.log 2>&1 || fail "cross-check disagreement or report generation failed (ANALYSIS/finalize_report.log)"
for f in PHASE3_EXECUTION_LOG.md PHASE3_COMPARISON_TABLES.md PHASE3_ABLATION_RESULTS.md PHASE3_STATISTICAL_ANALYSIS.md PHASE3_FAILURE_TABLES.md PHASE3_DECISIONS.json PHASE3_PLATFORM_CONTINUITY.md PHASE3_DEVIATIONS.md PHASE3_G4_FORENSIC_REPORT.md ANALYSIS/EXPLORATORY_no_straddling_cell.json ANALYSIS/EXPLORATORY_qwen3_pre_reboot_only.json; do
  [ -s $f ] || fail "missing report $f"; done
grep -q "all values agree" ANALYSIS/CROSSCHECK.md || fail "cross-check did not confirm"
note "reports written; independent cross-check agrees with the frozen analysis"
stage=draft
python scripts/write_results_section.py --p3 . --out $PUB/PHASE4/manuscript/07_results_AUTO.md > /dev/null || fail "results draft"
note "PHASE4/manuscript/07_results_AUTO.md written (numbers only; interpretation pending)"

stage=seal
{ echo "# Phase 3 SHA-256 manifest (finalization job ${SLURM_JOB_ID:-local}, $(date -u +%FT%TZ))"
  echo "## raw cells (gitignored; on the cluster in $RAW)"; cat ANALYSIS/controller_SHA256SUMS.txt
  echo "## sealed eval3 (cluster only)"; sha256sum $SEAL/SHA256SUMS | sed "s#$SEAL/##"
  echo "## outputs"; find ANALYSIS results scripts tests -type f ! -path "ANALYSIS/DRYRUN/*" -print0 | sort -z | xargs -0 sha256sum
  sha256sum PHASE3_*.md PHASE3_DECISIONS.json platform_evidence.json LIMITATIONS.md $PUB/PHASE4/manuscript/07_results_AUTO.md | sed "s#$PUB/##"
} > PHASE3_SHA256_MANIFEST.txt
cd $REPO
if git status --short -- research/AGENTRUN_PUBLICATION_2026 | grep -qE "SEALED_LOCAL|RAW_RESULTS/eval3_|PHASE3/logs/"; then fail "sealed/raw files would enter git"; fi
git add research/AGENTRUN_PUBLICATION_2026/PHASE3 research/AGENTRUN_PUBLICATION_2026/PHASE4
git commit -q -m "research: Phase 3 confirmatory analysis (HPC finalization job ${SLURM_JOB_ID:-local})

All 18 cells passed the integrity gates under G4 policy g4-v2 (gpu_mem_gib declared observational;
every identity field strict and closed by default); reporting-only G5 platform-continuity report;
frozen analyze_p2 with 100,000 permutations and Holm over the four primary contrasts; preregistered
sensitivity analyses plus two post-hoc exploratory ones (PHASE3_DEVIATIONS.md D7); independent
cross-check agrees. Interpretation pending.

Co-Authored-By: Claude Opus 5.5 <noreply@anthropic.com>" || fail "git commit"
note "committed in the HPC clone: $(git log --oneline -1)"
sed -i "s/^STATE: .*/STATE: ANALYSIS COMPLETE - interpretation, final report and manuscript prose pending/" "$STATUS"
cat >> "$STATUS" <<EOF

## Deliverables (in $P3)
PHASE3_EXECUTION_LOG.md, PHASE3_STATISTICAL_ANALYSIS.md, PHASE3_COMPARISON_TABLES.md, PHASE3_ABLATION_RESULTS.md,
PHASE3_FAILURE_TABLES.md, PHASE3_DECISIONS.json, results/*.csv, ANALYSIS/*, PHASE3_SHA256_MANIFEST.txt,
PHASE4/manuscript/07_results_AUTO.md. Fetch to the laptop with:
  git fetch <user>@<cluster-login>:AGENTRUN_HPC/finalize/AGENTRUN research/memory-ablation-2026-11:hpc-final
EOF
note "finalization complete"
