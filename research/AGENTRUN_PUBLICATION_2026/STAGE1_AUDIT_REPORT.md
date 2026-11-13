# Stage 1 audit report: AGENTRUN memory-reliability study

**13 November 2026.** This summarises the Stage 1 evidence audit. Details are in the companion files listed at the end; every number here is traceable to them.

## 1. Bottom line

- **Evidence integrity.** The November memory-reliability evidence is complete, internally consistent and free of detected leakage. All 12 Campaign 2 agent datasets are present: 5,184 runs, 0 missing, 0 duplicates, identical frozen hashes. The leakage audit passes all 77 checks.
- **Not ready for confirmatory claims.** Every result comes from one 96-task synthetic benchmark (eval2), now a validation set; from one greedy run per cell; and mostly from one model family.
- **Novelty.** The closest literature, especially DISCERN (11 Nov 2026), already covers provenance-based resolution and deterministic gating.
- **What remains defensible.** A capacity-resolved empirical characterisation of where each reliability component helps. It needs the confirmatory experiments in `EXPERIMENT_ROADMAP.md`.

## 2. Verified findings (eval2, greedy; 96 tasks in 22 scenario-variant families)

Inference is the exact family-level sign-flip test, with a 95% family-bootstrap CI.

| Finding | n | Effect | Evidence strength |
|---|---|---|---|
| Memory raises success (7B + 8B pooled, harness v2) | 192 pairs | 29.2% → 81.8% (+52.6 pp, CI +31.6 to +75.6) | Strong. Expected by design |
| Deterministic gate (E − D), 7B + 8B, v2 | 192 | +16.7 pp (CI +3.9 to +33.2), p = 0.012; S4 stale carries +12.0 of it (S4 alone: +72 pp) | Supported. Mostly a stale-record fix |
| Same, harness v1 | 192 | +13.0 pp (CI +3.1 to +27.1), p = 0.019 | Supported |
| Provenance (D − C), v1 | 192 | +10.4 pp, p = 0.006 | Supported |
| Provenance (D − C), v2 | 192 | +5.2 pp, p = 0.18 | **Not supported** |
| Same-model text verifier (C − B), v2 | 192 | −11.5 pp, p = 0.008; verifier precision 7/29 under v2 | Supported (negative). A known phenomenon |
| Same, v1 | 192 | −5.2 pp, p = 0.094 | **Not robust** (earlier documents overstated it) |
| Harness v2 − v1 | 480 per model | +15.8 pp for both Qwen2.5-7B (p = 0.017) and Qwen3-8B (p = 0.024) | Supported; mechanism unknown |
| Memory hurts unsupported-premise tasks (S5), v1 | 32 | −34 pp | Observed (negative); −9 under v2 |
| 1.5B never uses memory | 256 memory-dependent runs | 0 `memory_search` calls; 0 of 64 memory tasks solved in any configuration | Observed |
| Gate at 3B / 14B, v2 | 96 each | +5.2 pp (p = 0.41) / +3.1 pp (p = 0.66) | No evidence of an effect |
| 2,000 distractors, hash retriever | 192 (16 families) | −29.7 pp, p = 0.001 | Strong; synthetic setting |
| BM25 instead of hash, at 2,000 | 192 (16 families) | +28.6 pp, p = 0.001 | Strong; synthetic setting |
| Harmful outcomes, configuration E, 7B + 8B | 192 per harness | 0 (one-sided 95% upper bound ≈ 1.6%) | Low, not zero-proven |

- **Multiplicity.** Ten of these contrasts survive Benjamini–Hochberg at 5%; only three survive Holm.
- **Missingness.** None.
- **Decoding variance.** Unmeasured.

## 3. What the audit found wrong or missing in earlier work

- `PROJECT_AUDIT.md` declared Stage 1 complete. It was not: 16 of the 18 documents its brief required did not exist.
- The v1 text-verifier penalty was described as established; it is not robust (p = 0.094).
- "6 correct rejections of the invented 12500.00 draft" should be **12** (4 tasks × configurations C, D, E).
- The store-isolation leakage check had silently skipped the 1.5B, 3B and 14B runs (store files not copied). Now fixed: 77/77 pass with full coverage.
- The adapter benchmark-v2-dev budget-3 run existed only on the cluster. It has been recovered and hash-verified (51/55).
- **Pre-existing corrections (`CORRECTIONS.md`, 14 items) still apply:**
  - invented examples;
  - the Qwen3 "fabricator" claim is false;
  - the 3B harmful counts include empty-value answers;
  - the 100% result was evaluation adaptation.

## 4. Benchmark validity

| Split | Valid use now |
|---|---|
| Legacy 23 tasks | Historical diagnostic only |
| Benchmark v2 dev (55) | Development |
| Benchmark v2 sealed (130) | Not accessed. Confirmatory for the fine-tuning thread only; must be moved out of the repository |
| memlab eval (48) | Exploratory (Campaign 1) |
| memlab eval2 (96) | Clean when run; now a validation set |
| memlab eval3 | Does not exist yet; needed for confirmation |

## 5. Recommended contribution

**"Where should memory reliability live?"** A capacity-resolved ablation of memory safeguards (memory, same-model verifier, provenance, deterministic gate) for small open-weight agents, with harness sensitivity as a control. See `RESEARCH_CONTRIBUTION.md`. The October QLoRA paper stays separate.

## 6. Ready to draft?

- **A paper draft can start now** for the methods, related work and clearly labelled exploratory eval2 results.
- **The paper cannot be completed** without at least:
  - E0: jobs 14–20, especially v1r and the seeds;
  - E1: a new sealed split with held-out templates, pre-registered;
  - one of E2 (second model family) or E4 (external benchmark).
- **All of these need the Slurm controller**, which is down.

## 7. Single most important next action

**Get the SIT Slurm controller restored.** Report "Slurmctld(primary) at sitgpumaster is DOWN; login node 192.168.192.11 unreachable" to the administrator. Meanwhile, build and seal the eval3 split and its pre-registration offline, so that the confirmatory run can start as soon as the controller is back.

## Companion files (all in `research/AGENTRUN_PUBLICATION_2026/`)

`CONTINUATION_STATUS.md` · `REPOSITORY_AND_DATA_AUDIT.md` · `STATISTICAL_AUDIT.md` · `BENCHMARK_AND_LEAKAGE_AUDIT.md` · `RELATED_WORK_AND_NOVELTY.md` · `RESEARCH_CONTRIBUTION.md` · `EXPERIMENT_ROADMAP.md` · `PUBLICATION_ROADMAP.md` · `OPEN_ISSUES.md` · `analysis/` · `scripts/` · `literature/` · previous session: `PROJECT_AUDIT.md`, `DATA_INTEGRITY_REPORT.md`
