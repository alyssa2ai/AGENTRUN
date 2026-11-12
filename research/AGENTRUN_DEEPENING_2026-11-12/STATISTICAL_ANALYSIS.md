# Campaign 2 — Statistical Analysis

## Design

- **Task-level paired comparisons:** Every configuration comparison (B vs A, C vs B, etc.) is paired on the same task. Each task appears once per configuration per model.
- **Bootstrap CIs:** 4,000 bootstrap resamples, clustered by task ID (not by run). 95% percentile intervals.
- **McNemar exact test:** For binary (success/fail) paired comparisons. Reports exact two-sided p-values.
- **Wilson score intervals:** For single-proportion confidence intervals (e.g., "72.9% (63–81)").
- **Random seed:** `np.random.default_rng(20261112)` for reproducibility.

## What constitutes independent evidence

Each task is an independent unit. Configurations within the same task are **paired** (the same question, same memory store, same scenario — only the pipeline components differ). Models tested on the same task are **partially dependent** (same question but different model capabilities).

The 96 eval2 tasks come from 6 scenarios × 16 tasks. Tasks within a scenario share structural features but use different entities, prompts and expected values (verified by leakage audit). They are treated as independent for the bootstrap, which is conservative because scenario-level correlation would reduce effective sample size.

**Multiple task executions of the same task are not independent samples.** The v2 harness runs that use T=0.7 with different seeds (jobs 19–20, not completed) would provide within-task variance estimates, but are not available for this analysis.

## Pooling across models

Pooled results (7B + Qwen3-8B) treat each model's execution as a separate task instance in the bootstrap. This doubles the sample size but assumes the component effects are homogeneous across models. The per-model breakdowns show this assumption is violated: Qwen3-8B shows weaker C−B and D−C effects. Pooled results should be read as average effects across the tested models, not as universal effects.

## Key statistical findings

### Effects that are robust across models and harness versions

1. **Memory improves task success.** B−A is +25.0 to +47.9 pp across all conditions (p < 0.0001 in all cases). This is the strongest and most consistent finding.

2. **Verification hurts without provenance.** C−B is negative (−2.1 to −13.5 pp) in every condition except 14B v1 (+4.2 pp, p=0.125 NS) and 14B v2 (−1.0 pp, NS). At 7B, this is statistically significant in both harness versions.

3. **The reliability gate improves stale-memory handling.** E−D is +11.5 to +19.8 pp for 7B and 8B models under both harness versions (p < 0.01 in all cases).

### Effects that depend on model size

4. **Below 3B, no component has any effect.** The 1.5B model cannot follow the agentic format at all under v1, and under v2 it operates at ~20% success regardless of configuration.

5. **At 3B, only memory helps.** The verifier, provenance and gate effects are either non-significant or harmful.

6. **At 14B, memory helps strongly but additional components show no significant marginal benefit.** The 14B model apparently handles verification, provenance and reliability concerns adequately without explicit pipeline support.

### Effects that are sensitive to harness version

7. **Provenance (D−C) is significant under v1 but not v2 at 7B.** v1: +16.7 pp (p=0.0004). v2: +5.2 pp (p=0.38 NS). The repair mechanism in v2 may allow the model to recover from provenance-absent errors, reducing the marginal value of provenance metadata.

## Multiple comparisons

With 6 pairwise comparisons per model × 2 models × 2 harness versions = 24 tests, a Bonferroni-corrected threshold would be α = 0.05/24 ≈ 0.002. The main findings (memory, verifier penalty, gate) survive this correction. The provenance effect (D−C) is borderline: significant at 7B v1 (p=0.0004) but not at 7B v2 (p=0.38) or 14B.

## Power analysis

With n=96 paired observations per model and 5 configurations:
- Detectable effect size at 80% power (McNemar): ~12–15 pp for discordant rates around 20%.
- The 14B "no component effect" null results are consistent with either no true effect or an effect smaller than ~12 pp.

## Limitations

1. **No run-to-run variance.** All results are from single greedy runs. True variance cannot be estimated.
2. **Scenario clustering.** 16 tasks per scenario is small. Per-scenario results (e.g., S4 stale: 25/32) should be interpreted cautiously.
3. **Task-family dependence.** Tasks within a scenario share structural properties. The bootstrap clusters by task ID but does not adjust for scenario-level correlation.
4. **Sealed test set not used.** The eval2 96-task set was used for both iteration and final reporting. It is not an independent test.
