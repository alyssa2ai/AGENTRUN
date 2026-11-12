# AGENTRUN — MITACS Discussion Brief

## Positioning

**Reliability-aware memory for multi-tool language-model agents across model capacities.**

## 30-second summary

AGENTRUN is a multi-tool agent system with persistent memory. We systematically evaluated how memory components — retrieval, verification, provenance tracking and reliability gating — affect agent reliability across model sizes from 1.5B to 14B parameters. On a fresh 96-task benchmark, persistent memory improves task success by 32 percentage points. Verification without source provenance consistently hurts performance. A reliability gate is essential for stale-data scenarios. These component effects are significant only at 7B — smaller models can't exploit them, larger models don't need them.

## 2-minute explanation

AGENTRUN started as a multi-tool agent with QLoRA fine-tuning and persistent memory. The original evaluation on 23 tasks reported 100% success, but we discovered evaluation leakage — the model had memorized answers from training data. This invalidated the results and motivated a proper research investigation.

We built a fresh 96-task benchmark with 6 memory challenge scenarios (context loss, retrieval, conflict, stale data, unsupported questions, tool failure) and verified zero leakage across 17 automated checks. We then ran a systematic ablation on SIT HPC with two NVIDIA L40 GPUs, testing 5 memory pipeline configurations across 4 model sizes in the Qwen2.5 family plus a cross-family Qwen3-8B comparison.

The key findings are:

1. **Memory reliably helps** — +32 pp average improvement, p < 0.0001 across all conditions ≥ 3B.
2. **Verification without provenance hurts** — the model second-guesses correct answers when it can't trace where they came from.
3. **Reliability gating is critical for stale data** — it takes success from 12% to 78% on stale-memory tasks.
4. **Model capacity determines which components matter** — below 3B nothing helps; at 7B everything helps; at 14B the model self-manages.
5. **Retrieval quality is a scaling bottleneck** — naive hash retrieval fails at 2,000 records; BM25 maintains performance.

## 5-minute technical explanation

### The system

AGENTRUN is an MCP-based agent with:
- Persistent JSON memory stores per conversation
- Multi-step tool use (search, calculate, verify, store)
- Retrieval-augmented generation from memory
- A reliability pipeline with 4 composable stages:
  - B: Memory retrieval (retrieve relevant records for the query)
  - C: Verification (model checks its own answer before committing)
  - D: Provenance (retrieved records carry source, timestamp, confidence)
  - E: Reliability gate (model assesses answer reliability before responding)

### The benchmark

96 tasks across 6 scenarios, 16 per scenario. Each task has:
- A user question
- A pre-populated memory store with scenario-specific properties
- An expected answer
- Scenario fixtures (conflicting records, stale timestamps, absent entities)

Generated deterministically from seed. Zero overlap with training data (verified by TF-IDF similarity < 0.15 against all reference prompts, plus entity-level isolation).

### The experiment

21 planned Slurm jobs, 14 completed (6,539 task evaluations):
- 5 configurations × 2 harness versions × 2 base models = 1,920 main comparisons
- 5 configurations × 2 harness versions × 4 Qwen2.5 sizes = 3,840 size-sweep runs
- 2 retrieval conditions × 192 runs = 384 retrieval-at-scale tests
- Plus legacy and v2-benchmark validation runs

Paired McNemar tests with task-clustered bootstrap confidence intervals.

### The results

**Memory effect (+32 pp pooled):** The largest and most robust finding. Consistent across models, harness versions, scenarios. Every model ≥ 3B benefits.

**Verification penalty (−5 to −13 pp):** When the model verifies its own answer without knowing where the answer came from, it defaults to "I don't know." Adding provenance metadata (+10 pp) fixes this by giving the verifier evidence to confirm against.

**Reliability gate (+13 pp):** Largest effect on stale-memory tasks. The gate explicitly checks for temporal consistency, catching outdated values that retrieval alone misses.

**Model-size threshold:** At 1.5B, the model can't follow the agent format at all. At 3B, it benefits from memory but can't exploit verification/provenance/gating. At 7B, every component adds significant value. At 14B, memory helps strongly but the additional components are not needed — the model's own capacity handles reliability.

**Retrieval scaling:** Hash-based lookup (the original AGENTRUN approach) fails when stores grow past a few dozen records. BM25 maintains perfect recall at 2,000 records.

### What's novel

Not "memory helps agents" — that's expected. The contributions are:
1. The component interaction: verification hurts without provenance (not previously documented).
2. The capacity threshold: reliability components are useful only in a specific model-size range.
3. The retrieval scaling analysis: quantifying when naive retrieval breaks.
4. The benchmark methodology: fresh tasks with automated leakage prevention.

### What's not ready

- 7 of 21 experiments didn't complete (infrastructure failure, not methodology failure).
- No run-to-run variance estimates (all greedy, single runs).
- The eval2 set was used for iteration, not held out as a blind test.
- No cross-family generalization beyond Qwen.
