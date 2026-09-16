# AGENTRUN 2.0 — Paper Review Notes

**Reviewer:** Claude Code (acting as peer reviewer)
**Date:** 2026-09-17
**Paper:** `docs/paper_agentrun_2.0.md`

---

## Major Corrections Made

### 1. Citation Errors — FIXED
- **Removed**: Reference #10 (Roberts et al., 2023 — "How Much Context Do LLMs Need?") — this paper is about context window sizing, NOT benchmark contamination. Misapplied in the original draft.
- **Removed**: Reference #11 (Mialon et al., 2023 — "CLUTRR") — this paper is an inductive reasoning benchmark for children, NOT about agent evaluation or contamination. Completely misapplied.
- **Reduced**: Total reference count from 11 to 9. All remaining citations are verified and directly relevant.

### 2. Causal Language — SOFTENED
- **Original**: "the full +5 improvement is therefore attributable to the augmented training data"
- **Revised**: "The observed aggregate recovery from V1 to V2 (18/23 → 23/23) is associated with the transition from the E4 condition (V1 adapter + V2 parser) to the V2 condition (V2 adapter + V2 parser), which introduced 11 targeted training trajectories while retaining the corrected parser."
- Added explicit caveat: "We emphasize that this decomposition isolates the parser effect but does not provide a clean causal estimate of data augmentation alone, as the trajectories were curated based on observed V1 failures."

### 3. Introduction Strengthened
- Added explicit framing of the parser-as-infrastructure problem before presenting the experimental setup
- Clarified that the parser sits between model output and tool execution, making it a confound that is easily misattributed
- Removed vague "fundamental identification problem" phrasing; replaced with concrete description of the confound

### 4. Limitations Section — EXPANDED
Added three new limitation points:
- **Evaluation adaptation risk**: v2's training data was curated using knowledge of v1's failures on the same benchmark, introducing potential overfitting to benchmark-specific patterns even without direct exposure to test prompts.
- **Single-run per condition**: Without seed variation, we cannot distinguish signal from stochastic noise in generation. The 0-parser-effect finding is point-estimated, not interval-estimated.
- **Parser regression mechanism unverified**: We hypothesize that Pass 2's greedy first-JSON extraction caused the two regressions (`multi_search_weather`, `adversarial_chained_search_calc`), but without E4 trace data we cannot confirm this. The hypothesis is plausible but unverified.

---

## Claims Intentionally Weakened

| Original Claim | Revised Claim | Reason |
|---|---|---|
| "the full +5 improvement is attributable to the augmented training data" | "the observed aggregate recovery ... is associated with the transition ... which introduced 11 targeted training trajectories" | Cannot claim causation without randomized control |
| "the primary bottleneck was model capability rather than serving infrastructure" | "suggesting that for this benchmark, the primary bottleneck was model capability rather than serving infrastructure" | "Suggesting" not "establishing" |
| "Parser fixes are necessary but not sufficient" | Kept, but qualified with "on this benchmark" | Claim is about this specific setting, not universal |
| "infrastructure improvements can have non-monotonic effects" | Kept, with mechanism hypothesis labeled as such | Mechanism is inferred, not proven |

---

## Evidence Limitations

| Aspect | Status | Impact |
|---|---|---|
| E4 per-task traces (tool_calls, final_answer, latency) | **NOT AVAILABLE** | Cannot verify *why* each task was recovered/regressed at the trace level |
| E4 raw JSON schema | Minimal (task_id + passed/failed only) | Limits forensic analysis of failure modes |
| Multi-seed variance | **NOT COMPUTED** | All scores are point estimates; no confidence intervals |
| Cross-model generalization | **NOT TESTED** | Results may be Qwen-specific |
| Fresh held-out benchmark (E8) | **NOT CONDUCTED** | Generalization to unseen tasks is unknown |

---

## What Would Strengthen This Paper (Future Work)

1. **E7 — Multi-seed evaluation**: Run V1, E4, and V2 with 3+ random seeds each. Report mean ± std per condition. This would convert point estimates into interval estimates.

2. **E8 — Fresh held-out benchmark**: Construct a new 20-25 task benchmark with matched category distribution but novel task instances. Evaluate Base, V1, E4, and V2 on it. This would test whether the E4 result generalizes beyond the original benchmark.

3. **E5 — Random-augmentation control**: Train a V2-random variant with 46 trajectories drawn randomly (not targeted at V1 failures). Compare V2-targeted vs. V2-random on E4's benchmark. This would isolate "targetedness" from "quantity."

4. **Trace-level E4 re-run**: Re-run E4 with full trace capture (tool_calls, final_answer, latency per task). This would verify the hypothesized mechanism for the two parser regressions.

5. **Parser-failure-flag metric**: Add a binary flag to `eval/harness.py` that records whether a task failed due to parser mis-extraction vs. model error vs. tool error. This metric directly answers the paper's research question at the per-task level.

---

## Final Verdict

**Paper readiness: Workshop-submission quality (with minor revisions)**

The paper correctly identifies and resolves the parser/data confound that was the project's central weakness. The E4 ablation is well-designed and the decomposition (parser effect = 0, data effect = +5) is clearly presented. The writing is measured and avoids overclaiming.

**Before submission, address:**
1. Add the expanded limitations section (already done in this revision)
2. Consider adding a brief "Threats to Validity" subsection in the methodology
3. The paper would benefit significantly from E7 (multi-seed) results — if those are unavailable, the limitation should be stated more prominently in the results section, not just in limitations

**Overall assessment**: This is a honest, well-controlled small-scale study that makes a genuine contribution to understanding confounds in agent fine-tuning evaluation. It is not a sweep­ing claim but a careful measurement — and that is exactly what the field needs more of.
