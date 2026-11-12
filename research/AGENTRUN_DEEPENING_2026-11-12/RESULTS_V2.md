# Campaign 2 — Full Results

**Source:** `research/AGENTRUN_DEEPENING_2026-11-11/tables/c2/C2_TABLES.md` (regenerated 2026-11-12 with all 14 completed jobs).
**Scoring:** `memlab.score_run()` for ablation runs; `scorer_v2` for benchmark v2 runs; `eval/harness.py` R0 for legacy 23.
**Split:** eval2 (96 tasks, 16 per scenario, frozen in `benchmark/FREEZE_eval2.json`).
**Leakage audit:** All 17 checks pass (see `tables/leakage_audit_eval2.json`).

---

## 1. Main comparison: memory component ablation (v1 harness, 7B + Qwen3-8B)

### Pooled results (192 task pairs)

| Config | Success (95% Wilson CI) | Harmful | Format/step-limit |
|---|---|---|---|
| A: stateless baseline | 47/192 = 24.5% (19–31) | 0/192 | 51/192 |
| B: retrieval | 109/192 = 56.8% (50–64) | 5/192 | 52/192 |
| C: verified retrieval | 99/192 = 51.6% (45–59) | 1/192 | 52/192 |
| D: + provenance | 119/192 = 62.0% (55–69) | 2/192 | 39/192 |
| E: + reliability gate | 144/192 = 75.0% (68–81) | 0/192 | 27/192 |

### Pairwise component effects (McNemar exact, task-clustered bootstrap CIs)

| Comparison | diff (pp) | 95% CI | p |
|---|---|---|---|
| B − A (memory) | +32.3 | [+24.0, +40.6] | <0.0001 |
| C − B (verifier) | −5.2 | [−8.9, −2.1] | 0.006 |
| D − C (provenance) | +10.4 | [+4.2, +16.7] | 0.002 |
| E − D (gate) | +13.0 | [+7.8, +18.8] | <0.0001 |
| E − A (full pipeline) | +50.5 | [+41.1, +59.4] | <0.0001 |

### Per-scenario breakdown (pooled, v1 harness)

| Scenario | A | B | C | D | E |
|---|---|---|---|---|---|
| S1: context loss | 0/32 | 27/32 | 24/32 | 29/32 | 31/32 |
| S2: retrieval | 0/32 | 28/32 | 21/32 | 24/32 | 26/32 |
| S3: conflict | 0/32 | 12/32 | 13/32 | 19/32 | 25/32 |
| S4: stale memory | 0/32 | 4/32 | 4/32 | 10/32 | 25/32 |
| S5: unsupported | 27/32 | 16/32 | 16/32 | 16/32 | 16/32 |
| S6: tool failure | 20/32 | 22/32 | 21/32 | 21/32 | 21/32 |

### Per-model results (v1 harness)

**Qwen2.5-7B-Instruct:**
- A: 25.0% → B: 50.0% → C: 41.7% → D: 58.3% → E: 72.9%
- Memory: +25.0 pp (p<0.0001); Verifier: −8.3 pp (p=0.008); Provenance: +16.7 pp (p=0.0004); Gate: +14.6 pp (p=0.0005)

**Qwen3-8B:**
- A: 24.0% → B: 63.5% → C: 61.5% → D: 65.6% → E: 77.1%
- Memory: +39.6 pp (p<0.0001); Verifier: −2.1 pp (p=0.625 NS); Provenance: +4.2 pp (p=0.481 NS); Gate: +11.5 pp (p=0.007)

---

## 2. Harness variant comparison (v1 vs v2)

The v2 harness adds a repair turn (the model may retry after a format error) and two explicit output formatting rules. All comparisons below are paired on the same (task, config).

### Pooled improvement (v2 − v1)

| Model | v1 success | v2 success | Δ (pp) | p |
|---|---|---|---|---|
| Qwen2.5-7B | 49.6% | 65.4% | +15.8 | <0.0001 |
| Qwen3-8B | 58.3% | 74.2% | +15.8 | <0.0001 |

### Best v2 results

- **Qwen2.5-7B, config E, v2:** 85/96 = **88.5%**
- **Qwen3-8B, config E, v2:** 92/96 = **95.8%**
- **Pooled, config E, v2:** 177/192 = **92.2%** (88–95 CI)

### Failure mode reduction

| Metric | Q2.5-7B v1 | Q2.5-7B v2 | Q3-8B v1 | Q3-8B v2 |
|---|---|---|---|---|
| Format errors | 66 | 6 | 28 | 0 |
| Max steps hit | 38 | 15 | 89 | 7 |
| Over-abstention | 123 | 104 | 60 | 84 |
| False conflict | 14 | 34 | 16 | 30 |

v2 drastically reduces format errors and step-limit exhaustion. However, false-conflict detections increase, and over-abstention patterns shift.

---

## 3. Model-size sweep (Qwen2.5-Instruct family)

### Harness v1

| Size | A | B | C | D | E | Format/step |
|---|---|---|---|---|---|---|
| 1.5B | 0/96 | 0/96 | 0/96 | 0/96 | 0/96 | 480/480 |
| 3B | 4/96 | 32/96 | 26/96 | 33/96 | 35/96 | 238/480 |
| 7B | 24/96 | 48/96 | 40/96 | 56/96 | 70/96 | 104/480 |
| 14B | 26/96 | 59/96 | 63/96 | 66/96 | 62/96 | 113/480 |

### Harness v2

| Size | A | B | C | D | E | Format/step |
|---|---|---|---|---|---|---|
| 1.5B | 20/96 | 18/96 | 18/96 | 19/96 | 19/96 | 8/480 |
| 3B | 23/96 | 51/96 | 41/96 | 44/96 | 49/96 | 35/480 |
| 7B | 28/96 | 74/96 | 61/96 | 66/96 | 85/96 | 21/480 |
| 14B | 24/96 | 70/96 | 69/96 | 72/96 | 75/96 | 66/480 |

### Component effects by model size (v2 harness)

| Size | B−A (memory) | C−B (verifier) | D−C (provenance) | E−D (gate) |
|---|---|---|---|---|
| 1.5B | −2.1 (NS) | 0.0 (NS) | +1.0 (NS) | 0.0 (NS) |
| 3B | +29.2 (p<0.0001) | −10.4 (p=0.002) | +3.1 (NS) | +5.2 (NS) |
| 7B | +47.9 (p<0.0001) | −13.5 (p=0.0002) | +5.2 (NS) | +19.8 (p<0.0001) |
| 14B | +47.9 (p<0.0001) | −1.0 (NS) | +3.1 (NS) | +3.1 (NS) |

**Key insight:** Memory benefits require a minimum model capacity (~3B). The full component stack (verifier → provenance → gate) only produces statistically significant marginal gains at 7B. At 14B, the model already handles reliability scenarios well enough that the additional components show no significant effect.

---

## 4. Retrieval at scale

Qwen2.5-7B, v2 harness, memory scenarios (S1–S4), configs B/D/E only.

| Retriever | B | D | E | Recall | Harmful |
|---|---|---|---|---|---|
| hash256, no padding (7–12 records) | 45/64 | 36/64 | 56/64 | 1.00 | 7 |
| hash256 + 2,000 padding | 27/64 | 22/64 | 31/64 | 0.76 | 10 |
| BM25 + 2,000 padding | 42/64 | 41/64 | 52/64 | 1.00 | 6 |
| bge-small + 2,000 | not run | — | — | — | — |

| Comparison | Δ (pp) | 95% CI | p |
|---|---|---|---|
| hash+2000 − no padding | −29.7 | [−39.1, −20.3] | <0.0001 |
| BM25+2000 − hash+2000 | +28.6 | [+19.3, +38.5] | <0.0001 |

**Key insight:** Naive hash-based retrieval fails catastrophically when the store grows. BM25 maintains perfect recall and near-baseline task success at 2,000 records. The dense retrieval condition (bge-small) was not completed.

---

## 5. Legacy 23-task benchmark

| Run | Condition | Budget | Pass rate |
|---|---|---|---|
| adapter, budget 3 | QLoRA adapter | 3 | 23/23 (100%) |
| adapter, budget 6 | QLoRA adapter | 6 | 23/23 (100%) |
| base, budget 3 | No adapter | 3 | 21/23 (91.3%) |
| base, budget 6 | No adapter | 6 | 22/23 (95.7%) |

Failed tasks are consistently `adversarial_division_by_zero` (base, all conditions) and `chain_weather_then_calc` (base, budget 3 only).

Adapter T=0.7 runs (3 seeds): all 23/23 at budget 3.
Base T=0.7 runs: seed 1 = 21/23, seed 2 = 22/23, seed 3 = 22/23.

### Benchmark v2, dev split (55 tasks)

| Run | Correct | R0-rule | Exhausted |
|---|---|---|---|
| base, budget 3 | 92.7% | 83.6% | 1.8% |
| base, budget 6 | 94.5% | 85.5% | 0.0% |
| adapter, budget 6 | 92.7% | 87.3% | 0.0% |

The sealed test split (130 tasks) was not used.

---

## 6. Qwen3-8B abstention anomaly

Under v1 harness with the full pipeline (config E), Qwen3-8B fails to abstain on unsupported questions:
- **S5 correct (A): 15/16** — without memory, correctly abstains.
- **S5 correct (B): 6/16** — with retrieval, starts fabricating.
- **S5 correct (E): 1/16** — with full pipeline, almost never abstains correctly.

Under v2 harness, this reverses: S5 correct jumps to 16/16 at all configs. The v2 formatting rules contain explicit abstention guidance that prevents the model from hallucinating answers to unsupported questions.

Qwen2.5-7B does not show this pattern (S5 correct is ≥10/16 across all configs in both harnesses).

---

## 7. Harmful answer rates

| Model | Harness | Harmful across all configs |
|---|---|---|
| Qwen2.5-7B | v1 | 1/480 (0.2%) |
| Qwen2.5-7B | v2 | 7/480 (1.5%) |
| Qwen3-8B | v1 | 7/480 (1.5%) |
| Qwen3-8B | v2 | 3/480 (0.6%) |
| Qwen2.5-3B | v1 | 24/480 (5.0%) |
| Qwen2.5-3B | v2 | 37/480 (7.7%) |
| Qwen2.5-14B | v1 | 10/480 (2.1%) |
| Qwen2.5-14B | v2 | 3/480 (0.6%) |
| Qwen2.5-1.5B | v1 | 0/480 (0.0%) |
| Qwen2.5-1.5B | v2 | 24/480 (5.0%) |

The 3B model has the highest harmful-answer rate, particularly under v2. The 1.5B model produces no harmful answers under v1 because it produces no real answers at all (100% format errors).
