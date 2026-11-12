# AGENTRUN: one-page discussion brief (12 November 2026)

## The question

Does persistent memory make a multi-tool LLM agent more reliable, and under what conditions does it make it worse? What do verification, provenance and a deterministic reliability check add, and how does that depend on model size?

## Where it came from

AGENTRUN began as a QLoRA fine-tuning study of Qwen2.5-7B for tool use on a 23-task benchmark, run on a Colab T4. Two lessons from that phase shaped this work: one apparent drop (95.7% to 78.3%) was partly a parsing and client artefact, and the later 100% came from an adapter whose extra training data was designed from failures on the same 23 tasks. The memory layer had never been evaluated at all.

## What I did

- A paired ablation with five configurations: A stateless, B memory retrieval, C + verifier, D + provenance (record id, date, source), E + a rule that labels superseded and conflicting records.
- Six scenarios: lost context, retrieval among distractors, conflicting records, stale records, unsupported questions, tool failure.
- Programmatic scoring that keeps **task success** apart from **harmful answers** (stating a wrong, stale or arbitrary value).
- Two frozen, fresh task splits (48 and 96 tasks); an automated leakage audit (77 of 77 checks pass on the second).
- On the SIT HPC, two NVIDIA L40s under Slurm, about 6,600 agent runs: 1,440 on 11 November, 5,184 on 12 November, plus 450 runs of AGENTRUN's own benchmarks. 14 of 21 jobs in the second campaign finished; the last 7 never started because the Slurm controller became unreachable.

## Findings

| Task success, 96 fresh tasks, Qwen2.5-7B + Qwen3-8B pooled | A | B | C | D | E |
|---|---|---|---|---|---|
| Original harness | 24.5% | 56.8% | 51.6% | 62.0% | 75.0% |
| Revised harness (v2) | 29.2% | 81.8% | 70.3% | 75.5% | **92.2%** |

1. **Memory helps** in every model of 3B and above: +32 points pooled (p < 0.0001), replicated on two fresh splits.
2. **A text-only verifier hurts:** -5 points (original harness) and -12 points (revised), both significant. It rejects correct answers when it cannot see where the evidence came from.
3. **Provenance and the staleness rule fix it.** Stale-record tasks: 4/32 with plain retrieval, 25/32 with the rule (32/32 with the revised harness).
4. **Memory made agents worse at abstaining.** On unsupported questions Qwen3-8B was right 15/16 times without memory and 1/16 times with the full system: not by inventing answers, but by searching in a loop until it ran out of steps.
5. **That failure mode has a measured fix.** Two prompt rules ("search memory before giving up", "never repeat a call that already answered; otherwise abstain") raised success by 15.8 points on both models (p < 0.0001) and restored abstention to 16/16. Cost: false conflict flags doubled, and Qwen2.5-7B submitted four invented answers without calling any tool, which the verifier then caught.
6. **Model size, one family (Qwen2.5 1.5B to 14B):** reliability components help in an inverted U. 1.5B never consults memory; 3B gains from memory only; 7B gains from every component; 14B gains from memory and little else, partly because it loops on a calculator that does not support `round()`.
7. **Retrieval quality reaches the answers.** With 2,000 records in memory, AGENTRUN's hash retriever drops task success from 71% to 42%; BM25 restores it to 70%.
8. **My fine-tuned adapter does not generalise:** 23/23 on the original benchmark in all five matched runs, but no better than the base model on 55 fresh tasks (92.7% vs 94.5%).

## What I can and cannot claim

Can: the component effects above, on synthetic but leakage-audited tasks, with paired tests; the capacity dependence inside one model family; that the earlier fine-tuning gain is benchmark-specific.

Cannot: anything about free-text or agent-written memories (fixtures are templated facts with clean keys); other model families; significance for differences in harmful answers (too few events); run-to-run variance for the revised harness (those jobs did not run); novelty of the reliability rule (last-write-wins is standard; related work includes STALE, MemoryAgentBench and work showing LLMs often fail to self-correct without external feedback).

## Next experiment

Agent-written, free-text memories across sessions, with one confidently wrong record injected; compare learned key extraction with the clean-key rule; dense retrieval; three seeds per model; at least one non-Qwen family.
