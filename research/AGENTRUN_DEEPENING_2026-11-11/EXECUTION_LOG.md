# Execution log

Times are UTC. IST = UTC + 5:30. Early times on 11 November are approximate.

## 2026-11-11

| Time | Action | Outcome |
|---|---|---|
| ~08:45 | Inspected the repository: `agent.py`, `ft_agent.py`, `memory.py`, `mcp_server.py`, `tools.py`, `agentrun_v2/`, `eval/`, `results/`, docs | Memory is a Python class used only by the Gemini agent; no runtime verification or provenance exists (ARCHITECTURE.md) |
| ~08:50 | Local environment check | Python 3.11 has pytest, numpy, scipy; no GPU, no Slurm, no local model; a Groq key is present in the environment |
| ~08:55 | `py -3.11 -m pytest` in the repository | 185 passed, 1 failed (`test_env_data_regenerates_byte_for_byte`, CRLF on Windows; pre-existing; writes to a temp dir only) |
| ~08:55 | `py -3.11 results/verify_results.py` | Base 22, V1 18, E4 18, V2 23 of 23; invariant true |
| ~09:00 | `ssh sitgpumaster` | Failed: the alias is not defined on this machine |
| 09:00-09:25 | Wrote `scripts/memlab.py`, `build_benchmark.py`, `run_ablation.py`, `tests/test_memlab.py`; built dev and eval splits | 9 tests pass |
| 09:05-09:25 | Three rounds of dev smoke runs on the hosted endpoint (`raw_results/dev_*`) | Found and fixed: final answer as a tool call rejected by the endpoint; "not found" retried six times; malformed and empty generations |
| 09:27 | Final freeze (`benchmark/FREEZE.json`); static leakage audit | 14 of 14 gates pass |
| 09:27 | Started three hosted eval runs | |
| 09:29-10:39 | PC suspended (all three runs paused together) | Keep-awake requested; runs resumed by themselves |
| 10:40-10:50 | Wrote `analyze.py`, `leakage_audit.py`, `lit_check.py`; arXiv related-work queries | Web search was unavailable in the session; the arXiv API was used instead |
| ~10:58-11:10 | All three hosted runs stopped | Daily token cap (200,000 per model): 35, 29 and 7 complete blocks. Organisation id redacted from the logs |
| ~11:10 | Hosted analysis and transcript audit | 71 blocks; audit passes |
| 11:14 | `ssh gpuuser12@192.168.192.11` (login supplied by the user) | Connected with key authentication |
| 11:15 | Created `/home/gpuuser12/AGENTRUN_HPC/20261111/`; job 4133 (diagnostic) | Completed. `InvalidAccount` shown briefly, then it ran; `nvidia-smi` broken on the node; 496 GiB RAM available |
| 11:16 | Job 4134 (CUDA probe using an existing environment, read only) | CUDA works on the L40 |
| 11:16-11:26 | Created the project venv; `pip install` on the login node | torch 2.15.0, transformers 5.22.2, peft 0.21.2 |
| 11:17-11:21 | Wrote `hf_client.py` and `retrieval_bench.py`; added `--backend hf` to the runner; transferred 20 source files and the adapter | Hashes in `manifests/source_sha256.txt` |
| 11:21 | Job 4135 (pilot, dev split) | Failed: offline model lookup. Fixed by loading the cached snapshot path |
| 11:22-11:26 | Job 4136 (pilot, dev split, Qwen2.5-7B) | Completed: 60 runs in 246 s |
| 11:29 | Submitted job 4137 (retrieval) and array 4138 (six ablation runs, two at a time) | The SSH session dropped right after submission; the jobs continued |
| 11:30 | Job 4137 | Failed after 12 rows: name pool exhausted for 10,000-record stores |
| 11:30-12:25 | Array 4138_0 to 4138_5 | All completed, exit 0, 240 runs each |

## 2026-11-12

| Time | Action | Outcome |
|---|---|---|
| 03:38 | Reconnected; checked queue and manifests | Queue empty; six ablation runs done; retrieval failed |
| 03:40-03:43 | Fixed `retrieval_bench.py`; moved the failed output aside; job 4144 | Completed, 96 rows |
| 03:45 | Copied raw results, logs, manifests and scripts to the laptop | 1,440 run lines verified |
| 03:50 | Leakage audit on nine runs | 3 failures, all false positives from empty result lists; gate corrected; 59 of 59 pass |
| 03:50-04:10 | `analyze.py` for `hpc_greedy`, `hpc_all` and the post hoc lenient re-score; `summarize_retrieval.py` | Tables and figures generated |
| 04:10-04:50 | Wrote RESULTS, FAILURE_ANALYSIS, LEAKAGE_AUDIT, OVERNIGHT_STATUS and the MITACS documents; updated protocol and reproducibility notes | |

## Changes to existing files

None. All new files are under `research/AGENTRUN_DEEPENING_2026-11-11/`. Nothing was committed or pushed. The real `memory_store.json` is unchanged (same SHA-256 before and after). On the cluster, only `/home/gpuuser12/AGENTRUN_HPC/` and two small embedding models in the Hugging Face cache were added.

## Mistakes made along the way, and how they were caught

- A command that would have stopped every Python process on the laptop was blocked by the permission system; only the two smoke-run processes started for this study were then stopped, by PID.
- Two patches to the analysis script were written with broken string escapes and left it unable to run until fixed; no table was produced by a broken script.
- The first copy of the cluster results was corrupted by a stray line in the stream and was redone.
- The first leakage audit of the HPC runs raised three false alarms (see above and LEAKAGE_AUDIT.md).
- The first retrieval job crashed on a fixture limit; its partial output is kept separately and not used.

## Not done

See OVERNIGHT_STATUS.md, section 11.

## 2026-11-12, campaign 2

| Time (UTC) | Action | Outcome |
|---|---|---|
| ~04:20 | Committed the first study on branch `research/memory-ablation-2026-11` (`998e42e`) | |
| 04:20-04:50 | Audit of the first study; wrote harness variants v1r and v2, padded stores, the v2-runner bridge, the eval2 builder; started downloading Qwen2.5 1.5B, 3B and 14B on the login node | frozen v1 harness and first eval split verified unchanged by hash |
| 04:45-04:58 | Pilot array 4145 on the dev split (v2 harness on two models, padded stores, legacy runner) | all exit 0; legacy pilot 21/23 |
| 04:54 | Froze eval2 (96 tasks); static leakage audit | 17/17 pass |
| 04:58 | Submitted campaign array 4148 (21 jobs, two at a time); committed the design before any result (`ca664fa`) | |
| 05:31-08:42 | Jobs 0-13 completed | all exit 0 |
| after 08:42 | Jobs 14-20 never dispatched | Slurm controller unreachable (observed 12:08 UTC by another session) |
| ~12:10 | Another session (not this one) pulled jobs 0-13, wrote `../AGENTRUN_DEEPENING_2026-11-12/` and committed `65cd860` | its numbers match; several interpretations and all three "examples" did not, see its CORRECTIONS.md |
| 13:50 | Cluster unreachable from the laptop (both addresses time out) | the remaining 7 jobs cannot be started from here |
| 13:50-15:30 | Removed byte-identical duplicate result folders and empty folders; re-ran the eval2 audit on all 12 agent runs (77/77); regenerated tables and figures; checked every interpretation against transcripts (`scripts/c2_breakdowns.py`); identified the repository adapter as V2 from its trainer state; wrote RESULTS_CAMPAIGN2, the MITACS brief, talking points and narrative check; marked the other session's folder as superseded | |
