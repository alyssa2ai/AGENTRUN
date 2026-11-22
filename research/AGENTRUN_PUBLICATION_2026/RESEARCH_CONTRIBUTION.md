# Recommended research contribution

**13 November 2026.** Recommendation for the November memory-reliability study (thread 2). The October QLoRA and evaluation-confound paper (thread 1, ANTIC 2026 submission) stays a separate contribution. No compelling scientific reason was found to merge them:

- they answer different questions with different benchmarks;
- the only shared evidence is a single base-versus-adapter control run.

## 1. The single central question

> **How does the benefit of each memory-reliability component (memory access, a same-model verifier, provenance metadata, a deterministic staleness/conflict gate) depend on model capacity and on the agent harness?**

Working title: *"Where should memory reliability live? A capacity-resolved ablation of memory safeguards for small open-weight agents."*

**Why this one.** It is the only framing in which our evidence is both supported by the data and not already published (see `RELATED_WORK_AND_NOVELTY.md` §5).

- **Rejected framings.** "Provenance helps", "a deterministic gate helps", "self-verification hurts" and "here is a new staleness benchmark" are each pre-empted by DISCERN, PACMI, GPM, TOKI, STALE or the self-correction literature.
- **What this framing uses.** Two assets that are uncommon in that literature:
  - a cumulative five-step ablation, run on one benchmark at four sizes of one family plus a second family;
  - a harness comparison of the same size as the component effects.

## 2. Hypotheses: observed, supported, or still to be tested

| # | Hypothesis | Current status (eval2, greedy, 96 tasks, 22 families) |
|---|---|---|
| H1 | Memory helps only above a capacity threshold; below it the model does not use memory | **Observed.** 1.5B: 0 of 256 memory-dependent runs call `memory_search`, and it solves none of the 64 memory tasks. 3B: memory +29.2 pp (family CI +13.3 to +49.3) |
| H2 | The deterministic gate's benefit peaks at intermediate capacity (7B–8B) | **Supported, not confirmed.** Pooled 7B/8B v2: +16.7 pp (family CI +3.9 to +33.2; sign-flip p = 0.012). 3B: +5.2 (p = 0.41). 14B: +3.1 (p = 0.66). The "peak" rests on non-significant differences at 3B and 14B. The 14B result is affected by stack artefacts (Thai final answers; calculator `round()` rejections, `CORRECTIONS.md` item 5) |
| H3 | The gate's benefit is a stale-record selection fix, not general | **Observed.** S4 carries +12.0 of +16.7 pp (v2), +7.8 of +13.0 (v1) |
| H4 | A same-model verifier without provenance lowers success | **Observed under v2** (−11.5 pp, sign-flip p = 0.008). **Not robust under v1** (−5.2, p = 0.094). Known phenomenon (self-correction literature); report as a replication in the memory setting, not as a discovery |
| H5 | Harness design changes success as much as a reliability component | **Observed:** +15.8 pp for both 7B and Qwen3-8B (p = 0.017, 0.024). The mechanism is **unknown**: the repair turn fired only 14 times, and the gains come from different scenarios for the two models. Needs v1r (job 15) |
| H6 | Memory without safeguards causes answers to unsupported questions | **Observed under v1** (S5 −34 pp); smaller under v2 (−9) |
| H7 | The pattern holds on a new sealed split, a second model family, sampled decoding and free-text memories | **Not tested.** Required before the paper's claims can be called confirmatory |

## 3. What the paper would claim (if H7 holds) and what it would not

**Would claim:**

- an empirical map of component value against capacity, with family-level inference;
- that a 7B–8B agent gains most from deterministic metadata checks, and that this gain is concentrated in stale-record selection;
- that small models do not benefit from memory at all because they do not query it;
- that harness differences can be as large as component effects, so component studies must fix and report the harness.

**Would not claim:**

- a new architecture;
- a new benchmark of record;
- that deterministic gating beats learned resolution in general;
- any result for frontier models (the hosted runs in Campaign 1 are too few and too uncontrolled);
- that the gate works without clean timestamps.

## 4. Why it is worth publishing (and its limits)

- **Practical value.** People deploying small open-weight agents get guidance on which safeguard to add at which size.
- **Methodological value.**
  - family-clustered inference on templated agent benchmarks;
  - per-scenario decomposition instead of a pooled average that depends on the scenario mix;
  - a harness-sensitivity control.
- **Honest scope.** A workshop or Findings-level empirical paper, not a main-track method paper. Its strength depends entirely on the confirmatory experiments in `EXPERIMENT_ROADMAP.md` (E1–E4). Without them, the evidence is exploratory: one benchmark, one decoding run, a single main family.
