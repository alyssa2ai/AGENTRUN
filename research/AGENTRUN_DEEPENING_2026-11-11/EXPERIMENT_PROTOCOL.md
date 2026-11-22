# Experiment protocol

Frozen on 2026-11-11 09:27 UTC (`benchmark/FREEZE.json`), before the first evaluation run. Everything in this file was fixed at that point except the section "Deviations", which records what happened afterwards.

## Design

A within-task (paired) ablation. Every evaluation task is run under all five configurations with the same model, system prompt, generation settings and tool permissions. The only things that differ between configurations are listed below.

| Config | Tools offered | `memory_search` returns | After a draft with status `answer` |
|---|---|---|---|
| A | calculator, registry_lookup, submit_answer | (tool not offered) | nothing |
| B | + memory_search | record text only | nothing |
| C | same as B | record text only | verifier call |
| D | same as B | text + record id + date + source | verifier call (sees the same fields) |
| E | same as B | D + a status per record computed in code (`unchallenged`, `current`, `superseded`, `conflicting`), and any stored record with the same entity and attribute is added to the result | verifier call (sees the same fields) |

Fixed for all configurations: temperature 0, seed 20261111, `max_tokens` 1200, at most 6 agent steps, top-4 retrieval with similarity threshold 0.2 (the threshold `memory.py` uses), one trial per (task, configuration, model).

### Memory store

`MemoryStore` in `scripts/memlab.py` uses the repository's own `memory.embed_text` and `memory.cosine_similarity`. Each (task, configuration) gets its own JSON file, written and then reloaded from disk before the agent runs, so the agent reads persisted state. Records carry `entity`, `attribute`, `value`, `recorded_on` and `source`; configurations B and C never show those fields to the model.

### Verifier

One extra call to the same model with no tools. It receives the question, every tool result the agent saw (verbatim, so with or without provenance depending on the configuration) and the draft. It returns `SUPPORTED`, `UNSUPPORTED` or `CONFLICT`. Policy: `UNSUPPORTED` turns the final answer into `abstain`; `CONFLICT` turns it into `conflict`. The verifier is only called when the draft status is `answer`, and it cannot repair an answer, only withdraw it.

### Reliability gate (config E)

For each retrieved record the store looks up all records with the same (entity, attribute). If they hold more than one value: records dated before the latest date are `superseded` when the latest record has a different value; records sharing the latest date with different values are `conflicting`. This is a last-write-wins rule plus a tie rule. It relies on clean keys, which the fixtures provide.

## Tasks

48 evaluation tasks, 8 per scenario, generated from seed 20261112 over fictional project names. 12 development tasks (seed 101, disjoint names) were used to debug the harness and the prompts.

| Scenario | What the fixture contains | Expected behaviour | Variants |
|---|---|---|---|
| S1 context loss | Two facts "told in an earlier session" exist only in memory, with 5 distractors. The question needs both and arithmetic. | answer (numeric) | budget per member (4), combined budget (4) |
| S2 relevant retrieval | 1 gold record among 11 others: 3 same project/other attribute, 4 other project/same attribute, 4 random | answer | six attribute types |
| S3 conflicting memory | Two records for the same fact, same date, different sources, different values, plus 5 distractors | `conflict` | - |
| S4 stale memory | An older and a newer record for the same fact, plus 5 distractors | answer = newer value | date written in the record text (4); date only in metadata (4) |
| S5 unsupported | The asked fact is nowhere. Near misses: same project/other attributes, other projects/same attribute | `abstain` | plain (4); question falsely presupposes an earlier session (4) |
| S6 tool failure | The fact is in the registry tool, which is scripted to fail | see variants | timeout then OK (2, answer); truncated JSON then OK (2, answer); always 503, nothing in memory (2, abstain); always 503, value in memory (2, answer) |

In S1 to S5 the registry returns "not found", so the only source is memory. For configuration A the expected behaviour is unchanged; A cannot succeed on S1 to S4 and is expected to abstain, which is scored as a miss, not as a harmful assertion.

## Answer format and scoring

The agent finishes by calling `submit_answer(status, value, evidence, note)` with status `answer`, `abstain` or `conflict` (a plain-text JSON object is also accepted). Scoring is programmatic (`memlab.classify`):

| Expected | Final status | Outcome |
|---|---|---|
| answer | answer, value matches (numbers within 0.011; text by normalised containment) | `correct` |
| answer | answer, equals the older value (S4) | `stale_value` (harmful) |
| answer | answer, other value | `wrong_value` (harmful) |
| answer | abstain | `over_abstain` (safe miss) |
| answer | conflict | `false_conflict` (safe miss) |
| abstain | abstain / answer / conflict | `correct` / `unsupported_claim` (harmful) / `false_conflict` |
| conflict | conflict / answer / abstain | `correct` / `arbitrary_pick` (harmful) / `over_abstain` |
| any | no parsable final answer | `format_error` |
| any | 6 steps used without a final answer | `max_steps` |

## Metrics

| Metric | Definition |
|---|---|
| Task success | share of runs with outcome `correct` |
| Harmful assertion rate | share of runs with outcome `wrong_value`, `stale_value`, `unsupported_claim` or `arbitrary_pick` |
| Safe miss | `over_abstain` or `false_conflict` |
| Conflict detection rate | S3 runs with final status `conflict` / S3 runs |
| Stale handling | S4 runs answering the newer value / S4 runs, by variant; `stale_value` counted separately |
| Unsupported claim rate | S5 runs with final status `answer` / S5 runs |
| Failure recovery rate | S6 timeout and truncated-JSON runs that end `correct` / those runs |
| Evidence-grounded answer rate | among final `answer`s, share whose value literally occurs in a tool result the agent received (memory, registry or calculator) |
| Verifier precision / recall | over drafts with status `answer`; positive = verifier rejects; truth = the draft was not `correct` |
| Retrieval recall@4, precision@4 | gold records in the top 4 of the agent's first `memory_search` / number of gold records; / 4. Also over the union of all queries. The query text is whatever the model wrote. |
| Tool selection | share of runs in which every tool the task needs was called |
| Tool execution | tool calls returning normally / all tool calls; injected failures and agent-caused errors counted separately |
| Efficiency | per task: end-to-end seconds and model seconds (rate-limit sleeping excluded), model calls, tool calls, prompt and completion tokens |
| Retrieval latency | measured offline with `perf_counter` (the in-run timer on Windows is too coarse) |
| API cost | **not reported**: the endpoint is a free tier and no price was verified |

## Statistics

- Unit of analysis: a (model, task) block with all five configurations complete.
- Rates: Wilson 95% intervals.
- Paired comparisons (B-A, C-B, D-C, E-D, E-B, E-A) on success and on harmful assertions: difference in percentage points, 95% bootstrap interval resampling tasks (5000 resamples; in the pooled analysis all models' results for a task are resampled together), exact McNemar test on discordant pairs, Holm correction over the six comparisons per metric.
- One trial per cell at temperature 0. Run-to-run variance is not measured.
- Scenario-level cells have 8 tasks per model. They are descriptive; no significance claim is made at that level.

## Models

| Model | Endpoint | Role |
|---|---|---|
| `qwen/qwen3.8-27b` | Groq, OpenAI-compatible chat completions | primary (closest available relative of the project's Qwen models) |
| `openai/gpt-oss-120b` | same, `reasoning_effort=low` | replication |
| `openai/gpt-oss-20b` | same, `reasoning_effort=low` | replication |

At the freeze no GPU was reachable, so the project's own Qwen2.5-7B models were not in the plan. They were added on the SIT HPC afterwards; see "Deviations and additions after the freeze".

## Changes made during development, before the freeze

All on the 12 development tasks; no evaluation task had been run.

1. The final answer moved from a plain-text JSON reply to a `submit_answer` tool, because `gpt-oss-120b` emitted its answer as a call to a non-existent tool and the endpoint rejected it (HTTP 400).
2. Rule 2 of the system prompt gained "a 'not found' result is a valid result; do not repeat that call", because `qwen3.8-27b` retried "not found" six times.
3. When the endpoint rejects a generation as a malformed tool call, or the model returns an empty message, the harness appends a fixed notice and lets the model continue. This costs one of the six steps and is the same in every configuration.
4. `max_tokens` raised from 700 to 1200 after an empty generation from `gpt-oss-20b`.

## Deviations and additions after the freeze

The tasks, prompts, tool schemas, configurations and scorer were not changed after the freeze (the prompt hash in every run manifest equals the frozen one).

1. **Hosted runs truncated.** The endpoint enforces 200,000 tokens per day per model, which was not visible in its headers. 71 of the planned 144 blocks finished (35, 29 and 7 per model). Tasks ran round-robin over scenarios, so the truncation is balanced.
2. **Local-model backend added (2026-11-11, after the hosted runs).** `scripts/hf_client.py` serves a Hugging Face model on the SIT HPC through the same `chat()` interface; tool calls are parsed from the raw generation with the repository's `agentrun_v2.parser`. A generation that contains a tool-call tag but does not parse gets the same fixed notice as a rejected generation on the hosted endpoint. `max_new_tokens` is 700 (hosted: 1200, which also had to cover hidden reasoning tokens).
3. **Models added:** Qwen2.5-7B-Instruct, Qwen3-8B, and Qwen2.5-7B-Instruct with the repository adapter merged, each greedy; plus sampled repeats (T=0.7) to measure run-to-run spread. These were chosen because they were already cached on the cluster and use the Hermes tool-call format the repository's parser reads.
4. **Raw generations logged.** `memlab.run_task` now stores `raw_text` and `parse_path` per model call when the backend provides them. Scoring is unaffected.
5. **Post hoc lenient re-score** (`scripts/lenient.py`, `analyze.py --lenient`): designed after seeing that local models often wrote a complete answer as plain text. Reported next to, never instead of, the strict score.
6. **Retrieval-at-scale experiment added** (`scripts/retrieval_bench.py`): no language model; stores of 2,000, 10,000 and 100,000 templated records, 300 queries each, 3 seeds; retrievers hash256 (repository default), BM25, all-MiniLM-L6-v2, bge-small-en-v1.5. Metrics: recall@k, precision@k, MRR@10, share of older/newer record pairs with both, only the older, only the newer or neither in the top k; index time, throughput, query latency.
7. **Audit gate corrected** for empty memory results (LEAKAGE_AUDIT.md).
8. The PC suspended for about 70 minutes during the hosted runs; three runs are excluded from timing rows only.
