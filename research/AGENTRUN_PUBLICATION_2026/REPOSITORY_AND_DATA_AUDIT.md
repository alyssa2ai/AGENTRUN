# Repository and data audit

**13 November 2026.** Every statement was checked in this session against git, the files on the laptop or the compute node. Builds on `DATA_INTEGRITY_REPORT.md` (previous session) and corrects it where noted.

## 1. Repository and commits

- Branch `research/memory-ablation-2026-11`, HEAD `dbedd58`; `main` at `d80b38a`. Nothing has been pushed from this branch.

| Commit | Content |
|---|---|
| `d80b38a` and earlier (main) | Thread 1: QLoRA fine-tuning study, 23-task benchmark, ANTIC 2026 submission package |
| `998e42e` | First memory study (48-task split, hosted + SIT HPC runs, retrieval-only benchmark) |
| `ca664fa` | Campaign 2 design, frozen eval2 split, harness variants, padded stores, v2-runner bridge (committed **before** any campaign-2 result) |
| `65cd860` | Another session's 15-report folder `AGENTRUN_DEEPENING_2026-11-12/` (later superseded) and the campaign-2 size-sweep and retrieval raw results |
| `4e9bab7` | Corrected campaign-2 analysis, `CORRECTIONS.md`, remaining raw results |
| `c14d6f2`, `dbedd58` | MITACS dossier and its generation sources |

- **Uncommitted, pre-existing (thread 1):** `agentrun_v2/`, `benchmark_v2/`, `docs/{abc_audit,annotation_guide,benchmark_v2,followup_status,related_work,research_protocol_v1}.md`, `scripts/`, `serving/colab_server_v3.py`, six test files, `.gitattributes`, and modifications to `.gitignore`, `README.md`, `requirements-dev.txt`. `.sealed/` is git-ignored. Not touched by this session.
- **Uncommitted, this audit:** `research/AGENTRUN_PUBLICATION_2026/` and the files copied into the study's `raw_results/` (section 4).

## 2. The two research threads

| | Thread 1: fine-tuning and evaluation validity | Thread 2: memory reliability |
|---|---|---|
| Period | Aug–Oct 2026 | 11–12 Nov 2026 |
| Evidence | 23-task benchmark (Base/V1/E4/V2), benchmark v2 (55 dev + 130 sealed), trace audit | 48-task split (campaign 1), 96-task eval2 (campaign 2) |
| Write-up | ANTIC 2026 submission (`publication/antic2026_submission/`), separate contribution | none yet |

They share code and a base model but answer different questions. This audit concerns thread 2. The only thread-1 evidence used here is the client-matched base-versus-adapter re-run, which was executed inside campaign 2.

## 3. Dataset inventory (thread 2)

All in `research/AGENTRUN_DEEPENING_2026-11-11/raw_results/`.

| Dataset | Split | Models | Runs | Format |
|---|---|---|---|---|
| `hpc_*_greedy_t1`, `hpc_*_temp07_*` | eval (48) | Qwen2.5-7B, Qwen3-8B, Qwen2.5-7B+V2 adapter; 3 sampled repeats | 6 × 240 = 1,440 | `runs.jsonl` + manifest + stores |
| `eval_*_t1` | eval (48) | gpt-oss-120b, gpt-oss-20b, qwen3.8-27b (hosted) | 358 written, 355 in complete blocks | same |
| `hpc_pilot_dev_*`, `dev_*` | dev (12) | development only | 60 + smoke runs | same |
| `hpc_retrieval_bench` | none (synthetic stores) | 4 retrievers | 96 result rows | `results.jsonl` |
| `c2_qwen25_{1p5b,3b,7b,14b}_{v1,v2}`, `c2_qwen3_8b_{v1,v2}` | eval2 (96) | 5 models × 2 harnesses | 10 × 480 = 4,800 | `runs.jsonl` + manifest + 384 stores |
| `c2_qwen25_7b_v2_{hash,bm25}_pad2000` | eval2, S1–S4, configs B/D/E | Qwen2.5-7B | 2 × 192 = 384 | `runs.jsonl` + manifest (padded stores are not written to disk by design) |
| `c2_legacy23_*` | original 23 tasks | base and V2 adapter | 10 × 23 = 230 | `scores.json` + `v2_log.jsonl` |
| `c2_v2dev55_*` | benchmark v2 dev (55) | base and V2 adapter | 4 × 55 = 220 | same |

Campaign 2 totals: **5,184 agent runs + 450 benchmark task evaluations**, now all with per-task data on the laptop.

## 4. Completeness and provenance checks (this session)

For each of the 12 campaign-2 agent datasets (`raw_results/c2_qwen*`):

| Check | Result |
|---|---|
| Every expected (task, configuration) pair present | yes, 0 missing |
| Duplicate (task, configuration) records | 0 |
| Manifests per dataset | exactly 1 (no resumed runs) |
| Benchmark hash in manifest = `FREEZE_eval2.json` (`42552d7b…`) | yes, all 12 |
| Prompt hash (`429fa001…`) and harness hash (`e714e871…`) | identical in all 12 |
| Decoding | temperature 0, seed 20261111, all 12 |
| Model snapshot recorded | yes: Qwen2.5-1.5B `989aa798…`, 3B `aa8e7253…`, 7B `a09a3545…`, 14B `cf98f3b3…`, Qwen3-8B `b968826d…` |
| API/generation errors logged | 3 (Qwen2.5-7B v1; handled by the harness's fixed notice); 0 elsewhere |

**Gap found and fixed.** The size-sweep datasets (1.5B, 3B, 14B) had no `stores/` folders on the laptop, because the session that copied them took only `runs.jsonl`, `manifest.jsonl` and `DONE`. The leakage audit silently skips the store-isolation check when a store file is missing, so that check had covered only the 7B and 8B runs. This session copied the 6 × 384 store files from `sit-gpu` (no existing file overwritten), re-ran the audit, and all 77 checks pass with store isolation now verified for all ten unpadded runs.

**Recovered.** `c2_v2dev55_adapter_b3` (adapter, v2-dev, budget 3) existed only on the cluster. It was copied and hash-checked (`scores.json` `edff47a8…`, `v2_log.jsonl` `934a51b4…`); it scores 51/55, matching the summary in the job log.

**Analysis reproducibility.** The previous session re-ran `scripts/analyze_c2.py` and the regenerated `tables/c2/C2_TABLES.md` was identical to the committed file apart from line endings. Independently, `research/AGENTRUN_MITACS_INTERVIEW_2026-11-12/build/verify_numbers.py` (code not shared with the analysis scripts) reproduces every headline figure (0 mismatches).

## 5. Campaign 2 job reconciliation (Slurm array 4148)

Evidence: `manifests/jobs_finished.tsv` on the cluster (and the copy in `hpc/from_cluster/manifests/`), Slurm logs `logs/hpc/c2-4148_*.{out,err}`, `hpc/campaign2.sbatch`.

| Index | Experiment | Evidence | Classification |
|---|---|---|---|
| 0–13 | 7B/8B v1+v2; base and adapter benchmark re-runs; 1.5B/3B/14B v1+v2; hash and BM25 padded runs | finish line with `exit=0` in `jobs_finished.tsv`; stdout/stderr logs; complete raw data | **completed** |
| 14 | dense retriever + 2,000 records | no finish line, no log file, no raw-result folder | **never dispatched** |
| 15–16 | harness v1r (repair turn only), 7B and 8B | same | **never dispatched** |
| 17–18 | V2 adapter on eval2, v1 and v2 | same | **never dispatched** |
| 19–20 | harness v2 at T = 0.7, seeds 1–2 | same | **never dispatched** |

"Never dispatched" rather than "failed": a started job writes its Slurm log at start, and none exists for 14–20. The array ran with concurrency `%2`; job 13 finished at 08:42 UTC, after which the controller became unreachable. Exact cause unknown.

## 6. HPC state (rechecked 13 Nov 2026, 10:45 UTC; read-only)

| Component | State |
|---|---|
| Login node `sitgpumaster` (192.168.192.11) | port 22 unreachable |
| Compute node `sit-gpu` (192.168.192.9) | reachable; up 52 days; load 0 |
| Slurm | `scontrol ping`: "Slurmctld(primary) at sitgpumaster is DOWN"; `squeue`: "Unable to contact slurm controller" |
| GPUs | `nvidia-smi` fails (NVML 580.178 mismatch); CUDA works via PyTorch 2.15.0+cu132 (2 × NVIDIA L40), verified by the previous session at 10:12 UTC |
| Workspace and backup | intact; backup `AGENTRUN_HPC/backups/c2_backup_20261112_120842/` with 5,336 files and `SHA256SUMS.txt` (previous session's count) |

No job was submitted, no service touched, no `sudo` used, and the unrelated BeyondSilence service was not disturbed. Running experiments directly on `sit-gpu` without Slurm would bypass the scheduler; this was not done.

## 7. Provenance limits

- Model weights were loaded from the cluster's Hugging Face cache by snapshot hash; weight files themselves were not re-hashed.
- The local runs used transformers 5.22.2, torch 2.15.0+cu132, bfloat16, greedy (`hpc/from_cluster/manifests/pip_freeze.txt`). Results may differ under other serving stacks; the 14B model's Thai output (see `STATISTICAL_AUDIT.md`) may be stack-specific.
- The hosted-model runs depend on an endpoint whose weights and serving can change; they cannot be reproduced exactly.
