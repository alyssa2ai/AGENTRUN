#!/bin/bash
#SBATCH --job-name=agentrun-eval3
#SBATCH --partition=gpu-nodes
#SBATCH --nodes=1
#SBATCH --ntasks=1
#SBATCH --cpus-per-task=4
#SBATCH --gres=gpu:1
#SBATCH --mem=64G
#SBATCH --time=03:00:00
#SBATCH --output=logs/eval3_build_%j.out
#SBATCH --error=logs/eval3_build_%j.err
# Build and seal eval3 AFTER the mechanism freeze (FREEZE_evarb.json, PREREGISTRATION.md §3).
# Everything is written to SEALED (outside the source tree). Only counts, agreement statistics,
# split-boundary checks and hashes reach this log. Step logs (which may contain item text) are deleted.
# Submit from PHASE2/:  sbatch hpc/eval3_build.sbatch
set -uo pipefail
W=$HOME/AGENTRUN_HPC/20261111
source $W/environment/venv/bin/activate
export HF_HUB_OFFLINE=1 TRANSFORMERS_OFFLINE=1 TOKENIZERS_PARALLELISM=false PYTHONUNBUFFERED=1
P2=$W/source/research/AGENTRUN_PUBLICATION_2026/PHASE2
SEALED=$HOME/AGENTRUN_HPC/sealed/eval3
echo "job=$SLURM_JOB_ID host=$(hostname) start=$(date -Is)"
# 0. refuse to build unless the frozen mechanism on the cluster matches FREEZE_evarb.json
python - "$P2" <<'EOF' || { echo "FREEZE CHECK FAILED - not building eval3"; exit 2; }
import hashlib, json, sys, pathlib
p2 = pathlib.Path(sys.argv[1]); f = json.loads((p2 / "FREEZE_evarb.json").read_text())
bad = [k for k, v in f["files"].items() if hashlib.sha256((p2 / k).read_bytes().replace(b"\r\n", b"\n")).hexdigest() != v]
print("freeze", f["version"], "files", len(f["files"]), "mismatches", bad); sys.exit(1 if bad else 0)
EOF
if [ -f $SEALED/SHA256SUMS ]; then echo "eval3 already sealed - verifying only"; ( cd $SEALED && sha256sum -c --quiet SHA256SUMS && echo "seal verified" ); exit 0; fi
mkdir -p $SEALED && chmod 700 $HOME/AGENTRUN_HPC/sealed $SEALED
cd $P2/benchmark
step() { echo "start $(date -Is) $1 $2"; "$@" > $SEALED/step_$(date +%s%N).log 2>&1; rc=$?; echo "exit=$rc $(date -Is) $1 $2"; }
test -f $SEALED/eval3_skeleton.jsonl || python skeleton.py --split eval3 --out $SEALED | python -c "import json,sys;d=json.load(sys.stdin);print({k:d[k] for k in ('split','n_items','skeleton_sha256') if k in d})"
step python write_and_annotate.py write --split eval3 --dir $SEALED --model Qwen/Qwen2.5-14B-Instruct
python assemble.py --split eval3 --dir $SEALED --quiet
step python write_and_annotate.py annotate --split eval3 --dir $SEALED --model meta-llama/Llama-3.1-8B-Instruct --tag llama8b
step python write_and_annotate.py annotate --split eval3 --dir $SEALED --model Qwen/Qwen2.5-14B-Instruct --tag qwen14b
python agreement.py --split eval3 --dir $SEALED --tags llama8b qwen14b --quiet
python seal_checks.py --split eval3 --dir $SEALED --ref-dir $P2/data; echo "seal_checks exit=$?"
# provenance: generator code hashes, model snapshots, job; no content
python - "$P2" "$SEALED" <<'EOF'
import hashlib, json, os, sys, pathlib, time, glob
p2, s = pathlib.Path(sys.argv[1]), pathlib.Path(sys.argv[2])
h = lambda p: hashlib.sha256(pathlib.Path(p).read_bytes().replace(b"\r\n", b"\n")).hexdigest()
gen = {f"benchmark/{n}": h(p2 / "benchmark" / n) for n in ("skeleton.py", "assemble.py", "write_and_annotate.py", "agreement.py",
       "seal_checks.py", "ANNOTATION_GUIDELINES.md")}
snap = {m: sorted(glob.glob(os.path.expanduser(f"~/.cache/huggingface/hub/models--{m.replace('/', '--')}/snapshots/*")))[-1].rsplit("/", 1)[-1]
        for m in ("Qwen/Qwen2.5-14B-Instruct", "meta-llama/Llama-3.1-8B-Instruct")}
prov = {"split": "eval3", "slurm_job_id": os.environ.get("SLURM_JOB_ID"), "built_utc": time.strftime("%Y-%m-%dT%H:%M:%SZ", time.gmtime()),
        "freeze_evarb_sha256": h(p2 / "FREEZE_evarb.json"), "generator_sha256": gen, "model_snapshots": snap,
        "writer": "Qwen/Qwen2.5-14B-Instruct greedy (retries T=0.7 seeded)", "annotators": ["meta-llama/Llama-3.1-8B-Instruct", "Qwen/Qwen2.5-14B-Instruct"],
        "human_validation": "none"}
(s / "eval3_PROVENANCE.json").write_text(json.dumps(prov, indent=1) + "\n"); print(json.dumps(prov, indent=1))
EOF
rm -f $SEALED/step_*.log
( cd $SEALED && sha256sum eval3_* | sort -k2 > SHA256SUMS && chmod a-w eval3_* SHA256SUMS )
echo "SHA256SUMS of sealed files:"; awk '{print $1"  "$2}' $SEALED/SHA256SUMS
echo "SHA256SUMS itself: $(sha256sum $SEALED/SHA256SUMS | cut -d' ' -f1)"
( cd $SEALED && sha256sum -c --quiet SHA256SUMS && echo "seal verified" )
echo "job finished $(date -Is)"
