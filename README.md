# AGENTRUN

**QLoRA fine-tuning of a tool-using 7B model on a fixed 23-task benchmark: a fine-tuning regression, an infrastructure ablation, and a failure-informed recovery.**

[![tests](https://github.com/alyssa2ai/AGENTRUN/actions/workflows/tests.yml/badge.svg)](https://github.com/alyssa2ai/AGENTRUN/actions/workflows/tests.yml)
[![DOI](https://zenodo.org/badge/DOI/10.5281/zenodo.22346935.svg)](https://doi.org/10.5281/zenodo.22346935)
[![License: MIT](https://img.shields.io/badge/code%20license-MIT-blue.svg)](LICENSE)

AGENTRUN fine-tunes `Qwen/Qwen2.5-7B-Instruct` with QLoRA on small sets of tool-use trajectories and evaluates it on a fixed, machine-scored, 23-task multi-tool benchmark. Tools run through the Model Context Protocol (MCP). The first adapter scored lower than the base model. We considered two candidate causes, a brittle serving-layer tool-call parser and gaps in training-data coverage, and ran an ablation (E4) that re-evaluated the first adapter behind the corrected parser.

**Research question.** When fine-tuning changes the benchmark score of a tool-using agent, how much of the change comes from the model and how much from the infrastructure around it? This project looks at one such component, the parser that extracts tool calls from model output.

## Key results

All four conditions use the same base model, the same 23 tasks, the same scoring function, greedy decoding, and a budget of `max_steps=3`. Each condition was run once (N=1), with no seeds and no confidence intervals. Base, V1, and V2 were run on 2026-09-01 through `ft_agent.py` and the MCP tool server. E4 was run on 2026-09-16 through an evaluation loop written inside the Colab notebook (see below).

| Condition | Adapter (training trajectories) | Parser | Passed | Accuracy |
|---|---|---|---:|---:|
| **Base** | none | single-pass | 22 / 23 | 95.7% |
| **V1** | V1 (35) | single-pass | 18 / 23 | 78.3% |
| **E4**† | V1 (35), unchanged | two-pass | 18 / 23 | 78.3% |
| **V2** | V2 (46 = 35 + 11 targeted) | two-pass | 23 / 23 | 100.0% |

† E4 also used a different evaluation client and tool stack, and ran on a different date (see below).

These two comparisons answer different questions and carry different evidential weight:

- **V1 → E4 (adapter fixed; parser and evaluation client changed).** The V1 adapter is held fixed and the server-side parser changes from single-pass to two-pass. The aggregate score does not move (18 → 18), but four tasks change outcome. Two are recovered (`adversarial_false_premise`, `multi_three_tools`) and two regress (`multi_search_weather`, `adversarial_chained_search_calc`). **This is not a parser-only comparison.** E4 was scored by a notebook-local loop that differs from the Base/V1/V2 client: it used shorter tool schemas, serialized tool calls and results differently, used its own tool implementations, and ran two weeks later against live search and weather data. The four flips therefore cannot be attributed to the parser alone. In the V1 traces, the two "recovered" tasks failed for non-parser reasons (step-budget exhaustion; missing false-premise wording). A client-matched re-run of E4 has not been performed ([details](docs/e4-experiment-guide.md#what-e4-did-and-did-not-hold-constant)).
- **E4 → V2 (iterative intervention, not a controlled ablation).** V2 adds 11 trajectories that were written **after inspecting V1's failures on this benchmark**. The V2 training run also added a paged 8-bit optimizer, gradient checkpointing, and `use_cache=False` ([details](provenance/hyperparameters.md)). All five remaining failures pass under V2. That is an observation about a failure-informed intervention. It is not an isolated data effect, and it is not evidence of generalization.

Base → V2 is a single task (22 → 23), because the base model was already near the ceiling. The 100% score should not be read as broad agent reliability or as state of the art.

The per-task matrix is in [`RESULTS_VERIFIED.md`](RESULTS_VERIFIED.md), which is regenerated from the raw result files by [`results/verify_results.py`](results/verify_results.py).

## Contributions

1. **A documented fine-tuning regression.** QLoRA on 35 trajectories took a 7B model from 22/23 to 18/23, and the per-task traces are released.
2. **An adapter-fixed infrastructure ablation (E4).** Changing the parser and the evaluation client, with the adapter held fixed, left the aggregate score unchanged but changed which tasks failed. This is a concrete case of aggregate scores hiding infrastructure effects. Separating the parser's share from the client's would need a re-run (not done).
3. **A transparent account of an iterative fix (V2).** It reports what was changed, why, and which confounds remain.
4. **Auditable artifacts.** These cover the benchmark definitions, both training sets (each regenerates byte-for-byte from the committed scripts), serving code, per-task results, a provenance record with VERIFIED / INFERRED / UNKNOWN labels, and CPU-only tests that recheck every reported number.

## Limitations

- **Small benchmark, N=1.** There are 23 tasks and one run per condition, so there are no variance estimates. A one-task difference is within plausible run-to-run noise. Search and weather tools query live services (Tavily, Open-Meteo), so re-runs will not see identical observations.
- **Evaluation-adaptation risk.** The 11 V2 trajectories were chosen after looking at V1 failures on these same 23 tasks. Their prompts are disjoint from the benchmark prompts (checked by `tests/test_benchmark_and_data.py`), but several share task templates and categories. For example, training has *"What is 25 divided by 0?"* and the benchmark has *"What is 50 divided by 0?"*. Prompt-level disjointness is not category-level independence, and neither one establishes generalization.
- **Confounded E4 → V2 step.** The V2 run changed the training data, the adapter, and the optimizer and memory settings together. No size-matched random-augmentation control (E5) was run.
- **Scoring strength varies by task.** All 23 tasks fail on step exhaustion or an unexpected tool error. Beyond that, 15 tasks check answer content, 7 check only that the required tools were called, and 1 (`no_tool_needed_2`) has no positive check. No task penalizes unnecessary tool calls. See [`docs/benchmark.md`](docs/benchmark.md).
- **Fixed step budget.** The budget of `max_steps=3` can penalize models that call tools sequentially rather than in parallel. Other budgets were not evaluated.
- **One model family, one decoding mode, no external benchmark.** No other base models, no sampling-based decoding, and no cross-benchmark evaluation (for example BFCL or ToolBench).
- **E4 is not client-matched and has outcomes only.** E4 was scored in the Colab notebook with a different evaluation loop and tool stack from Base, V1, and V2, and it recorded pass/fail per task but no traces or final answers. Another E4 run in the same notebook, made without a working search key, scored 13/23 (its search calls errored). The reported 18/23 is the run with the key working. The notebook shows both, but its execution order is ambiguous.

## Architecture

```text
  local machine                                     Google Colab (T4 GPU)
 ┌───────────────────────────────────────┐        ┌───────────────────────────────┐
 │ evaluation/run_eval_*.py              │  HTTPS │ serving/colab_server_*.py     │
 │   └─ eval/harness.py  (scoring)       │ (ngrok)│   Qwen2.5-7B-Instruct, 4-bit  │
 │   └─ ft_agent.py      (agent loop) ───┼───────►│   + LoRA adapter (V1 / V2)    │
 │         ▲   max_steps = 3             │◄───────┼── tool-call parser            │
 │         │                             │ text / │   (single-pass or two-pass)   │
 │         ▼                             │ calls  └───────────────────────────────┘
 │   mcp_server.py (MCP, stdio)          │
 │   calculator · word_count ·           │
 │   web_search (Tavily) · get_weather   │
 │   (Open-Meteo)                        │
 └───────────────────────────────────────┘
```

The model generates text on the Colab server, and the server's parser turns it into structured tool calls. The local client runs those calls through MCP and feeds the observations back, until the model gives a final answer or the step budget runs out. The model, the parser, the tool layer, the step budget, and the scorer are separate components. Base, V1, and V2 differ only in the adapter and the parser. E4 also replaces the client-side loop and tool layer (see [`docs/architecture.md`](docs/architecture.md)).

## Reproduction

**CPU-only checks (no GPU, model download, network, or API key needed):**

```bash
git clone https://github.com/alyssa2ai/AGENTRUN.git
cd AGENTRUN
python -m pip install -r requirements-dev.txt
python -m pytest                    # parser, scoring, benchmark, data, result-consistency tests
python results/verify_results.py    # recompute every reported score from results/*.json
```

**Full re-run (needs a GPU and external services):**

| Step | Requires | Entry point |
|---|---|---|
| Regenerate training data | CPU | `training/generate_dataset.py`, `training/augment_training_data.py` |
| Train V1 / V2 adapters | Colab T4 GPU, Hugging Face download | `training/colab_train_7b.py`, `training/colab_train_7b_v2.py` |
| Serve a condition | Colab T4 GPU, ngrok token | `serving/colab_server{,_base,_e4,_v2}.py` |
| Run the benchmark | live server URL, `TAVILY_API_KEY`, internet | `evaluation/run_eval_{base,finetuned,e4,v2}.py` |

No seeds were set in the original runs, and the search and weather observations are live. A re-run is a replication attempt, not a bit-exact reproduction. Report any difference from the committed results; do not overwrite them. Full procedure: [`docs/reproducibility.md`](docs/reproducibility.md).

## Repository map

| Path | Contents |
|---|---|
| [`eval/`](eval/) | Benchmark definitions (`tasks.py`) and scoring (`harness.py`). Frozen. |
| [`training/`](training/) | V1 (35) and V2 (46) training sets, generators, and Colab QLoRA scripts |
| [`serving/`](serving/) | Colab inference servers for Base, V1, E4, and V2, containing both parser variants |
| [`evaluation/`](evaluation/) | Benchmark runners and pairwise comparison |
| [`results/`](results/) | Per-task result JSON, reports, and the verification script |
| [`provenance/`](provenance/) | Machine-readable provenance, hyperparameters, and seed status |
| [`tests/`](tests/) | CPU-only tests (run in CI) |
| [`notebooks/`](notebooks/) | Colab session log for the E4 run (credentials redacted) |
| [`publication/`](publication/) | LaTeX manuscript, bibliography, and supplementary material |
| [`docs/`](docs/) | [Architecture](docs/architecture.md), [benchmark](docs/benchmark.md), [reproducibility](docs/reproducibility.md), [experiment log](docs/experiment-log.md), [project map](docs/project-map.md), [research audit (historical)](docs/research/2026-09_research_audit_and_roadmap.md) |

`agent.py`, `main.py`, and `memory.py` are the Phase 1 Gemini agent that preceded the Qwen experiments. They are not used by the four reported conditions.

## Publication status

- **Preprint (published):** L, Alyssa. *AGENTRUN: Failure-Driven QLoRA Specialization for Multi-Tool Agent Behavior in a 7B Language Model.* Zenodo, 5 September 2026. [doi:10.5281/zenodo.22346935](https://doi.org/10.5281/zenodo.22346935) (CC BY 4.0). This preprint is not peer reviewed. It **predates the E4 ablation** (16 September 2026), so it reports Base, V1, and V2 only.
- **Updated manuscript:** [`publication/manuscript.tex`](publication/manuscript.tex) (*Disentangling Parser and Data Effects in Tool-Using LLM Fine-Tuning*) adds E4. It has not been published or peer reviewed.
- **WI-IAT submission:** withdrawn on 9 October 2026. No submission is currently under review.

## Citation

Please cite the Zenodo preprint (see also [`CITATION.cff`](CITATION.cff)):

```bibtex
@misc{l2026agentrun,
  author       = {L, Alyssa},
  title        = {{AGENTRUN}: Failure-Driven {QLoRA} Specialization for Multi-Tool Agent Behavior in a {7B} Language Model},
  year         = {2026},
  publisher    = {Zenodo},
  doi          = {10.5281/zenodo.22346935},
  url          = {https://doi.org/10.5281/zenodo.22346935},
  note         = {Preprint}
}
```

## License and security

The code is under the [MIT License](LICENSE). The Zenodo preprint text is CC BY 4.0. No model weights are distributed; adapters can be reproduced with the training scripts. API keys belong in a local `.env` (see `.env.example`), which is git-ignored. See [`CONTRIBUTING.md`](CONTRIBUTING.md) for contribution and release guidelines.
