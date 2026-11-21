# AGENTRUN

**Two studies on tool-using language-model agents: a QLoRA fine-tuning ablation on a 23-task benchmark (2026-09),
and a pre-registered evaluation of evidence-basis arbitration for conflicting persistent memory (2026-11).**

[![tests](https://github.com/alyssa2ai/AGENTRUN/actions/workflows/tests.yml/badge.svg)](https://github.com/alyssa2ai/AGENTRUN/actions/workflows/tests.yml)
[![DOI](https://zenodo.org/badge/DOI/10.5281/zenodo.22346935.svg)](https://doi.org/10.5281/zenodo.22346935)
[![License: MIT](https://img.shields.io/badge/code%20license-MIT-blue.svg)](LICENSE)

| | Study 1 — QLoRA specialization | Study 2 — persistent-memory reliability |
|---|---|---|
| Question | how much of a fine-tuning score change comes from the model and how much from the infrastructure around it | does arbitration that states its *evidence basis*, and enforces only what that basis supports, improve reliability — and can indiscriminate enforcement increase harmful answers |
| Design | 4 conditions, 23 tasks, N=1 per condition, no seeds | pre-registered; 18 model x decoding cells, 12 conditions, 268 sealed tasks, 57,888 runs |
| Status | preprint on Zenodo (not peer reviewed); updated manuscript unpublished | manuscript complete, **not submitted anywhere**, not peer reviewed |
| Where | this repository root (`eval/`, `training/`, `serving/`, `evaluation/`, `results/`) | [`research/AGENTRUN_PUBLICATION_2026/`](research/AGENTRUN_PUBLICATION_2026/) |

The two studies share a name and a repository, and nothing else: different question, different models, different
benchmark, different method, different code. Results from one are never pooled with the other. Study 1 remains
exactly as published; Study 2 was added in November 2026.

---

# Study 1 — QLoRA specialization for multi-tool use

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

---

# Study 2 — Evidence-basis arbitration for conflicting persistent memory

**An agent with persistent memory will eventually read two records that disagree.** The common remedy — label
records by reliability from their metadata, and enforce those labels at the terminal action — can make small
models *worse*. This study tests an alternative: an arbiter that reports the **evidence basis** for each
resolution (an explicit correction naming the rival value, a stated validity date, the record date, an
authoritative source, a genuine contradiction, or insufficient evidence) and a **strength**, with the policy
enforcing only resolutions of strong strength.

Everything was frozen before the data existed: the mechanism (14 November 2026), the evaluation set
(16 November), and the analysis and hypotheses (17 November). Every job re-verified all three hashes at start.

## Scale

| | |
|---|---|
| Models | 4 primary (3B–8B, two families) + 2 secondary, all open-weight |
| Cells | 18 (model x decoding), 12 conditions each |
| Tasks | 268 sealed, in 135 families |
| Runs | **57,888**, with 0 missing pairs, 0 duplicates and 0 harness errors |
| Inference | family-clustered sign-flip permutation, 100,000 seeded draws; Holm over four contrasts |

## Pre-registered results

All four contrasts are supported. Differences are percentage points of task success, pooled over the four primary
models (51,456 runs), with 95% family-bootstrap intervals.

| Hypothesis | Contrast | Difference | 95% CI | Holm-adjusted *p* | Verdict |
|---|---|---:|---|---:|---|
| H-primary | EBG − RT | **+17.1** | [12.2, 22.1] | 4×10⁻⁵ | supported |
| S1 | EBG − T | +14.5 | [10.5, 18.6] | 4×10⁻⁵ | supported |
| S2 | EBG − LG | +15.9 | [10.4, 21.2] | 4×10⁻⁵ | supported |
| S3 | EBG − B | +15.3 | [10.3, 20.5] | 4×10⁻⁵ | supported |
| S4 | EBG − RT, harmful | −19.4 | [−24.6, −14.6] | — | **not falsified** |

Harmful answers fell from 22.6% to 3.1%; arbitrary picks from 252 runs to 13. An independent re-implementation
recomputed the 60 model × condition counts and the four effect sizes and agrees exactly.

## Three results that cut against the proposed design

These are reported as prominently as the supportive ones, because together they locate the contribution more
precisely than the headline contrasts do.

1. **Gating costs accuracy.** Enforcing *every* arbitration rather than only strong ones scored **9.7 pp higher**
   (71.1% against 61.3%) while more than doubling the harmful rate (6.9% against 3.1%) and raising false
   resolution from 1.9% to 12.9%. Gating is a trade, not a dominance, and this benchmark does not price it.
2. **Most of the benefit is in the labels, not the enforcement.** Evidence-basis labels with no enforcement at all
   are worth +11.8 pp over metadata labels; gating adds a further +6.0 pp.
3. **Enforcement inherits the reliability of its labels.** The same gating driven by an LLM arbiter gave no
   success gain and 8.1 pp *more* harm, with 37.0% false resolution — worse than no mechanism at all.

The best condition still answers only 61.3% of tasks correctly, and its residual failure is over-conservatism
(20.2% false conflicts, 11.5% unnecessary abstentions) rather than harm. Effects also differ by model family: the
Llama models gain by converting abstentions into answers rather than harmful answers into correct ones, so the
harm-reduction claim is demonstrated on the models that actually produce harm.

## Deviations, disclosed

An unplanned compute-node reboot changed the host kernel and GPU driver partway through two of the eighteen cells,
affecting 980 of 57,888 rows (1.69%). Removing the affected cell moves the pooled estimates by at most 0.1 pp —
but no task and condition was run on both platforms, so **whether the driver change altered generation is unknown
and not knowable from this campaign**, and the paper says so. The full ledger, the forensic record and a
reporting-only platform-continuity check are in
[`PHASE3/PHASE3_DEVIATIONS.md`](research/AGENTRUN_PUBLICATION_2026/PHASE3/PHASE3_DEVIATIONS.md).

## Where things are

| Path | Contents |
|---|---|
| [`PHASE2/`](research/AGENTRUN_PUBLICATION_2026/PHASE2/) | the frozen mechanism (`evarb/`), the runner and analysis scripts, the benchmark builders, the pre-registration and freeze records, and the tests |
| [`PHASE3/`](research/AGENTRUN_PUBLICATION_2026/PHASE3/) | the campaign: final report, statistical analysis, comparison and ablation tables, failure analysis, deviations, forensic report, machine-readable verdicts, result CSVs and the SHA-256 manifest |
| [`PHASE4/`](research/AGENTRUN_PUBLICATION_2026/PHASE4/) | the long-form manuscript and the reproducibility package (environment, model snapshots, dataset rules, analysis instructions, expected outputs, limitations) |
| [`PHASE5_PUBLICATION/`](research/AGENTRUN_PUBLICATION_2026/PHASE5_PUBLICATION/) | the typeset paper: LaTeX source, bibliography, nine vector figures with their data, the supplement, and the compiled PDFs in `build/` |

## Reproducing the analysis

The analysis is reproducible byte for byte from the archived raw outputs; the permutations and bootstraps are
seeded and the integrity gates re-verify the inputs first. See
[`PHASE4/reproducibility/`](research/AGENTRUN_PUBLICATION_2026/PHASE4/reproducibility/). Three limits are stated
there and in the paper: GPU kernels are not bitwise deterministic across hardware or library versions; two cells
were not produced on a single host platform; and one of those re-seeded its sampler when it resumed.

## What is not released

The confirmatory evaluation items, their annotations and the per-run transcripts are **withheld until
publication**, so the test set stays uncontaminated — their hashes are public in `PHASE2/FREEZE_eval3.json`, so a
later release can be checked against the frozen versions. Cluster job logs are withheld because their progress
lines carry per-task outcomes. Model weights are not redistributed; the exact snapshot hashes are listed.

---

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
| [`research/AGENTRUN_PUBLICATION_2026/`](research/AGENTRUN_PUBLICATION_2026/) | **Study 2**: mechanism, pre-registration, campaign reports, manuscript and publication package |

`agent.py`, `main.py`, and `memory.py` are the Phase 1 Gemini agent that preceded the Qwen experiments. They are not used by the four reported conditions.

## Publication status

- **Preprint (published):** L, Alyssa. *AGENTRUN: Failure-Driven QLoRA Specialization for Multi-Tool Agent Behavior in a 7B Language Model.* Zenodo, 5 September 2026. [doi:10.5281/zenodo.22346935](https://doi.org/10.5281/zenodo.22346935) (CC BY 4.0). This preprint is not peer reviewed. It **predates the E4 ablation** (16 September 2026), so it reports Base, V1, and V2 only.
- **Updated manuscript:** [`publication/manuscript.tex`](publication/manuscript.tex) (*Disentangling Parser and Data Effects in Tool-Using LLM Fine-Tuning*) adds E4. It has not been published or peer reviewed.
- **WI-IAT submission:** withdrawn on 9 October 2026. No submission is currently under review.

**Study 2 (persistent memory).** The manuscript in
[`PHASE5_PUBLICATION/`](research/AGENTRUN_PUBLICATION_2026/PHASE5_PUBLICATION/) is complete and typeset for
*Transactions on Machine Learning Research*. It has **not been submitted anywhere, is not under review, and is
not peer reviewed**; no submission account exists and no preprint has been posted. The venue comparison that led
to that choice is in
[`VENUE_SELECTION.md`](research/AGENTRUN_PUBLICATION_2026/PHASE5_PUBLICATION/VENUE_SELECTION.md). See
[`PUBLICATION_STATUS.md`](PUBLICATION_STATUS.md) for the full status of both studies.

## Citation

For **Study 1**, please cite the Zenodo preprint (see also [`CITATION.cff`](CITATION.cff)):

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

**Study 2 has no citable publication yet.** It is unsubmitted and unreviewed; please cite the repository and the
commit you used, and do not describe it as published, submitted or peer reviewed.

## License and security

The code is under the [MIT License](LICENSE). The Zenodo preprint text is CC BY 4.0. No model weights are distributed; adapters can be reproduced with the training scripts. API keys belong in a local `.env` (see `.env.example`), which is git-ignored. See [`CONTRIBUTING.md`](CONTRIBUTING.md) for contribution and release guidelines.
