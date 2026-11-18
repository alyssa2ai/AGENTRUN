# 6. Threats to validity and limitations

> Draft, 18 November 2026. Sources: `PHASE3/LIMITATIONS.md` (written 17 November 2026 before any eval3 outcome, with execution notes added 18 November before any eval3 outcome was analysed; "to be extended, never softened, after results"), `PHASE2/PREREGISTRATION.md` §12, §15–16, `PHASE2/BENCHMARK_EVAL3_SPEC.md` §2, `PHASE2/BASELINE_COMPARISON.md` §4. Everything in this section was fixed before the confirmatory results were known. A paragraph on limitations revealed by the results will be added: [RESULTS PENDING — filled from PHASE3 verified outputs].

## 6.1 Construct validity: the data

- **No human validation.** No human authored or adjudicated eval3. The texts were written by Qwen2.5-14B, and the only independent checks are two model annotators. On the development split p2val2 they agreed with gold on 58/90 (Llama-3.1-8B) and 71/90 (Qwen2.5-14B) items; on eval3 on 174/268 and 232/268 (`FREEZE_eval3.json`). Annotator agreement is not ground truth, and annotator disagreement may reflect annotator error rather than a faulty item.
- **Writer, annotator and evaluated model overlap.** Qwen2.5-14B wrote the texts, is one of the two annotators, and is a secondary evaluated model. Its results are reported separately for this reason.
- **The author defined the categories.** The categories and their semantics were chosen by the mechanism's author and are encoded in the skeleton generator. What is independent of the author is the wording of every record and historical question and the blind check that the wording carries the intended meaning, not the choice of what to test. A benchmark designed by the author of the method may favour the method's notion of evidence.
- **Synthetic, templated records.** eval3 has heavy surface regularity: the seal checks report many duplicated masked texts and 8-gram template overlaps with development texts, and 16 of 19 masked brief templates are shared with p2val2. Items are synthetic templates, not natural memory logs. Current-state question templates and distractor texts are shared with every split.
- **Untested surface forms.** Value dates appear in ISO form only; 8 of 276 skeleton items were excluded mechanically (values written in long-form dates), so long-form value dates are untested. Text is English only.
- **Implicit conflicts are out of scope.** eval3 tests conflicts and resolutions signalled lexically or by metadata. Conflicts without explicit cues, as in STALE [@chao2026stale], are not tested; Evarb is expected at best to fall back to time order or leave them unresolved.

## 6.2 Construct validity: the mechanism

- **Known failures of the frozen Evarb-0.2, stated before any eval3 outcome** (`PREREGISTRATION.md` §12; pinned in `PHASE2/tests/test_known_limitations.py`):
  - *Long-range negation:* a negator more than four tokens before the cue is missed. A same-date record such as "It is not the case that, after the long review, the team was revised from 40 to 60" is resolved to 60 with strong (enforceable) strength.
  - *`negated_both_stand`:* "…does not replace X. Both figures stand until they are reconciled" is resolved to the rival value (moderate) instead of a contradiction; 0 of 4 on p2val2.
  - *"correcting" is not a correction cue:* a same-day "correcting … to Y" record yields a strong contradiction, which the gated policy would enforce.
  
  eval3 items of these forms count against Evarb as written. Evarb-0.2 was not changed.
- **Lexical, English cue lists.** Paraphrases outside the lists fall back to time order.
- **Historical and as-of questions** score zero at component level for every method, because component scoring asks for the current value; question intent is handled in the agent loop. Component-level accuracy figures therefore understate agent-level behaviour on these categories.
- **Composite primary contrast.** EBG and RT differ in the arbiter, gating, notice wording and safe submission at once. H-primary can show that the combination helps, not which element is responsible; attribution rests on exploratory ablations.

## 6.3 Internal validity: development history and analyst degrees of freedom

- **The mechanism was developed on data from the same generator family.** Evarb-0.1 was tuned on the development fixtures and looked at once on p2val, after which the semantics and the mechanism were revised. p2val2 was untouched by tuning, but its results were known before the preregistration was frozen and informed the power analysis and the primary-set decision.
- **Development evidence that bears on the hypotheses** (`PREREGISTRATION.md` §15): on p2val2 (90 single-item families), EBG − RT was about +1 pp on Llama-3.1-8B, and ungated enforcement (EBG-all) scored higher than gated EBG with more harmful answers. These were known at the freeze and did not change the hypotheses.
- **Audit not blind.** The p2val2 item audit was done by the mechanism's maintainer. That it preceded the outcome files rests on file timestamps and the auditor's own statement; the hash record was written after all outputs existed (`PREREGISTRATION.md` §16).
- **Primary-set change and wording inconsistency.** The primary item set was changed on 16 November from double-agreement items to all valid items, before any eval3 output existed and before any p2val2 mechanism output was opened. §6 and §8 of the frozen preregistration still describe the earlier rule. The analysis follows §5; the double-agreement subset is reported as a sensitivity analysis (Section 4.8).
- **Prompts** were fixed before eval3 but were developed on earlier splits.

## 6.4 Statistical conclusion validity

- **Power is a development estimate.** It treats the p2val2 effect as the truth. EBG − LG is under-powered at half the measured effect (0.53).
- **Decoding repetitions are not independent samples.** The three T = 0.7 seeds measure decoding noise, not new tasks; the family is the unit of inference.
- **Family structure differs from development.** p2val2 has single-item families; eval3 has up to two items per family, so variance estimates from development may not transfer.
- **Pooling across models.** H-primary is pooled over four primary models. A pooled effect can coexist with no effect in one model; per-model results are reported for this reason, without tests counted toward the claims.

## 6.5 External validity

- **Model scale.** Models are small open-weight (3B–14B). No frontier model is evaluated. Results do not extend to larger models.
- **One harness.** One tool-using harness (memlab, evarb loop 0.2) with a synthetic tool registry and a simple retrieval store. Other harnesses, retrieval methods or step budgets may change the results.
- **Second family partly format-limited.** The second family is represented by Llama-3.1-8B, which needs the `FamilyClient` adapter and had 9 format failures per configuration on p2val2. A conclusion about family generality therefore rests on a model that is partly format-limited. Llama-3.2-3B failed the readiness criterion and is reported separately.
- **Qwen3-8B** is run with thinking disabled.
- **Latency** is wall time under single-occupancy Slurm jobs on one L40 while other projects' CPU jobs may share the node. The T = 0.7 and 14B budget numbers were partly estimated.

## 6.6 Execution notes recorded before any eval3 outcome was analysed

The following deviations from the planned execution were recorded in `PHASE3/LIMITATIONS.md` on 18 November 2026, before any eval3 outcome was analysed.

1. **Concurrent cells.** From 18 November 08:58 UTC, cells 9–17 ran up to two at a time, one per L40 (Slurm generic resources; `CUDA_VISIBLE_DEVICES` 0 and 1), under a second controller job (`PHASE2/hpc/phase3_controller_v2.sbatch`, job 4257) that replaced retry controller 4243. Cells 0–7 ran alone on the node's GPUs. Model, decoding, configurations, data and code were unchanged, and the in-job freeze, seal and preregistration checks passed for every cell. Wall-time latency for cells that overlapped another AGENTRUN cell was measured with a second GPU process on the node, so it is not strictly single-occupancy. The measured throughput of the running Llama-3.1-8B cell did not change when the second cell started (13.9 vs 14.2 runs per minute). Latency is a reported, untested quantity (`PREREGISTRATION.md` §11).
2. **Wall-time limit for the 14B cell.** The Qwen2.5-14B cell was given a 36-hour wall-time limit on the command line (the sbatch file is unchanged), so that it would not be split by the 12-hour default.
3. **Incidental exposure of progress lines.** While checking cell 8's progress on 18 November, the last five progress lines of its Slurm log were displayed in the operator's terminal. They contained the task id, configuration and scored outcome for three eval3 runs. No task text, gold label or aggregate was seen, nothing was changed as a result, and progress has since been read from row counts only. We disclose this because the preregistration's rule is that nobody connected to the mechanism reads eval3 contents before scoring; three per-run outcome labels were seen, after the freeze and with no possible effect on frozen materials.

## 6.7 Separation from other work

This study is separate from the authors' earlier work on fine-tuning tool-using models, which used a different benchmark and asked a different question; no result from that work is used here.
