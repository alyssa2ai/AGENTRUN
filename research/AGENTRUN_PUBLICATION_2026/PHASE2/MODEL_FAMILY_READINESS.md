# Second model family: readiness

**14 November 2026.** Raw outputs: `raw/smoke/`. Job log: `logs/smoke_family_4183.*`. Script: `scripts/model_smoke.py`. Adapter: `evarb/clients.py`.

## 1. Correction to Phase 1

Phase 1 (`PHASE1_FINAL_REPORT.md` §8) reported the cached Llama snapshots as **incomplete** ("8.9 MB and 5.3 GB"). **That was wrong.** The snapshot directories contain symbolic links into the shared `hub/blobs/` store, so `du` on the model directory measured only the links.

Followed with `ls -lL`, the shards add up to exactly each index's `total_size`, plus about 30 KB of safetensors headers:

| Model | Snapshot | Shards | Sum of shards | Index `total_size` |
|---|---|---|---|---|
| Llama-3.1-8B-Instruct | `0e9e39f2…` | 4 | 16,060,556,376 B | 16,060,522,496 B |
| Llama-3.2-3B-Instruct | `0cb88a4f…` | 2 | 6,425,529,048 B | 6,425,499,648 B |

**No download was needed or made.** The Phase 1 documents are left as committed; this file is the correction.

## 2. Checks before selection

| Check | Result |
|---|---|
| Available checkpoints | Qwen2.5 1.5B / 3B / 7B / 14B, Qwen3-8B, Llama-3.2-3B, Llama-3.1-8B; also DeepSeek-Coder-V2-Lite, a code model not suited to this harness |
| Disk | `/home` 3.5 TB, 89% used, 399 GB free. Nothing is added by this phase |
| L40 compatibility / VRAM | bf16 on one L40 (44.6 GiB usable). Peak allocated: Llama-3.2-3B 6.2 GiB, Llama-3.1-8B 15.5 GiB, Qwen2.5-3B 5.9 GiB. Load 5–20 s from the NFS cache |
| Software | torch 2.15.0+cu132, transformers 5.22.2 (cluster venv). `nvidia-smi` still fails (NVML mismatch); CUDA works through PyTorch |
| Licence | Llama 3.1 / 3.2 Community License: research use permitted. The checkpoints were already in the user's cache; licence acceptance happened when they were downloaded, outside this session |
| Chat template | Llama tool calls are `{"name": …, "parameters": …}` (optionally after `<|python_tag|>`, ended by `<|eom_id|>`). The template **rejects** an assistant turn with more than one tool call |

## 3. Adapter

`evarb/clients.FamilyClient` subclasses the frozen `HFClient` without changing it:
- it re-parses Llama JSON calls when the frozen parser finds none, logged as `parse_path = family_llama_json`;
- it splits multi-call assistant turns into consecutive call/result pairs when building the prompt;
- it strips `<|eom_id|>` and `<|python_tag|>` from text replies;
- it is a no-op for Qwen (0 re-parses on the Qwen control).

Unit tests are in `tests/test_clients.py`.

## 4. Minimal load and inference test

Slurm job 4183, one GPU, 4 minutes. Each model ran the first 10 p1dev tasks (Phase 1 development split) under configs B and G with the unchanged Phase 1 loop: 20 runs per model.

| Model | Turns | Frozen parser alone | With adapter: parsed tool call or submission | Readiness (≥ 95%) | Outcomes (20 runs) |
|---|---|---|---|---|---|
| Qwen2.5-3B (control) | 71 | 69 tool calls | **97.2%** | pass | 11 correct, 6 false conflict, 2 wrong value, 1 step limit |
| **Llama-3.1-8B** | 99 | **0** | **96.0%** | **pass** | 3 correct, 10 over-abstain, 3 step limit, 2 format error, 2 false conflict |
| Llama-3.2-3B | 98 | **0** | 85.7% | **fail** | 8 correct, 12 over-abstain |

**Why the unparsed turns fail.** They are not parser misses: they are plain-text narration with no call, for example "Since the registry lookup did not return a result, we will search memory.<|eom_id|>". The v2 harness's single repair notice handles some of them.

**Llama over-abstains on these tasks.** Llama-3.2-3B also called the calculator with invented operands before retrieving anything. This is model behaviour in an unchanged harness, and Phase 3 measures it rather than tuning it away.

## 5. Decision

- **Llama-3.1-8B-Instruct is the second-family model.** It passes the readiness criterion and is in the Phase 3 design (`PHASE3_EXECUTION_PLAN.md`).
- **Llama-3.2-3B-Instruct is included as a format-limited condition.** It misses the 95% criterion. Its format errors and over-abstentions are reported separately, and its results are not pooled with the other models.
- **Qwen3-8B** is the same vendor as Qwen2.5 (a different generation). It is reported as Qwen, **not** as a second family.

**Limitation.** One second family with two sizes is the minimum for a cross-family claim. Generalisation beyond Qwen and Llama is not tested. Gemma and Mistral would need a download (gated licences) and a further adapter check.
