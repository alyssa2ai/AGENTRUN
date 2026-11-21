# 7. Confirmatory results

All numbers in this section come from the frozen analysis run inside the cluster finalization job (Slurm job 4359)
over the 18 completed cells. Every cell holds exactly 268 × 12 = 3216 rows: 57,888 rows in all, with no missing
pair, no duplicate and no harness error. The confirmatory analysis pools the four primary models over greedy
decoding and three T = 0.7 seeds — 51,456 scored runs on 268 tasks in 135 families. An independent re-computation of
the 60 model × configuration counts and the four primary effect sizes agrees with the frozen analysis exactly.

## 7.1 The four preregistered contrasts

| Hypothesis | Contrast | Difference (pp) | 95% CI | p | Holm-adjusted p | Preregistered verdict |
|---|---|---|---|---|---|---|
| H-primary | EBG − RT | **+17.1** | [12.2, 22.1] | 1 × 10⁻⁵ | 4 × 10⁻⁵ | **SUPPORTED** |
| S1 | EBG − T | **+14.5** | [10.5, 18.6] | 1 × 10⁻⁵ | 4 × 10⁻⁵ | **SUPPORTED** |
| S2 | EBG − LG | **+15.9** | [10.4, 21.2] | 1 × 10⁻⁵ | 4 × 10⁻⁵ | **SUPPORTED** |
| S3 | EBG − B | **+15.3** | [10.3, 20.5] | 1 × 10⁻⁵ | 4 × 10⁻⁵ | **SUPPORTED** |

Differences are in percentage points of task success, paired within model and decoding, with 95% percentile
bootstrap confidence intervals over families and two-sided sign-flip permutation p-values on family-level summed
differences (100,000 draws; the floor of the Monte-Carlo estimate is 1 × 10⁻⁵). Holm correction is over these four
contrasts. All four confidence intervals lie above zero.

## 7.2 S4: harm

S4 asked whether EBG's harmful-answer rate is no higher than RT's. It is substantially lower: **3.1%** of EBG runs
were harmful (135 of 4288) against **22.6%** for RT (968 of 4288), a paired difference of **−19.4 pp**
(95% CI [−24.6, −14.6]). Arbitrary picks, the specific harm that motivated the mechanism, fall from 252 under RT to
13 under EBG. The preregistered verdict is **NOT FALSIFIED**: the confidence interval for the EBG − RT harmful
difference does not lie above zero, and EBG's arbitrary picks do not exceed RT's.

## 7.3 Success and harm by configuration

Pooled over the four primary models and four decodings (n = 4288 runs per configuration):

| Config | Success | Harmful | Arbitrary pick | Unnecessary abstention | Format error | Step limit | Missing |
|---|---|---|---|---|---|---|---|
| B (memory, no labels) | 1972 (46.0%) | 302 (7.0%) | 172 | 658 (15.3%) | 118 (2.8%) | 104 (2.4%) | 0 |
| G (metadata labels, advisory) | 1867 (43.5%) | 337 (7.9%) | 109 | 510 (11.9%) | 135 (3.1%) | 91 (2.1%) | 0 |
| R (record-conflict scanner) | 1931 (45.0%) | 689 (16.1%) | 153 | 330 (7.7%) | 227 (5.3%) | 79 (1.8%) | 0 |
| T (temporal annotator, advisory) | 2009 (46.9%) | 316 (7.4%) | 35 | 557 (13.0%) | 110 (2.6%) | 72 (1.7%) | 0 |
| RT (R + T, enforced) | 1897 (44.2%) | 968 (22.6%) | 252 | 415 (9.7%) | 234 (5.5%) | 77 (1.8%) | 0 |
| LA (LLM arbiter, advisory) | 2053 (47.9%) | 568 (13.2%) | 295 | 633 (14.8%) | 128 (3.0%) | 79 (1.8%) | 0 |
| LG (LLM arbiter, gated) | 1948 (45.4%) | 914 (21.3%) | 510 | 676 (15.8%) | 122 (2.8%) | 55 (1.3%) | 0 |
| EB (evidence-basis labels) | 2372 (55.3%) | 115 (2.7%) | 13 | 566 (13.2%) | 109 (2.5%) | 86 (2.0%) | 0 |
| **EBG (full mechanism)** | **2630 (61.3%)** | **135 (3.1%)** | **13** | 494 (11.5%) | 120 (2.8%) | 42 (1.0%) | 0 |
| EBG-all (ungated enforcement) | **3047 (71.1%)** | 294 (6.9%) | 166 | 545 (12.7%) | 121 (2.8%) | 44 (1.0%) | 0 |
| EBG-unsafe (no safe submission) | 2638 (61.5%) | 142 (3.3%) | 12 | 374 (8.7%) | 247 (5.8%) | 49 (1.1%) | 0 |
| EBG-noR3 (no search-before-submit) | 2573 (60.0%) | 145 (3.4%) | 14 | 604 (14.1%) | 104 (2.4%) | 42 (1.0%) | 0 |

Two features of this table matter as much as the preregistered contrasts, and neither favours a simple reading.

First, **the development finding replicates on sealed data**. Metadata-derived labels made agents *worse* than no
labels at all (G 43.5% against B 46.0%), and *enforcing* record-derived labels was worse still and far more harmful
(RT 44.2% success, 22.6% harmful, against B's 46.0% and 7.0%). Enforcement is not neutral: applied to labels the
evidence does not support, it tripled the harm rate relative to plain memory.

Second, **ungated enforcement of the same evidence-basis labels scored higher than EBG** — 71.1% against 61.3% —
while more than doubling the harmful rate, 6.9% against 3.1%, and restoring arbitrary picks from 13 to 166. Section 9
takes this apart. It is the central tension in our results and we do not resolve it in EBG's favour.

## 7.4 Per-model effects

Per-model differences are descriptive; the confirmatory claims rest on the pooled, family-clustered tests above.

| Contrast | Qwen2.5-3B | Qwen2.5-7B | Qwen3-8B | Llama-3.1-8B |
|---|---|---|---|---|
| EBG − RT, success (pp) | +10.0 [3.0, 17.1] | +26.6 [20.2, 33.1] | +25.0 [18.2, 32.1] | +6.8 [3.3, 10.5] |
| EBG − RT, harmful (pp) | −25.2 | −27.7 | −24.5 | −0.3 |
| EBG − T (pp) | +17.0 [11.4, 22.8] | +15.7 [9.7, 21.7] | +16.0 [9.4, 22.6] | +9.3 [5.8, 13.0] |
| EBG − LG (pp) | +12.2 [4.6, 19.9] | +23.2 [14.9, 31.4] | +11.8 [5.1, 18.8] | +16.3 [10.6, 22.3] |
| EBG − B (pp) | +10.8 [4.2, 17.6] | +18.2 [11.0, 25.5] | +17.6 [9.3, 26.3] | +14.7 [9.8, 19.9] |

The direction is positive for every model on every contrast, and every interval excludes zero. The magnitude is not
uniform: the two mid-sized Qwen models gain two to four times as much on H-primary as Qwen2.5-3B or Llama-3.1-8B.

The Llama-3.1-8B result deserves emphasis because it was pre-stated as a risk. On the p2val2 development split this
model showed essentially no EBG benefit over RT (+1.1 pp), and the preregistration said that a repeat on eval3 would
be "a failure to generalise across families" and would be reported as such. On eval3 the benefit is small but
positive and its interval excludes zero (+6.8 pp [3.3, 10.5]). The harm reduction, however, does not transfer at all
(−0.3 pp): Llama-3.1-8B was already producing very few harmful answers under RT, because it abstains instead — 35.3%
unnecessary abstention under RT, 44.0% under EBG, 60.7% under B. For this model EBG converts abstentions into
answers rather than converting harmful answers into correct ones, which is a different mechanism from the one the
hypothesis describes.

## 7.5 Secondary cells

The two greedy-only secondary models are analysed separately and are never pooled with the primary models.

| Contrast | Qwen2.5-14B (secondary) | Llama-3.2-3B (format-limited) |
|---|---|---|
| EBG − RT | +29.9 [23.0, 36.9] | +12.3 [6.3, 18.3] |
| EBG − T | +22.8 [15.9, 29.9] | +29.5 [22.8, 36.3] |
| EBG − LG | +13.8 [8.5, 19.3] | +7.1 [1.5, 12.6] |
| EBG − B | +17.2 [10.1, 24.3] | +34.7 [27.7, 41.7] |

Qwen2.5-14B shows the largest EBG − RT effect of any model in the study. Llama-3.2-3B failed the preregistered
readiness criterion before the campaign and is reported here only for completeness: its absolute success is very low
(41.8% under EBG, 7.1% under B) and it abstains unnecessarily on 88.7% of B runs, so its differences measure
recovery from near-total failure rather than the effect the hypotheses concern.

## 7.6 Absolute performance

No configuration is good in absolute terms. The best preregistered configuration, EBG, answers 61.3% of pooled
primary tasks correctly, and on the subset of tasks that have a definite answer rather than a genuine conflict the
pooled answer accuracy under EBG is 46.0%. Qwen2.5-7B and Qwen3-8B reach 75.0% and 77.8% overall under EBG;
Llama-3.1-8B reaches 33.0%. The contribution is a relative one about mechanism design, not a claim that small agents
handle conflicting persistent memory well.
