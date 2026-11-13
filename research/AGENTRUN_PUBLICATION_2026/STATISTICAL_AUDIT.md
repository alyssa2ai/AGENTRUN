# Statistical audit (memory-reliability study, Campaign 2)

**13 November 2026.** Every number below was recomputed from raw run files. Sources:

- `research/AGENTRUN_MITACS_INTERVIEW_2026-11-12/build/verified_numbers.json`: success counts, Wilson intervals, task-level bootstrap and exact McNemar. Written by `verify_numbers.py`, which shares no code with the original analysis.
- `analysis/family_clustered_results.{md,json}`: bootstrap over scenario-variant families (previous session).
- `analysis/cluster_permutation.{md,json}`: exact family sign-flip permutation tests and per-scenario decomposition (this session).

Scoring uses the frozen scorer `memlab.score_run`. "Success" means the agent reached the scenario's correct outcome. That is either the gold value, or a correct abstention or conflict report where the scenario calls for one.

## 1. Design and sample sizes

- **Benchmark (eval2):** 96 tasks, 16 per scenario (S1 context loss, S2 retrieval, S3 conflict, S4 stale, S5 unsupported, S6 tool failure). There are 22 scenario-variant families of 2–8 tasks each.
- **Configurations:** each task runs once per configuration.
  - A: stateless
  - B: + memory
  - C: + text verifier
  - D: + provenance
  - E: + deterministic staleness/conflict gate
- **Decoding:** greedy (T = 0, seed 20261111) for all Campaign 2 data.
- **Unit counts:** per model and harness, 96 paired units for each configuration contrast. "Pooled" means Qwen2.5-7B + Qwen3-8B, giving 192 pairs. Harness comparisons give 480 pairs per model (96 tasks × 5 configurations).
- **Missingness:** zero. All 4,800 unpadded and 384 padded runs exist, with no duplicates. Three Qwen2.5-7B v1 runs hit a malformed tool call; these were handled by the harness's fixed notice and scored like any other run.
- **Repeated sampling:** none in Campaign 2. Every contrast is a single greedy run per task, so the run-to-run variance of these numbers is unknown. Campaign 1 used three sampled repeats on a different 48-task split.

## 2. Success by configuration (eval2, greedy; successes / 96, Wilson 95% CI)

| Model, harness | A | B | C | D | E |
|---|---|---|---|---|---|
| Qwen2.5-1.5B v1 | 0 | 0 | 0 | 0 | 0 |
| Qwen2.5-1.5B v2 | 20 | 18 | 18 | 19 | 19 |
| Qwen2.5-3B v1 | 4 | 32 | 26 | 33 | 35 |
| Qwen2.5-3B v2 | 23 | 51 | 41 | 44 | 49 |
| Qwen2.5-7B v1 | 24 [17, 35] | 48 [40, 60] | 40 [32, 52] | 56 [48, 68] | 70 [63, 81] |
| Qwen2.5-7B v2 | 28 [21, 39] | 74 [68, 84] | 61 [54, 72] | 66 [59, 77] | 85 [81, 93] |
| Qwen3-8B v1 | 23 [17, 33] | 61 [54, 72] | 59 [51, 71] | 63 [56, 74] | 74 [68, 84] |
| Qwen3-8B v2 | 28 [21, 39] | 83 [78, 92] | 74 [68, 84] | 79 [73, 89] | 92 [90, 98] |
| Qwen2.5-14B v1 | 26 | 59 | 63 | 66 | 62 |
| Qwen2.5-14B v2 | 24 | 70 | 69 | 72 | 75 |

Notes on individual rows:

- **Qwen2.5-1.5B v1:** all 480 runs ended in a format error or the step limit. That row measures protocol compliance, not memory.
- **Qwen2.5-1.5B v2:** its configuration A has 12 harmful outcomes. All of its successes, in every configuration, are on S5 and S6, where abstaining or reporting failure is correct. It solves none of the 64 S1–S4 memory tasks in any configuration, so it never uses memory successfully.
- **Qwen2.5-14B v1:** E ends below D (−4). Under v1, E has 31 format/step failures versus 23 for D.

## 3. Headline contrasts under three inference schemes

| Contrast | n pairs | diff (pp) | Task bootstrap 95% CI | Family bootstrap 95% CI | Exact McNemar p | Exact family sign-flip p (F) |
|---|---|---|---|---|---|---|
| v1 pooled B − A (memory) | 192 | +32.3 | [+21.9, +42.2] | [+10.9, +55.1] | <0.0001 | 0.0069 (22) |
| v1 pooled C − B (text verifier) | 192 | −5.2 | [−8.9, −2.1] | [−10.9, −0.8] | 0.0063 | **0.094** (22) |
| v1 pooled D − C (provenance) | 192 | +10.4 | [+5.2, +15.6] | [+4.7, +16.0] | 0.0017 | 0.0061 (22) |
| v1 pooled E − D (gate) | 192 | +13.0 | [+7.3, +19.3] | [+3.1, +27.1] | <0.0001 | 0.019 (22) |
| v2 pooled B − A | 192 | +52.6 | [+43.2, +62.5] | [+31.6, +75.6] | <0.0001 | <0.0001 (22) |
| v2 pooled C − B | 192 | −11.5 | [−16.7, −6.8] | [−21.4, −4.1] | <0.0001 | 0.0078 (22) |
| v2 pooled D − C | 192 | +5.2 | [0.0, +10.4] | [−1.1, +11.5] | 0.11 | **0.18** (22) |
| v2 pooled E − D | 192 | +16.7 | [+10.4, +23.4] | [+3.9, +33.2] | <0.0001 | 0.012 (22) |
| Harness v2 − v1, Qwen2.5-7B | 480 | +15.8 | [+8.8, +23.1] | [+4.0, +28.1] | <0.0001 | 0.017 (22) |
| Harness v2 − v1, Qwen3-8B | 480 | +15.8 | [+9.8, +22.3] | [+3.3, +29.5] | <0.0001 | 0.024 (22) |
| 2,000 padding records, hash retriever − no padding (7B v2, S1–S4, B/D/E) | 192 | −29.7 | [−39.1, −20.8] | [−47.8, −12.6] | <0.0001 | 0.0010 (16) |
| BM25 − hash, both with 2,000 padding records | 192 | +28.6 | [+19.8, +38.0] | [+12.0, +47.9] | <0.0001 | 0.0010 (16) |
| 3B v2 E − D | 96 | +5.2 | n/r | [−3.2, +14.7] | 0.33 | 0.41 (22) |
| 14B v2 E − D | 96 | +3.1 | n/r | [−4.8, +11.6] | 0.51 | 0.66 (22) |

"n/r": not reported by `verify_numbers.py`.

**How the schemes differ.**

- **Task-level schemes** (task bootstrap, McNemar) treat the 96 tasks as independent. They are not. Tasks in one family share a template, a scenario mechanism and often the same failure mode.
- **Family bootstrap.** Resampling the 22 families widens most intervals by 1.5–2.5×. It still has a weakness: percentile bootstrap intervals are optimistic with ~20 clusters.
- **Exact family sign-flip test.** This has no large-sample assumption. It is the most conservative of the three and is the criterion this audit recommends for the paper.

**Smallest attainable p.** With 16 families, the smallest attainable two-sided p in the sign-flip test is 2/2¹⁶ ≈ 0.00003. The two retrieval contrasts reach 0.0010, which is well above that floor.

**Robust under every scheme:**

- the memory effect (B − A);
- provenance under v1;
- the gate (E − D) under both harnesses;
- the text-verifier penalty under v2;
- the harness effect for both models;
- the padding collapse and the BM25 recovery.

**Not robust:**

- **The v1 text-verifier penalty, −5.2 pp.** The family bootstrap CI excludes 0, but the exact family test gives p = 0.094. Earlier documents, including `PROJECT_AUDIT.md`, present it as established; it is not.
- **Provenance under v2, +5.2 pp.** Neither the family bootstrap nor the permutation test supports it.
- **The gate at 3B or 14B.** No evidence of an effect.

## 4. Where the pooled effects come from (per-scenario decomposition)

Each scenario holds 32 pooled pairs. Values are the difference within the scenario, in pp.

| Contrast | S1 | S2 | S3 | S4 | S5 | S6 |
|---|---|---|---|---|---|---|
| v1 B − A (memory) | +84 | +88 | +38 | +12 | **−34** | +6 |
| v2 B − A (memory) | +81 | +100 | +97 | +22 | −9 | +25 |
| v1 C − B (text verifier) | −9 | −22 | +3 | 0 | 0 | −3 |
| v2 C − B (text verifier) | −3 | **−44** | 0 | −3 | 0 | −19 |
| v1 D − C (provenance) | +16 | +9 | +19 | +19 | 0 | 0 |
| v1 E − D (gate) | +6 | +6 | +19 | **+47** | 0 | 0 |
| v2 E − D (gate) | +3 | +12 | +9 | **+72** | 0 | +3 |
| Harness, 7B | −11 | +11 | **+50** | +12 | +18 | +15 |
| Harness, Qwen3-8B | 0 | −8 | +18 | +1 | **+61** | +22 |

**What this means.**

- **The pooled numbers depend on the benchmark's mix.** Each scenario is one sixth of eval2, a design choice. A benchmark weighted toward retrieval would show a larger memory effect and a smaller gate effect.
- **The gate is mostly a stale-record mechanism.** Under v2, S4 contributes +12.0 of the pooled +16.7 pp. The paper should report the gate as "fixes stale-record selection" with the S4 number, not as a general +17 pp improvement.
- **Memory harms the unsupported-claim scenario (S5) under v1 (−34 pp).** Given memory, the model answers questions it should decline. Under v2 this shrinks to −9. This negative finding must be kept.
- **The text verifier's harm is concentrated in retrieval (S2) and tool failure (S6).** These are the scenarios where it rejects correct drafts.
- **The harness gain comes from different scenarios for the two models.** It comes from S3 (conflict) for 7B and from S5 (unsupported) for Qwen3-8B. The mechanism is unresolved. Harness v2 added both a repair turn and two prompt rules, and the repair turn fired in only 14 runs. The v1r variant that would separate them (job 15) never ran.

## 5. Harmful outcomes (wrong, stale, unsupported or arbitrary answers)

Pooled 7B + 8B, 192 runs per configuration:

| | A | B | C | D | E |
|---|---|---|---|---|---|
| v1 | 0 | 5 | 1 | 2 | 0 |
| v2 | 0 | 8 | 1 | 1 | 0 |

- **Counts are small.** With 0 of 192 for E, the one-sided 95% upper bound on the harmful rate is about 1.6% (rule of three). That is consistent with a low rate, not proof of zero.
- **Configuration A's 0 is not a safety property.** A cannot answer the memory scenarios at all.
- **Harm rises when capacity drops.** Qwen2.5-3B produces 24 (v1) and 37 (v2) harmful outcomes over 480 runs, but 15 and 20 of these are `answer` statuses with an empty value; genuinely wrong asserted values are 9 and 17 (`CORRECTIONS.md` item 6). Qwen2.5-1.5B v2 asserts 22 wrong values and 2 unsupported claims, 12 of them in configuration A, and never calls `memory_search` (0 of 256 memory-dependent runs).

## 6. Verifier behaviour (what the text verifier actually checks)

Counts of verifier decisions on drafts, from `verified_numbers.json`. TP = rejected a draft that was wrong; FP = rejected a correct draft.

| | C: TP / FP | D: TP / FP | E: TP / FP |
|---|---|---|---|
| Pooled v1 | 4 / 11 | 4 / 6 | 0 / 2 |
| Pooled v2 | 7 / 22 | 11 / 12 | 6 / 6 |

In configuration C the verifier is a second call to the same model and has no provenance. Its rejections are mostly of correct drafts (precision 7/29 = 24% under v2). This is the mechanism behind the C − B penalty.

**Corrected statement.** The invented "12500.00" draft occurred on 4 tasks, and the verifier rejected it in all 12 verified runs (C, D, E × 4). The "6 correct rejections" in `PROJECT_AUDIT.md` is the Qwen2.5-7B v2 configuration-C true-positive count, not the number of invented drafts caught.

## 7. Statistical versus practical significance

| Finding | Effect | Practical reading |
|---|---|---|
| Memory (v2, 7B/8B) | +52.6 pp (family CI +31.6 to +75.6) | Large. Expected by construction: four scenarios cannot be solved without memory. Not a discovery in itself. |
| Gate (v2, 7B/8B) | +16.7 pp pooled; +72 pp on stale-record tasks | Large and specific: a few lines of deterministic code fix a failure the model does not fix itself. |
| Text verifier (v2) | −11.5 pp | Moderate harm. Practically important as a warning against same-model verification without provenance. |
| Harness v2 | +15.8 pp for both models | Moderate. Mechanism unresolved. |
| Padding / retriever | −29.7 pp, then +28.6 pp | Large. But the padding is synthetic and the hash retriever is deliberately weak. It shows the retriever is a first-order factor, not how real retrievers behave. |
| Gate at 3B / 14B | +5.2 / +3.1 pp | Small and statistically indistinguishable from zero. |

## 8. Threats to statistical validity

1. **Single greedy run per cell.** There is no measure of decoding variance. Planned jobs 19–20 (T = 0.7, two seeds) never ran.
2. **Clustering.** Tasks are not independent. Use family-level inference in the paper.
3. **Multiplicity.** There are 14 headline contrasts plus the size sweep. Over the 14 exact sign-flip p-values, the two standard corrections give very different answers:
   - **Benjamini–Hochberg (false discovery rate 5%):** keeps all ten contrasts with p ≤ 0.024, so the robust set in §3 is unchanged.
   - **Holm (family-wise error 5%):** keeps only three: memory under v2, padding collapse and BM25 recovery. The fourth-smallest p, 0.0061, exceeds the Holm threshold 0.05/11 = 0.0045.

   With 22 families the exact test cannot produce very small p-values for moderate effects. So the gate, provenance-v1 and harness effects should be reported as "supported on eval2 (FDR-controlled), to be confirmed on a new sealed split", not as confirmed.
4. **eval2 has now been analysed extensively.** Further hypothesis selection on it is exploratory. A new sealed split is needed for confirmatory claims (see `BENCHMARK_AND_LEAKAGE_AUDIT.md`).
5. **Model-family breadth.** Two families: Qwen2.5 at four sizes and Qwen3 at one. The capacity curve is confounded with Qwen2.5-specific behaviour, such as 14B's Thai-language final answers (see `CORRECTIONS.md`).
6. **Scorer validity.** The scorer is deterministic, with spot checks by the previous session and `CORRECTIONS.md`. There has been no independent human annotation of the 5,184 runs.
