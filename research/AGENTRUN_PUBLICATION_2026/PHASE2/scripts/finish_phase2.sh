#!/bin/bash
# Finish Phase 2 after Slurm jobs 4199 (p2val2), 4200 (eval3 seal) and 4201 (agent runs) have run.
# Run from the laptop (Git Bash), in PHASE2/:   bash scripts/finish_phase2.sh <stage>
#   status   queue state and exit lines of the three jobs (read-only)
#   fetch    copy p2val2 data, LLM-arbiter outputs, agent runs and logs back; verify every sha256 against the cluster
#            (does NOT look at any evarb output; do the p2val2 text audit after this stage)
#   freeze   write FREEZE_eval3.json from the eval3 job log + a remote seal check (counts/hashes only; reads no sealed content)
#   analyze  component comparison, agent-level analysis, power, budget (run only AFTER the p2val2 text audit)
# Never submits jobs. Never reads ~/AGENTRUN_HPC/sealed/eval3 contents.
set -euo pipefail
H=<user>@<cluster-login>
R=AGENTRUN_HPC/20261111/source/research/AGENTRUN_PUBLICATION_2026/PHASE2
J1=${J1:-4199}; J2=${J2:-4200}; J3=${J3:-4213}
MODELS="qwen25_3b qwen25_7b llama31_8b"
cd "$(dirname "$0")/.."

case "${1:-}" in
status)
  ssh -o BatchMode=yes $H "squeue -a -o '%.10i %.10u %.22j %.8T %.10M %R'; cd $R/logs && grep -H -E '^(exit=|job finished|FREEZE|SEAL|seal verified)' *_${J1}*.out *_${J2}*.out *_${J3}_*.out 2>/dev/null | tail -40" || true
  ;;
fetch)
  mkdir -p data/p2val2 raw/llm_arbiter logs
  scp -q -o BatchMode=yes "$H:$R/data/p2val2/*" data/p2val2/
  scp -q -o BatchMode=yes "$H:$R/raw/llm_arbiter/*__p2val2_groups.jsonl" "$H:$R/raw/llm_arbiter/*__client.json" raw/llm_arbiter/
  scp -q -o BatchMode=yes "$H:$R/logs/*_${J1}*" "$H:$R/logs/*_${J2}*" "$H:$R/logs/*_${J3}_*" logs/
  for S in p2val2 p2val; do for T in $MODELS; do
    mkdir -p raw/${S}_${T}_greedy; scp -q -o BatchMode=yes "$H:$R/raw/${S}_${T}_greedy/*" raw/${S}_${T}_greedy/ || echo "MISSING run dir ${S}_${T}_greedy"
  done; done
  ssh -o BatchMode=yes $H "cd $R && sha256sum data/p2val2/* raw/llm_arbiter/*p2val2* raw/p2val*_greedy/* logs/*_${J1}* logs/*_${J2}* logs/*_${J3}_*" \
    | sort -k2 > /tmp/remote_sums.txt
  sha256sum -c /tmp/remote_sums.txt --quiet && echo "ALL FETCHED FILES MATCH THE CLUSTER ($(wc -l < /tmp/remote_sums.txt) files)"
  python -c "import json;d=json.load(open('data/p2val2/p2val2_MANIFEST.json'));print('p2val2 skeleton',d['n_skeleton'],'valid',d['n_valid'],'excluded',len(d['excluded_ids']))"
  python -c "import json;d=json.load(open('data/p2val2/p2val2_AGREEMENT.json'));print({k:v for k,v in d.items() if k not in ('flags','primary_by_category')})"
  echo "NEXT: audit every p2val2 item (text vs. skeleton brief/gold) BEFORE running 'analyze'; record it in data/p2val2/P2VAL2_ITEM_AUDIT.md"
  ;;
freeze)
  ssh -o BatchMode=yes $H "cd ~/AGENTRUN_HPC/sealed/eval3 && sha256sum -c SHA256SUMS && stat -c '%A %n' eval3_* SHA256SUMS" > logs/eval3_remote_seal_check.txt
  python scripts/write_freeze_eval3.py --log logs/eval3_build_${J2}.out --remote-check logs/eval3_remote_seal_check.txt \
    --prereg PREREGISTRATION.md --out FREEZE_eval3.json
  ;;
analyze)
  cd scripts
  python component_report.py --split p2val2 --primary ../data/p2val2/p2val2_PRIMARY_IDS.json --out ../data/BASELINE_p2val2
  for S in p2val2 p2val; do
    RUNS=$(for T in $MODELS; do echo ../raw/${S}_${T}_greedy; done)
    python analyze_p2.py --tasks ../data/$S/${S}_tasks.jsonl --runs $RUNS --out ../data/AGENT_$S --holm EBG-RT,EBG-T,EBG-LG,EBG-B
  done
  python subset_tasks.py --tasks ../data/p2val2/p2val2_tasks.jsonl --ids ../data/p2val2/p2val2_PRIMARY_IDS.json \
    --out ../data/p2val2/p2val2_tasks_primary.jsonl
  python analyze_p2.py --tasks ../data/p2val2/p2val2_tasks_primary.jsonl --runs $(for T in $MODELS; do echo ../raw/p2val2_${T}_greedy; done) \
    --out ../data/AGENT_p2val2_primary --holm EBG-RT,EBG-T,EBG-LG,EBG-B
  python power_phase3.py --tasks ../data/p2val2/p2val2_tasks.jsonl --runs $(for T in $MODELS; do echo ../raw/p2val2_${T}_greedy; done) \
    --eval3-families 138 --items-per-family 2 --out ../data/POWER_phase3
  python budget_phase3.py --runs $(for T in $MODELS; do echo ../raw/p2val2_${T}_greedy; done) --out ../data/BUDGET_phase3
  echo "NEXT: update BASELINE_COMPARISON, PREREGISTRATION §9 (then freeze), PHASE3_EXECUTION_PLAN §2, STATUS, FINAL_REPORT"
  ;;
*) echo "usage: $0 status|fetch|freeze|analyze"; exit 1 ;;
esac
