# Phase 3 failure analysis

Companion to the machine-generated `PHASE3_FAILURE_TABLES.md`, which holds every model × configuration cell. This
document is the narrative reading. Two kinds of failure are separated: **task failures**, where an agent did not
answer correctly, and **execution failures**, where the campaign infrastructure did not do what it should have.

All rates below are over the 4288 pooled primary runs per configuration (four primary models × four decodings ×
268 tasks) unless stated otherwise. Mechanism-level rates (*conflict preserved*, *false resolution*) come from the
descriptive metrics over all six models.

---

## 1. Execution failures: none at the analysis level

| Check | Result |
|---|---|
| Cells completed | 18 / 18 |
| Rows per cell | 3216 / 3216, every cell |
| Total rows | 57,888 |
| Missing (task, config) pairs | **0** |
| Duplicate pairs | **0** |
| Harness-error rows | **0** |
| Unparsable lines | **0** |
| Last Slurm segment exit code | 0 for every cell |

No run was scored as `missing`, so the preregistered missing-run rule (§7: a missing pair or harness error counts as
a failure) never had to be applied. Two cells were interrupted and resumed; neither lost a completed run. See §4.

---

## 2. Task failures under the full mechanism (EBG)

EBG answers 61.3% of pooled primary runs correctly. The remaining 38.7% break down as follows.

| Failure mode | Runs | Rate |
|---|---|---|
| False conflict — reports a conflict where the evidence resolves | 867 | 20.2% |
| Unnecessary abstention | 494 | 11.5% |
| Stale value — answers with the superseded value | 119 | 2.8% |
| Format error — no parsable final answer | 120 | 2.8% |
| Step-limit exhaustion | 42 | 1.0% |
| Arbitrary pick | 13 | 0.3% |
| Unsupported claim | 0 | 0.0% |

**The residue is over-conservatism, not harm.** False conflicts and unnecessary abstentions together are 31.7% of
runs; the whole harmful category is 3.1%. The mechanism was designed to move errors in that direction, and the data
show it did. Whether that is the right trade is a deployment question this benchmark cannot settle, because it
assigns no relative cost to a wrong confident answer versus a missed correct one.

Part of the false-conflict residue is the arbiter's own documented limitations, pinned by tests before the freeze
and deliberately not fixed during the campaign: a negator more than four tokens before the cue is missed;
"correcting" is not treated as a correction cue; `negated_both_stand` resolves to the rival instead of a
contradiction. We cannot say how much of the 20.2% those account for without a transcript study (§6).

---

## 3. How the comparators fail

| Config | Success | Harmful | Arbitrary pick | Conflict preserved | False resolution | Unnecessary abstention | Format error |
|---|---|---|---|---|---|---|---|
| B | 46.0% | 7.0% | 172 | 65.2% | 12.8% | 19.5% | 3.2% |
| G | 43.5% | 7.9% | 109 | 72.8% | 9.2% | 16.0% | 3.7% |
| T | 46.9% | 7.4% | 35 | 79.6% | 3.6% | 16.9% | 3.1% |
| R | 45.0% | 16.1% | 153 | 74.2% | 12.3% | 9.4% | 6.1% |
| RT | 44.2% | 22.6% | 252 | 66.8% | 19.0% | 11.1% | 6.2% |
| LA | 47.9% | 13.2% | 295 | 57.8% | 21.9% | 18.4% | 3.5% |
| LG | 45.4% | 21.3% | 510 | 42.4% | **37.0%** | 17.1% | 3.3% |
| EB | 55.3% | 2.7% | 13 | 81.6% | 2.0% | 16.7% | 3.1% |
| **EBG** | **61.3%** | **3.1%** | **13** | **88.5%** | **1.9%** | 12.8% | 3.3% |
| EBG-all | 71.1% | 6.9% | 166 | 77.3% | 12.9% | 13.9% | 3.3% |
| EBG-unsafe | 61.5% | 3.3% | 12 | 89.0% | 1.6% | 9.9% | **6.4%** |
| EBG-noR3 | 60.0% | 3.4% | 14 | 83.3% | 1.9% | 17.6% | 2.9% |

Three failure patterns stand out.

**Label-induced failure replicates.** Metadata-derived labels (G) made agents *worse* than no labels at all — 43.5%
against B's 46.0%, with more harm and more false conflicts (31.4% against 26.4% on primary models). This is the
development finding that motivated the study, reproduced on sealed confirmatory data without modification.

**Enforcement-induced failure is larger than label-induced failure.** Enforcing record-derived labels (RT) produced
the worst harm in the study among the non-LLM configurations: 22.6% harmful and 252 arbitrary picks, against B's
7.0% and 172. Enforcement is not neutral; applied to labels the evidence does not support, it roughly tripled harm
relative to plain memory.

**Gating an unreliable arbiter is worse than not gating it.** LG — the LLM arbiter under the same gated policy —
falsely resolves 37.0% of genuinely unresolvable groups and preserves only 42.4% of them, the worst of any
configuration including plain memory. Its 510 arbitrary picks are the highest in the study. For Qwen2.5-7B
specifically, LG falsely resolves 75.9% of conflicts. The gating machinery is identical to EBG's; only the source of
the labels differs.

---

## 4. The two interrupted cells

| | `qwen3_8b_T07_s3` | `llama32_3b_greedy` |
|---|---|---|
| Interruption | node reboot 2026-11-20T10:11:58 | same |
| Jobs | 4315 → requeued → 4326 | 4324 → requeued → 4327 |
| Failure on requeue | `run_p2.py:89` `JSONDecodeError` on the truncated final line | same |
| Quarantined bytes | 1153 | 3617 |
| Complete rows in the quarantine | **0** | **0** |
| Rows lost | 0 | 0 |
| Final rows | 3216 | 3216 |
| Duplicates | 0 | 0 |

The recovery worked as designed: the runner's resume skips completed `(task, config)` pairs, and the controller
quarantined only the damaged tail — a single partial row in each case — before resubmitting. The one interrupted
pair per cell was re-executed.

Two collateral losses are permanent and are recorded rather than worked around. Slurm's requeue **overwrote** the
console logs of the two interrupted starts (`phase3_4315_15.out`, `phase3_4324_17.out`); their manifest lines
survive with the code hashes, freeze state and start timestamps. And the resumed sampled cell re-seeded its random
stream rather than continuing it, so that cell is not byte-reproducible without reproducing the interruption.

Full account: `PHASE3_DEVIATIONS.md` D1–D3, `PHASE3_G4_FORENSIC_REPORT.md`, `PHASE3_PLATFORM_CONTINUITY.md`.

---

## 5. Failure by model family

| Model, EBG | Success | Unnecessary abstention | Format error | Harmful | EBG − RT harm (pp) |
|---|---|---|---|---|---|
| Qwen2.5-3B | 59.5% | 3.6% | 0.0% | 2.9% | −25.2 |
| Qwen2.5-7B | 75.0% | 0.6% | 0.1% | 4.3% | −27.7 |
| Qwen3-8B | 77.8% | 0.0% | 0.0% | 4.7% | −24.5 |
| Llama-3.1-8B | 33.0% | 44.0% | 11.1% | 0.7% | **−0.3** |
| Qwen2.5-14B (secondary) | 73.5% | 1.2% | 13.8% | — | −16.0 |
| Llama-3.2-3B (format-limited) | 41.8% | 35.9% | 0.0% | — | −3.0 |

The two families fail differently, and this bounds the harm-reduction claim. The Qwen models commit to wrong values
and the mechanism stops them, which is the effect the hypotheses describe. Llama-3.1-8B abstains (44.0% of EBG runs,
60.7% of B runs) or fails to format an answer (11.1%) instead of committing; it is the least harmful model in the
study under every configuration, so there is almost no harm for the mechanism to remove, and its success gain comes
from converting abstentions into answers. Qwen2.5-14B's 13.8% format-error rate is constant across all twelve
configurations and is a harness-formatting artefact, not a mechanism effect.

---

## 6. What this analysis does not cover

The eval3 task texts, gold labels and per-run transcripts remain sealed until publication, so every statement here
is at the level of the frozen scorer's outcome categories and their rates. We did not inspect individual failing
runs. In particular we cannot say which of EBG's 867 false conflicts the arbiter could have resolved from the text
and which are items where reporting a conflict is correct, nor can we confirm that the Phase 1 failure mechanisms
(M8 label-following, M9 enforcement of metadata labels, M11 false resolution under enforcement) are what produced
the eval3 residue. Both require a transcript study after the data release.
