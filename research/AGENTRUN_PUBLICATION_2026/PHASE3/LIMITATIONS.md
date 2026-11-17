# Limitations (written 17 November 2026, before any eval3 outcome; to be extended, never softened, after results)

## Data
- **No human validation of eval3.** Texts were written by Qwen2.5-14B; the only independent checks are two model annotators (Llama-3.1-8B, Qwen2.5-14B), which agree with gold on 58/90 and 71/90 p2val2 items. Annotator agreement is not ground truth.
- The writer is also a secondary evaluated model and an annotator.
- eval3 has heavy surface regularity: the seal checks report many duplicated masked texts and 8-gram template overlaps (counts in `eval3_SEAL_CHECKS.json`). Items are synthetic templates, not natural memory logs.
- 268 of 276 skeleton items are valid; 8 were excluded mechanically (values written in long-form dates). Long-form value dates are therefore untested.
- ISO-only value dates; English only; lexical cue lists in the mechanism.

## Mechanism (evarb-0.2, frozen)
- Long-range negation, "both figures stand" (negated_both_stand 0/4 on p2val2) and the cue "correcting" are known failures, pinned in `PHASE2/tests/test_known_limitations.py`. They count against Evarb as written.
- Historical / as-of questions score 0 at component level for every method; intent is handled in the agent loop.

## Evidence before the freeze
- p2val2 (a development validation set with 90 single-item families) showed: EBG−RT ≈ +1 pp on Llama-3.1-8B; ungated enforcement (EBG-all) scored higher than gated EBG with more harmful answers; the audit of p2val2 was done by the mechanism's maintainer and is not blind (`PREREGISTRATION.md` §15–16).
- Power treats the p2val2 effect as truth; EBG−LG is under-powered at half the measured effect (0.53).

## Design
- Models are small open-weight (3B–14B); no frontier model. Results do not extend to larger models.
- Tool-using agent with a synthetic tool registry; one harness (`memlab`, evarb loop 0.2). Prompts were fixed before eval3 but were developed on earlier splits.
- Four primary models, one second family (Llama). Llama-3.1-8B needs a `FamilyClient` adapter and has 9 format failures per configuration on p2val2, so a family-level conclusion rests on a model that is partly format-limited.
- T=0.7 repetitions measure decoding noise, not independent samples of tasks; family is the unit of inference.
- Latency is wall time under single-occupancy Slurm jobs on one L40 while other projects' CPU jobs may share the node; T=0.7 and 14B budget numbers were partly estimated.
- Qwen3-8B is run with thinking disabled.
