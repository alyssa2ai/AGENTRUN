# AGENTRUN persistent-memory reliability study — final completion report

**Date:** 2026-11-21. **Branch:** `research/memory-ablation-2026-11` (local commits only; nothing pushed).
**Repository:** the HPC clone at `$HOME/AGENTRUN_HPC/finalize/AGENTRUN`, mirrored to the laptop checkout.

Phase 3 (confirmatory campaign and analysis) and Phase 4 (manuscript and reproducibility package) are complete.
This report states what exists, what was measured, what deviated, and what remains unresolved.

---

## 1. The experiment matrix

| Check | Result |
|---|---|
| Cells executed | **18 / 18** |
| Rows per cell | **3216 / 3216** (268 tasks × 12 configurations), every cell |
| Total rows | **57,888** |
| Unique (task, config) pairs | 3216 per cell; **0 duplicates** |
| Missing pairs | **0** |
| Harness-error rows | **0** |
| Unparsable lines | **0** |
| Final execution status | every cell `DONE`, last Slurm segment exit 0 |
| Quarantined partial fragments | 2, retained in place, **0 complete rows** in either |
| Raw-file checksums (`phase3_raw/SHA256SUMS`) | **54 / 54 OK** |
| Sealed eval3 checksums | **OK** |
| `FREEZE_evarb.json` file hashes | **0 mismatches** |
| Preregistration hash | `221013b3cee87c00`, verified at all 20 job starts |
| 14 frozen code hashes | **identical across all 20 manifest lines**; live files still match |
| Integrity gates G1–G4 | **PASS** (policy `g4-v2`), with 2 reported observational differences |

The four primary models contributed 16 cells (greedy plus three T = 0.7 seeds each); the two secondary models
contributed one greedy cell each. The confirmatory analysis uses the 16 primary cells: 268 tasks, 135 families,
51,456 scored runs.

**No cell was re-run.** The preregistration permits a restart only for a freeze mismatch, a seal mismatch or a
runner defect; none occurred.

---

## 2. G4 resolution

Finalization job 4270 stopped on 2026-11-20 at `STATE: FAILED (gates)` with two failures reading
*"manifest field `client` differs between starts"*, for `qwen3_8b_T07_s3` and `llama32_3b_greedy`.

**Cause.** The gate compared the manifest's `client` object as one opaque JSON blob. The only subfield that differs
anywhere in the campaign is `client.gpu_mem_gib`, 44.6 → 44.4 — the device total memory as the driver reports it,
read once in the client constructor and used only to write the manifest. The model is loaded with an explicit
device map and no memory budget, so the value cannot reach placement, batching or generation. All eighteen
identity-bearing client fields, the split hash, the configuration list and the 14 code hashes are identical across
both starts of both cells.

**Correction (`g4-v2`).** `client` is partitioned, closed by default:

- 18 **identity** fields (backend, family, family adapter, model, model path, adapter, adapter hash, temperature,
  seed, decoding, max new tokens, dtype, thinking, parser version, torch, transformers, CUDA, GPU) must be present
  in every start and equal across starts; a difference or absence fails the gate and prints the field path and the
  values;
- exactly one **observational** field, `gpu_mem_gib`, is excluded from the identity comparison only, retained and
  reported in `gates.json` and on stdout;
- any client key in neither set **fails** until explicitly classified, whether or not it differs.

The same policy is shared by `verify_phase3.py`, so the two validators cannot drift. The original validator is
preserved verbatim as `finalize_gates_v1_frozen.py` (sha256 `8c1870f0…`) and a test asserts it is unmodified. No
manifest, raw output, preregistration or Evarb-0.2 file was edited, replaced or regenerated, and the G4 check was
not removed or weakened.

**Tests** (`PHASE3/tests/test_finalize_gates_v2.py`, all passing): a `gpu_mem_gib`-only change passes and is
reported; a changed client adapter, parser version or framework version fails; an unknown field fails until
classified, including when identical across starts; missing client metadata fails; every identity field is
individually enforced; and against the real campaign, all 18 cells pass, exactly the two known cells report
telemetry, and the 16 single-start cells are untouched.

---

## 3. G5 platform-continuity disclosure

A reporting-only check (`platform_continuity.py`, `g5-v1`) derives per-cell start structure from the frozen
manifests, joins it with recorded host evidence, and separates facts by epistemic status. It always exits 0 and
feeds no statistical computation.

**Verified:** the node rebooted at 2026-11-20T10:11:58; it had been up since 2026-10-03; the post-reboot kernel is
6.8.0-149-generic and the NVIDIA module 580.178.04, loaded at 10:12:02; both L40s report identical memory, so device
identity cannot explain the change; `client.gpu_mem_gib` moved 44.6 → 44.4; the console logs of the two interrupted
starts were overwritten by Slurm's requeue; the quarantined fragments hold zero complete rows; the resumed sampled
cell re-seeds its random stream.

**Inferred:** the pre-reboot kernel (6.8.0-139-generic) and NVIDIA module (580.173.02), from boot and package dates
plus the recorded `nvidia-smi` driver/library mismatch of 2026-11-11 and its disappearance after the reboot. One
privileged command would settle it: `journalctl -b -1 -k | grep NVRM`.

**Unknown:** whether the two driver versions differ in generation behaviour, and the pre-reboot ECC, persistence and
firmware state. The first cannot be settled from this campaign — no (task, config) pair exists on both platforms.

**Scope:** 980 of 57,888 rows (**1.69%**), in `qwen3_8b_T07_s3` (871 of 3216) and `llama32_3b_greedy` (109 of 3216).
Because the runner iterates tasks outer and configurations inner, the post-reboot segments carry all 12
configurations for every whole task, balanced to within one row per configuration; exactly two tasks
(`eval3-0202` 5/7, `eval3-0267` 11/1) have their own rows split across platforms.

**Re-seeding:** `HFClient.__init__` seeds PyTorch once per process, so the resumed segment of `qwen3_8b_T07_s3`
restarted its sampling stream at row 2345 instead of continuing it. No bias — the design fixes the seeds and makes
no claim about stream continuity — but that cell is not byte-reproducible without reproducing the interruption.
`llama32_3b_greedy` is greedy and unaffected; no other cell was resumed.

---

## 4. Statistical outcomes

### Preregistered confirmatory results

| Hypothesis | Contrast | Difference | 95% CI | p | Holm-adjusted p | Verdict |
|---|---|---|---|---|---|---|
| H-primary | EBG − RT | **+17.1 pp** | [12.2, 22.1] | 1 × 10⁻⁵ | 4 × 10⁻⁵ | **SUPPORTED** |
| S1 | EBG − T | **+14.5 pp** | [10.5, 18.6] | 1 × 10⁻⁵ | 4 × 10⁻⁵ | **SUPPORTED** |
| S2 | EBG − LG | **+15.9 pp** | [10.4, 21.2] | 1 × 10⁻⁵ | 4 × 10⁻⁵ | **SUPPORTED** |
| S3 | EBG − B | **+15.3 pp** | [10.3, 20.5] | 1 × 10⁻⁵ | 4 × 10⁻⁵ | **SUPPORTED** |
| S4 | EBG − RT harmful | **−19.4 pp** | [−24.6, −14.6] | 1 × 10⁻⁵ | — | **NOT FALSIFIED** |

Two-sided sign-flip permutation on family-level summed differences, 100,000 seeded draws (floor 1 × 10⁻⁵);
95% percentile bootstrap over 135 families, 10,000 seeded resamples; Holm over the four primary contrasts at
α = 0.05. None of the three preregistered falsification criteria was met.

### Harmful-answer and abstention analysis

| Configuration | Success | Harmful | Arbitrary picks | Unnecessary abstention | False resolution | Conflict preserved |
|---|---|---|---|---|---|---|
| B | 46.0% | 7.0% | 172 | 19.5% | 12.8% | 65.2% |
| G | 43.5% | 7.9% | 109 | 16.0% | 9.2% | 72.8% |
| T | 46.9% | 7.4% | 35 | 16.9% | 3.6% | 79.6% |
| R | 45.0% | 16.1% | 153 | 9.4% | 12.3% | 74.2% |
| RT | 44.2% | **22.6%** | 252 | 11.1% | 19.0% | 66.8% |
| LA | 47.9% | 13.2% | 295 | 18.4% | 21.9% | 57.8% |
| LG | 45.4% | 21.3% | **510** | 17.1% | **37.0%** | 42.4% |
| EB | 55.3% | 2.7% | 13 | 16.7% | 2.0% | 81.6% |
| **EBG** | **61.3%** | **3.1%** | **13** | 12.8% | **1.9%** | **88.5%** |
| EBG-all | **71.1%** | 6.9% | 166 | 13.9% | 12.9% | 77.3% |
| EBG-unsafe | 61.5% | 3.3% | 12 | 9.9% | 1.6% | 89.0% |
| EBG-noR3 | 60.0% | 3.4% | 14 | 17.6% | 1.9% | 83.3% |

### Preregistered sensitivity analyses

| Item set | Tasks | EBG − RT | EBG − T | EBG − LG | EBG − B |
|---|---|---|---|---|---|
| Primary (confirmatory) | 268 | +17.1 | +14.5 | +15.9 | +15.3 |
| Double-agreement subset | 161 | +14.3 | +12.7 | +19.7 | +14.7 |
| Flagged complement | 107 | +21.3 | +17.2 | +10.2 | +16.4 |
| Qwen2.5-14B-agreed subset | 232 | +15.3 | +13.9 | +15.5 | +14.8 |

Every contrast keeps its sign, every interval excludes zero, every Holm-adjusted p stays below 0.05.

### Post-hoc exploratory sensitivity to the platform transition

| Analysis | Rows | EBG − RT | EBG − T | EBG − LG | EBG − B |
|---|---|---|---|---|---|
| Confirmatory | 51,456 | +17.1 | +14.5 | +15.9 | +15.3 |
| Straddling cell excluded | 48,240 | +17.0 | +14.4 | +15.9 | +15.3 |
| Qwen3-8B, pre-reboot decodings only | 9,648 | +24.8 | +15.7 | +11.9 | +17.4 |

Removing the affected cell moves the pooled estimates by at most 0.1 pp. This shows the conclusions do not depend on
that cell; it does **not** show the driver change was inert.

### Exploratory ablations (BH-adjusted)

| Contrast | Difference | 95% CI | p (BH) | Harmful difference |
|---|---|---|---|---|
| EB − G | +11.8 pp | [8.3, 15.2] | 2.2 × 10⁻⁵ | −5.2 pp |
| EB − T | +8.5 pp | [5.4, 11.6] | 2.2 × 10⁻⁵ | −4.7 pp |
| EBG − EB | +6.0 pp | [3.9, 8.2] | 2.2 × 10⁻⁵ | +0.5 pp |
| EBG − R | +16.3 pp | [11.7, 21.0] | 2.2 × 10⁻⁵ | −12.9 pp |
| **EBG − EBG-all** | **−9.7 pp** | [−15.2, −4.3] | 0.0013 | −3.7 pp |
| EBG − EBG-unsafe | −0.2 pp | [−1.0, 0.7] | 0.776 | −0.2 pp |
| LG − LA | −2.4 pp | [−5.6, 0.6] | 0.167 | **+8.1 pp** |

### Failure analysis

Under EBG, 20.2% of runs report a false conflict and 11.5% abstain unnecessarily, against 3.1% harmful, 2.8% stale
value, 2.8% format error, 1.0% step limit and 0.3% arbitrary picks. The residue is over-conservatism. Model
families fail differently: Llama-3.1-8B abstains on 44.0% of EBG runs and fails to format 11.1%, is the least
harmful model under every configuration, and so shows a harm difference of only −0.3 pp against −24.5 to −27.7 pp
for the three Qwen models.

### Independent cross-check

60 of 60 model × configuration counts and 4 of 4 pooled primary differences recomputed by a second route agree
exactly with the frozen analysis.

---

## 5. Deviations and limitations

`PHASE3/PHASE3_DEVIATIONS.md` holds the ledger D1–D7: the host platform transition (D1), the requeue, truncated
write and quarantine recovery with two console logs permanently lost (D2), re-seeding on resume (D3), the G4
correction (D4), the new G5 report (D5), `pytest` installed into the campaign venv after the campaign closed (D6),
and the two post-hoc exploratory analyses (D7). None changes the preregistered analysis.

Seven claims are explicitly **not** established, and are listed as such in `PHASE3_FINAL_REPORT.md` §7: that the
platform transition was inert; that the pre-reboot kernel and driver versions are known rather than inferred; that
gating is the right default; that harm reduction generalises to the Llama family; that safe submission improves
success; that EBG's residual false conflicts are the arbiter's fault; and that eval3 is a benchmark of record.

---

## 6. Manuscript

**Path:** `research/AGENTRUN_PUBLICATION_2026/PHASE4/manuscript/` — 16 section files plus `MANUSCRIPT.md`, the
assembled document (~20,600 words).

| § | File | State |
|---|---|---|
| Title, abstract | `00_title_and_abstract.md` | new |
| 1 Introduction, problem, motivation | `01_introduction.md` | preserved; results paragraph filled |
| 2 Related work, novelty | `02_related_work.md` | preserved; placeholder filled |
| 3 Architecture, Evarb-0.2, evidence-basis arbitration | `03_method_evarb.md` | preserved |
| 4 Experimental design | `04_experimental_design.md` | preserved; two placeholders filled |
| 5 Dataset and benchmark construction | `05_dataset.md` | preserved; placeholder filled |
| 6 Implementation | `06_implementation.md` | new |
| 7 Confirmatory results | `07_results.md` | new (over `07_results_AUTO.md`) |
| 8 Statistical analysis | `08_statistical_analysis.md` | new |
| 9 Ablation studies | `09_ablation_studies.md` | new |
| 10 Failure analysis | `10_failure_analysis.md` | new |
| 11 Platform and resume deviation analysis | `11_platform_and_resume_deviation.md` | new |
| 12 Discussion | `12_discussion.md` | new |
| 13 Threats to validity and limitations | `13_threats_and_limitations.md` | preserved; renumbered from 6; §13.8 added |
| 14 Reproducibility and artifact availability | `14_reproducibility.md` | new |
| 15 Conclusion and future work | `15_conclusion.md` | new |

**Citations:** `scripts/assemble_manuscript.py` writes `CITATION_CHECK.md` — **37 bibliography entries, 37 cited,
0 undefined, 0 uncited, 0 `[CITATION NEEDED]`, 0 `[RESULTS PENDING]`**. The bibliography verified in `56b17f3`
(Crossref / arXiv / JSTOR) is preserved unchanged; no reference was added, removed or invented, and no further
literature search was run.

**Interpretation.** The four preregistered contrasts are supported and S4 is not falsified, and the manuscript says
so; it gives equal weight to the results that cut against the design — ungated enforcement scoring 9.7 pp higher at
more than double the harm, gating an LLM arbiter producing no gain and 8.1 pp more harm, most of the benefit lying
in the labels rather than the enforcement, the 61.3% absolute ceiling, and the Llama family gaining through a
different mechanism. p2val2 and the Phase 1 pilot are marked throughout as development evidence. The earlier QLoRA
specialization study is referenced in exactly one sentence and is otherwise kept separate.

---

## 7. Reproducibility package

**Path:** `research/AGENTRUN_PUBLICATION_2026/PHASE4/reproducibility/` — 29 files, all hashed in `SHA256SUMS`
(verified 29/29), with `SHA256SUMS_SOURCES` giving the repository originals each copy was made from.

Environment and dependencies, model identifiers and snapshot hashes, dataset access and restriction rules, frozen
configurations (byte-identical copies, verified), Slurm scripts and analysis scripts (host identifiers redacted),
analysis instructions, expected outputs, test instructions, limitations and failure modes, and a new `DEVIATIONS.md`
pointing at the Phase 3 ledger with the three consequences a reproducer needs.

**Public versus restricted.** Code, frozen manifests, the preregistration, development splits and their runs,
aggregate results and the package itself are shareable. The eval3 items, annotations, per-run transcripts and
cluster logs are **restricted** until publication; model weights are not redistributed. Nothing in the package
claims availability for a restricted artifact.

**Redaction.** The package contains no credentials, tokens, keys, IP addresses, host names or user identifiers; a
check in `build_repro_manifest.py` fails if any appear. See §9 for the wider repository.

---

## 8. Tests and manifests

| Suite / check | Result |
|---|---|
| Phase 2 mechanism suite, campaign source tree | **92 passed** |
| Phase 2 mechanism suite, HPC clone (minus `test_clients.py`) | **88 passed** |
| `tests/test_clients.py` in the clone | **collection error**: `agentrun_v2` is untracked and absent from the clone; the same suite passes in the campaign tree where the package exists. Reported, not omitted — `PHASE3/ANALYSIS/TEST_REPORT.md` |
| Phase 3 suite (pipeline + G4 + G5) | **28 passed** |
| Integrity gates G1–G4 | **PASS** |
| `verify_phase3.py` | **no integrity problems** |
| Raw checksums / seal / freeze / preregistration | **OK / OK / OK / OK** |
| Independent cross-check | **all values agree** |
| Citation and placeholder check | **PASS** |
| `PHASE3_SHA256_MANIFEST.txt` | 153 lines: raw cells, sealed inputs, every analysis output, every script, every test, every report, every manuscript file, the reproducibility manifest |
| `reproducibility/SHA256SUMS` | 29/29 verified |

---

## 9. Remaining unresolved issues

1. **Cluster identifiers elsewhere in the repository.** The reproducibility package and the Phase 3 reports are
   clean, but roughly nineteen pre-existing files under `research/` (audit reports, earlier execution logs, the
   interview dossier, `PHASE1/HPC_RESOURCE_SHARING.md`, `PHASE2/scripts/finish_phase2.sh`) still contain the
   cluster's private IP addresses and account name. They predate this work and were not rewritten. **They must be
   scrubbed before any public release.**
2. **The pre-reboot kernel and driver versions are inferred.** One privileged command on the node would convert
   them to verified facts.
3. **Whether the driver change altered generation is unknowable from this campaign.** It would need a dedicated
   determinism experiment on both driver versions, outside this study's scope.
4. **Two cells are not byte-reproducible** (platform straddle; plus re-seeding in one). The analysis remains byte-
   reproducible from the archived raw outputs.
5. **No transcript-level failure study.** eval3 stays sealed until publication, so EBG's 20.2% false conflicts
   cannot yet be separated into arbiter limitation and correct caution.
6. **`agentrun_v2` is untracked**, which is why one test file cannot run in a fresh clone. Tracking it or adding it
   to the requirements would fix this; not done here, to avoid changing tracked content after the freeze.
7. **Nothing is pushed.** All commits are local to `research/memory-ablation-2026-11` on the cluster clone and the
   laptop checkout, as instructed. Keys noted in earlier sessions as present in public git history remain the
   user's to rotate; nothing in this work touched them.

---

## 10. Local commits

| Commit | Content |
|---|---|
| `e39febc` | Phase 3 G4 resolution (`g4-v2`), reporting-only G5 platform report, deviations ledger, tests |
| `39d69b0` | Phase 3 confirmatory analysis (written by HPC finalization job 4359) |
| `b47c09d` | Phase 3 final reports, failure analysis, test report, regenerated manifest |
| `3cb393f` | Phase 4 manuscript complete |
| *(this commit)* | Reproducibility package finalized and this completion report |

Branch `research/memory-ablation-2026-11`; no push, no force, no history rewrite, no destructive git operation.
Earlier commits, raw data, logs and frozen artefacts are untouched.

**Slurm jobs run today:** 4356 and 4357 (cancelled before starting, resource fit), 4358 (failed at `verify`, the
same blob comparison in the second validator), **4359 (complete)**.
