# Drafting notes (manuscript sections 1–6, results-independent)

**18 November 2026.** Files in this directory: `01_introduction.md`, `02_related_work.md`, `03_method_evarb.md`, `04_experimental_design.md`, `05_dataset.md`, `06_threats_and_limitations.md`, `references.bib`, this file. No existing file was edited.

**Integrity record.** No file under `PHASE3/SEALED_LOCAL/`, `PHASE3/RAW_RESULTS/`, `PHASE3/logs/` or `PHASE3/ANALYSIS/INTERIM/` was opened or listed, and no `eval3_*` file was read. The only eval3 information used is what `PHASE2/FREEZE_eval3.json` and the specification documents contain (counts, annotator agreement statistics, seal-check counts, hashes). No eval3 outcome, effect size or hypothesis verdict appears in the drafts. The preregistration hash in `FREEZE_eval3.json` (`221013b3…`) was re-computed from `PHASE2/PREREGISTRATION.md` and matches. The LF-normalised hash of `FREEZE_evarb.json` matches `provenance.freeze_evarb_sha256` (`5ae8ebe3…`).

## 1. Results placeholders

Each is written as `[RESULTS PENDING — filled from PHASE3 verified outputs]`.

| File | Location | What goes there |
|---|---|---|
| `01_introduction.md` | end of §1.5 | one-paragraph summary of confirmatory outcomes (H-primary, S1–S4), whatever their sign |
| `02_related_work.md` | §2.5, "What may be defensible" | whether basis-gated enforcement was useful; adjust the novelty paragraph to the outcome |
| `04_experimental_design.md` | §4.8, end | sensitivity results on the double-agreement subset (and the Qwen-agreed subset) |
| `04_experimental_design.md` | §4.11 | execution summary: cells completed, missing-pair counts per cell, re-submissions |
| `05_dataset.md` | end | nothing outcome-related; only if per-category descriptive tables are added |
| `06_threats_and_limitations.md` | header note | limitations revealed by the results (to be extended, never softened) |

## 2. Citation needs

| File | Marker | Notes |
|---|---|---|
| `02_related_work.md` §2.5 | `[CITATION NEEDED: a broader search of non-arXiv venues (ACL Anthology, OpenReview) and of work posted after 14 Nov 2026 before submission]` | The repository's literature search was arXiv-only (Semantic Scholar rate-limited; no web search). Most entries were checked at abstract level only; six were read in full (`PHASE1/RELATED_WORK_DEEP_DIVE.md`). Re-run before submission. |
| `04_experimental_design.md` §4.6 | `[CITATION NEEDED: Holm (1979) step-down procedure; Benjamini & Hochberg (1995) false discovery rate; a reference for the cluster/sign-flip permutation test and the cluster bootstrap]` | None of these is in the repository's literature files. |
| `05_dataset.md` §5.3 | `[CITATION NEEDED: Cohen (1960) for κ]` | Not in the repository literature files. (`docs/related_work.md` has Gwet 2008 and Feinstein & Cicchetti 1990 with DOIs, but those belong to the earlier fine-tuning study's agreement analysis and are not used here.) |

Additional places where a reviewer may ask for a citation, currently written without one:
- The agent backbones (Qwen2.5, Qwen3, Llama-3.1, Llama-3.2 model cards or reports): no bibliographic metadata in the repository. [CITATION NEEDED: model reports for Qwen2.5, Qwen3, Llama 3.1/3.2]
- "standard bitemporal practice" in §2.5 item 3 (`RELATED_WORK_DEEP_DIVE.md` calls it "decades-old bitemporal-database practice"). [CITATION NEEDED: a bitemporal database reference]
- ToolSandbox and AppWorld are named only as AMV-Guard's benchmarks; ToolSandbox has an entry in `docs/related_work.md` (arXiv 2408.04682) but with "Lu et al." only, so no full author list is available. Not cited.

## 3. References

- **27 entries** in `references.bib`, all confirmed against `literature/arxiv_metadata.json` (24 papers) or `literature/arxiv_title_search.json` (6 papers). All 27 are cited in the drafts. Three papers in the metadata are not cited: Kim & Koch (2611.09662), Helwig (2609.05510) and Wu & You (2610.24090); they are background only.
- Fields: `title`, `author`, `year` (first arXiv publication), `eprint` (arXiv id), `archivePrefix`. No DOI, venue or pages.
- **Kamoi et al.** has a TACL journal reference and DOI in the metadata (`10.1162/tacl_a_00713/125177`; `RELATED_WORK_AND_NOVELTY.md` gives `10.1162/tacl_a_00713`). The two DOI strings differ; neither was added. Check before adding a venue.
- **Venue comments** in the arXiv metadata (LongMemEval "ICLR 2025", Huang et al. "ICLR 2024", Pakhomov & Nijkamp "IAB workshop at NeurIPS 2026, non-archival") are author comments, not verified venues; not added.
- **FortMem** (Semantic Scholar only, unverified) is not cited, as `RELATED_WORK_AND_NOVELTY.md` instructs.
- Statements about papers read at **abstract level only** (all of §2.1–2.3 except DISCERN, PACMI, AMV-Guard, GPM, STALE, CICM): StateWise, PPMF, MemLineage, Zhao et al., Zhou et al., MEMOIR, TOKI, MemoryAgentBench, Pakhomov & Nijkamp, LongMemEval, LoCoMo, Xu et al. (Delivered), Pathirage & Srijomkwan, Zhang & Sun, Self-RAG, CRAG, Huang et al., Kamoi et al. Full texts should be checked before submission (`OPEN_ISSUES.md` #3 asked for this for the closest six; done for those).

## 4. Statements I was unsure of, or that rest on inference

1. **Phase 1 pilot numbers in the introduction** (Qwen2.5-7B same-day corrections 22/24 → 3/24; 5–6 of 6 conflicts turned into arbitrary picks under RT) are quoted as motivating development evidence, as the brief allows. They come from `PHASE1_FINAL_REPORT.md` and `FAILURE_TAXONOMY.md` §6.2–6.3. Decide whether to keep the numbers or describe the phenomenon qualitatively.
2. **Run totals** (3,216 runs per cell; 57,888 in all) are my arithmetic (268 × 12 × 18), not a figure from the documents. The execution plan's "≤ 46,368" predates Qwen3-8B. Replace with the verified count from the Phase 3 outputs.
3. **18 cells.** The preregistration lists four primary models × four decodings + two greedy-only models = 18; `LIMITATIONS.md` refers to cells 0–17. `PHASE3_EXECUTION_PLAN.md` (16 Nov) still lists 14 cells (no Qwen3-8B) and `PHASE2_FINAL_REPORT.md` §3 lists three primary models; both predate the addition. I did not state the cell-index-to-model mapping because no frozen document gives it for the 18-cell design.
4. **Execution note: cell 8.** `LIMITATIONS.md` says cells 9–17 ran up to two at a time and cells 0–7 ran alone; it does not say how cell 8 ran. Reproduced as written; check.
5. **Execution note: exposure of three eval3 outcome labels.** Reproduced from `LIMITATIONS.md` with an added sentence of interpretation ("after the freeze and with no possible effect on frozen materials"). Confirm the authors accept that wording.
6. **Families: 138 vs 135.** The specification gives 138 families (skeleton, before exclusion); the preregistration and `FREEZE_eval3.json`-based count give 135 families among the 268 valid tasks. I used 135 for analysis and explained 138 as the pre-exclusion figure. "Up to two items per family" in §6.4 follows from this.
7. **Cause of the 8 exclusions.** `LIMITATIONS.md` says long-form value dates; `BENCHMARK_EVAL3_SPEC.md` says the writer prompt required ISO value dates. Both are reported as stated; how the cause was established without reading the sealed items is not documented in the files I read.
8. **Seal-check counts** (`n_gold_texts` 552, `template_overlap_8gram` 280, `exact_masked_duplicates` 252, `duplicate_texts_within` 223) are reported with their field names because their precise denominators are defined in `seal_checks.py`, which I did not read. Check the definitions before interpreting them in prose.
9. **eval3 annotator statistics** (174/268, κ 0.471; 232/268, κ 0.767; 161 double-agreement, 107 flagged) are taken from `FREEZE_eval3.json`. They are annotation statistics, not outcomes. I reported them in §5.3 and §6.1. Confirm that the team is content to publish them before results.
10. **p2val2 name slice** [21200:22400] is taken from `benchmark/skeleton.py` (`SPLITS`), not from a specification document.
11. **Task attributes.** §3.2 lists example attributes (budget, staging port, team size, lead, cloud region, a deadline). Five are from `skeleton.py`; the sixth ("deadline") is inferred from `PHASE2_FINAL_REPORT.md` ("deadline items"). Check.
12. **Registry failures "by design"** (§3.2) is inferred from the Campaign 2 S6 tool-failure scenario in `FAILURE_TAXONOMY.md`; I did not verify that eval3 tasks include registry failures.
13. **Notice wording.** §3.4 says notices name the records and state the basis truthfully; checked against the notice strings in `evarb/policy.py`.
14. **"In-job preregistration check"** (§4.1) relies on `LIMITATIONS.md` ("in-job freeze, seal and pre-registration checks passed for every cell"). The sbatch file itself was not read.
15. **Phase 3 start** (Slurm array 4233, commit `d82155c`) is taken from the git log message, not from a document.
16. **Configuration table:** EB is listed with "safe submission —" although the code sets `safe=True` for EB; with no notices possible in EB, the flag has no effect. Same for LA.
17. **Composite contrast** (§3.7, §6.2): the observation that EBG − RT changes several elements at once is my analysis, not stated in the preregistration. It is a fair reading of Table 3.3 but should be confirmed by the authors.
18. **Llama-3.1-8B "9 format failures per configuration on p2val2"** is from `LIMITATIONS.md`; `PREREGISTRATION.md` §15 says "9 format failures" without "per configuration". Reproduced as in `LIMITATIONS.md`.
19. **Separation from the earlier study.** §6.7 contains the single permitted sentence about the earlier fine-tuning study. No other mention of it appears; nothing from `publication/antic2026_submission`, the V1 notebooks or E4 is used.
20. **`RESEARCH_CONTRIBUTION.md`** (13 Nov) frames the study as a capacity-resolved component ablation (H1–H7). That framing predates Phase 1 and Phase 2 and is superseded by the preregistered research question. I used it only for the novelty discipline in §2.5, not for hypotheses.
