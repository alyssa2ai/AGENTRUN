# AGENTRUN research deepening, 11-12 November 2026

A controlled ablation of persistent memory, verification, provenance and a deterministic reliability check in a multi-tool LLM agent, plus a retrieval-at-scale experiment. Nothing in the existing repository was modified; everything is in this directory.

## Read in this order

| File | What it is |
|---|---|
| [MITACS_DISCUSSION_BRIEF.md](MITACS_DISCUSSION_BRIEF.md) | One page for the interview |
| [MITACS_TALKING_POINTS.md](MITACS_TALKING_POINTS.md) | 30-second and 2-minute versions, likely questions, what not to claim |
| [RESULTS.md](RESULTS.md) | All numbers, with uncertainty, and the verdict on each hypothesis |
| [FAILURE_ANALYSIS.md](FAILURE_ANALYSIS.md) | Ten failure modes with real transcripts |
| [OVERNIGHT_STATUS.md](OVERNIGHT_STATUS.md) | SIT HPC: jobs, states, errors, resume commands |
| [ARCHITECTURE.md](ARCHITECTURE.md) | Audit of the repository, diagrams, one task traced end to end |
| [RESEARCH_QUESTION.md](RESEARCH_QUESTION.md) | Question, hypotheses, configurations |
| [EXPERIMENT_PROTOCOL.md](EXPERIMENT_PROTOCOL.md) | Frozen design, metrics, statistics, and every deviation |
| [LEAKAGE_AUDIT.md](LEAKAGE_AUDIT.md) | 59 automated checks and the remaining threats |
| [REPRODUCIBILITY.md](REPRODUCIBILITY.md) | Environments, seeds, commands, output paths |
| [EXECUTION_LOG.md](EXECUTION_LOG.md) | What was inspected, changed, run, failed |

## The result in two rows

Task success by configuration:

| | A stateless | B memory | C + verifier | D + provenance | E + reliability gate |
|---|---|---|---|---|---|
| Local 7-8B models on the L40 (144 task blocks, complete) | 21.5% | 45.8% | 36.1% | 53.5% | 63.2% |
| Hosted larger models (71 blocks, truncated by quota) | 28.2% | 67.6% | 66.2% | 71.8% | 70.4% |

Memory helps in every model. A text-only verifier hurts small models. Provenance is what makes verification work. The deterministic gate helps small models and is redundant for larger ones. The repository's own retriever loses the right record 95% of the time at 100,000 records.

## Status

| Part | Status |
|---|---|
| Repository audit, architecture | done |
| 48-task benchmark, frozen, leakage-audited | done |
| Local-model ablation on SIT HPC (6 runs, 1,440 agent runs) | complete |
| Retrieval at scale on SIT HPC | complete |
| Hosted-model ablation | 71 of 144 blocks (daily quota) |
| Fine-tuning | not started (not needed for the question) |
| Legacy 23-task benchmark | untouched; existing results re-verified (22, 18, 18, 23 of 23) |

## Related work checked

Queried through the arXiv API on 2026-11-11 (`scripts/lit_check.py`, output in `logs/lit_check_arxiv.txt`). The check was by title and abstract only; the papers were not read in full.

| Work | Relation |
|---|---|
| LongMemEval (arXiv:2410.10813), LoCoMo (2402.17753), MemoryAgentBench (2507.05257) | Benchmarks of long-term memory, including knowledge updates and conflict resolution, in conversational settings |
| STALE (2605.06527) | Benchmark of whether agents notice that a memory is no longer valid |
| Governed Persistent Memory (2608.12476), Governed Shared Memory (2606.24535) | Systems that treat superseded, contradicted and stale records explicitly, with provenance |
| A frozen last-write resolver on MemoryAgentBench (2610.09193) | A zero-learning "newest statement wins" rule answers most of that benchmark's conflict-resolution questions |
| Self-RAG (2310.11511), Corrective RAG (2401.15884), FaithEval (2410.03727), ConflictBank (2408.12076) | Verification and knowledge conflicts in retrieval-augmented generation |
| MemGPT (2310.08560), Mem0 (2504.19413), Zep (2501.13956) | Memory architectures; Zep is explicitly temporal |

Consequence: the reliability gate is **not** a novel method. What this study contributes is a controlled, paired ablation of these components inside a multi-tool agent, across model sizes, with a negative result for same-model verification without provenance.

## Layout

```
benchmark/      dev.jsonl, eval.jsonl, FREEZE.json
scripts/        memlab.py (harness), hf_client.py (local GPU backend), run_ablation.py, analyze.py,
                leakage_audit.py, retrieval_bench.py, summarize_retrieval.py, lenient.py,
                build_benchmark.py, lit_check.py
tests/          9 CPU tests for the harness
raw_results/    eval_* (hosted), hpc_* (SIT HPC), dev_* (development smoke runs)
tables/         generated tables, per-run scores, failure examples, leakage audit
figures/        fig1-fig4 and per-set copies under hpc_*/
hpc/            from_cluster/ (what ran) and the earlier unexecuted plan
logs/           console logs
```
