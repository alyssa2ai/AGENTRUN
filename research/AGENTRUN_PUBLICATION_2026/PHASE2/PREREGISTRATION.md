# Pre-registration: Phase 3 confirmatory evaluation (FROZEN 17 November 2026)

**Status, 17 November 2026: FROZEN by the local commit that records this file's sha256 in `FREEZE_eval3.json` (`preregistration_sha256`), made before the first Phase 3 submission.** The ⏳ items of the 16 November draft were filled from measured p2val2 data (§9) and from the sealed eval3 *counts* (268 valid tasks, 135 families, taken from the seal manifest and a count-only query; no task content, label or outcome was read). **No eval3 outcome has been seen.** Nothing here may be changed after the freeze in response to eval3 results; a later change is a documented protocol amendment.

## 1. Research question

For small open-weight tool-using agents with persistent memory: does evidence-basis arbitration of conflicting memory records, with enforcement gated on the strength of that evidence (EBG), give more correct terminal answers than enforcing a lexical temporal arbiter (RT), without adding harm on genuine conflicts?

## 2. Hypotheses

| # | Hypothesis | Test | Falsified if |
|---|---|---|---|
| **H-primary** | EBG − RT > 0 in task success on eval3 primary items, pooled over the primary models and decodings | §8, Holm family | the Holm-adjusted p ≥ 0.05, **or** the 95% CI lies at or below 0 (the latter is reported as evidence against) |
| S1 | EBG − T > 0 (enforcement on evarb vs. advice on TEA) | Holm family | as above |
| S2 | EBG − LG > 0 (deterministic arbiter vs. LLM arbiter under the same gated policy) | Holm family | as above |
| S3 | EBG − B > 0 (vs. no labels) | Holm family | as above |
| S4 (harm) | harmful-answer rate (wrong value, stale value, unsupported claim, arbitrary pick) EBG ≤ RT, and arbitrary-pick on genuine conflicts EBG ≤ RT | reported with CIs; one-sided interpretation | EBG's harmful rate exceeds RT's with a 95% CI excluding 0 |
| E1–E5 (exploratory, BH) | EB − T; EBG − EB (value of enforcement); EBG − EBG-all (gating); EBG − EBG-unsafe (safe submission); EBG − EBG-noR3 (search-before-submit); per-model and per-category effects; LG − LA | BH within the exploratory set | not confirmatory; no claim rests on them |

## 3. Frozen materials

| Item | Frozen as |
|---|---|
| Mechanism | evarb-0.2, `FREEZE_evarb.json` (12 files + 3 frozen dependencies, frozen 2026-11-14T08:14:16Z) |
| Harness, prompts, scorer | `memlab.py` sha256 `dc28584c…`; `hf_client.py` hash recorded in every run manifest |
| Runner / analysis | `scripts/run_p2.py`, `scripts/analyze_p2.py` (hashes in `FREEZE_evarb.json`) |
| Evaluation data | eval3, sealed on the cluster; sealed 16 Nov 2026 10:46 UTC by Slurm job 4200; hashes in `FREEZE_eval3.json` |
| This document | sha256 recorded in `FREEZE_eval3.json` at freeze |

## 4. Model configurations

| Role | Model | Snapshot | Decodings |
|---|---|---|---|
| primary | Qwen2.5-3B-Instruct | cluster HF cache, recorded per run | greedy + T=0.7 seeds 1, 2, 3 |
| primary | Qwen2.5-7B-Instruct | 〃 | greedy + 3 seeds |
| primary | Qwen3-8B (thinking disabled; added 16 Nov 2026 before any eval3 run) | 〃 | greedy + 3 seeds |
| primary (second family) | Llama-3.1-8B-Instruct (`0e9e39f2…`) with `evarb.clients.FamilyClient` | 〃 | greedy + 3 seeds |
| secondary | Qwen2.5-14B-Instruct (`cf98f3b3…`) | 〃 | greedy only; reported separately (also the eval3 writer and an annotator) |
| format-limited | Llama-3.2-3B-Instruct | 〃 | greedy only; reported separately, never pooled (failed the 95% readiness criterion) |

bf16, one L40, `max_new_tokens` and chat-template settings as in the run manifests; base seed 20261111 for greedy runs.

Configurations, all 12 per cell: B, G, R, T, RT, EB, **EBG**, LA, LG, EBG-all, EBG-unsafe, EBG-noR3 (`SYSTEM_ARCHITECTURE.md` §4).

## 5. Dataset and split boundaries

- eval3: 276 skeleton items, 23 categories × 12; **268 mechanically valid tasks in 135 families** (category × attribute; the 138 of the draft was an estimate; verified from the sealed file by a count-only query); entities from name slice [14000:17600], distractors [17600:20000], disjoint from every other split (checked by `seal_checks.py` inside the sealed job).
- Gold fixed by the skeleton before any text exists; texts by Qwen2.5-14B, blind annotation by Llama-3.1-8B and Qwen2.5-14B. **No human validation.**
- **Primary item set: every mechanically valid eval3 item** (gold fixed by the skeleton before any text existed; texts validated by `assemble.py`).
- **Secondary (sensitivity) item sets, reported, not tested for the claims:** (a) both annotators agree with gold at non-low confidence (`eval3_PRIMARY_IDS.json`, hash in `FREEZE_eval3.json`); (b) the Qwen2.5-14B annotator agrees with gold.
- **Why the primary set changed (decided 16 Nov 2026, 10:14 UTC, from p2val2 annotation statistics only, before any p2val2 mechanism or baseline output was opened and before any eval3 output exists):** on p2val2 the double-agreement rule kept 51/90 items and removed whole categories, because the blind annotators fail at the temporal reasoning the benchmark tests (Llama-3.1-8B: 0/4 on `update_record_time`, `three_value_chain`, `valid_time_same_import`, `hypothetical_change`, `quoted_claim`; Qwen2.5-14B: 2/4 on the first three). The texts of e.g. `update_record_time` items are plain, unambiguous statements that differ only by record date. Restricting the confirmatory set to items small models already agree on would bias it toward easy items and drop the categories under test. Record: `data/p2val2/PRIMARY_RULE_DECISION.md`.
- Every development split (dev fixtures, p1dev, p1hold, p2dev, p2val, p2val2) is excluded from confirmatory analysis.

## 6. Exclusions

- Items failing the mechanical validation in `assemble.py` (no own value, no entity, value in question) are excluded before sealing; ids only are recorded.
- Flagged items (annotator disagreement or low confidence) are excluded from the primary analysis and reported in a secondary analysis.
- **No run-level exclusions.** Unparsable outputs, harness errors and step-limit hits are failures.

## 7. Missing runs

A (task, config) pair with no row, or with a harness error, is scored as a failure (`outcome = missing`) and counted separately. A cell (model × decoding) with > 5% missing pairs is re-submitted once (the runner resumes); missing pairs remaining after that are failures. A whole cell that cannot run is reported as missing; the primary test is then run on the cells that exist, and this is stated.

## 8. Statistical analysis (`scripts/analyze_p2.py`, frozen)

- **Unit:** task. Success per task = mean over the decodings of one model; contrasts are paired within model and decoding.
- **Item set:** the primary subset is written with `scripts/subset_tasks.py` (counts and hash printed only) and passed to `analyze_p2.py --tasks`; the flagged complement is analysed the same way and reported separately.
- **Clustering:** family = (category, attribute). The test is a two-sided **sign-flip permutation of family-level summed differences**, families pooled across models (a family's sign is flipped for all models together); 100,000 seeded Monte-Carlo permutations (> 20 families).
- **CI:** 95% percentile bootstrap over families (10,000 seeded resamples) of the mean task-level difference.
- **Multiplicity:** Holm over {EBG−RT, EBG−T, EBG−LG, EBG−B}, pooled over the primary models, α = 0.05. Everything else is exploratory with BH.
- Per-model results, per-category results, harmful-answer rates and the secondary/format-limited models are reported for every contrast, without tests counted toward the claims.

## 9. Power (computed 17 Nov 2026)

`scripts/power_phase3.py` on the measured p2val2 agent-level greedy runs (90 tasks; Qwen2.5-3B, Qwen2.5-7B, Llama-3.1-8B, Qwen3-8B): paired task differences per contrast, stratified bootstrap to eval3's **135 families × 2 items × 4 models**, sign-flip test at the strictest Holm level (0.0125), 2,000 simulations (`data/POWER_phase3.md|json`).

| Contrast | measured pp (p2val2) | power at measured / at half (Holm α) |
|---|---|---|
| EBG−RT (H-primary) | +15.8 | 1.00 / 0.961 |
| EBG−T | +12.5 | 1.00 / 0.883 |
| EBG−LG | +13.1 | 1.00 / 0.528 |
| EBG−B | +18.6 | 1.00 / 0.996 |

The seed rule is satisfied for H-primary (power at half the measured effect ≥ 0.8), so the number of seeds stays at 3. EBG−LG is under-powered at half the effect (0.53); this is stated, not corrected. The power simulation treats p2val2's effect as the truth; it is a development estimate, and p2val2 effects are for an item set with 90 single-item families, whereas eval3 has two items per family.

## 10. Stopping criteria

- The campaign runs to completion of all 18 cells (`PHASE3_EXECUTION_PLAN.md`); there is no interim efficacy look.
- Stop early only for an integrity failure: freeze mismatch, seal mismatch, or a runner defect. A defect fix restarts the affected cells from scratch, and the incident is reported.
- If the primary cells finish but the secondary ones cannot, the confirmatory analysis is run on the primary cells and the rest is reported as not run.

## 11. Cost and latency (reported, not tested)

Per configuration: model calls per run, LLM-arbiter calls per run, wall latency (single-occupancy job), tokens. Budget: `PHASE3_EXECUTION_PLAN.md` §2.

## 12. Known limitations of the frozen mechanism and data (stated before any eval3 outcome)

- **Long-range negation:** a negator more than 4 tokens before the cue is missed. A same-date record such as "It is not the case that, after the long review, the team was revised from 40 to 60" is resolved to 60 with **strong** strength (enforceable). Pinned in `tests/test_known_limitations.py`. eval3 items of this form, if any, count against evarb as written; evarb-0.2 is not changed.
- **Found on p2val2 (validation, 16 Nov), not fixed:** (a) `negated_both_stand` is resolved to the rival (moderate) instead of a contradiction (0/4); (b) "correcting" is not a correction cue, so a same-day "correcting … to Y" record yields a strong contradiction (enforceable). Both pinned in `tests/test_known_limitations.py`.
- **Lexical, English cue lists;** paraphrases outside them fall back to time order.
- **ISO-only value dates:** the v2 writer must keep every value verbatim, so date values in eval3 appear in ISO form; long-form value dates are not tested (`data/p2val/P2VAL_EXCLUSION_REVIEW.md`).
- **No human validation of eval3;** the writer (Qwen2.5-14B) is also one annotator and a secondary model.
- Any later modification of evarb is a new development version (evarb-0.3+) and is not covered by this pre-registration.

## 13. Outcomes that would falsify the contribution

- EBG − RT ≤ 0 (CI) → evidence-basis gating does not improve on enforcing the lexical arbiter.
- EBG − LG ≤ 0 → a deterministic arbiter gives no advantage over an LLM arbiter under the same policy.
- EBG harmful rate > RT harmful rate → gating does not remove the false-resolution harm found in Phase 1 (H4).
All are reported whatever their sign.

## 14. Verification of the procedures (16 November 2026, before any real Phase 2 or Phase 3 agent run)

| Check | How | Result |
|---|---|---|
| The frozen loop runs all 12 configurations, incl. LA/LG, and writes the run format the analysis expects | `scripts/dryrun_pipeline.py` with three SIMULATED agents on p2val (77 tasks × 12 configs × 3), CPU | 0 loop exceptions |
| Missing (task, config) rows are scored as failures and counted | the dry run deletes 1% of rows | counted as `missing`; denominators stay complete (231 per config) |
| Pairing within model and decoding; family sign-flip pooled across models; family bootstrap CI | `analyze_p2.py` on the dry-run files; `tests/test_analysis.py` | 77 families, 231 task pairs per contrast; exact sign-flip and bootstrap unit tests pass |
| Holm applied only to {EBG−RT, EBG−T, EBG−LG, EBG−B} pooled over models; everything else BH and labelled exploratory | dry-run output: `confirmatory: true` only for those four "ALL" rows | as specified |
| Power script runs on the run format and responds to effect size | `power_phase3.py` on the dry run; `tests/test_phase2_tools.py` | runs; power increases with effect and family count |
| Primary-subset helper | `tests/test_phase2_tools.py::test_subset_tasks` | pass |
| Generators: entity / distractor slices disjoint, no duplicates, no gold in writer input, deterministic | `benchmark/audit_generators.py` (counts only), locally and on the cluster copy | all hard checks pass; p2val2 skeleton sha256 `7494eb22…` identical on both |

The dry-run numbers are meaningless (simulated agents) and are not reported anywhere as results.

## 15. p2val2 observations known before the freeze (not eval3)

Agent level, greedy, 90 valid items, four models (`data/AGENT_p2val2.md`): EBG−RT +15.8 pp [9.2, 22.8] pooled, but per model +10.0 / +24.4 / +27.8 / **+1.1** (Qwen2.5-3B / 7B / Qwen3-8B / Llama-3.1-8B). EBG−LG +13.1 pp pooled. Enforcement of every label (EBG-all) scored higher than gated EBG on p2val2 (243/360 vs 218/360), with more harmful answers (29 vs 14); the ungated variant is an exploratory contrast (E3), not the primary. Llama-3.1-8B shows no EBG benefit over RT, with 9 format failures and heavy abstention in every configuration. These observations were available before the freeze and do not change the hypotheses: if the Llama result repeats on eval3, it is a failure to generalise across families and is reported as such.

## 16. Chronology disclosure for the p2val2 audit

`P2VAL2_ITEM_AUDIT.md` (sha256 `1fa5cfa1…`, mtime 10:03:05 UTC) predates every p2val2 mechanism or LLM-arbiter output file on the cluster (earliest 10:05:03 UTC); the blind annotation outputs (10:01 and 10:03:59 UTC) existed around it, and the hash record `PRE_OUTCOME_HASHES.txt` was written at 10:15 UTC, after all outputs existed. That the audit was done before outcomes were opened rests on file timestamps and the auditor's own statement; the auditor is the mechanism's maintainer. It is a documented quality check, **not** an independent or blind audit.
