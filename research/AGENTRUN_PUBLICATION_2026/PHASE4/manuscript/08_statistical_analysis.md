# 8. Statistical analysis

## 8.1 What was tested, and how

The unit is the task. Success per task is the mean over a model's decodings, contrasts are paired within model and
decoding, and families — (category, attribute) pairs, 135 of them among the 268 valid tasks — are the clusters. The
test is a two-sided sign-flip permutation of family-level summed differences with families pooled across models, so
a family's sign flips for all four models together; with 135 families the exact enumeration is infeasible and the
analysis uses 100,000 seeded Monte-Carlo draws, whose smallest attainable estimate is 1 × 10⁻⁵. Confidence intervals
are 95% percentile bootstraps over families, 10,000 seeded resamples, of the mean task-level difference. Holm
correction runs over the four preregistered contrasts at α = 0.05; everything else is exploratory and reported with
Benjamini–Hochberg adjustment [@holm1979simple; @benjamini1995fdr; @good2005permutation; @efron1979bootstrap;
@field2007clustered]. Missing pairs and harness errors count as failures and stay in every denominator; in this
campaign there were none of either.

All four primary contrasts reach the Monte-Carlo floor before correction, so Holm's step-down leaves them at
4 × 10⁻⁵, and family support is lopsided rather than marginal: for EBG − RT, 43 to 66 families favour EBG per model
against 3 to 25 against.

## 8.2 Preregistered sensitivity analyses

Section 4.8 records a wording inconsistency in the frozen preregistration about which items form the primary set.
The analysis follows §5 — all 268 mechanically valid items — and reports the alternatives as sensitivity analyses so
that a reader who prefers the §6 reading can apply it.

| Analysis | Tasks | Families | EBG − RT | EBG − T | EBG − LG | EBG − B |
|---|---|---|---|---|---|---|
| **Primary (confirmatory)** | 268 | 135 | **+17.1** [12.2, 22.1] | **+14.5** [10.5, 18.6] | **+15.9** [10.4, 21.2] | **+15.3** [10.3, 20.5] |
| Double-agreement subset | 161 | 94 | +14.3 [8.8, 20.4] | +12.7 [7.8, 17.8] | +19.7 [13.8, 25.7] | +14.7 [9.3, 20.3] |
| Flagged complement | 107 | 67 | +21.3 [13.4, 29.3] | +17.2 [11.8, 23.0] | +10.2 [1.3, 19.4] | +16.4 [7.5, 25.5] |
| Qwen2.5-14B-agreed subset | 232 | 123 | +15.3 [10.2, 20.7] | +13.9 [9.6, 18.4] | +15.5 [9.8, 21.4] | +14.8 [9.5, 20.3] |

Every contrast keeps its sign, every interval excludes zero, and every Holm-adjusted p stays below 0.05 in all three
sensitivity sets. The preregistered conclusions do not depend on the item-set reading. Effects are somewhat larger on
the flagged complement than on the double-agreement subset, which is the opposite of what an "annotator noise
inflates the effect" account would predict.

## 8.3 Independent cross-check

A second implementation recomputed the 60 model × configuration success counts and the four pooled primary
differences directly from the raw run files, by a different route from the frozen analysis. All 60 counts and all
four differences agree exactly (EBG − RT 17.1 against 17.1, 1072 task pairs against 1072, and likewise for the other
three). The pipeline is configured to stop if they do not.

## 8.4 Post-hoc exploratory sensitivity to the platform transition

Two of the eighteen cells contain rows produced after an unplanned node reboot that changed the host kernel and the
NVIDIA driver (Section 11). Both analyses below were specified **after** that transition came to light and **before**
any confirmatory outcome was inspected, but they are post-hoc with respect to the preregistration. They are
exploratory, they are reported separately, and they do not change the preregistered verdicts.

| Analysis | Rows | EBG − RT | EBG − T | EBG − LG | EBG − B |
|---|---|---|---|---|---|
| Confirmatory (all 16 primary cells) | 51,456 | +17.1 [12.2, 22.1] | +14.5 [10.5, 18.6] | +15.9 [10.4, 21.2] | +15.3 [10.3, 20.5] |
| Exploratory: straddling cell excluded | 48,240 | +17.0 [12.1, 22.0] | +14.4 [10.5, 18.5] | +15.9 [10.5, 21.2] | +15.3 [10.3, 20.5] |
| Exploratory: Qwen3-8B, pre-reboot decodings only | 9,648 | +24.8 [17.9, 31.8] | +15.7 [9.2, 22.2] | +11.9 [5.1, 19.0] | +17.4 [9.0, 26.1] |

Dropping `qwen3_8b_T07_s3` entirely moves the pooled primary estimates by at most 0.1 pp. Restricting Qwen3-8B to
its three fully pre-reboot decodings gives +24.8 pp on H-primary against +25.0 pp with all four — a difference of
0.2 pp, far inside the bootstrap interval.

**What this establishes:** the preregistered conclusions do not depend on the one cell whose rows straddle the
platform change. **What it does not establish:** that the platform change had no effect on generation. These
analyses drop or isolate the straddling cell; they do not compare the same task and configuration across the two
driver versions, which this campaign cannot do, because no such pair exists. Agreement here is consistent with the
transition being inert and equally consistent with an effect too small to move a family-clustered permutation test
at this sample size, and it says nothing about the two individual tasks whose own rows are split across platforms.

## 8.5 Exploratory contrasts

The remaining contrasts were preregistered as exploratory and are reported with BH adjustment. Their substantive
reading is in Section 9.

| Contrast | Difference (pp) | 95% CI | p (BH) | Harmful difference (pp) |
|---|---|---|---|---|
| EBG − EB | +6.0 | [3.9, 8.2] | 2.2 × 10⁻⁵ | +0.5 [−0.1, 1.2] |
| EBG − R | +16.3 | [11.7, 21.0] | 2.2 × 10⁻⁵ | −12.9 [−18.0, −8.2] |
| EB − T | +8.5 | [5.4, 11.6] | 2.2 × 10⁻⁵ | −4.7 |
| EB − G | +11.8 | [8.3, 15.2] | 2.2 × 10⁻⁵ | −5.2 |
| LG − LA | −2.4 | [−5.6, 0.6] | 0.167 | **+8.1** [6.1, 10.2] |
| EBG − EBG-all | **−9.7** | [−15.2, −4.3] | 0.0013 | −3.7 [−6.6, −1.3] |
| EBG − EBG-unsafe | −0.2 | [−1.0, 0.7] | 0.776 | −0.2 [−0.6, 0.2] |
