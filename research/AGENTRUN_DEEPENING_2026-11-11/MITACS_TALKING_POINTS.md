# MITACS talking points

Numbers are from RESULTS.md. "Local" = Qwen2.5-7B, Qwen3-8B and Qwen2.5-7B + adapter on the SIT HPC L40s (144 task blocks, complete). "Hosted" = three larger models through an API (71 blocks, cut short by quota).

## 30 seconds

AGENTRUN is my multi-tool agent runtime: an LLM that calls tools over MCP and keeps a persistent memory. I wanted to know whether that memory actually makes the agent more reliable, so I built a controlled ablation: the same 48 tasks run with no memory, with memory, with a verifier, with provenance, and with a rule-based staleness check. Memory roughly doubled or tripled task success. The surprise was that an LLM verifier on its own made small models worse, and that passing the record's date and source through did most of the useful work.

## 2 minutes

The project started as a QLoRA fine-tuning study of Qwen2.5-7B for tool use. That taught me a hard lesson about evaluation: one result dropped because of a parser defect, and a later 100% turned out to be contaminated by train/evaluation leakage, so I do not report it as generalisation.

For this study I audited the repository first and found that the memory layer had never been evaluated at all. So I designed one experiment around the question: when does persistent memory make an agent more reliable, and when does it make it wrong?

I froze 48 tasks in six scenarios before running anything: lost context, retrieval among distractors, conflicting records, stale records, questions with no supporting evidence, and tool failures. Each task runs under five configurations that differ in exactly one component. Scoring is programmatic and keeps "did the task" separate from "asserted something false". An automated leakage audit with 59 checks passes on every run.

I ran it on my institute's HPC, on two NVIDIA L40s under Slurm, with Qwen2.5-7B, Qwen3-8B and my own adapter, 1,440 runs in total, and on three larger hosted models.

Four results. Memory helps: success goes from about 22% to 46% on the small models and from 28% to 68% on the larger ones. A verifier that only sees text hurts small models, because it rejects correct answers; 14 of its 16 rejections were wrong. Provenance fixes that: with record ids, dates and sources, verifier precision goes from 2 in 16 to 7 in 8. And a ten-line deterministic rule for "which record is current" lifted stale-record tasks from 7 to 18 of 24 on small models, but added nothing on stronger models.

The failures were just as informative: agents that never look in their memory, agents that cannot stop searching and say "I don't know", and small models that have the right answer but write it in the wrong format.

## Three questions I should expect

**1. "How do you know this is not leakage again?"**

Three layers. The task entities are invented names from a seeded generator, so no model can know the answers, and an automated check confirms none of them occurs in my training data, the old benchmark or the real memory file. Each task gets its own memory store, written to disk and checked afterwards to contain only that task's records. And the scorer's ground truth is never in any message sent to the model; the audit greps every transcript for it. The benchmark and prompts were hashed before the first evaluation run and the runner refuses to start if the hash differs. The remaining threat is honest: I wrote the tasks and the method on the same day, the facts are templated, and two prompt rules were tuned on a development split with the same templates.

**2. "Your verifier made things worse. Why, and is that a flaw in your implementation?"**

It is a property of the design, and I think it is the most useful finding. The verifier is the same 7B model, shown the question, the retrieved text and the draft. The retrieved text contains the right record plus distractors, and the model read "there are records about other projects" or "another tool said not found" as "unsupported". Two things support that it is not just a bug: on the larger hosted models the identical verifier had zero false rejections, and on the small models the same verifier became accurate once the evidence carried record ids, dates and sources. There is a second weakness it cannot escape: when generator and verifier are the same model they share blind spots. I have a transcript where both read "most recent deadline" as "the later date" and the check passed.

**3. "Is the reliability gate novel? And would it survive real data?"**

Not novel as an idea. Last-write-wins and conflict flags are standard, and there is 2026 work specifically on stale and conflicting agent memory (the STALE benchmark, Governed Persistent Memory, MemoryAgentBench's conflict split). What I add is a controlled comparison inside a multi-tool agent showing where it matters: it helps models that cannot reason reliably over metadata and is redundant for those that can. Would it survive real data? Not as written. It depends on each record having a clean entity and attribute key, which my fixtures provide and real conversations do not. That is the next experiment.

Other likely questions, short answers:

- *Why are the absolute numbers low for the 7B models?* Between 27% and 42% of their runs, depending on the configuration, end without a valid final answer (wrong format or step limit). With a post hoc lenient parser success rises from 46% to 58% in B and from 63% to 72% in E; the ordering does not change. I report both and label the lenient one as post hoc.
- *How much does it cost?* On the L40, about 33% more latency and 35% more tokens from the stateless agent to the full system.
- *What did the HPC add?* Complete data without API quotas, the project's own base model and adapter, deterministic greedy decoding (identical drafts in 144 of 144 repeated blocks), sampled repeats to see run-to-run spread, and the 100,000-record retrieval test.
- *Did fine-tuning help?* My adapter did worse than its base model on this task (24 vs 33 of 48 in the best configuration), mostly through format failures. It was trained on four other tools, so this measures transfer, not the adapter's intended use.

## What the evidence supports

- Memory improves task completion when the context is missing (both model sets, all six models, p < 0.0001).
- Text-only self-verification reduces success on small models (p = 0.0001) and is neutral on larger ones.
- Provenance improves on text-only verification on small models (p = 0.0002).
- A deterministic staleness rule adds to provenance on small models (p = 0.034, the weakest of these) and not on larger ones.
- No configuration fabricated an answer to an unsupported question in 1,795 scored runs under this prompt.
- The repository's hashed embedding retriever fails beyond a few thousand records.

## What is unfinished

- Hosted runs stopped at 71 of 144 blocks.
- One greedy trial per model for the headline; three models that share one base family.
- Harmful assertions are too rare (0 to 4 per configuration) for any significance claim.
- Free-text memories, agent-written memories and a single wrong memory were not tested.
- The legacy 23-task benchmark was not re-run with a matched client; the sealed 130-task benchmark was deliberately not touched.
- Memory-not-consulted and cannot-stop-searching have no fix yet.

## The next experiment

Multi-session tasks in which the agent writes its own memories, a dense retriever, and three perturbations (stale, conflicting, and one confidently wrong record), comparing provenance with learned key extraction against the current clean-key rule, with at least three seeds per model on the L40.

## Connection to reliable, interpretable, trustworthy AI

- **Reliable:** the study measures the difference between not answering and answering wrongly, and shows memory moves an agent from the first to the second unless provenance comes with it.
- **Interpretable:** provenance makes each answer traceable to a record id, date and source; the deterministic rule is a decision a person can read, unlike a second LLM's judgement.
- **Trustworthy:** the negative results are reported (verification hurting, the retriever failing, my own adapter transferring badly), and the evaluation is built to resist the leakage that invalidated my earlier result.

## Do not say

- "AGENTRUN solves memory reliability" or "the full system is always best" (not on larger models).
- "Verification reduces hallucination" (not shown; unsupported claims were zero everywhere, and the text-only verifier lowered success).
- "Statistically significant reduction in harmful answers" (it is not).
- "Novel memory reliability protocol".
- "Validated on Qwen 3.8-27B" (7 blocks only).
- Anything quoting the 100% fine-tuning result as generalisation.
- "The existing AGENTRUN runtime has verification and provenance" (they were written for this study; the shipped agent has text-only memory).
- "GPU utilisation was X%" (not measured; `nvidia-smi` is broken on the node).
