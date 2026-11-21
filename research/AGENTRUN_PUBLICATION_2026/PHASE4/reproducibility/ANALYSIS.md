# Statistical analysis and regeneration of every table

## Preregistered method (`PHASE2/scripts/analyze_p2.py`, frozen; PREREGISTRATION.md §8)
- **Unit:** task. A task's success is averaged over the decodings of one model. Contrasts are paired within model and decoding. A missing (task, configuration) pair or a harness error counts as a failure (outcome `missing`) and stays in the denominator. There are no run-level exclusions.
- **Clustering:** family = (category, attribute), 135 families.
- **Test:** two-sided sign-flip permutation of family-level summed differences. Families are pooled across models, so a family's sign is flipped for all models together. 100,000 seeded Monte-Carlo permutations, p = (hits + 1)/(100,001).
- **CI:** 95% percentile bootstrap over families, 10,000 seeded resamples, of the mean task-level difference.
- **Multiplicity:** Holm over {EBG−RT (H-primary), EBG−T (S1), EBG−LG (S2), EBG−B (S3)}, pooled over the four primary models, α = 0.05. Every other contrast is exploratory, with Benjamini–Hochberg over the exploratory set.
- **S4 (harm):** EBG−RT difference in harmful answers (wrong value, stale value, unsupported claim, arbitrary pick) with its CI. It is falsified if the CI lies above 0.
- **Verdict rule (§2):** a hypothesis is falsified if the Holm-adjusted p ≥ 0.05, or if the 95% CI lies at or below 0. `build_reports.py::verdict` implements this mechanically.

## Regenerating the outputs (from `PHASE3/`)
| Output | Command | Source script |
|---|---|---|
| `ANALYSIS/COMPLETENESS.*` | `bash scripts/run_phase3_analysis.sh verify` | `verify_phase3.py` |
| `ANALYSIS/CONFIRMATORY_primary_cells.*` | `… analyze` | `analyze_p2.py --holm EBG-RT,EBG-T,EBG-LG,EBG-B --n-perm 100000` |
| `ANALYSIS/SENSITIVITY_annotator_agreed.*`, `…_flagged_complement.*`, `…_qwen14b_agreed.*` | `… analyze` | `subset_tasks.py`, `agreement.py`, `agreed_ids_b.py`, `analyze_p2.py` |
| `ANALYSIS/SECONDARY_cells.*` | `… analyze` | `analyze_p2.py` on the 14B and Llama-3.2-3B cells |
| `ANALYSIS/METRICS.*` | `… analyze` | `phase3_metrics.py` (descriptive; per-decoding table) |
| `ANALYSIS/CROSSCHECK.*` | `… report` | `crosscheck_phase3.py`: independent recomputation of counts and primary effect sizes from raw runs; exits 1 on any disagreement |
| `PHASE3_EXECUTION_LOG.md`, `PHASE3_COMPARISON_TABLES.md`, `PHASE3_ABLATION_RESULTS.md`, `PHASE3_STATISTICAL_ANALYSIS.md`, `PHASE3_FAILURE_TABLES.md`, `PHASE3_DECISIONS.json`, `results/*.csv` | `… report` | `build_reports.py` (no new statistics) |
| `PHASE4/manuscript/07_results_AUTO.md` | `python scripts/write_results_section.py --p3 . --out ../PHASE4/manuscript/07_results_AUTO.md` | numbers copied from the above |

The analysis of 16 primary cells takes a few hours of single-threaded Python. The four permutation analyses dominate the runtime.
