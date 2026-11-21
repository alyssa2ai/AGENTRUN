# 4. Experimental design

> Draft, 18 November 2026. Source of record: `PHASE2/PREREGISTRATION.md` (frozen 17 November 2026). Supporting: `PHASE2/FREEZE_eval3.json`, `PHASE2/FREEZE_evarb.json`, `PHASE2/PHASE3_EXECUTION_PLAN.md`, `PHASE2/data/p2val2/PRIMARY_RULE_DECISION.md`, `PHASE3/LIMITATIONS.md`. Where this section paraphrases the preregistration, the preregistration is normative. No eval3 outcome is reported here.

## 4.1 Preregistration and freeze

The confirmatory evaluation was preregistered and frozen on **17 November 2026**, before the first Phase 3 submission and before any eval3 outcome existed. The freeze consists of:

| Item | Frozen as | Record |
|---|---|---|
| Mechanism | Evarb-0.2; 12 files and 3 frozen dependencies; frozen 2026-11-14T08:14:16Z | `FREEZE_evarb.json`; its LF-normalised sha256 `5ae8ebe3c2b110bd89348e113c3b0b7803efb6ec0020275a0dd1ab75fc2b7ad8` is recorded in the eval3 provenance (`FREEZE_eval3.json`, `provenance.freeze_evarb_sha256`) |
| Harness, prompts, scorer | `memlab.py`, sha256 `dc28584c518d18b6b2b6f684be77269f9ca00d502939ecf845985635d93b62df` | `FREEZE_evarb.json` |
| Runner and analysis | `scripts/run_p2.py` (`6be2011c…`), `scripts/analyze_p2.py` (`76fc67cc…`) | `FREEZE_evarb.json` |
| Evaluation data | eval3, built and sealed on the cluster by Slurm job 4200 (built 2026-11-16T10:46:42Z); 13 sealed files | `FREEZE_eval3.json` (`sealed_files`, `sha256sums_file_sha256` `c069d70f…`), written 2026-11-17T08:57:24Z |
| Preregistration | `PREREGISTRATION.md`, sha256 `221013b3cee87c003894ba1837e8a62b586e7acf02c22f0c6fbb59c34a6218d1` | `FREEZE_eval3.json` (`preregistration_sha256`) |

The preregistration states that nothing in it may be changed after the freeze in response to eval3 results, and that any later change is a documented protocol amendment. Any later modification of Evarb is a new development version (evarb-0.3 or later) and is not covered.

**Integrity gates.** At the start of every cell, the runner verifies the `FREEZE_evarb.json` hashes, checks the sealed eval3 files against their sha256 sums, and refuses a task file whose hash differs from the frozen one (`run_p2.py --expect-sha`) (`PHASE3_EXECUTION_PLAN.md` §3). The preregistration's own hash is checked inside each job (`PHASE3/LIMITATIONS.md`, execution notes).

## 4.2 Hypotheses

**Table 4.1.** Preregistered hypotheses (`PREREGISTRATION.md` §2).

| # | Hypothesis | Status in the analysis | Falsified if |
|---|---|---|---|
| **H-primary** | EBG − RT > 0 in task success on eval3 primary items, pooled over the primary models and decodings | confirmatory, Holm family | Holm-adjusted p ≥ 0.05, or the 95% CI lies at or below 0 (the latter reported as evidence against) |
| S1 | EBG − T > 0 (enforcement on Evarb vs advice on TEA) | confirmatory, Holm family | as above |
| S2 | EBG − LG > 0 (deterministic vs LLM arbiter under the same gated policy) | confirmatory, Holm family | as above |
| S3 | EBG − B > 0 (vs no labels) | confirmatory, Holm family | as above |
| S4 (harm) | harmful-answer rate EBG ≤ RT; and arbitrary-pick rate on genuine conflicts EBG ≤ RT | reported with CIs, one-sided interpretation | EBG's harmful rate exceeds RT's with a 95% CI excluding 0 |
| E1–E5 | EB − T; EBG − EB (enforcement); EBG − EBG-all (gating); EBG − EBG-unsafe (safe submission); EBG − EBG-noR3 (search-before-submit); per-model and per-category effects; LG − LA | exploratory, Benjamini–Hochberg within the exploratory set | not confirmatory; no claim rests on them |

The harmful outcomes are `wrong_value`, `stale_value`, `unsupported_claim` and `arbitrary_pick` (Section 3.2). The preregistration also lists outcomes that would falsify the contribution (§13): EBG − RT ≤ 0 (CI); EBG − LG ≤ 0; EBG harmful rate > RT harmful rate. All are to be reported whatever their sign.

## 4.3 Models

**Table 4.2.** Models and decodings (`PREREGISTRATION.md` §4).

| Role | Model | Decodings | Notes |
|---|---|---|---|
| primary | Qwen2.5-3B-Instruct [@qwen2024qwen25] | greedy; T = 0.7 with seeds 1, 2, 3 | |
| primary | Qwen2.5-7B-Instruct | greedy + 3 seeds | |
| primary | Qwen3-8B [@yang2025qwen3] | greedy + 3 seeds | thinking disabled; added 16 Nov 2026, before any eval3 run |
| primary (second family) | Llama-3.1-8B-Instruct [@grattafiori2024llama3] (snapshot `0e9e39f2…`) | greedy + 3 seeds | run through the `evarb.clients.FamilyClient` adapter |
| secondary | Qwen2.5-14B-Instruct (snapshot `cf98f3b3…`) | greedy only | reported separately; also the eval3 writer and one annotator |
| format-limited | Llama-3.2-3B-Instruct | greedy only | reported separately, never pooled; failed the 95% format-readiness criterion (`MODEL_FAMILY_READINESS.md`) |

All models run in bf16 on one NVIDIA L40, from a local Hugging Face cache in offline mode (`HF_HUB_OFFLINE=1`), with `max_new_tokens` and chat-template settings recorded in the run manifests. The base seed for greedy runs is 20261111.

## 4.4 Cells and run matrix

A **cell** is one model under one decoding. The design has **18 cells**: four primary models × four decodings (16 cells), plus Qwen2.5-14B greedy and Llama-3.2-3B greedy. Every cell runs all 268 valid eval3 tasks under all 12 configurations of Table 3.3, i.e. 3,216 (task, configuration) runs per cell and 57,888 runs in total (derived arithmetic; the execution plan states the bound ≤ 276 tasks × 12 configurations per cell).

Primary cells are scheduled before the secondary ones, so that a confirmatory analysis is possible on complete primary cells if the campaign is stopped (`PHASE3_EXECUTION_PLAN.md` §3). (The execution plan, dated 16 November, lists 14 cells with 12 primary ones because it predates the addition of Qwen3-8B; the preregistration's four primary models give 16 primary cells and 18 cells in all.)

## 4.5 Unit of analysis, item set and clustering

- **Unit:** the task. For each model, task success is the mean over that model's decodings; contrasts are paired within model and decoding (`PREREGISTRATION.md` §8).
- **Item set:** the primary item set is every mechanically valid eval3 item (268 tasks; Section 4.8). It is written with `scripts/subset_tasks.py`, which prints counts and a hash only, and passed to `analyze_p2.py --tasks`.
- **Clustering:** a family is a (category, attribute) pair. eval3 has 135 families among its valid tasks (Section 5).

## 4.6 Test, confidence intervals and multiplicity

- **Test:** two-sided sign-flip permutation test of family-level summed differences. Families are pooled across models, and a family's sign is flipped for all models together. 100,000 seeded Monte Carlo permutations.
- **Confidence interval:** 95% percentile bootstrap over families of the mean task-level difference, 10,000 seeded resamples.
- **Multiplicity:** Holm correction over the four confirmatory contrasts {EBG − RT, EBG − T, EBG − LG, EBG − B}, pooled over the primary models, at α = 0.05. All other contrasts are exploratory and controlled with Benjamini–Hochberg [@holm1979simple; @benjamini1995fdr]. The sign-flip permutation test follows the standard randomisation argument for paired differences [@good2005permutation], applied at the family level; the percentile bootstrap [@efron1979bootstrap] resamples whole families, as in cluster bootstrapping [@field2007clustered].
- **Reported without tests counted toward the claims:** per-model and per-category results, harmful-answer rates, and the secondary and format-limited models, for every contrast.

The analysis was verified before any real agent run with a dry run of three simulated agents on p2val (77 tasks × 12 configurations × 3), which checked that all 12 configurations run, that deleted rows are scored as missing failures with complete denominators, that pairing and family pooling behave as specified, and that only the four Holm-family pooled rows are marked confirmatory (`PREREGISTRATION.md` §14). The dry-run numbers are meaningless and are not reported.

## 4.7 Exclusions, missing runs and stopping rules

**Run-level exclusions.** None. Unparsable outputs, harness errors and step-limit hits are failures (`PREREGISTRATION.md` §6).

**Missing runs** (§7). A (task, configuration) pair with no row, or with a harness error, is scored as a failure (`outcome = missing`) and counted separately. A cell with more than 5% missing pairs is re-submitted once; the runner resumes and skips finished pairs. Missing pairs that remain after that are failures. A whole cell that cannot run is reported as missing; the primary test is then run on the cells that exist, and this is stated.

**Stopping** (§10). The campaign runs to completion of all 18 cells. There is no interim efficacy look. The only grounds for stopping early are integrity failures: a freeze mismatch, a seal mismatch, or a runner defect. A defect fix restarts the affected cells from scratch and is reported. If the primary cells finish but the secondary ones cannot, the confirmatory analysis is run on the primary cells and the rest is reported as not run.

**Cost and latency** (§11) are reported per configuration and not tested: model calls per run, LLM-arbiter calls per run, wall-clock latency and tokens.

## 4.8 The primary item set: a documented change and a wording inconsistency

**The change.** An earlier draft of the design defined the primary item set as the items on which both blind annotators agreed with the gold label at non-low confidence. On 16 November 2026 at 10:14 UTC this was changed to **all mechanically valid items** (`data/p2val2/PRIMARY_RULE_DECISION.md`; `PREREGISTRATION.md` §5). The decision was taken after the p2val2 annotations were available and before any mechanism, baseline or LLM-arbiter output on p2val2 was opened, and before any eval3 output existed. Only annotator-versus-gold agreement per category was examined. On the 90 valid p2val2 items, the double-agreement rule kept 51 items and left six categories with no primary item, because the small blind annotators failed the temporal-reasoning categories the benchmark is designed to test (for example, 0 of 4 for Llama-3.1-8B on `update_record_time`, `valid_time_same_import`, `three_value_chain`, `hypothetical_change` and `quoted_claim`). The preregistration argues that restricting the confirmatory set to items small models already agree on would bias it toward easy items and remove the categories under test. The double-agreement set (`eval3_PRIMARY_IDS.json`, hash in `FREEZE_eval3.json`) and the set on which the Qwen2.5-14B annotator agrees with gold are retained as **secondary sensitivity sets**, reported but not tested for the claims.

**The inconsistency.** The frozen preregistration is internally inconsistent on this point. §5 states that the primary item set is every mechanically valid eval3 item. §6 ("Exclusions") still contains the earlier rule: "Flagged items (annotator disagreement or low confidence) are excluded from the primary analysis and reported in a secondary analysis." §8 likewise refers to "the flagged complement" being analysed separately. The §6 and §8 wording was not updated when §5 was revised. **The analysis follows §5 and `PRIMARY_RULE_DECISION.md`**: the primary set is all 268 valid items, and the flagged and double-agreement subsets are sensitivity analyses. We report this as a defect in the frozen document rather than correct it silently. The sensitivity results on the double-agreement subset are reported alongside the primary results so that a reader who prefers the §6 reading can apply it: on the 161-item double-agreement subset the four contrasts are +14.3, +12.7, +19.7 and +14.7 pp, all with intervals above zero and Holm-adjusted p < 0.05, against +17.1, +14.5, +15.9 and +15.3 pp on the primary set (Section 8.2). The conclusions do not depend on which reading is taken.

## 4.9 Power

Power was computed on 17 November 2026 (`scripts/power_phase3.py`; `PREREGISTRATION.md` §9) from the measured p2val2 agent-level greedy runs (90 tasks; Qwen2.5-3B, Qwen2.5-7B, Llama-3.1-8B, Qwen3-8B). Paired task differences per contrast were resampled with a stratified bootstrap to eval3's structure of 135 families × 2 items × 4 models, and tested with the sign-flip test at the strictest Holm level (0.0125), with 2,000 simulations.

**Table 4.3.** Power at the effect measured on the development split and at half that effect (`PREREGISTRATION.md` §9). The measured differences are development estimates used only for planning.

| Contrast | p2val2 difference (pp), development | Power at measured / at half |
|---|---|---|
| EBG − RT (H-primary) | +15.8 | 1.00 / 0.961 |
| EBG − T | +12.5 | 1.00 / 0.883 |
| EBG − LG | +13.1 | 1.00 / 0.528 |
| EBG − B | +18.6 | 1.00 / 0.996 |

The preregistered seed rule (power at half the measured effect ≥ 0.8 for H-primary) was met, so the number of sampled seeds stayed at three. EBG − LG is under-powered at half the development effect (0.53); this is stated, not corrected. The simulation treats the p2val2 effect as the truth. p2val2 has 90 single-item families, whereas eval3 has two items per family, so the estimate may not transfer.

## 4.10 Development observations disclosed before the freeze

The preregistration (§15) records what was known from development data at the freeze, so that readers can judge whether the hypotheses were shaped by it. On p2val2 (agent level, greedy, 90 items, four models), the pooled EBG − RT difference was +15.8 pp, but heterogeneous across models (+10.0, +24.4, +27.8 and +1.1 pp for Qwen2.5-3B, Qwen2.5-7B, Qwen3-8B and Llama-3.1-8B). Ungated enforcement (EBG-all) scored higher than gated EBG (243 vs 218 of 360) with more harmful answers (29 vs 14). Llama-3.1-8B showed no EBG benefit over RT, with 9 format failures and heavy abstention in every configuration. These observations did not change the hypotheses. The preregistration states that, if the Llama-3.1-8B result repeats on eval3, it will be reported as a failure to generalise across families, and that the ungated variant remains an exploratory contrast (E3) rather than the primary configuration.

The p2val2 item audit was performed by the mechanism's maintainer. File timestamps place it before every p2val2 mechanism and LLM-arbiter output, but the hash record was written after all outputs existed; it is a documented quality check, not an independent or blind audit (`PREREGISTRATION.md` §16).

## 4.11 Execution

Phase 3 started as Slurm array job 4233 (repository commit `d82155c`). Deviations from the planned execution that were recorded before any eval3 outcome was analysed are listed in Section 13.6. **Results.** All 18 cells completed: 3216 rows each, 57,888 in all, with 0 missing pairs, 0 duplicates and 0 harness-error rows, and every cell's last Slurm segment exited cleanly. Nine cells ran as the original array, the remainder under a two-lane controller; two cells were interrupted by an unplanned node reboot on 2026-11-20 and resumed after the damaged tail of each output file was quarantined, without losing a completed run (Section 11 and `PHASE3/PHASE3_DEVIATIONS.md`).
