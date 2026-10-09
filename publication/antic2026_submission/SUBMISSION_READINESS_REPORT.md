# Submission Readiness Report — AGENTRUN for ANTIC 2026

Prepared 10 October 2026. Submission deadline: 15 October 2026.

**Verdict: the package is complete and builds cleanly. It is not yet ready to submit.** Two eligibility questions are unresolved: the prior preprint and the review mode. Several author-supplied statements also need your confirmation (Section 9).

## 1. Paper

| | |
|---|---|
| Title | *A Trace-Level Case Study of Fine-Tuning Regression and Evaluation-Stack Confounds in a Tool-Using 7B Language Model* |
| Running title | Fine-Tuning Regression and Evaluation-Stack Confounds |
| Author | Alyssa L, Dept. of ISE, Siddaganga Institute of Technology, Tumakuru, India (single author, as in all existing sources) |
| Category | **Full paper** (ANTIC: 12–15+ pages) |
| Length | 14 pages (llncs v2.24): 11.5 pages of text plus 2.5 of references; about 4,700 words before references, about 5,350 in total |
| Abstract | 218 words (limit 150–250) |
| References | 29, all cited |
| Figures / tables | 3 vector figures, 5 tables, 1 numbered equation |

## 2. Scientific framing

The paper is framed as a **trace-level case study**, not a method paper or a controlled ablation.

- **E4.** Stated explicitly (abstract, Sects. 3.4, 5, 6, 7) **not** to isolate the parser. It differs from V1 in:
  - the parser;
  - the client loop;
  - tool schemas, message serialisation and tool code;
  - possibly the task and scoring files, which were uploaded copies whose identity with the committed files was not recorded;
  - the run date, with live search and weather data.

  The V1→E4 transitions are reported as "parser + client" changes, with four candidate explanations. Figure 1 shows the differences between the two evaluation stacks, and Figures 2–3 mark E4 with a dagger and hatching.
- **V2.** Stated **not** to isolate a single cause. It changed the data (11 failure-informed trajectories, several of which share benchmark templates), the optimiser and memory settings, and probably library versions. Its 23/23 is described as closing identified gaps on this benchmark, not as evidence of better tool use in general.
- **Uncertainty.** N=1 per condition, so run-to-run variation is unmeasured. Wilson intervals and exact McNemar tests on the existing task outcomes show that no pairwise difference is significant at 5% (V1 vs V2: p = 0.0625). These statistics are computed from the committed outcomes; no new runs were made.
- **Corrections of earlier claims, stated in the paper.**
  - The parser-based explanation of the V1 regression is withdrawn. No recorded final answer contains unparsed tool-call markup.
  - The preprint's "adversarial_search_then_calc" parser failure refers to a task that does not exist; the closest task passed in V1.

## 3. What changed relative to the previous manuscript (`publication/manuscript.tex`)

- New title and framing. The "Disentangling Parser and Data Effects" claim is gone.
- Reformatted from the generic `article` class to Springer **llncs**, using the class and `.bst` files from the ANTIC-hosted template, copied unmodified.
- Failure analysis rebuilt from the V1 traces; the old per-task parser mechanisms are removed.
- New material:
  - predicate-strength audit (Table 1);
  - per-condition evaluation-stack description (Table 3, Fig. 1);
  - paired statistics (Table 4);
  - trace table (Table 5);
  - scoring-artifact findings: `multi_search_weather` answers are unchecked; V2's false-premise answer passes on "Marvel" alone.
- Related work rewritten as a critical survey of 29 verified references. Corrections to the old bibliography: AgentBench has 8 environments, not 11; Toolformer has 9 authors; Gorilla is cited at its published NeurIPS venue.
- Mandatory "Disclosure of Interests" section and an AI-use statement added in the `credits` environment.
- The historical `publication/manuscript.tex` and the preprint were **not** modified.

## 4. Experiments and results verified from source files

| Item | Verified against | Result |
|---|---|---|
| Base 22, V1 18, E4 18, V2 23 | `results/eval_results_*.json` (per-task tallies; SHA-256 recorded in `figures/data/results_snapshot.json`) | ✅ |
| V1→E4: +2/−2 (false_premise, three_tools / search_weather, chained_search_calc) | same | ✅ |
| E4→V2: +5/−0 | same | ✅ |
| Identical 23 task IDs in all conditions | same | ✅ |
| Base/V1/V2 on 2026-09-01 via `ft_agent.py` + MCP; E4 on 2026-09-16 via notebook loop | result-file timestamps; notebook cell 16 source and output | ✅ |
| E4 client differences (schemas, serialisation, tools, no re-parse) | notebook cell 16 source vs `ft_agent.py` | ✅ |
| E4 used uploaded copies of `tasks.py` and `harness.py` | notebook cells 10–15 | ✅; identity with committed files unknown |
| Other E4 run: 13/23 without a working search key | notebook cell 31 output | ✅ |
| V1 failure causes (calc skipped ×2, step budget, wording, no tool call) | V1 traces | ✅ |
| No recorded final answer contains tool-call markup (69 answers) | Base/V1/V2 traces | ✅ |
| 35 / 46 / 11 trajectories; prompt-level disjointness; shared templates | `training/*.jsonl`, `eval/tasks.py`, repository tests | ✅ |
| V1 vs V2 optimiser and gradient-checkpointing difference | both training scripts | ✅ |
| Predicate strength 15 / 7 / 1 | `eval/tasks.py` | ✅ |
| Client-matched E4 re-run | — | **not performed**; stated as future work |

## 5. Citations

All 29 entries were checked against arXiv, Crossref, the ACL Anthology, ICLR/TMLR/MLSys listings or Zenodo. Details are in `REFERENCE_VERIFICATION.md`. Unresolved: four entries are cited as arXiv preprints because no peer-reviewed version was found (τ-bench, FireAct, the lm-eval "Lessons" paper, and "Benchmark Cheater"). Check once more before the camera-ready.

## 6. Build and validation (actually run)

| Check | Result |
|---|---|
| `latexmk -pdf main.tex` (MiKTeX, pdfLaTeX + BibTeX) | ✅ exit 0, 14 pages |
| Undefined citations or references; missing files | ✅ none |
| BibTeX warnings | ✅ 0 |
| Overfull boxes | ✅ none |
| Underfull boxes | One `\vbox` (badness 2334) on the Figure 3 page while floats are placed. Inspected: no visible defect. |
| Type 3 fonts | ✅ none. All fonts are Type 1 (CM/EC via `cm-super`) or embedded TrueType (figures). `cm-super` was installed locally for this. |
| Template integrity | ✅ `llncs.cls` and `splncs04.bst` byte-identical to the ANTIC-hosted ZIP |
| Layout hacks (`\vspace`, `\enlargethispage`, size changes) | ✅ none. One table uses `\tabcolsep`/`@{}` column spacing; no global settings changed. |
| ZIP extracted to an empty directory and compiled there | ✅ exit 0, 14 pages, same warnings as above |
| Delivered PDF built from exactly the ZIP contents | ✅ the PDF is the build from the extracted ZIP; sources compared byte-for-byte |
| Every page visually inspected | ✅ all 14 pages of the final PDF rendered and inspected; earlier problems (Fig. 1 text overflow, Fig. 3 label collisions, cramped table columns, "word_-count" line breaks, rendering of pass^k) were found and fixed |
| Secrets or absolute paths in the ZIP | ✅ none (pattern scan) |
| Figures regenerate from the script and snapshot | ✅ |
| Repository tests still pass | ✅ unchanged; no code changes were made for this task |

## 7. Compliance summary

See `ANTIC_2026_AUTHOR_RULES_AND_CHECKLIST.md` for sources.

- **Satisfied:**
  - Springer llncs template; full-paper length; abstract and keywords.
  - Heading, caption, figure and table rules; vector figures with lettering ≥ 6 pt that are greyscale-safe.
  - No colour in text, tables or equations; editable tables and equations.
  - Numbered alphabetical citations with DOIs; alt text.
  - Disclosure of Interests section; corresponding-author e-mail; no layout changes.
- **Uncertain or unresolved:**
  - Eligibility given the prior preprint.
  - Review mode (blind or not).
  - Meteor fields and file types.
  - "MathPhySci" wording in Springer's instructions versus the template's `splncs04`.
  - Whether ANTIC 2026 will appear in CCIS; it is not in Springer's list dated 19 Aug 2026.
- **Not satisfied, needs you:**
  - Confirmation of the author name in full.
  - ORCID (recommended).
  - Confirmation of the competing-interests, AI-use and funding statements.

## 8. Remaining issues that could affect integrity or eligibility

1. **Prior Zenodo preprint (same Base/V1/V2 experiments).** ANTIC asks for "original and unpublished results", and Springer requires transparency about overlap. The text is new and the paper cites and corrects the preprint, but the organisers should be asked first. A draft inquiry is in `PREPRINT_OVERLAP_REVIEW.md`; it has not been sent.
2. **Review mode unknown.** If double-blind, the manuscript must be anonymised, and the Zenodo DOI still identifies the author.
3. **Exposed credentials in the public git history** (from the earlier repository audit). If they have not been rotated, the new commits should not be pushed. This package was committed locally only.
4. **Single-author statements.** The AI-use, competing-interest and funding statements are drafts taken from repository files and must reflect your actual situation.

## 9. Information needed from you

- Is "Alyssa L" the full name to print? Springer requires names in full; if "L" is an initial, give the full surname.
- Your ORCID, if you have one.
- Confirm or correct: "no competing interests"; the scope of AI assistance; any funding to acknowledge.
- Whether to send the organiser inquiry, and whether you will present in person in Lucknow (online presentation is allowed only for foreign authors).
- Whether the exposed ngrok and Tavily keys have been rotated, before anything is pushed.

## 10. Output paths

- Main source: `publication/antic2026_submission/overleaf/main.tex`
- Overleaf ZIP: `publication/antic2026_submission/AGENTRUN_ANTIC2026_Overleaf.zip`
- PDF: `publication/antic2026_submission/AGENTRUN_ANTIC2026_Submission.pdf`
- Rules checklist: `publication/antic2026_submission/ANTIC_2026_AUTHOR_RULES_AND_CHECKLIST.md`
- Reference report: `publication/antic2026_submission/REFERENCE_VERIFICATION.md`
- Preprint review and draft inquiry: `publication/antic2026_submission/PREPRINT_OVERLAP_REVIEW.md`
