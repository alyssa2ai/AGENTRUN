# Experiment Log

## Overview

This log documents the progression of the AgentLab project from baseline evaluation through two rounds of QLoRA fine-tuning, failure analysis, and targeted intervention.

---

## Phase 1: Frontier Agent Baseline (historical context)

**What was built:** A production-grade multi-tool agent using Google Gemini 3.6 Flash as the LLM, with MCP (Model Context Protocol) for tool execution. Tools included calculator, word count, web search, and weather lookup.

**Purpose:** Established a high-capability baseline and the full agent infrastructure (MCP server, provider adapters, memory system).

> **Note:** The Phase 1 frontier agent code is present in this repository (agent.py with `gemini-3.6-flash`, `mcp_server.py`, `providers/`, etc.). It is retained for completeness but is not part of the QLoRA distillation experiment.

---

## Phase 2: Benchmark Infrastructure

**What was built:** A 23-task held-out evaluation benchmark (`eval/tasks.py`) with machine-checkable assertions for every task. Categories:

| Category | Tasks | Description |
|---|---|---|
| `math` | 3 | Basic arithmetic and order-of-operations |
| `text` | 1 | Word count |
| `weather` | 2 | Current weather lookup |
| `search` | 2 | Web search |
| `multi_tool` | 4 | Parallel tool use |
| `chained_reasoning` | 1 | Tool output → next tool input |
| `time_sensitive` | 1 | Current information (needs live search) |
| `no_tool_expected` | 2 | Direct answer, no tool needed |
| `adversarial_math` | 3 | Negative numbers, decimals, percentages |
| `adversarial_reasoning` | 2 | False premise, chained search→calc |
| `adversarial_error_handling` | 1 | Division by zero |
| `adversarial_ambiguity` | 1 | Ambiguous entity (Springfield) |

**Scoring harness:** `eval/harness.py` — checks `required_tools`, `numeric_check`, `answer_contains`, `answer_contains_any`, `expect_tool_error`.

---

## Phase 3: Base Model Evaluation

**Date:** 2026-09-01 15:55:51

**What was evaluated:** Qwen/Qwen2.5-7B-Instruct with no LoRA adapter, via Colab T4 GPU (4-bit quantization). MCP tools were executed locally by `ft_agent.py`; the model was hosted on Colab.

**Results: 22/23 = 95.7%**

| Task | Result |
|---|---|
| `adversarial_division_by_zero` | ❌ FAIL — model did not call calculator when asked to divide by zero; instead answered directly |
| All others | ✅ PASS |

**Observation:** The base model is already strong on most tasks. The single failure was on the adversarial division-by-zero task, where the model avoided calling the calculator tool when given a problem designed to produce a tool error.

---

## Phase 4: LoRA v1 Fine-Tuning

**Date:** 2026-09-01 18:01:23

**What was trained:** LoRA adapter on Qwen2.5-7B-Instruct using QLoRA (4-bit NF4 quantization). Training data: `training_data.jsonl` — 35 clean tool-use trajectories.

**Training:** `training/colab_train_7b.py` in Google Colab (T4 GPU, ~45 minutes). Adapter output: `/content/agentlab_qwen_lora_7b`.

**Serving:** `serving/colab_server.py` — Colab-hosted inference server with ngrok tunnel.

**Results: 18/23 = 78.3%** (regression of −17.4 pp vs. base)

| Task | Result | Failure Mode |
|---|---|---|
| `multi_wordcount_calc` | ❌ FAIL | `missing_required_tools:['calculator']` — used word count result but did not call calculator |
| `multi_three_tools` | ❌ FAIL | `hit_max_steps, numeric_mismatch` — exhausted steps before completing |
| `chain_weather_then_calc` | ❌ FAIL | `missing_required_tools:['calculator']` — called weather tool but not calculator |
| `adversarial_false_premise` | ❌ FAIL | `missing_expected_content_any` — did not reject the false premise |
| `adversarial_division_by_zero` | ❌ FAIL | Same as base — also did not call calculator |
| All others | ✅ PASS | |

**Analysis of v1 regression:**

The v1 model was trained on 35 trajectories. The regression was not random — it clustered in multi-step tasks:
- Tasks requiring tool chaining (word count → calculator, weather → calculator)
- Tasks requiring a second tool call after the first tool returned results
- The false-premise task, which required reasoning about fictional entities

---

## Phase 4.1: Diagnostic and Fix

### Finding 1: Tool-Call Parser Bug

The v1 Colab server (`serving/colab_server.py`) used a single-pass regex to extract `<tool_call>...</tool_call>` blocks from model output. When the fine-tuned model emitted malformed tool-call tags (missing closing tag before the next opening tag), the parser returned empty and the server treated it as a final answer.

**Evidence:** In `adversarial_chained_search_calc`, the model intended to call both `web_search` and `calculator`, but the parser silently dropped the first tool call due to malformed tags.

**Fix:** `serving/colab_server_v2.py` implements a two-pass parser:
1. **Pass 1 (strict):** Match properly closed `<tool_call>...</tool_call>` blocks
2. **Pass 2 (fallback):** If Pass 1 finds nothing, extract the first JSON object starting from the first `<tool_call>` opening tag

This handles the case where the model's output lacks a closing `</tool_call>` tag before the next `<tool_call>`.

### Finding 2: Training Data Gap Audit

Trajectory-level inspection of v1 failures revealed:

| Gap | Trajectories needed |
|---|---|
| word_count → calculator | 3 examples |
| get_weather → calculator | 3 examples |
| 3-tool chain + explicit final synthesis | 2 examples |
| Calculator error / division by zero | 2 examples |
| False-premise correction | 1 example |

**Total new trajectories:** 11 (audit identified 10 unique gaps, with one overlap)

---

## Phase 5: LoRA v2 Fine-Tuning

**Date:** 2026-09-01 (training run); evaluation 2026-09-01 22:32:05

**What was changed:**
1. Parser fix in `serving/colab_server_v2.py` (deployed for v2 evaluation)
2. Augmented training data: `training/training_data_augmented.jsonl` — 46 trajectories (35 original + 11 new)
3. Training-script memory settings: `colab_train_7b_v2.py` additionally enables gradient checkpointing, sets `use_cache=False`, and passes a paged 8-bit AdamW optimizer explicitly, so the 46-trajectory run fits the same 15 GB T4. `colab_train_7b.py` sets none of these and uses the Trainer default optimizer.

**What was NOT changed:**
- Base model: Qwen/Qwen2.5-7B-Instruct (identical)
- LoRA hyperparameters: identical (4-bit NF4, rank=16, alpha=16, attention-only)
- Learning rate, batch size, gradient accumulation, epochs, sequence length: identical
- Benchmark (identical 23 tasks, identical max_steps=3)
- MCP tool infrastructure (identical tools)

The optimizer/gradient-checkpointing difference is documented in
`docs/reproducibility.md` §4 and in `provenance/hyperparameters.md`. It does not
enter the V1→E4 comparison, because E4 reuses the V1 adapter, but it does mean the E4→V2
difference (+5 tasks) reflects the adapter, the training data, and these
optimizer settings changing together.

**Training:** `training/colab_train_7b_v2.py` in Google Colab. Adapter output: `/content/agentlab_qwen_lora_7b_v2`.

**Serving:** `serving/colab_server_v2.py` with corrected two-pass parser and v2 adapter.

**Results: 23/23 = 100.0%**

| Task | v1 | v2 |
|---|---|---|
| `multi_wordcount_calc` | ❌ | ✅ |
| `multi_three_tools` | ❌ | ✅ |
| `chain_weather_then_calc` | ❌ | ✅ |
| `adversarial_false_premise` | ❌ | ✅ |
| `adversarial_division_by_zero` | ❌ | ✅ |

---

## Summary of Results

| Model | Trajectories | Tasks | Passed | Accuracy |
|---|---|---|---|---|
| Base Qwen 7B | 0 (untuned) | 23 | 22 | 95.7% |
| LoRA v1 | 35 | 23 | 18 | 78.3% |
| LoRA v2 | 46 | 23 | 23 | **100.0%** |

**v1 → v2: +21.7 pp** (18/23 → 23/23)
**Base → v2: +4.3 pp** (22/23 → 23/23)

*(Table above is the Phase 5 state. The E4 condition was added later — see Phase 6 below — bringing the comparison to four conditions.)*

---

## Phase 6: E4 Controlled Ablation — Parser vs Data Effect

**Date:** 2026-09-16

**What was tested:** V1 LoRA adapter (35 trajectories, same weights as V1) evaluated with the V2 two-pass parser (same parser as V2). It was intended to isolate the parser effect from the data effect. *(Correction, 2026-10-09: in practice E4 also changed the evaluation client and tool stack. See the correction note below.)*

**Configuration:**
- Adapter: `agentlab_qwen_lora_7b` (V1; not re-trained)
- Parser: V2 two-pass robust parser (`serving/colab_server_e4.py`)
- Training data: `training/training_data.jsonl` (unchanged from V1)
- Tavily: real API key (active)
- Benchmark: `eval/tasks.py` — 23 tasks, max_steps=3, greedy decoding
- Hardware: Google Colab T4 GPU

**Result: 18/23 = 78.3%** — identical to V1 with the old parser.

**Per-task comparison (V1 → E4):**

| Task | V1 | E4 | Change |
|---|---|---|---|
| `adversarial_false_premise` | ❌ | ✅ | parser recovered |
| `multi_three_tools` | ❌ | ✅ | parser recovered |
| `multi_search_weather` | ✅ | ❌ | parser regressed |
| `adversarial_chained_search_calc` | ✅ | ❌ | parser regressed |
| `multi_wordcount_calc` | ❌ | ❌ | unchanged |
| `chain_weather_then_calc` | ❌ | ❌ | unchanged |
| `adversarial_division_by_zero` | ❌ | ❌ | unchanged |
| All others (16 tasks) | same | same | — |

**Decomposition:**

| Effect | Recovered | Regressed | Net |
|---|---|---|---|
| Parser + client (V1→E4) | 2 (`false_premise`, `multi_three_tools`) | 2 (`search_weather`, `chained_search_calc`) | **0** |
| Retraining run (E4→V2) | 5 (all E4 failures) | 0 | **+5** |

**Interpretation:** The V2 two-pass parser produced zero net aggregate improvement over the V1 single-pass parser when applied to the same V1 adapter. It recovered 2 tasks where the V1 parser silently dropped tool calls (false-premise rejection, 3-tool parallel calls) but introduced regressions on 2 other tasks where the V1 parser's incorrect behavior happened to produce a correct direct answer. The full +5 improvement from V1 to V2 therefore coincides with the retraining run that added the 11 targeted trajectories — along with that run's optimizer and gradient-checkpointing settings — rather than with a net parser-score gain.

**Correction (2026-10-09).** The interpretation above is the September reading and is kept for the record. Two parts of it do not survive a re-check of the artifacts:

1. *"Applied to the same V1 adapter" did not mean "only the parser changed".* The reported E4 score comes from a notebook-local evaluation loop (`notebooks/colab_e4_session.ipynb`, cell 16), not from `evaluation/run_eval_e4.py` and `ft_agent.py` with MCP. That loop used different tool schemas, a different tool-call/result serialization, its own tool implementations, and ran 15 days later against live data. The full table is in `docs/e4-experiment-guide.md`.
2. *"Tasks where the V1 parser silently dropped tool calls" is contradicted by the V1 traces.* In V1, `multi_three_tools` called all three tools and failed on `hit_max_steps`, and `adversarial_false_premise` called `web_search` and failed the content check. The two regressed tasks passed in V1 with all their tools called. E4 recorded no traces, so the mechanism behind each flip is unknown.

The defensible reading is narrower. With the V1 adapter fixed, changing the parser **and** the evaluation client left the aggregate at 18/23 while four task outcomes flipped. A client-matched E4 re-run has not been done.

**Files:**
- `serving/colab_server_e4.py` — Colab server (V1 adapter + V2 parser)
- `evaluation/run_eval_e4.py` — local eval script
- `results/eval_results_e4.json` — machine-readable results
- `results/eval_report_e4.md` — human-readable report
- `docs/e4-experiment-guide.md` — reproduction guide

---

## Phase 7: Repository Audit and Release Preparation (2026-10)

No new model runs were made in this phase. The changes were:

- The V1/V2 training-configuration description was corrected (optimizer, gradient checkpointing, `use_cache`), and the E4→V2 step is now labelled as confounded by these settings. See `provenance/hyperparameters.md`.
- CPU-only tests were added under `tests/` and run in CI. They recompute every reported score, the V1→E4 and E4→V2 transitions, the 35/46/11 trajectory counts, and prompt-level train/benchmark disjointness, and they pin the strength of each task's scoring predicate.
- **New disclosure.** Seven tasks check only that tools were called, and `no_tool_needed_2` has no positive check (`docs/benchmark.md`). Scores were not changed.
- **E4 re-examined.** The reported E4 score was produced by a notebook-local evaluation loop with a different tool stack, not by `evaluation/run_eval_e4.py`. The V1 traces also contradict the earlier parser-drop explanations. E4 is now described as an adapter-fixed comparison in which both the parser and the evaluation client changed. See the Phase 6 correction note and `docs/e4-experiment-guide.md`.
- Both training sets were regenerated from the committed scripts and matched byte for byte.
- `tools.py` calculator: `eval` was replaced with an equivalent AST evaluator that bounds exponents. Results are unchanged for all allowed inputs.
- Live ngrok and Tavily credentials were found in the committed notebook history. They are redacted from the current tree and need to be rotated (`docs/release-checklist.md`).
- The notebook moved to `notebooks/colab_e4_session.ipynb` and the research audit to `docs/research/`.

**Publication status (as of 2026-10-09).** The Zenodo preprint (doi:10.5281/zenodo.22346935, 2026-09-05) is published and predates E4. The updated manuscript in `publication/` has not been published. The WI-IAT submission was withdrawn on 2026-10-09.

---

## Key Takeaways

1. **Small training sets can cause regression.** 35 trajectories on a 7B model produced a weaker agent than the base model on multi-step tasks.

2. **Targeted augmentation coincided with the recovery.** The 11 added trajectories target the specific patterns V1 failed, and the run that included them (V2) recovered all five remaining failures. This is an observation on one benchmark, not a demonstration that data quality beats quantity — a size-matched random-augmentation control (E5) was never run.

3. **The evaluation set must stay fixed.** Using the same 23 tasks for all four evaluations (base, v1, E4, v2) kept the comparison controlled, and changing the benchmark between runs would have made it invalid. Fixed is not the same as held out, though. V1's failures on these tasks informed the V2 training data, so for V2 the benchmark is a development set as well as a test set (see `docs/benchmark.md`).

4. **The parser is part of the system.** The tool-call parser in the Colab server is a component of the inference system. A single-pass regex was fragile against the fine-tuned model's slightly different output patterns.

5. **Base model is strong.** Qwen2.5-7B-Instruct with no fine-tuning achieved 22/23, confirming that the base model already has strong instruction-following and tool-use capability. The LoRA fine-tuning aimed to specialize, not to wholesale create capability.
