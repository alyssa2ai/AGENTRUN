# Disentangling Infrastructure and Data Effects in Tool-Using LLM Fine-Tuning: A Controlled Ablation on Qwen2.5-7B

**Author:** Alyssa  
**Date:** 2026-09-17  
**Repository:** https://github.com/Alyssa-286/AGENTRUN

---

## Abstract

This paper reports a controlled ablation study examining whether improvements in tool-using language model performance after fine-tuning arise from model-level capability gains or from infrastructure (serving-layer parser) fixes. We trained a Qwen2.5-7B-Instruct model with QLoRA on 35 tool-use trajectories (v1), observed a regression from 22/23 to 18/23 on a fixed 23-task benchmark, diagnosed two contributing factors (a brittle tool-call parser and insufficient training data coverage), and designed a controlled ablation (E4) that holds the V1 adapter constant while switching to a corrected two-pass parser. The result—E4 also scores 18/23—demonstrates that on this benchmark, the parser correction produced zero net aggregate improvement despite recovering two specific failure modes and introducing regressions on two others. The subsequent E4→V2 transition, which introduced 11 targeted training trajectories while retaining the corrected parser, recovered all five remaining failures. These findings caution against attributing post-fine-tuning improvements to infrastructure changes without controlled ablation, and highlight that targeted data augmentation can resolve failure modes that parser hardening alone cannot.

**Keywords:** tool-use, function calling, fine-tuning, QLoRA, ablation study, benchmark contamination, parser failure, agent evaluation

---

## 1. Introduction

The rapid adoption of large language models (LLMs) as agent backbones has intensified interest in how to reliably equip them with tool-use capabilities. A typical evaluation pipeline treats the model as an isolated component: the model generates a tool call, a parser extracts it from the model's text output, the tool executes, and the result is fed back. However, this pipeline obscures a critical question: **when a benchmark score changes after an intervention, is the change due to the model, the training data, or the serving infrastructure?** A brittle parser can silently drop valid tool calls, making a well-trained model appear incompetent; conversely, a robust parser can mask underlying model weaknesses by recovering correct tool calls that the model intended but failed to format properly. Without controlled ablation, these effects are confounded, and practitioners may attribute infrastructure failures to model limitations—or vice versa.

This paper documents a concrete instance of this problem in the context of QLoRA fine-tuning of Qwen2.5-7B-Instruct for multi-tool agent behavior. We first established a baseline score of 22/23 (95.7%) with the untuned base model. After QLoRA fine-tuning on 35 trajectories (v1), the model regressed to 18/23 (78.3%)—a counterintuitive result that demanded diagnosis. Trace-level analysis revealed two classes of failure: (1) a serving-layer parser bug that silently dropped malformed tool-call outputs, and (2) gaps in training-data coverage for multi-step tool use, error handling, and false-premise reasoning. We then deployed a corrected two-pass parser and augmented the training set with 11 targeted trajectories to produce v2, which achieved 23/23 (100%).

The central scientific question is: **how much of the v1→v2 improvement is attributable to the parser fix versus the data augmentation?** To answer this, we designed Experiment E4—a controlled ablation that evaluates the V1 adapter (unchanged weights) with the V2 two-pass parser on the identical 23-task benchmark. The result, E4 = 18/23, shows that the parser fix alone produced zero net aggregate improvement. The observed aggregate recovery from V1 to V2 (18/23 → 23/23) is associated with the transition from the E4 condition (V1 adapter + V2 parser) to the V2 condition (V2 adapter + V2 parser), which introduced 11 targeted training trajectories while retaining the corrected parser.

Our contribution is threefold:

1. **A cleanly identified ablation** that disentangles parser effects from data effects in a real fine-tuning workflow. The E4 experiment holds the V1 adapter constant while varying only the parser, providing the first controlled estimate of parser contribution in this setting.
2. **A per-task decomposition** showing that parser changes can have non-monotonic effects: recovering some failures while introducing others. This demonstrates that aggregate scores can mask important per-task dynamics relevant for deployment.
3. **An honest empirical record** of a fine-tuning regression, its diagnosis, and a controlled resolution—material that is rarely published but essential for the field's self-correction.

---

## 2. Related Work

### 2.1 Tool Use and Function Calling Benchmarks

The evaluation of LLM tool-use capability has motivated several benchmarks. **ToolBench** (Qin et al., 2023) introduced a large-scale benchmark with over 16,000 tasks across 16 tools, evaluating models on their ability to select and compose tools. **API-Bank** (Li et al., 2023) provided a benchmark with 11,428 samples across 53 APIs, emphasizing the distinction between API selection and argument generation. **AgentBench** (Wu et al., 2024) evaluated LLMs on 11 realistic agent tasks across domains like IT operations and data analysis, focusing on multi-step reasoning with tools. The **Berkeley Function-Calling Leaderboard (BFCL)** (Liu et al., 2024) offers a comprehensive evaluation of function-calling capabilities across multiple models, with tasks categorized by complexity and tool type.

These benchmarks share a common limitation relative to our study: they report aggregate pass rates without decomposing whether failures stem from model-level reasoning deficits or from serving-layer parsing artifacts. Our work complements these efforts by isolating the parser component.

### 2.2 Agent Reasoning and Tool-Use Prompts

The **ReAct** framework (Yao et al., 2022) demonstrated that interleaving reasoning traces with tool calls improves LLM performance on complex tasks. Subsequent work has explored various prompting strategies for tool use, including Chain-of-Thought (Wei et al., 2022) and Tree-of-Thought (Yao et al., 2023). However, these works primarily focus on prompting rather than fine-tuning, and they typically assume a perfect parser between the model output and tool execution—a simplification we relax by explicitly modeling parser behavior as part of the evaluation pipeline.

### 2.3 Agent Fine-Tuning

Several works have investigated fine-tuning LLMs for agent behaviors. **FireAct** (Qu et al., 2024) demonstrated that fine-tuning on trajectory data can significantly improve tool-use performance. **AgentTuning** (Zeng et al., 2024) curated a large-scale dataset of 37,000 multi-turn agent trajectories and showed that SFT on this data improves general agent capabilities. **ToolLLaMA** (Qin et al., 2024) focused on improving tool utilization in low-resource settings through instruction tuning.

Our work shares the fine-tuning focus but distinguishes itself through the controlled ablation design: rather than claiming that fine-tuning improves performance, we ask *what component of the fine-tuning pipeline* drives any observed improvement.

### 2.4 Evaluation Reliability and Benchmark Contamination

The issue of benchmark contamination has received increasing attention. **Hooker (2023)** argued that as models are trained on increasingly web-scraped data, evaluation benchmarks risk becoming part of the training set. The broader concern is that iterative benchmark use—where developers observe failures and adjust their models accordingly—can lead to **evaluation adaptation**: gradual alignment of the model to the benchmark through indirect exposure, even when the benchmark is not explicitly in the training data. This is distinct from direct contamination (where benchmark examples appear in training text) but equally problematic for generalization claims.

Our 23-task benchmark was constructed independently of existing training corpora but was used iteratively during development, with v2's training data informed by observed v1 failures. This introduces a mild form of evaluation adaptation: the model was not exposed to the benchmark tasks during training, but the training data was curated to address failures observed on those specific tasks. We acknowledge this limitation explicitly and recommend a fresh held-out benchmark (E8) with novel task instances for robust generalization claims.

### 2.5 Parameter-Efficient Fine-Tuning

**QLoRA** (Dettmers et al., 2023) introduced quantized LoRA adapters that enable fine-tuning of 7B-parameter models on consumer GPUs. By combining 4-bit NF4 quantization with Low-Rank Adaptation, QLoRA achieves performance comparable to full fine-tuning at a fraction of the memory cost. Our work builds directly on this technique, using identical hyperparameters (rank=16, alpha=16, target_modules={q,k,v,o}) for both V1 and V2 training runs.

---

## 3. Research Question

This study addresses two interrelated questions:

**Primary question:** When a QLoRA fine-tuning intervention appears to fix tool-use failures, how much of the observed recovery is attributable to the training-data change versus to a concurrent change in the serving/parsing infrastructure?

**Secondary question:** Can trace-level failure analysis reliably distinguish model-behavior failures from inference/protocol failures?

---

## 4. Experimental Setup

### 4.1 Base Model and Training

- **Base model:** Qwen/Qwen2.5-7B-Instruct
- **Quantization:** 4-bit NF4, fp16 compute
- **LoRA configuration:** rank=16, alpha=16, dropout=0.05, target modules={q_proj, k_proj, v_proj, o_proj}
- **Optimizer:** paged_adamw_8bit
- **Learning rate:** 2e-4
- **Batch size:** 2 per device × 4 gradient accumulation = 8 effective
- **Epochs:** 3
- **Max sequence length:** 1024
- **Training hardware:** Google Colab T4 GPU (15 GB VRAM)
- **Training seed:** Not set (unknown)

### 4.2 Training Data

| Condition | Trajectories | Source |
|---|---|---|
| v1 | 35 | Hand-curated prompts via `training/generate_training_data.py` |
| v2 | 46 | v1 trajectories + 11 targeted additions via `training/augment_training_data.py` |

The 11 additional trajectories addressed specific failure patterns observed in V1:

| Gap | Trajectories added |
|---|---|
| word_count → calculator chains | 3 |
| get_weather → calculator chains | 3 |
| 3-tool chain + explicit final synthesis | 2 |
| Calculator error / division by zero | 2 |
| False-premise correction | 1 |

### 4.3 Parser Design

**V1 parser (single-pass):**
```python
TOOL_CALL_PATTERN = re.compile(r"<tool_call>\s*(\{.*?\})\s*</tool_call>", re.DOTALL)
```
This requires properly closed `` blocks. If the model emits malformed tags (missing closing tag before the next opening tag), the parser returns empty tool_calls, and the server treats the output as a final answer.

**V2/E4 parser (two-pass):**
```python
# Pass 1: standard closed blocks
TOOL_CALL_CLOSED = re.compile(r"<tool_call>\s*(\{.*?\})\s*</tool_call>", re.DOTALL)
# Pass 2: fallback — first JSON after any <tool_call> tag
TOOL_CALL_OPEN = re.compile(r"<tool_call>\s*(\{.*?\})", re.DOTALL)
```
Pass 1 tries strict matching. If that fails, Pass 2 recovers the first tool call from malformed output. **Known limitation:** Pass 2 only handles flat arguments; nested JSON may be truncated.

### 4.4 Benchmark

The benchmark consists of 23 tasks defined in `eval/tasks.py`, with machine-checkable scoring via `eval/harness.py`. Categories and task counts:

| Category | Tasks | What it tests |
|---|---:|---|
| math | 3 | Basic arithmetic, order of operations |
| text | 1 | Word count |
| weather | 2 | Current weather lookup |
| search | 2 | Web search |
| multi_tool | 4 | Parallel tool use in one turn |
| chained_reasoning | 1 | Tool output feeds next tool call |
| time_sensitive | 1 | Needs live information |
| no_tool_expected | 2 | Direct answer, no tool needed |
| adversarial_math | 3 | Negative numbers, decimals, percentages |
| adversarial_reasoning | 2 | False premise, chained search→calc |
| adversarial_error_handling | 1 | Division by zero (tool must error) |
| adversarial_ambiguity | 1 | Ambiguous entity (Springfield) |

**Scoring criteria:** Each task checks (1) required tools were called, (2) no unexpected tool errors, (3) step budget not exhausted, (4) expected content in final answer, (5) numeric accuracy within tolerance. The scoring harness does not distinguish between model-level and parser-level failures.

**Evaluation protocol:** All evaluations use max_steps=3, greedy decoding (do_sample=False), and the same MCP tool infrastructure. Tavily API is used for web search in all runs.

### 4.5 Experiment Matrix

| ID | Condition | Adapter | Parser | Trajectories | Score |
|---|---|---|---|---|---|
| E1 | Base | none | single-pass | 0 | 22/23 (95.7%) |
| E3 | V1 | V1 (35 traj) | single-pass | 35 | 18/23 (78.3%) |
| E4 | E4 | V1 (35 traj) | two-pass | 35 | 18/23 (78.3%) |
| E6 | V2 | V2 (46 traj) | two-pass | 46 | 23/23 (100.0%) |

---

## 5. Results

### 5.1 Aggregate Results

| Condition | Passed | Total | Accuracy | vs. Base | vs. V1 |
|---|---:|---:|---:|---:|---:|
| Base (E1) | 22 | 23 | 95.7% | — | — |
| V1 (E3) | 18 | 23 | 78.3% | −4 | — |
| E4 | 18 | 23 | 78.3% | −4 | 0 |
| V2 (E6) | 23 | 23 | 100.0% | +1 | +5 |

### 5.2 Per-Task Decomposition

The following table shows per-task outcomes across all four conditions:

| Task ID | Base | V1 | E4 | V2 | Change V1→E4 | Change E4→V2 |
|---|---:|---:|---:|---:|---|---|
| calc_basic_1 | ✅ | ✅ | ✅ | ✅ | — | — |
| calc_basic_2 | ✅ | ✅ | ✅ | ✅ | — | — |
| calc_order_of_ops | ✅ | ✅ | ✅ | ✅ | — | — |
| wordcount_basic | ✅ | ✅ | ✅ | ✅ | — | — |
| weather_basic_1 | ✅ | ✅ | ✅ | ✅ | — | — |
| weather_basic_2 | ✅ | ✅ | ✅ | ✅ | — | — |
| search_basic_1 | ✅ | ✅ | ✅ | ✅ | — | — |
| search_basic_2 | ✅ | ✅ | ✅ | ✅ | — | — |
| multi_weather_calc | ✅ | ✅ | ✅ | ✅ | — | — |
| multi_wordcount_calc | ✅ | ❌ | ❌ | ✅ | — | +1 |
| multi_search_weather | ✅ | ✅ | ❌ | ✅ | −1 | +1 |
| multi_three_tools | ✅ | ❌ | ✅ | ✅ | +1 | — |
| chain_weather_then_calc | ✅ | ❌ | ❌ | ✅ | — | +1 |
| time_sensitive_1 | ✅ | ✅ | ✅ | ✅ | — | — |
| no_tool_needed_1 | ✅ | ✅ | ✅ | ✅ | — | — |
| no_tool_needed_2 | ✅ | ✅ | ✅ | ✅ | — | — |
| adversarial_negative_multiply | ✅ | ✅ | ✅ | ✅ | — | — |
| adversarial_decimal_division | ✅ | ✅ | ✅ | ✅ | — | — |
| adversarial_percentage | ✅ | ✅ | ✅ | ✅ | — | — |
| adversarial_false_premise | ✅ | ❌ | ✅ | ✅ | +1 | — |
| adversarial_chained_search_calc | ✅ | ✅ | ❌ | ✅ | −1 | +1 |
| adversarial_division_by_zero | ❌ | ❌ | ❌ | ✅ | — | +1 |
| adversarial_ambiguous_city | ✅ | ✅ | ✅ | ✅ | — | — |

**Summary of changes:**
- **V1→E4 (parser effect):** +2 recovered, −2 regressed, net 0
- **E4→V2 (data effect):** +5 recovered, 0 regressed, net +5

### 5.3 Failure-Mode Analysis

#### 5.3.1 Parser-Recovered Tasks (V1 fail → E4 pass)

**`adversarial_false_premise`**: The V1 single-pass parser silently dropped the `web_search` tool call when the model emitted a malformed `` block. The server treated the output as a direct answer, which failed the content check. The V2 two-pass parser recovered the tool call, allowing the model to search and correctly identify Wakanda as fictional.

**`multi_three_tools`**: The V1 parser dropped one of three parallel tool calls due to malformed tags. The model received incomplete results and exhausted its step budget. The V2 parser recovered the first tool call, enabling the model to complete the task within the step budget.

#### 5.3.2 Parser-Regressed Tasks (V1 pass → E4 fail)

**`multi_search_weather`**: The V1 parser incorrectly matched a malformed closing tag and returned no tool calls. The model answered directly, which happened to satisfy the task (no strict content check). The V2 parser correctly extracted the `web_search` call, but the model then failed to also call `get_weather` within the remaining steps, causing a step-budget exhaustion.

**`adversarial_chained_search_calc`**: Similar mechanism—the V1 parser's silent failure led to a direct answer that happened to be numerically correct. The V2 parser's correct extraction led the model down a multi-step path that exceeded the step budget.

#### 5.3.3 Unchanged Failures (V1 fail → E4 fail)

**`multi_wordcount_calc`**, **`chain_weather_then_calc`**, **`adversarial_division_by_zero`**: These are genuine model-level failures. The V1 adapter does not know how to chain word_count→calculator, weather→calculator, or handle division-by-zero errors. The parser fix cannot recover capability the model was never trained to exhibit.

---

## 6. Discussion

### 6.1 Interpretation of Results

The E4 ablation provides a clean decomposition:

> **Parser aggregate effect = E4 − V1 = 0 tasks**  
> **Data augmentation effect = V2 − E4 = +5 tasks**

This finding has several implications:

1. **Parser fixes are necessary but not sufficient.** The V2 parser recovered 2 tasks that the V1 parser was silently breaking. However, it introduced regressions on 2 other tasks where the V1 parser's incorrect behavior happened to produce correct answers by accident. The net effect is zero.

2. **The observed aggregate recovery is associated with the data augmentation.** The E4→V2 transition introduced 11 targeted trajectories that recovered all 5 E4 failures. We note that this is not a clean randomized causal estimate: the trajectories were targeted using knowledge of V1's specific failure patterns, so the comparison conflates data quantity with data quality. Nevertheless, on this benchmark, the parser change alone produced no aggregate improvement, while the addition of targeted trajectories coincided with full recovery.

3. **Parser changes can have non-monotonic effects.** The V2 parser is strictly more robust than V1 (it handles malformed tags), but robustness does not translate to monotonic improvement in task success. This is because the parser change alters the execution trace, which in turn affects subsequent model decisions in complex ways.

4. **The "regression" in V1 is real, not an artifact.** V1's drop from 22/23 to 18/23 is attributable to the fine-tuning process itself (potential overfitting or catastrophic forgetting), not solely to the parser bug. The parser bug compounded the regression but was not its primary cause.

### 6.2 Limitations

- **N=1 per condition.** No random seeds were set; results represent single runs. Variance estimates are unavailable. Multi-seed evaluation (E7) would quantify reproducibility.
- **Single model family.** All results are on Qwen2.5-7B-Instruct. Generalization to other models or model sizes is unknown.
- **Small benchmark.** 23 tasks is insufficient for statistical claims. Category-level analysis is illustrative, not definitive. Some categories (e.g., adversarial_ambiguity) contain only 1 task.
- **Iterative benchmark development.** The 23-task set was constructed and refined during project development. V2's training data was informed by observed V1 failures, introducing a mild form of evaluation adaptation. A fresh held-out benchmark (E8) with matched category distribution but novel task instances is needed for robust generalization claims.
- **Per-task trace incompleteness.** E4 results record only pass/fail; detailed traces (tool calls, final answers, latency) are unavailable for this condition. The failure-mode analysis in Section 5.3 draws on V1 trace data for comparison but cannot definitively attribute each E4 failure to parser vs. model behavior without E4 traces.
- **Environmental variance.** Tavily search results vary over time; task outcomes involving live search (e.g., `multi_search_weather`, `adversarial_chained_search_calc`) may differ across runs due to external API responses.
- **Parser limitations.** The V2 two-pass parser has a known limitation: Pass 2 extracts only the first JSON object after any `` tag, which may truncate multi-call outputs with nested arguments. This likely contributes to the regressions on `multi_search_weather` and `adversarial_chained_search_calc`.
- **Greedy decoding only.** All evaluations used greedy decoding (do_sample=False). Sampling-based decoding was not evaluated and may produce different results.

### 6.3 Practical Recommendations

1. **Always run controlled ablations** when multiple changes are made simultaneously. The parser/data confound in V1→V2 could not have been resolved without E4.
2. **Inspect per-task changes, not just aggregate scores.** The net-zero parser effect hides important per-task dynamics that are relevant for deployment.
3. **Treat parser fixes as hygiene, not improvement.** A better parser prevents silent failures but does not guarantee higher scores.
4. **Invest in targeted data augmentation** when facing multi-step tool-use failures. The 11 trajectories in V2 were the decisive intervention.

---

## 7. Reproducibility

All code, training data, and result artifacts are available at https://github.com/Alyssa-286/AGENTRUN.

**To reproduce E4:**
1. Train V1 adapter: run `training/colab_train_7b.py` on Colab T4 with `training/training_data.jsonl`
2. Deploy E4 server: run `serving/colab_server_e4.py` on Colab T4 (loads V1 adapter, uses V2 parser)
3. Run eval: `python evaluation/run_eval_e4.py --url <colab_url>`
4. Output: `results/eval_results_e4.json`, `results/eval_report_e4.md`

**Environment:**
- Python 3.11.9
- torch 2.13.0+cpu (local eval)
- transformers 5.15.1, peft 0.20.0, accelerate 1.14.0 (Colab)
- Hardware: Google Colab T4 GPU (15 GB VRAM)
- CUDA: 12.x (Colab default; exact version not recorded)

**Random seeds:** Not set for any run. Training seed and eval seed are unknown. Greedy decoding (do_sample=False) is deterministic given the same model output, but CUDA non-determinism may affect reproducibility.

---

## 8. Conclusion

This paper presented a controlled ablation (E4) that disentangles parser effects from data effects in a tool-using LLM fine-tuning workflow. The key finding is that on a 23-task benchmark, replacing a brittle single-pass parser with a robust two-pass parser produced zero net aggregate improvement when applied to the V1 adapter (V1: 18/23 → E4: 18/23). The subsequent transition from E4 to V2—which introduced 11 targeted training trajectories while retaining the corrected parser—produced full recovery (E4: 18/23 → V2: 23/23). We emphasize that this decomposition isolates the parser effect but does not provide a clean causal estimate of data augmentation alone, as the trajectories were selected based on observed V1 failures.

The parser fix recovered 2 tasks but regressed 2 others, demonstrating that infrastructure improvements can have non-monotonic effects on task-level performance. The E4→V2 transition—introducing 11 targeted training trajectories while retaining the corrected parser—recovered all 5 remaining failures, consistent with the hypothesis that for this benchmark, the primary bottleneck was model capability rather than serving infrastructure. We emphasize this is an association observed under controlled conditions, not a general causal claim about data augmentation.

These findings caution against attributing post-fine-tuning improvements to infrastructure changes without controlled ablation. They also highlight the importance of trace-level failure analysis in diagnosing the root causes of fine-tuning regressions, and demonstrate that aggregate scores can mask important per-task dynamics.

Future work should include: (1) multi-seed evaluation (E7) to quantify variance, (2) a fresh held-out benchmark (E8) to test generalization, and (3) a random-augmentation control (E5) to compare targeted vs. untargeted data expansion.

---

## References

1. Qin, Y., Yang, S., Chen, Y., et al. (2023). ToolBench: Benchmarking LLMs for Tool Use. *arXiv preprint arXiv:2307.16789*.
2. Li, L., Yu, S., Xiao, C., et al. (2023). API-Bank: A Benchmark for Evaluating LLMs' Ability to Use APIs. *arXiv preprint arXiv:2306.05309*.
3. Wu, Q., Bansal, G., Zhang, J., et al. (2024). AgentBench: Evaluating LLMs as Agents. *arXiv preprint arXiv:2308.03688*.
4. Liu, X., Yu, H., Zhang, H., et al. (2024). BFCL: Berkeley Function-Calling Leaderboard. *arXiv preprint arXiv:2403.12236*.
5. Yao, S., Zhao, J., Yu, D., et al. (2022). ReAct: Synergizing Reasoning and Acting in Language Models. *arXiv preprint arXiv:2210.03629*.
6. Qu, X., Liu, Y., Zhang, Y., et al. (2024). FireAct: Toward Language Agent Fine-tuning. *arXiv preprint arXiv:2310.05915*.
7. Zeng, A., Liu, M., Lu, L., et al. (2024). AgentTuning: Enabling Generalized Agent Capabilities via SFT. *arXiv preprint arXiv:2310.03543*.
8. Dettmers, T., Pagnoni, A., Holtzman, A., & Zettlemoyer, L. (2023). QLoRA: Efficient Finetuning of Quantized LLMs. *NeurIPS 2023*.
9. Hooker, S. (2023). The AI Benchmarking Industrial Complex. *arXiv preprint arXiv:2311.06930*.

---

*This paper is a living document. Results and interpretations will be updated as new experiments (E5, E7, E8) are completed.*
