# hpc/

- `from_cluster/`: what actually ran on the SIT HPC on 2026-11-11 and 2026-11-12: batch scripts, Slurm logs, job manifests, package list. See ../OVERNIGHT_STATUS.md.
- `memlab_qwen7b.sbatch` and the notes below: the plan written **before** the cluster was reachable. It was never executed and was superseded by `from_cluster/scripts/ablation_array.sbatch`, which loads the model directly with transformers instead of starting a vLLM server. Kept as a record only.

---

## What the L40 is for

The ablation in this study does not need a GPU: the model is a hosted endpoint and retrieval is a pure-Python hash embedding. The GPU matters for the one experiment that could not be done today: running the same ablation on the project's own models (base Qwen2.5-7B-Instruct and the LoRA adapters in the repository root), served locally.

## Steps once `ssh <cluster-login>` works

1. Inspect before submitting anything:

       hostname; whoami; sinfo -p gpu-nodes -N; scontrol show partition gpu-nodes
       scontrol show node <compute-node>; squeue -p gpu-nodes; df -h $HOME; nvidia-smi

2. Check what is already there: `module avail`, `conda env list`, `ls ~/.cache/huggingface/hub`. Do not assume Qwen2.5-7B is cached (about 15 GB in fp16) or that the node has internet access.
3. Copy the repository (or `git clone`) and set `AGENTRUN_DIR` in `memlab_qwen7b.sbatch`.
4. Verify the `--gres` syntax printed by `scontrol show node <compute-node>` (the script assumes `gpu:1`), then `sbatch hpc/memlab_qwen7b.sbatch`.
5. Record the job id, `sacct -j <id> --format=JobID,JobName,Partition,State,Elapsed,AllocTRES,ExitCode`, and copy `raw_results/` back.

## What is unverified for that run

`scripts/memlab.py` talks to an OpenAI-compatible `/chat/completions` endpoint, and `run_ablation.py --base-url` points it at any such server. The batch script starts one (vLLM) on the node. Unverified: whether vLLM is installable on the cluster, and whether Qwen2.5-7B's tool calls are parsed by that server the way the Groq endpoint parses its models. The LoRA adapters would additionally need `--lora-modules` on the server.
