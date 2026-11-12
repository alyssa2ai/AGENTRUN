# Campaign 2 — Leakage Audit

## Background

The original AGENTRUN project reported 100% task success on 23 tasks. This was subsequently invalidated because the evaluation tasks overlapped with training data, meaning the model could recall answers rather than derive them through tool use.

Campaign 2 was specifically designed to prevent this. The eval2 split uses entirely new entities, prompts and expected values with automated verification.

## Audit pipeline

The leakage audit is implemented in `scripts/leakage_audit.py` and runs the following checks:

### 1. Benchmark integrity

| # | Check | What it verifies |
|---|---|---|
| 1 | `eval_file_matches_freeze` | The eval2.jsonl file matches the SHA-256 hash frozen before experiments |
| 2 | `prompts_match_freeze` | All task prompts match the frozen reference |
| 3 | `eval_regenerates_from_seed` | Running the benchmark generator with the same seed produces identical tasks |
| 4 | `harness_variants_match_freeze` | v1/v1r/v2 harness variants match their frozen definitions |

### 2. Entity isolation

| # | Check | What it verifies |
|---|---|---|
| 5 | `dev_eval_entities_disjoint` | No entity name appears in both dev and eval splits (664 distinct entities) |
| 6 | `eval2_entities_disjoint_from_first_eval_split` | eval2 entities are disjoint from the first eval split |
| 7 | `dev_eval_person_names_disjoint` | Person names are fully separated |
| 8 | `no_entity_shared_between_eval_tasks` | Each eval task uses unique entities |
| 9 | `eval_prompts_unique` | No two eval prompts are identical |
| 10 | `dev_eval_prompts_disjoint` | Dev and eval prompts are disjoint |
| 11 | `eval2_prompts_disjoint_from_first_eval_split` | eval2 prompts don't overlap with the first split |

### 3. Answer leakage prevention

| # | Check | What it verifies |
|---|---|---|
| 12 | `expected_values_absent_from_prompts` | No expected answer appears in any prompt |
| 13 | `expected_values_absent_from_system_prompt_and_schemas` | No expected answer in system prompt or tool definitions |
| 14 | `no_eval_entity_in_system_prompt_or_schemas` | No eval entity name in system-level text |
| 15 | `scenario_fixtures_consistent` | Scenario-specific fixtures don't contain cross-scenario leakage |

### 4. Training data isolation

| # | Check | What it verifies |
|---|---|---|
| 16 | `no_eval_entity_name_in_training_or_existing_benchmarks` | Eval entity names absent from all training data, legacy benchmarks, dev benchmarks, corpus data, and memory stores |
| 17 | `no_exact_or_template_match_with_training_and_legacy_prompts` | TF-IDF similarity between eval2 prompts and all 69 reference prompts never exceeds 0.80 (max observed: 0.142) |

### 5. Per-run integrity (applied to each completed ablation run)

| Check | What it verifies |
|---|---|
| `no_ground_truth_fields_in_any_message` | The model never sees the expected answer in any message |
| `provenance_and_reliability_fields_only_in_their_configs` | Provenance metadata only appears in configs D and E |
| `baseline_never_received_memory` | Config A runs never receive any memory content |
| `baseline_tools_never_returned_a_memory_only_answer` | Config A tool returns never contain memory-derived answers |
| `each_store_holds_exactly_its_own_task_records` | No cross-task contamination in memory stores |

## Results

**All 17 checks pass. All per-run integrity checks pass for all 4 main ablation runs (1,920 total runs verified).**

Files checked for training overlap:
- `training/training_data.jsonl`
- `training/training_data_augmented.jsonl`
- `eval/tasks.py`
- `benchmark_v2/dev.jsonl`
- `agentrun_v2/env/env_data/corpus.jsonl`
- `memory_store.json`

No hits on any entity name or prompt template.

## What the audit does NOT cover

1. **Pre-training contamination:** The audit cannot verify that Qwen model weights don't contain memorized knowledge that happens to match eval2 answers. This is mitigated by using novel entity names.
2. **Structural leakage:** The 6 scenarios have known structures. A model might learn "S4 tasks always ask for the newer value" from task structure alone. This would be a legitimate learned heuristic, not data leakage.
3. **Cross-task learning within a run:** Each task runs independently with a fresh context. The model cannot transfer information between tasks within a run.
