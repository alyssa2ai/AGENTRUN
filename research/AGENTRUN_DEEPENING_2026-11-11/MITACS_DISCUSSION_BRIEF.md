# AGENTRUN: one-page discussion brief (12 November 2026)

## The question

Does giving a multi-tool LLM agent persistent memory make it more reliable, and what do verification, provenance and a deterministic reliability check add when the memory is stale, contradictory or missing?

## What I did

A controlled, paired ablation. 48 frozen tasks in six scenarios (context loss, retrieval among distractors, conflicting records, stale records, unsupported questions, tool failure), each run under five configurations with everything else held fixed:

A stateless · B memory retrieval · C + a verifier · D + provenance (record id, date, source) · E + a rule that labels superseded and conflicting records in code.

Scoring is programmatic and separates **task success** from **harmful assertions** (stating a wrong, outdated or arbitrary value). A leakage audit of 59 automated checks passes on all runs.

## What ran

- **SIT HPC, 2 x NVIDIA L40, Slurm:** Qwen2.5-7B-Instruct, Qwen3-8B and Qwen2.5-7B with my LoRA adapter; 1,440 agent runs (three greedy runs plus three sampled repeats), all complete. A retrieval experiment on stores of up to 100,000 records.
- **Hosted endpoint:** three larger models, 355 runs, cut short by a daily quota (71 of 144 planned task blocks).

## What I found

| | A | B | C | D | E |
|---|---|---|---|---|---|
| Task success, local 7-8B models (144 blocks) | 21.5% | 45.8% | 36.1% | 53.5% | 63.2% |
| Task success, hosted larger models (71 blocks) | 28.2% | 67.6% | 66.2% | 71.8% | 70.4% |
| Harmful assertions, local / hosted | 0 / 0 | 2 / 4 | 0 / 1 | 1 / 0 | 0 / 0 |

1. **Memory helps a lot** (+24 points on small models, +39 on larger ones; p < 0.0001 in both).
2. **A same-model verifier without provenance hurt small models** (-9.7 points, p = 0.0001): 14 of its 16 rejections were of correct answers. On larger models it was neutral.
3. **Provenance is what makes verification work** (+17 points over C on small models, p = 0.0002; verifier precision 2/16 to 7/8).
4. **A simple deterministic rule beat the model's own reasoning about dates on small models** (stale-record tasks 7/24 to 18/24) and added nothing on larger models, which already used the dates correctly.
5. **Memory introduced the only wrong answers.** The stateless agent was never wrong because it never answered; retrieval alone produced 6 harmful answers in 215 blocks; with provenance and the rule, 0 or 1.
6. **Three failure modes no component fixed:** the agent not consulting its memory at all; the agent looping instead of saying "I don't know" once it has a memory tool; and answers in the wrong output format (the same lesson as my earlier parser study).
7. **The retriever in my repository does not scale:** recall@4 falls from 0.46 at 2,000 records to 0.05 at 100,000, where BM25 and dense embeddings stay at 0.96 to 1.00.

## What I can and cannot claim

Can: memory improves completion; provenance and an explicit staleness rule matter more than an LLM verifier; the benefit of reliability machinery shrinks as the base model gets stronger; most failures are about access, stopping and format, not retrieval.

Cannot: that the full system "solves" memory reliability; anything about natural, unstructured memories (fixtures are templated facts with clean keys); statistical significance for harmful-assertion differences (too few events); that the method is novel (STALE, Governed Persistent Memory, MemoryAgentBench and others cover stale and conflicting agent memory; my contribution is a controlled ablation in a multi-tool agent, with the negative result about verification).

Also not claimed: the earlier 100% fine-tuning result, which was affected by train/evaluation leakage.

## Next experiment

Remove the clean keys: let the agent write its own memories in free text over several sessions, inject one wrong memory, and test whether provenance plus a learned key extractor still prevents stale and conflicting answers. Run it with a dense retriever, on the L40, with at least three seeds per model.
