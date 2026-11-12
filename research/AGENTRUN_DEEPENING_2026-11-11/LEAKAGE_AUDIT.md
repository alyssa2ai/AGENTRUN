# Leakage and isolation audit

Automated by `scripts/leakage_audit.py`; machine-readable output in `tables/leakage_audit.json`, console log in `logs/leakage_audit.log`. Last run on 2026-11-12 over the benchmark files and all nine evaluation runs (three hosted, six on the SIT HPC): **59 gates, 59 pass, 0 hard failures.**

## Why this matters here

The project's earlier 100% result was invalidated by train/evaluation leakage. This study has three places where leakage could enter: the model's training data, the memory store (which is an explicit channel into the prompt), and the harness itself.

## Static checks on the benchmark (14 gates)

| Check | Result |
|---|---|
| `benchmark/eval.jsonl` matches the SHA-256 in `FREEZE.json` | pass |
| Prompts, tool schemas and configuration match the frozen hash | pass |
| The eval split regenerates byte-identically from its seed | pass |
| Dev and eval project names are disjoint | pass |
| Dev and eval person names are disjoint | pass |
| Dev and eval prompts are disjoint; eval prompts are unique | pass |
| No expected value (including the stale value and both conflict values) appears in any task prompt | pass |
| No expected text value appears in the system prompt, verifier prompt or tool schemas | pass |
| No eval project name appears in the system prompt or tool schemas | pass |
| Fixtures are consistent with their scenario: S5 has no record for the asked fact and no registry fact; S1-S4 have no registry fact; S6 has a memory record only in the fallback variant | pass |
| No project is shared between two eval tasks | pass |
| No eval project name occurs in `training/training_data.jsonl`, `training/training_data_augmented.jsonl`, `eval/tasks.py`, `benchmark_v2/dev.jsonl`, the v2 corpus, or the real `memory_store.json` | pass |
| No exact or number-normalised template match between eval prompts and the 35 + 11 training prompts and the 23 legacy prompts (repository's own `agentrun_v2.benchmark.leakage.check`); highest character TF-IDF cosine 0.153, threshold 0.80 | pass |

The last two rows cover the fine-tuned adapter: nothing it was trained on names an evaluation entity or resembles an evaluation prompt.

## Transcript checks on every raw run (5 gates x 9 runs)

| Check | Result |
|---|---|
| No message sent to the model contains a ground-truth field name (`expected`, `gold_record_ids`, `stale_value`, `conflict_values`, `needed_tools`) | pass, all runs |
| Record dates and ids appear in memory results only in D and E; reliability labels only in E | pass, all runs |
| Configuration A never received a memory result | pass, all runs |
| In configuration A, no tool result outside S6 contained an expected value (the baseline could not have been handed the answer) | pass, all runs |
| The persisted store of each (task, configuration) contains exactly that task's records and nothing else; A has no store | pass, all runs |

## Design measures

- **Ground truth isolation.** Only `task["prompt"]` is sent directly. Records reach the model only as `memory_search` results, registry facts only as `registry_lookup` results. The scorer runs after the conversation ends.
- **Memory isolation.** One store per (task, configuration), built from that task's fixture and reloaded from disk. No store is shared between tasks, configurations, models or splits. The project's real `memory_store.json` was neither read by the harness nor modified (SHA-256 `efbe8bd7...`, unchanged; file date 2026-08-23).
- **Development and evaluation separation.** Prompts were debugged on the 12 dev tasks only. The eval split was frozen at 2026-11-11 09:27 UTC, before the first eval run; `run_ablation.py` refuses to run if the hashes differ.
- **Parametric knowledge.** Project names and people are invented from a seeded syllable generator, so the answers cannot be known to the model.
- **Raw outputs kept.** Every transcript, tool observation, raw generation (local runs) and verifier output is in `raw_results/`.
- **No exclusions.** No evaluation task was removed. Hosted runs that could not finish because of the daily quota are excluded as whole blocks, balanced across scenarios, and counted in RESULTS.md.

## One audit error, found and fixed

The first audit of the HPC runs reported 3 failures of the provenance-isolation gate. Inspection showed four `memory_search` calls that returned an empty result list (`{"results": []}`) in configurations D and E; the gate expected a date field in every D/E result and an empty list has none. No field leaked. The gate now checks non-empty results only. The failing output is described here so the change is visible; the affected calls are in `eval-S6_tool_failure-02`.

## Remaining threats (not removed by the audit)

1. **The benchmark author knows the method.** The same assistant wrote the fixtures, the configurations and the scorer in one day. The scenarios were designed to exercise the components being tested.
2. **Template regularity.** All records come from six sentence templates. A model can learn the pattern within one conversation; this favours lexical retrieval and clean conflict detection.
3. **Clean keys.** The reliability gate reads `entity` and `attribute` fields stored with each record. Real memories do not come with keys.
4. **Prompt tuned on dev.** Two system-prompt rules were added after dev runs (see EXPERIMENT_PROTOCOL.md). The dev tasks share templates with the eval tasks, so the prompt is tuned to this task format, although not to any eval instance.
5. **Post hoc analyses.** The lenient re-score and the "runs that called memory" breakdown were designed after seeing results. Both are labelled.
6. **Existing sealed benchmark.** `E:\agentrun\.sealed\` (the 130-task v2 test split) is still inside the repository. This study did not open or copy it, and it was not transferred to the cluster.
7. **Earlier secret exposure.** Unrelated to this experiment, but still open: an ngrok token and two Tavily keys remain in public git history from before 2026-10 and should be rotated. No key was written to any file or log by this study; the endpoint's organisation id that appeared in an error message was redacted from the logs.

---

## Second evaluation split (eval2, 12 November)

`py -3.11 scripts/leakage_audit.py --split eval2 --runs <all 12 c2_qwen* runs>`; output in `tables/leakage_audit_eval2.json` and `logs/leakage_audit_eval2.log`. **77 of 77 checks pass**: the 14 static checks above applied to eval2, three further ones (eval2 entities and prompts disjoint from the first eval split; harness variants match their freeze hash), and the five transcript checks on each of the 12 agent runs. The padded-store runs keep no per-run store file, so the store-content check is skipped for those two runs.

eval2 was generated from a new seed with names from a disjoint third slice of the name pool and frozen at 2026-11-12 04:54 UTC, before any eval2 run. The revised harness (v2) was developed on the 12 dev tasks only. The sealed 130-task v2 test split was neither used nor copied to the cluster. The v2 dev split (55 tasks) used for the client-matched re-run is not gated by the research protocol and passes the repository's own leakage checks against the training data.
