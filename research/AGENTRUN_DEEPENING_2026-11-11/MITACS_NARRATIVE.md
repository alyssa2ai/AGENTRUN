# Your interview narrative, checked against the data

Your draft is checked below sentence by sentence against the raw results. Where a sentence is inaccurate or could be challenged, the right-hand column gives a corrected version. A clean version you can read aloud is at the end.

## Checked sentence by sentence

| Your sentence | Verdict | Why / corrected version |
|---|---|---|
| "My research project is AGENTRUN, a multi-tool LLM agent runtime with persistent memory, retrieval and QLoRA-based specialization." | OK | |
| "Initially, I evaluated the system using a relatively small 23-task benchmark. However, I encountered limitations involving evaluation leakage, benchmark coverage and the difficulty of isolating the contribution of individual agent components." | OK, sharpen "leakage" | The repository describes it as evaluation adaptation: the V2 adapter's extra training data was designed from failures on the same 23 tasks. Say that rather than "the model memorised answers", which is not what was found. |
| "I wanted to investigate a deeper question: does persistent memory actually make multi-tool agents more reliable, and under what conditions can it make them worse?" | OK | |
| "My initial experiments were conducted under limited GPU resources. After obtaining access to our institutional HPC infrastructure with NVIDIA L40 GPUs, I expanded the work into controlled ablation studies." | OK | Concrete version: Colab T4 before; two NVIDIA L40s under Slurm now. |
| "I introduced experimental configurations comparing a stateless agent, memory-enabled retrieval, verification, provenance-aware verification and additional memory reliability checks." | OK | Be ready to say these were built for this study; the shipped AGENTRUN agent has text-only memory (configuration B). |
| "In a fresh 96-task evaluation across Qwen2.5-7B and Qwen3-8B, memory improved reported task success substantially." | OK, give the number | From 24.5% to 56.8% pooled (+32 points, p < 0.0001). Drop "reported": these are measured. |
| "However, an interesting result was that adding a text-only verifier sometimes reduced performance." | OK, can be stronger | It reduced performance in both harnesses: -5.2 points (p = 0.006) and -11.5 points (p < 0.0001), pooled. Per model it is significant for Qwen2.5-7B, not for Qwen3-8B under the original harness. |
| "Incorporating provenance and reliability checks improved the outcomes." | OK | 51.6% to 62.0% to 75.0%. Stale-record tasks 4/32 to 25/32. |
| "I also identified a significant failure mode: memory-enabled agents could become less willing to abstain when the available evidence was insufficient." | Reword | "Less willing" implies they answered anyway. They mostly did not: Qwen3-8B kept searching until it ran out of steps (15 of 16 correct without memory, 1 of 16 with the full system, 15 of the failures were step-limit runs). Say "less able to reach an abstention". Then add the fix: two prompt rules restored 16 of 16. |
| "This led me to investigate stale memories, conflicting evidence, retrieval quality and model-capacity effects." | Order | Stale and conflicting records were in the design from the start; retrieval at scale and model size were the follow-ups. Say "This led me to look further at retrieval quality and model capacity." |
| "We submitted a 21-task experimental campaign to SIT HPC." | **Correct this** | It was 21 Slurm jobs, each running up to 480 agent runs on 96 tasks. "21-task" undersells it badly. |
| "Fourteen jobs completed successfully before the HPC Slurm controller became unavailable." | OK | Jobs 0-13, all exit 0. Jobs 14-20 were never dispatched. |
| "I recovered the completed experimental datasets and extended the analysis to include additional model-size and retrieval experiments." | Reword | The model-size and retrieval experiments were among the 14 jobs that ran, not added afterwards. Say "I recovered the datasets from all 14 completed jobs, including the model-size sweep and the retrieval-at-scale runs." |
| "My current research direction is reliability-aware memory for multi-tool language-model agents. I am particularly interested in understanding how memory quality, evidence provenance and uncertainty handling interact with model capacity." | OK | This is exactly what the data supports. |

## Things worth adding (they are your strongest evidence)

- **Scale:** about 6,600 agent runs on the HPC over two days, against 23 tasks per condition on Colab.
- **The fix, not just the failure:** two prompt rules raised success by 15.8 points on both models (p < 0.0001); the full system reached 92% on fresh tasks.
- **The capacity result:** inside one model family, reliability components help in an inverted U (1.5B never uses memory, 3B gains from memory only, 7B gains from everything, 14B gains little beyond memory).
- **Retrieval reaches the answers:** with 2,000 records the default retriever cuts success from 71% to 42%; BM25 restores 70%.
- **The honest fine-tuning result:** your adapter scores 23/23 on the original benchmark every time, but is no better than the base model on 55 fresh tasks. That closes the loop on the leakage question with evidence rather than a disclaimer.

## Clean version to read aloud (about 2 minutes)

My research project is AGENTRUN, a multi-tool LLM agent runtime with persistent memory, retrieval and QLoRA-based specialisation.

I first evaluated it on a 23-task benchmark on a Colab T4. That taught me how fragile agent evaluation is: one drop in performance was partly an artefact of the parser and the evaluation client, and a later perfect score came from an adapter whose extra training data had been designed from failures on those same tasks. When I re-ran it on our cluster with a matched client, the adapter again scored 23 of 23, but on 55 fresh tasks it was no better than the base model.

So I asked a deeper question: does persistent memory actually make multi-tool agents more reliable, and when does it make them worse? With access to our institute's HPC, two NVIDIA L40 GPUs under Slurm, I built controlled ablations: a stateless agent, memory retrieval, a verifier, provenance-aware verification, and a rule that flags stale and conflicting records. Tasks are synthetic, frozen before each run, and checked by an automated leakage audit.

On 96 fresh tasks with Qwen2.5-7B and Qwen3-8B, memory raised task success from 25% to 57%. A verifier that saw only text lowered it, because it rejected correct answers it could not trace to a source. Adding provenance and the staleness rule took success to 75%, and on stale records from 4 to 25 out of 32.

I also found that memory can make an agent worse at admitting it does not know: Qwen3-8B, given a memory tool, kept searching instead of abstaining. Two simple prompt rules fixed that and raised success by about 16 points on both models.

Across 21 Slurm jobs, 14 completed before the cluster's scheduler became unavailable, about 6,600 agent runs in total. They include a model-size sweep within one family, which showed that the reliability components help most at around 7 billion parameters, and a retrieval test showing that our default retriever halves success once memory holds 2,000 records, while BM25 restores it.

My current direction is reliability-aware memory for multi-tool agents: how memory quality, evidence provenance and uncertainty handling interact with model capacity.
