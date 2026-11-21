# 10. Failure analysis

EBG answers 61.3% of pooled primary tasks correctly, so roughly two runs in five still fail. This section accounts
for them. Counts are over the 4288 pooled primary runs per configuration unless stated otherwise; the full tables,
including every model × configuration cell, are in `PHASE3/PHASE3_FAILURE_ANALYSIS.md` and
`PHASE3/PHASE3_FAILURE_TABLES.md`.

## 10.1 Where EBG's failures go

| Failure mode under EBG | Pooled primary | Share of all runs |
|---|---|---|
| False conflict (reports a conflict where the evidence resolves) | 867 | 20.2% |
| Unnecessary abstention | 494 | 11.5% |
| Stale value (answers with the superseded value) | 119 | 2.8% |
| Format error (no parsable final answer) | 120 | 2.8% |
| Arbitrary pick | 13 | 0.3% |
| Step-limit exhaustion | 42 | 1.0% |
| Unsupported claim | 0 | 0.0% |
| Missing row / harness error | 0 | 0.0% |

EBG's residual failure is dominated by **over-conservatism**, not by harm: false conflicts and unnecessary
abstentions together account for 31.7% of runs, against 3.1% harmful. The mechanism was designed to move errors in
exactly this direction, and it did. Whether that is the right place for them is a deployment question, not one this
benchmark settles.

## 10.2 The two mechanism-level failure modes it was built to prevent

*False resolution* — asserting an ordering the evidence does not support — falls from 12.8% of conflict groups under
plain memory, 19.0% under RT and 37.0% under LG to **1.9%** under EBG. *Conflict preservation* rises from 65.2%,
66.8% and 42.4% to **88.5%**. The preregistered known limitations of Evarb-0.2 are visible in the residue: the
arbiter misses a negator more than four tokens before the cue, does not treat "correcting" as a correction cue, and
resolves `negated_both_stand` to the rival instead of a contradiction. Those were pinned by tests before the freeze
and were not fixed during the campaign.

## 10.3 Model-family failure profiles differ in kind

| Model, EBG | Success | Unnecessary abstention | Format error | Harmful |
|---|---|---|---|---|
| Qwen2.5-3B | 59.5% | 3.6% | 0.0% | 2.9% |
| Qwen2.5-7B | 75.0% | 0.6% | 0.1% | 4.3% |
| Qwen3-8B | 77.8% | 0.0% | 0.0% | 4.7% |
| Llama-3.1-8B | 33.0% | 44.0% | 11.1% | 0.7% |
| Qwen2.5-14B (secondary) | 73.5% | 1.2% | 13.8% | — |
| Llama-3.2-3B (format-limited) | 41.8% | 35.9% | 0.0% | — |

The Llama family fails differently from the Qwen family. Llama-3.1-8B abstains on 44.0% of EBG runs and fails to
produce a parsable answer on 11.1%, while being the *least* harmful model in the study — it rarely commits to a
wrong value because it rarely commits. Its EBG − RT harm difference is therefore −0.3 pp, against −24.5 to −27.7 pp
for the Qwen models: there was almost no harm to remove. This is the sharpest limit on generalisation in our
results. The mechanism's harm-reduction claim is demonstrated on models that actually produce harmful answers; on a
model whose dominant failure is abstention and malformed output, EBG raises success (+6.8 pp over RT, +14.7 pp over
B) by converting abstentions into answers, which is a different causal story from the one the hypotheses state.

Qwen2.5-14B's 13.8% format-error rate under every configuration is a separate, configuration-independent artefact of
its output formatting in this harness, not a mechanism effect.

## 10.4 Execution failures

There were none in the analysis sense: all 18 cells reached 3216 rows, with 0 missing pairs, 0 duplicates and 0
harness-error rows across all 57,888 runs, so no run was scored as `missing`. Step-limit exhaustion is a task-level
failure rather than an execution failure, and EBG has the second-lowest rate of it (1.0%, against 2.4% for B).

Two cells were interrupted by the node reboot described in Section 11 and were resumed by the controller after the
damaged tail of each file was quarantined. Neither interruption cost a completed run, and neither produced a
duplicate. The recovery itself is reported there rather than here, because it is an infrastructure event, not an
agent failure.

## 10.5 What the failure analysis does not cover

The scorer's categories are mechanical. We did not inspect individual eval3 transcripts for qualitative failure
patterns, because the task texts remain sealed until publication; the failure analysis is therefore at the level of
outcome categories and rates, not of narrative error types. Phase 1's failure taxonomy supplied the mechanisms we
tested for (M8, M9, M11); confirming that those specific mechanisms are what produced the eval3 residue would need a
transcript study that we have not done.
