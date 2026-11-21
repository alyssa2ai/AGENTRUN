# Overnight status: SIT HPC campaign

Written 2026-11-12 about 04:15 UTC (09:45 IST). **Every submitted experiment has finished. Nothing is running or pending on the cluster.**

## 1. Connection

```bash
ssh <user>@<cluster-login>
```

Key authentication works from the laptop (no password prompt). The alias `<cluster-login>` is still not defined in `C:\Users\Bhagya\.ssh\config`; the explicit address is used everywhere.

## 2. Remote workspace

`/home/<user>/AGENTRUN_HPC/20261111/`

| Path | Contents |
|---|---|
| `source/` | the 20 files needed for the experiment (hashes in `manifests/source_sha256.txt`), plus `adapters/repo_root_adapter/` |
| `environment/venv/` | project Python environment |
| `experiments/raw_results/` | one directory per run (`runs.jsonl`, `manifest.jsonl`, `stores/`, `DONE`) |
| `experiments/logs/` | Slurm stdout and stderr per job, `pip_install.log` |
| `scripts/` | the `.sbatch` files |
| `manifests/` | `jobs_submitted.tsv`, `jobs_finished.tsv`, `pip_freeze.txt`, `source_sha256.txt` |

Not transferred: `.env`, any API key, virtual environments, training data, the sealed benchmark, the 0.5B adapter, publication files. No existing directory on the cluster was modified. A local copy of the logs, manifests and scripts is in `hpc/from_cluster/`, and all raw results are in `raw_results/hpc_*` on the laptop.

## 3. Environment (verified on the compute node)

| Item | Value |
|---|---|
| Login node | `<cluster-login>`, Intel i7-14700, 15 GB RAM, no GPU (not used for compute) |
| Compute node | `<compute-node>`, 2 x Intel Xeon Gold 6542Y (96 logical CPUs), 503 GiB RAM of which 496 GiB available |
| GPUs | 2 x NVIDIA L40, 44.6 GiB visible to PyTorch each |
| Slurm | partition `gpu-nodes`, no time limit, `--gres=gpu:1` syntax, accounting disabled |
| Python | 3.12.3 (system), venv in user space, no `module`, no conda |
| Packages | torch 2.15.0 (CUDA 13.2 build), transformers 5.22.2, peft 0.21.2, accelerate 1.15.0, sentence-transformers 6.2.0, numpy 2.5.4, scipy 1.18.1, scikit-learn 1.9.1, rank-bm25 0.2.2; full list in `manifests/pip_freeze.txt` |
| Models (already in `~/.cache/huggingface`) | Qwen/Qwen2.5-7B-Instruct, Qwen/Qwen3-8B; downloaded by this study: all-MiniLM-L6-v2 and bge-small-en-v1.5 (small) |

Three things found on the cluster:

- **`InvalidAccount`**: the first job showed this pending reason for a few seconds and then ran. Accounting is disabled (`AccountingStorageType` is null, `AccountingStorageEnforce = none`), so no account or QOS is required, and earlier successful scripts on this account pass none. Nothing was changed.
- **`nvidia-smi` fails on the compute node** with "Driver/library version mismatch" (kernel module 580.173.02, user library 580.178.04). **CUDA itself works**: job 4134 ran a PyTorch matmul on the L40, and all inference jobs ran on GPU. The consequence is that GPU utilisation cannot be read with `nvidia-smi`; PyTorch's own memory counters were used instead. An administrator has to reload the driver or reboot the node to fix it.
- **`FreeMem=1983` in `scontrol`** is page cache accounting, not a shortage: `free -h` on the node shows 496 GiB available.
- **`sacct` does not work** ("Slurm accounting storage is disabled"). Finished jobs are recorded by the batch scripts themselves in `manifests/jobs_finished.tsv`.

## 4 and 5. Slurm jobs

| Job ID | What | Submitted (UTC) | Finished (UTC) | State | Exit |
|---|---|---|---|---|---|
| 4133 | diagnostic (hardware, tools, network) | 11-11 11:15 | 11:15 | COMPLETED | 0 |
| 4134 | CUDA probe (PyTorch on the L40) | 11-11 11:16 | 11:16 | COMPLETED | 0 |
| 4135 | pilot, dev split | 11-11 11:21 | 11:21 | FAILED | 1 |
| 4136 | pilot, dev split (retry) | 11-11 11:22 | 11:26 | COMPLETED | 0 |
| 4137 | retrieval at scale | 11-11 11:29 | 11:30 | FAILED | 1 |
| 4138_0 | ablation, Qwen2.5-7B-Instruct, greedy | 11-11 11:29 | 11:46 | COMPLETED | 0 |
| 4138_1 | ablation, Qwen3-8B, greedy | 11-11 11:29 | 11:49 | COMPLETED | 0 |
| 4138_2 | ablation, Qwen2.5-7B + repository adapter, greedy | 11-11 11:29 | 11:59 | COMPLETED | 0 |
| 4138_3 | ablation, Qwen2.5-7B, T=0.7, seed 1 | 11-11 11:29 | 12:06 | COMPLETED | 0 |
| 4138_4 | ablation, Qwen2.5-7B, T=0.7, seed 2 | 11-11 11:29 | 12:15 | COMPLETED | 0 |
| 4138_5 | ablation, Qwen3-8B, T=0.7, seed 1 | 11-11 11:29 | 12:25 | COMPLETED | 0 |
| 4144 | retrieval at scale (resubmitted after the fix) | 11-12 03:40 | 03:43 | COMPLETED | 0 |

The array ran two tasks at a time (`--array=0-5%2`), one GPU, 8 CPUs and 48 GB each. Total GPU time for the six ablation jobs: about 100 minutes.

## 6 and 7. Configurations and counts

| Run directory | Model | Decoding | Tasks x configs | Completed | Failed | Pending |
|---|---|---|---|---|---|---|
| `hpc_qwen25_7b_greedy_t1` | Qwen2.5-7B-Instruct | greedy | 48 x 5 | 240 | 0 | 0 |
| `hpc_qwen3_8b_greedy_t1` | Qwen3-8B | greedy | 48 x 5 | 240 | 0 | 0 |
| `hpc_qwen25_7b_lora_greedy_t1` | Qwen2.5-7B + adapter `e50e7661...` | greedy | 48 x 5 | 240 | 0 | 0 |
| `hpc_qwen25_7b_temp07_seed1` | Qwen2.5-7B-Instruct | T=0.7, seed 1 | 48 x 5 | 240 | 0 | 0 |
| `hpc_qwen25_7b_temp07_seed2` | Qwen2.5-7B-Instruct | T=0.7, seed 2 | 48 x 5 | 240 | 0 | 0 |
| `hpc_qwen3_8b_temp07_seed1` | Qwen3-8B | T=0.7, seed 1 | 48 x 5 | 240 | 0 | 0 |
| `hpc_pilot_dev_qwen25_7b_greedy` | Qwen2.5-7B-Instruct | greedy | 12 x 5 (dev) | 60 | 0 | 0 |
| `hpc_retrieval_bench` | 4 retrievers | - | 96 result rows | 96 | 0 | 0 |

"Completed" means the evaluation ran and was scored; it does not mean the agent answered correctly. Configurations A to E as in EXPERIMENT_PROTOCOL.md, all six scenarios.

## 8. Raw results

- Cluster: `/home/<user>/AGENTRUN_HPC/20261111/experiments/raw_results/<run>/`
- Laptop: `research/AGENTRUN_DEEPENING_2026-11-11/raw_results/<run>/` (copied 2026-11-12, verified 1,440 lines across the six run files)

## 9. Metrics available now

All of them: see RESULTS.md. Headline for the three greedy local runs (144 blocks): task success A 21.5%, B 45.8%, C 36.1%, D 53.5%, E 63.2%. Retrieval recall@4 of the repository's embedding: 0.46 at 2,000 records, 0.05 at 100,000. These are complete results, not preliminary. The hosted-model set (71 blocks) is truncated and is labelled so.

## 10. Failed jobs and exact errors

| Job | Error | Cause | Fix |
|---|---|---|---|
| 4135 | `OSError: We couldn't connect to 'https://huggingface.co' to load the files, and couldn't find them in the cached files.` | In offline mode the library could not resolve the model id through the cache's refs | `hf_client.py` now loads the cached snapshot directory directly; 4136 succeeded |
| 4137 | `IndexError: list index out of range` in `memlab._World.name` | The fixture's person-name pool (1,450 names) ran out when generating a 10,000-record store | `retrieval_bench.py` gives the generator a pool sized to the store; the 12 rows written before the crash are kept in `hpc_retrieval_bench_failed_job4137/` and are not used; 4144 reran everything |

The pilot (4135, 4136) used an existing environment on the cluster (`~/ErrorEcho/.venv`, read only) because the project environment was still installing. All evaluation jobs used the project environment.

## 11. Remaining experiments (not run)

1. Hosted-model runs to the full 48 blocks (needs a new day of quota; resumable).
2. A client-matched run of the 23-task legacy benchmark on the L40 (base and adapter). The legacy benchmark and its results were left untouched.
3. The sealed 130-task v2 benchmark: deliberately not run and not transferred.
4. A second model family on the L40 (Llama-3.1-8B is cached; its tool-call format needs a parser that does not exist in the repository).
5. A dense retriever inside the agent loop (the retrieval experiment shows the default one fails at scale; the ablation still uses the default).
6. Free-text memories without structured keys; a single wrong memory; memory written by the agent itself.
7. No fine-tuning was started.

## 12. Commands for tomorrow

Check the queue and what finished:

```bash
ssh <user>@<cluster-login> "squeue -u <user>; cat ~/AGENTRUN_HPC/20261111/manifests/jobs_finished.tsv"
```

Check that a run is complete (240 lines and a DONE file):

```bash
ssh <user>@<cluster-login> "cd ~/AGENTRUN_HPC/20261111/experiments/raw_results && wc -l hpc_q*/runs.jsonl && ls hpc_*/DONE"
```

Resubmit the array (safe: finished runs are skipped):

```bash
ssh <user>@<cluster-login> "cd ~/AGENTRUN_HPC/20261111 && sbatch scripts/ablation_array.sbatch"
```

Copy results back and re-analyse, from `research/AGENTRUN_DEEPENING_2026-11-11/scripts` on the laptop:

```bash
py -3.11 analyze.py --tag hpc_greedy ../raw_results/hpc_qwen25_7b_greedy_t1 ../raw_results/hpc_qwen3_8b_greedy_t1 ../raw_results/hpc_qwen25_7b_lora_greedy_t1
```

```bash
py -3.11 summarize_retrieval.py
```

`sacct` is unavailable on this cluster; use `scontrol show job <id>` within a few minutes of completion, or the two manifest files.

---

# Campaign 2 status (12 November 2026)

Slurm array **4148**, 21 jobs, `hpc/campaign2.sbatch` (copy on the cluster: `scripts/campaign2.sbatch`), plus a dev-split pilot array **4145** (4 jobs, all exit 0).

| Index | Run | Status |
|---|---|---|
| 0-3 | Qwen2.5-7B and Qwen3-8B, harness v1 and v2, eval2 | complete, exit 0 |
| 4-5 | legacy 23 and v2 dev 55, base and adapter, budgets 3 and 6, sampled repeats | complete, exit 0 |
| 6-11 | Qwen2.5 1.5B, 3B, 14B, harness v1 and v2 | complete, exit 0 |
| 12-13 | hash256 and BM25 with 2,000 background records | complete, exit 0 |
| 14-20 | dense retriever; v1r; adapter on eval2 (v1, v2); v2 at T=0.7 (seeds 1, 2) | **never dispatched** |

Jobs 0-13 ran 04:58 to 08:42 UTC. An earlier session observed at 12:08 UTC that the login node (which runs the Slurm controller) did not answer and that `squeue` on the compute node failed with "Unable to contact slurm controller"; it also reports a backup at `/home/<user>/AGENTRUN_HPC/backups/c2_backup_20261112_120842`. At 13:50 UTC neither cluster address answered from the laptop, so neither statement could be re-checked. All results of jobs 0-13 are on the laptop except the per-task log of one v2-dev run (adapter, budget 3), whose summary is in `logs/hpc/c2-4148_5.out`.

To finish the campaign once the controller is back (resumable; finished runs are skipped):

```bash
ssh <user>@<cluster-login> "squeue -u <user>; cd ~/AGENTRUN_HPC/20261111 && sbatch --array=14-20%2 scripts/campaign2.sbatch"
```

Then copy the new `c2_*` directories into `raw_results/` and run, from `scripts/`:

```bash
py -3.11 analyze_c2.py
```
