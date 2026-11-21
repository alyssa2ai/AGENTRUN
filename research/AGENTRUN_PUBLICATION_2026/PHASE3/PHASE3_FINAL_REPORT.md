# Phase 3 final report

**Status: COMPLETE.** 18 of 18 cells executed, all integrity gates passed, the frozen preregistered analysis ran to
completion, an independent cross-check agrees with it exactly, and every deliverable listed in §8 exists and is
hashed in `PHASE3_SHA256_MANIFEST.txt`.

Produced by Slurm job **4359** on 2026-11-21 (CPU-only, 2 CPUs, 6 GB), committed in the HPC clone as `39d69b0`.
The earlier finalization job 4270 failed at its integrity gates on 2026-11-20 and is not the source of any number
here; §6 says what happened and what was changed.

This report separates five kinds of statement, and nothing is moved between them:

| Kind | Where |
|---|---|
| **Preregistered confirmatory results** | §2 |
| **Exploratory analyses** (preregistered as exploratory, or post-hoc) | §3 |
| **Development evidence** (Phase 1 and p2val2) | §4 |
| **Platform and recovery deviations** | §6 |
| **Unsupported or inconclusive claims** | §7 |

---

## 1. What ran

| | |
|---|---|
| Cells | 18 (4 primary models × 4 decodings + 2 greedy-only secondary) |
| Rows | 3216 per cell; **57,888** total |
| Missing pairs / duplicates / harness errors / unparsable lines | **0 / 0 / 0 / 0** |
| Confirmatory analysis sample | 268 tasks, 135 families, 51,456 runs (primary cells only) |
| Mechanism | Evarb-0.2, frozen 2026-11-14; 14 code hashes identical across all 20 job starts |
| Data | eval3, sealed 2026-11-16; split hash `602eb748…` in every manifest |
| Preregistration | frozen 2026-11-17, hash `221013b3cee87c00` verified at every job start |
| Integrity | gates G1–G4 PASS (policy `g4-v2`); 54/54 raw checksums OK; seal OK; freeze OK |
| Cross-check | 60/60 counts and 4/4 primary differences agree exactly |

## 2. Preregistered confirmatory results

| Hypothesis | Contrast | Difference (pp) | 95% CI | p | Holm p | Verdict |
|---|---|---|---|---|---|---|
| H-primary | EBG − RT | **+17.1** | [12.2, 22.1] | 1 × 10⁻⁵ | 4 × 10⁻⁵ | **SUPPORTED** |
| S1 | EBG − T | **+14.5** | [10.5, 18.6] | 1 × 10⁻⁵ | 4 × 10⁻⁵ | **SUPPORTED** |
| S2 | EBG − LG | **+15.9** | [10.4, 21.2] | 1 × 10⁻⁵ | 4 × 10⁻⁵ | **SUPPORTED** |
| S3 | EBG − B | **+15.3** | [10.3, 20.5] | 1 × 10⁻⁵ | 4 × 10⁻⁵ | **SUPPORTED** |
| S4 | EBG − RT harmful | **−19.4** | [−24.6, −14.6] | 1 × 10⁻⁵ | — | **NOT FALSIFIED** |

Harmful answers: EBG 135/4288 (3.1%) against RT 968/4288 (22.6%). Arbitrary picks: EBG 13, RT 252.

Preregistered sensitivity analyses (§8 of the preregistration; all four contrasts keep their sign, every interval
excludes zero and every Holm-adjusted p stays below 0.05):

| Item set | Tasks | EBG − RT | EBG − T | EBG − LG | EBG − B |
|---|---|---|---|---|---|
| Primary (confirmatory) | 268 | +17.1 | +14.5 | +15.9 | +15.3 |
| Double-agreement subset | 161 | +14.3 | +12.7 | +19.7 | +14.7 |
| Flagged complement | 107 | +21.3 | +17.2 | +10.2 | +16.4 |
| Qwen2.5-14B-agreed subset | 232 | +15.3 | +13.9 | +15.5 | +14.8 |

**None of the preregistered falsification criteria was met.** The preregistration listed EBG − RT ≤ 0, EBG − LG ≤ 0
and EBG harmful rate > RT harmful rate as outcomes that would falsify the contribution; all three are contradicted.

## 3. Exploratory analyses — not confirmatory

### 3.1 Component ablations (preregistered as exploratory, BH-adjusted)

| Contrast | Difference (pp) | 95% CI | p (BH) | Harmful difference (pp) |
|---|---|---|---|---|
| EBG − EB (value of gating over labels alone) | +6.0 | [3.9, 8.2] | 2.2 × 10⁻⁵ | +0.5 |
| EB − G (value of evidence-basis labels over metadata labels) | +11.8 | [8.3, 15.2] | 2.2 × 10⁻⁵ | −5.2 |
| EB − T (over advisory temporal labels) | +8.5 | [5.4, 11.6] | 2.2 × 10⁻⁵ | −4.7 |
| EBG − R | +16.3 | [11.7, 21.0] | 2.2 × 10⁻⁵ | −12.9 |
| **EBG − EBG-all** (gated vs ungated enforcement) | **−9.7** | [−15.2, −4.3] | 0.0013 | −3.7 |
| EBG − EBG-unsafe (safe submission) | −0.2 | [−1.0, 0.7] | 0.776 | −0.2 |
| LG − LA (gating an LLM arbiter) | −2.4 | [−5.6, 0.6] | 0.167 | **+8.1** |

Two of these cut against the proposed design and are reported as prominently as the supportive ones.
**Ungated enforcement scored 9.7 pp higher than the gated mechanism** (71.1% vs 61.3%) while more than doubling harm
(6.9% vs 3.1%), restoring arbitrary picks from 13 to 166 and raising false resolution from 1.9% to 12.9%. Gating is
a trade, not a dominance, and this benchmark does not price it. **Gating an LLM arbiter gave no success gain and
8.1 pp more harm**, with 37.0% false resolution — the worst of any configuration.

### 3.2 Post-hoc platform sensitivity (specified after the platform transition came to light)

| Analysis | Rows | EBG − RT | EBG − T | EBG − LG | EBG − B |
|---|---|---|---|---|---|
| Confirmatory | 51,456 | +17.1 | +14.5 | +15.9 | +15.3 |
| Straddling cell `qwen3_8b_T07_s3` excluded | 48,240 | +17.0 | +14.4 | +15.9 | +15.3 |
| Qwen3-8B, three pre-reboot decodings only | 9,648 | +24.8 | +15.7 | +11.9 | +17.4 |

Removing the affected cell entirely moves the pooled estimates by at most 0.1 pp. See §7 for what this does **not**
establish.

### 3.3 Secondary cells (never pooled with the primary models)

Qwen2.5-14B: EBG − RT +29.9 [23.0, 36.9], the largest effect in the study.
Llama-3.2-3B (failed the preregistered readiness criterion before the campaign): EBG − RT +12.3 [6.3, 18.3], from a
very low base (41.8% success under EBG, 7.1% under B, 88.7% unnecessary abstention under B).

## 4. Development evidence — not evidence for the hypotheses

The Phase 1 pilot results (label-induced harm, M8/M9/M11) and the p2val2 observations (including Llama-3.1-8B's
+1.1 pp EBG − RT) motivated the design and the power analysis. They are not tests of the hypotheses and are not
counted toward any claim. They are reported in the manuscript's Sections 1 and 4.10, marked as development
evidence.

One development expectation was not borne out: p2val2 suggested Llama-3.1-8B would show no EBG benefit, and the
preregistration said a repeat would be reported as a failure to generalise across families. On eval3 the benefit is
small but positive with an interval excluding zero (+6.8 pp [3.3, 10.5]). The harm reduction, however, did not
transfer (−0.3 pp), for the reason given in §7.

## 5. Failure profile

Under EBG, 20.2% of runs report a false conflict and 11.5% abstain unnecessarily, against 3.1% harmful: the residual
failure is over-conservatism. Full account in `PHASE3_FAILURE_ANALYSIS.md` and `PHASE3_FAILURE_TABLES.md`.

## 6. Platform and recovery deviations

Full ledger: `PHASE3_DEVIATIONS.md` (D1–D7); investigation: `PHASE3_G4_FORENSIC_REPORT.md`; generated report:
`PHASE3_PLATFORM_CONTINUITY.md`.

- **D1.** The compute node rebooted at 2026-11-20T10:11:58, changing the host kernel (6.8.0-139 → 6.8.0-149,
  before: inferred) and the NVIDIA kernel driver (580.173.02 → 580.178.04, before: inferred). 980 of 57,888 rows
  (1.69%), in `qwen3_8b_T07_s3` (871) and `llama32_3b_greedy` (109), were produced on the new platform. Frozen code,
  model snapshots, decoding parameters and framework versions are hash-identical before and after. The split is
  balanced across the 12 configurations to within one row; exactly two tasks (`eval3-0202`, `eval3-0267`) have their
  own rows split across platforms.
- **D2.** The reboot truncated the row being written in each of those cells. Slurm requeued both jobs; both failed
  in the resume path on the truncated line; the controller quarantined the damaged tail (1153 and 3617 bytes, each
  containing zero complete rows) and resubmitted. Both cells completed to 3216 rows with no duplicates and no lost
  runs. The console logs of the two interrupted starts were overwritten by the requeue and are permanently lost.
- **D3.** `qwen3_8b_T07_s3` re-seeded its sampling stream on resume at row 2345. No bias; a reproducibility limit.
- **D4.** The G4 integrity gate was corrected from `g4-v1` to `g4-v2`: 18 strict client-identity fields, one
  declared observational field (`gpu_mem_gib`) excluded from identity comparison only and reported, and fail-closed
  on anything unclassified. The original validator is preserved verbatim and hash-checked by a test. No manifest,
  raw output, preregistration or Evarb-0.2 file was modified.
- **D5.** A reporting-only G5 platform-continuity check was added; it never fails the pipeline and feeds no
  statistic.
- **D6.** `pytest` was installed into the campaign venv after the campaign closed, for testing only.
- **D7.** The two exploratory analyses in §3.2 were added post-hoc and are labelled as such everywhere.

**No cell was re-run.** The preregistration permits a restart only for a freeze mismatch, a seal mismatch or a
runner defect (§10); none occurred, and all three hash checks passed at every job start.

## 7. Unsupported or inconclusive claims

Stated explicitly so that no reader takes them as established:

1. **That the platform transition was inert.** Unknown and unknowable from this campaign. No (task, config) pair
   exists on both driver versions — the quarantined fragments hold zero complete rows — so there is nothing to
   compare. The §3.2 analyses show the conclusions do not depend on the straddling cell; they do not show the
   driver change had no effect, and they say nothing about the two tasks whose rows are split within themselves.
2. **That the pre-reboot kernel and driver versions were 6.8.0-139 and 580.173.02.** Inferred from boot and package
   dates plus the recorded `nvidia-smi` mismatch, not read: the previous boot's kernel log is not readable from
   this account. One privileged command would settle it (`journalctl -b -1 -k | grep NVRM`).
3. **That gating is the right default.** The data show it costs 9.7 pp of success and saves 3.8 pp of harm and 153
   arbitrary picks. Success and harm are not commensurable here, and the benchmark prices neither.
4. **That the mechanism reduces harm across model families.** Demonstrated on the Qwen models (−24.5 to −27.7 pp).
   Not demonstrated on Llama-3.1-8B (−0.3 pp), whose dominant failures are abstention (44.0% under EBG) and
   malformed output (11.1%), and whose success gain comes from converting abstentions into answers.
5. **That safe submission improves success.** It does not (−0.2 pp, p = 0.78). It is retained for format
   robustness.
6. **That Evarb-0.2's residual false conflicts are the arbiter's fault.** 20.2% of EBG runs report a conflict where
   the evidence resolves; separating arbiter limitation from correct caution needs a transcript study, which the
   eval3 seal prevents until publication.
7. **That eval3 is a benchmark of record.** It is synthetic, model-written, model-annotated, English-only,
   ISO-dated, with no human validation. It was built to be sealed and preregistered against, nothing more.

## 8. Deliverables

In `research/AGENTRUN_PUBLICATION_2026/PHASE3/`:

| File | Content |
|---|---|
| `PHASE3_FINAL_REPORT.md` | this report |
| `PHASE3_STATUS.md` | current state of the phase |
| `PHASE3_EXECUTION_LOG.md` | per-cell execution record (generated) |
| `PHASE3_STATISTICAL_ANALYSIS.md` | full statistical tables (generated) |
| `PHASE3_COMPARISON_TABLES.md` | per-model, per-decoding, per-category comparisons (generated) |
| `PHASE3_ABLATION_RESULTS.md` | component ablations (generated) |
| `PHASE3_FAILURE_TABLES.md` | outcome tables by model and configuration (generated) |
| `PHASE3_FAILURE_ANALYSIS.md` | failure narrative |
| `PHASE3_DEVIATIONS.md` | deviation ledger D1–D7 |
| `PHASE3_G4_FORENSIC_REPORT.md` | the gate-failure investigation |
| `PHASE3_PLATFORM_CONTINUITY.md` | G5 report, verified / inferred / unknown (generated) |
| `PHASE3_DECISIONS.json` | machine-readable verdicts |
| `platform_evidence.json` | host evidence with epistemic status |
| `results/*.csv` | contrasts, metrics, per-model, per-decoding, per-category, execution |
| `ANALYSIS/*.json`, `ANALYSIS/*.md` | every analysis output, the cross-check and the test report |
| `PHASE3_SHA256_MANIFEST.txt` | SHA-256 of every output |
| `LIMITATIONS.md` | pre-results limitations (unchanged) |

Raw cells, sealed inputs and cluster logs stay on the cluster and in gitignored directories; their hashes are in the
manifest.
