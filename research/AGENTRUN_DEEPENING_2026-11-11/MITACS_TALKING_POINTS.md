# MITACS talking points (12 November 2026)

Numbers are from [RESULTS.md](RESULTS.md) (11 November) and [RESULTS_CAMPAIGN2.md](RESULTS_CAMPAIGN2.md) (12 November). "Fresh tasks" means the 96-task split generated with new names and frozen before any run.

## 30 seconds

AGENTRUN is my multi-tool agent runtime: an LLM that calls tools over MCP and keeps a persistent memory. I asked whether that memory actually makes the agent more reliable. On our institute's L40 GPUs I ran controlled ablations: the same tasks with no memory, with memory, with a verifier, with provenance and with a rule-based staleness check, across model sizes from 1.5B to 14B. Memory roughly doubles task success, but a verifier that cannot see where evidence came from makes things worse, and memory can make an agent worse at saying "I don't know". Provenance, a simple staleness rule and two prompt rules fix most of that, and the components only pay off in a middle range of model sizes.

## 2 minutes

I started with QLoRA fine-tuning of Qwen2.5-7B for tool use, on a 23-task benchmark and a Colab T4. That phase taught me to distrust my own numbers: one drop turned out to be partly a parser and client artefact, and the later 100% came from an adapter trained on examples designed from failures on those same 23 tasks. When I re-ran it on our cluster with a matched client, the adapter again scored 23 of 23, five times out of five, but on 55 fresh tasks it was no better than the base model.

The memory layer had never been tested, so I designed an experiment around it. Six scenarios: lost context, retrieval among distractors, conflicting records, stale records, questions with no supporting evidence, and tool failures. Five configurations, each adding one component. Scoring is programmatic and separates "did the task" from "asserted something false". Tasks are frozen before any run and pass a 77-check leakage audit.

On 96 fresh tasks with Qwen2.5-7B and Qwen3-8B, memory raised success from 25% to 57%. Adding a verifier that only saw text cut it to 52%: it rejected correct answers because the evidence also contained other projects' records. Adding the record's date and source, then a rule that labels superseded and conflicting records, took it to 75%; on stale records, from 4 to 25 of 32.

The most interesting failure: with memory, Qwen3-8B stopped abstaining on unanswerable questions, 15 of 16 correct without memory, 1 of 16 with the full system. It did not make answers up; it kept searching memory and the registry until it ran out of steps. Two prompt rules, "search memory before giving up" and "never repeat a call that already answered, otherwise abstain", fixed that and lifted success by 16 points on both models, to 92% in the full configuration.

Finally, model size. Inside one family, the 1.5B model never even calls memory, the 3B model benefits from memory but not from verification or provenance, the 7B model benefits from everything, and the 14B model needs little beyond memory. So reliability machinery is most valuable in the middle of the capacity range, and retrieval quality matters too: at 2,000 records the default hash retriever halves success and BM25 restores it.

## Three concrete examples (real transcripts)

1. **Looping instead of abstaining.** Qwen3-8B, "Who is the lead of Project Caskaen?", full system, original harness. The fact is nowhere. It called the registry ("not found"), then memory (records about the project's other attributes, not its lead), then the registry again, then memory again, six steps in all, and never answered.
2. **A verifier that punishes correct answers.** Qwen2.5-7B, 11 November, verifier without provenance: it rejected a correct budget-per-member answer (17185.29) because "the evidence ... instead provid[es] data for other projects". Across the three local models that day, the text-only verifier rejected 14 correct drafts and 2 wrong ones; with record ids and dates in the evidence it was right in 7 of its 8 rejections.
3. **An invented answer, caught.** Qwen2.5-7B, revised harness, retrieval only: on four different context-loss tasks it submitted the same value, 12500.00, without calling a single tool, citing `registry_lookup` and `calculator` as evidence. With the verifier switched on, all four were rejected.

## Likely questions

**"How do you know this is not leakage again?"** Entities are invented names from a seeded generator, so no model can know the answers. Each task gets its own memory store, checked after the run to contain only its own records. The ground truth never appears in any message to the model; the audit scans every transcript for it. The splits were hashed before the first run and the runner refuses to start if the hash changes. The revised harness was developed on 12 dev tasks only, then tested on a split nobody had seen, with the original harness re-run on the same tasks as the control. What remains: I wrote the tasks and the method; the facts are templated; a model could learn the task structure within a run.

**"Why does the verifier hurt? Isn't that just a bad prompt?"** It is a property of using the same model to check itself without external evidence, which matches published findings that LLMs often fail to self-correct without external feedback (Huang et al., 2023, arXiv:2310.01798). Two observations support that reading: the identical verifier became more precise once the evidence carried provenance (7 of 8 rejections right on 11 November; on the fresh tasks the gain was smaller, 4/15 to 4/10 and 7/29 to 11/23), and on larger hosted models it had no false rejections. A better prompt might reduce the penalty; I did not tune it, by design.

**"Why does the 14B model benefit less?"** Partly capacity: it already resolves many stale and conflicting cases itself. Partly an artefact I found in the transcripts: in about 20 runs per harness it kept calling the calculator with `round(...)`, which the tool does not support, until it ran out of steps. So I would not claim "large models do not need reliability components"; I would say the measured marginal benefit is small at 14B on this tool set.

**"Is the reliability rule novel?"** No. Last-write-wins and conflict flags are standard, and 2025-2026 work such as STALE and MemoryAgentBench studies stale and conflicting agent memory. My contribution is the controlled comparison: which component helps, at which model size, measured with paired tests, including the negative result for verification without provenance.

**"What did the HPC add over Colab?"** Complete data without API quotas; the project's own base model and adapter; four model sizes in one family; a matched-client re-run of the original benchmark; and the end-to-end retrieval test. About 6,600 agent runs over two days, against 23 tasks per condition before.

## What the evidence supports

- Memory improves task completion when context is missing (two fresh splits, every model from 3B up, p < 0.0001).
- A text-only same-model verifier lowers success (p = 0.006 and p < 0.0001 on the two harnesses).
- Provenance plus a staleness rule raises success on 7-8B models, most of all on stale records.
- Memory can stop an agent from abstaining, and two prompt rules restore it.
- The value of the reliability components depends on model size non-monotonically (one family).
- The default retriever's failure at scale reaches end-task success; BM25 fixes it.
- The fine-tuned adapter's benchmark advantage does not transfer to fresh tasks.

## What is unfinished

- 7 of 21 jobs did not run: dense retrieval, the repair-only harness, the adapter on the memory benchmark, sampled repeats of the revised harness.
- One greedy trial per cell; one model family for the size sweep.
- Harmful answers are rare at 7-8B (1 to 7 per 480 runs), so differences in them are not significant. They are more common at 1.5B and 3B (up to 37 per 480).
- Synthetic, templated memories with clean keys; no agent-written memories; no single wrong memory.

## Do not say

- "Memory made the model hallucinate" or "fabricate" on unsupported questions. It looped; it did not invent answers (no unsupported claims at 7-8B in either campaign).
- "The full system is always best" (not at 3B or 14B).
- "Verification reduces hallucination."
- "Statistically significant reduction in harmful answers."
- "Novel memory reliability protocol" or "not previously documented".
- "21 tasks" for the campaign: it was 21 Slurm jobs on 96 tasks.
- "The 1.5B model produces no harmful answers": under the revised harness it asserted 24 wrong values.
- "The base model scores 25% on fresh tasks": 25% is the stateless configuration on the memory benchmark, a different task. On AGENTRUN's own benchmarks the base model scores 92.7-94.5% (fresh dev split) and 21-22 of 23 (original set).
- Any GPU utilisation figure (`nvidia-smi` is broken on the node; CUDA works).
