# Reproducibility

All paths are relative to `research/AGENTRUN_DEEPENING_2026-11-11/` unless they start with the repository root.

## Environment actually used

| Item | Value |
|---|---|
| Machine (hosted-model runs, analysis) | Windows 11 laptop, CPU only |
| Python | 3.11.9 (`py -3.11`); the default `python` (3.14) lacks pytest and numpy |
| Packages used | requests, numpy, matplotlib, scikit-learn (leakage TF-IDF only), pytest |
| Model endpoint | Groq, `https://api.groq.com/openai/v1/chat/completions`, key from the `GROQ_API_KEY` environment variable (never written to disk by this study) |
| Endpoint limits observed | 1000 requests/day and 8000 tokens/minute per model (response headers) |
| Generation settings | temperature 0, seed 20261111, max_tokens 1200; `reasoning_effort=low` for the two gpt-oss models |
| GPU / Slurm | hosted-model runs: none. Local-model and retrieval runs: SIT HPC, see below |
| Repository commit | recorded per run in `raw_results/<run>/manifest.jsonl` (`git_commit`); the working tree has uncommitted files, including this directory |

## SIT HPC (used for the primary results)

Details, job IDs and exact errors are in OVERNIGHT_STATUS.md.

| Item | Value |
|---|---|
| Access | `ssh gpuuser12@192.168.192.11` (login node `sitgpumaster`); the SSH alias is not configured on the laptop |
| Compute node | `sit-gpu`: 2 x NVIDIA L40 (44.6 GiB each visible to PyTorch), 96 logical CPUs, 503 GiB RAM |
| Scheduler | Slurm, partition `gpu-nodes`, `--gres=gpu:1`, accounting disabled (`sacct` unavailable) |
| Workspace | `/home/gpuuser12/AGENTRUN_HPC/20261111/` |
| Environment | Python 3.12.3 venv; torch 2.15.0 (CUDA 13.2), transformers 5.22.2, peft 0.21.2, accelerate 1.15.0, sentence-transformers 6.2.0; `hpc/from_cluster/manifests/pip_freeze.txt` |
| Models | Qwen/Qwen2.5-7B-Instruct and Qwen/Qwen3-8B from the cluster's Hugging Face cache, bfloat16, loaded offline; adapter = repository root `adapter_model.safetensors` merged into the base |
| Decoding | greedy (primary) or sampling T=0.7, top-p 0.9, seeds 1 and 2; max 700 new tokens; thinking disabled in the chat template |
| Tool-call parsing | the repository's `agentrun_v2.parser` (`two-pass-v2+client-fallback`); raw generations are stored in every run record |
| Jobs | 4133, 4134 (diagnostics), 4136 (pilot), 4138_0 to 4138_5 (ablation array, 2 at a time), 4144 (retrieval); failed and superseded: 4135, 4137 |
| Known node issue | `nvidia-smi` fails with a driver/library version mismatch; CUDA works. GPU utilisation was therefore not recorded |

To rerun on the cluster (from the workspace root; both are resumable and skip finished work):

```bash
sbatch scripts/ablation_array.sbatch
```

```bash
sbatch scripts/retrieval_bench.sbatch
```

The batch scripts are in `hpc/from_cluster/scripts/`. `hpc/memlab_qwen7b.sbatch` and `hpc/README.md` are the earlier, unexecuted plan (it assumed a vLLM server) and are kept only as a record.

## Seeds and frozen inputs

| Thing | Value |
|---|---|
| Name pool seed | 20261111 (`memlab.NAME_SEED`) |
| Dev split | seed 101, 12 tasks, `benchmark/dev.jsonl` |
| Eval split | seed 20261112, 48 tasks, `benchmark/eval.jsonl` |
| Hashes | `benchmark/FREEZE.json` (eval file, prompts and configuration, `memlab.py`) |
| Bootstrap seed | 20261111 (`analyze.RNG_SEED`) |
| Model seed | 20261111 (sent with every request; the endpoint does not guarantee determinism) |

`run_ablation.py` refuses to run the eval split if the benchmark file or the prompt/configuration hash differs from the freeze.

## Commands

From the repository root, with `GROQ_API_KEY` set:

```bash
cd research/AGENTRUN_DEEPENING_2026-11-11/scripts
```

```bash
py -3.11 -m pytest ../tests -q -p no:cacheprovider
```

```bash
py -3.11 run_ablation.py --model qwen/qwen3.8-27b --split eval --run-id eval_qwen38_27b_t1
```

```bash
py -3.11 run_ablation.py --model openai/gpt-oss-120b --split eval --run-id eval_gptoss120b_t1
```

```bash
py -3.11 run_ablation.py --model openai/gpt-oss-20b --split eval --run-id eval_gptoss20b_t1
```

```bash
py -3.11 leakage_audit.py --runs ../raw_results/eval_qwen38_27b_t1 ../raw_results/eval_gptoss120b_t1 ../raw_results/eval_gptoss20b_t1
```

```bash
py -3.11 analyze.py ../raw_results/eval_qwen38_27b_t1 ../raw_results/eval_gptoss120b_t1 ../raw_results/eval_gptoss20b_t1
```

Local-model analyses (after copying `raw_results/hpc_*` from the cluster):

```bash
py -3.11 analyze.py --tag hpc_greedy ../raw_results/hpc_qwen25_7b_greedy_t1 ../raw_results/hpc_qwen3_8b_greedy_t1 ../raw_results/hpc_qwen25_7b_lora_greedy_t1
```

```bash
py -3.11 analyze.py --lenient --tag hpc_greedy_lenient_posthoc ../raw_results/hpc_qwen25_7b_greedy_t1 ../raw_results/hpc_qwen3_8b_greedy_t1 ../raw_results/hpc_qwen25_7b_lora_greedy_t1
```

```bash
py -3.11 summarize_retrieval.py
```

`tables/hpc_all/` is the same command with the three `temp07` run directories added.

A run resumes where it stopped: finished (task, configuration) pairs in `runs.jsonl` are skipped. To repeat a run from scratch use a new `--run-id`; existing run directories are never overwritten. Do not run `build_benchmark.py --force`: it would replace the freeze record.

## Outputs

| Path | Contents |
|---|---|
| `benchmark/` | dev and eval tasks, freeze record |
| `raw_results/<run-id>/runs.jsonl` | one line per (task, configuration): full message transcript, every tool call and observation, retrieved record ids, usage and latency per model call, draft, verifier output, final answer |
| `raw_results/<run-id>/manifest.jsonl` | model, settings, hashes, start time (one line per start or resume) |
| `raw_results/<run-id>/stores/` | the persisted memory file each run read |
| `raw_results/dev_*` | development smoke runs (kept; not part of any result) |
| `logs/` | console logs of every run, existing-test summary, arXiv query output |
| `tables/hpc_greedy/`, `tables/hpc_all/`, `tables/hpc_greedy_lenient_posthoc/`, `tables/RETRIEVAL_AT_SCALE.md` | the same tables for the SIT HPC runs; figures in `figures/hpc_*/` and `figures/fig4_retrieval_at_scale.png` |
| `hpc/from_cluster/` | Slurm logs, job manifests, batch scripts and package list copied from the cluster |
| `tables/` | `RESULTS_TABLES.md`, CSV tables, `per_run_scores.csv`, `summary.json`, `failure_examples.json`, `leakage_audit.json` |
| `figures/` | `fig1_success_by_scenario.png`, `fig2_outcome_composition.png`, `fig3_cost.png` |

## Known sources of non-reproducibility

- The hosted endpoint may change model weights or serving code; `seed` is best effort.
- One trial per cell: a rerun can differ on individual tasks.
- Latency depends on the endpoint's load. The PC suspended once during the run; affected runs are excluded from the timing rows only.
