# Campaign 2 — Next Steps

## Immediate (when HPC access is restored)

1. **Complete the 7 missing jobs.** Estimated 2 hours of wall time. See `HPC_RECOVERY.md` for exact commands.

2. **Run the dense retrieval experiment** (job 14). This is the most scientifically important missing experiment — it completes the hash vs BM25 vs dense retrieval comparison.

3. **Download and back up new results.** Follow the same scp + backup procedure used for the initial 14 jobs.

## Short-term (within 1 week)

4. **Investigate the verifier penalty.** Why does verification consistently hurt? Hypotheses:
   - The verification prompt is too conservative (asks the model to confirm with certainty).
   - Without provenance, the model has no evidence basis for confirmation and defaults to "I can't verify."
   - The repair-turn mechanism in v2 might partially solve this by giving the model a second chance.
   
   **Experiment:** Design a softer verification prompt that asks "is this plausible?" rather than "can you confirm?" and test it at 7B.

5. **Investigate the Qwen3-8B S5 abstention failure.** Examine the v1 traces for S5 tasks to determine:
   - What retrieved records the model uses to fabricate answers.
   - Whether the fabricated answers are internally consistent.
   - Whether this is a training-data artifact (Qwen3 trained to be more helpful) or an architecture effect.

6. **Run the sealed 130-task test set.** Only after the methodology is frozen and no further harness changes are planned. Use only the configurations that will be reported as final results.

## Medium-term (1–4 weeks)

7. **Extend retrieval scaling.** Test BM25 and dense retrieval at 5,000 and 10,000 background records.

8. **Test cross-model generalizability.** If resources are available, test the pipeline on a non-Qwen model family (e.g., Llama 3.x 8B) to verify that the component effects are not Qwen-specific.

9. **Formalize the capacity threshold finding.** The observation that reliability components are effective only at ~7B is an interesting finding, but the mechanism is unknown. Is it about instruction-following capability, context utilization, or something else?

10. **Measure run-to-run variance.** Jobs 19–20 (T=0.7 seeds) will provide initial variance estimates. Consider running 5+ seeds at 7B config E to properly characterize within-task variance.

## For the ANTIC 2026 submission (if applicable)

11. **Decide scope.** The current results support a focused contribution on:
    - Reliability-aware memory for multi-tool agents.
    - Model capacity as a determinant of component utility.
    - Retrieval quality as a bottleneck for memory-augmented agents.

12. **Run the test set.** The eval2 96-task set has been used for iteration. A publication-quality result should come from the sealed 130-task test set.

13. **Related work.** Need systematic comparison with:
    - MemoryBank, MemGPT, RAISE (persistent memory for agents)
    - ToolBench, API-Bank (multi-tool benchmarks)
    - Self-consistency, chain-of-verification (verification methods)
    
    Currently no formal related-work survey has been conducted.

## Things NOT to do

- **Do not run more experiments on the eval2 split and report them as "confirmatory."** It was used for iteration. Only the sealed test set provides uncontaminated confirmatory evidence.
- **Do not pool 7B and 14B results to inflate sample sizes.** The size-sweep results show different component effects at different scales.
- **Do not claim the 92.2% v2 pooled result as a headline number.** It pools two models with different characteristics. The per-model numbers are more honest.
- **Do not claim novelty for the memory improvement.** Memory helping agents is expected. The novel contributions are the component interactions, capacity thresholds and retrieval-quality findings.
