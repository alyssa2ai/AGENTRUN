# Author information — to be completed by the authors before any submission

The submission build (`main.tex`) is **anonymous by design**. The TMLR style file hides authors unless the
`[accepted]` or `[preprint]` option is given, and the official template warns that non-anonymous submissions are
rejected without review. Nothing in `submission/` names a person, an institution, a funder or a grant.

This file is the single place where that information goes. **It is deliberately empty of invented content.**
Nothing below has been filled in from guesswork; every field needs your confirmation.

---

## 1. Required before submission

| Field | Value | Status |
|---|---|---|
| Author list and order | — | **you must supply** |
| Affiliations | — | **you must supply** |
| Corresponding author and e-mail | — | **you must supply** |
| ORCID for each author | — | **you must supply** (ARR requires this for all authors; TMLR requires complete OpenReview profiles) |
| Author contributions statement | — | **you must supply** |
| Acknowledgements | — | **you must supply, or omit** |
| Funding / grant numbers | — | **you must supply, or state none** |
| Competing interests | — | **you must supply, or state none** |
| IRB / human subjects | Not applicable: no human subjects, no human annotation, no user study | confirm |
| Compute disclosure | One 48 GB GPU; 18 cells; the per-cell wall-clock times are in `PHASE3/results/execution.csv` | confirm |

## 2. What the repository can support, if you want it in the paper

These are facts the artifacts establish. They are **not** in the manuscript, because they are organisational
rather than scientific, and because some of them would de-anonymise the submission.

- The campaign ran on a shared institutional GPU cluster, two L40-class GPUs, under a batch scheduler.
- Models were obtained from Hugging Face under their own licences (Qwen licence; Llama 3.1/3.2 community licence).
- The eval3 texts were produced by Qwen2.5-14B-Instruct, so that model's licence terms on outputs apply to them.

## 3. Anonymity checklist for the camera-ready switch

When the paper is accepted and you de-anonymise:

1. In `main.tex`, change `\usepackage{tmlr}` to `\usepackage[accepted]{tmlr}`.
2. Replace the placeholder `\author{...}` block with the real author block (see `main_preprint.tex` for the
   `\name / \email / \addr` syntax).
3. Fill `\def\month{}`, `\def\year{}` and `\def\openreview{}` with the values TMLR gives you.
4. Add the acknowledgements and funding sections, which are currently absent.
5. Re-run the privacy scan (`PUBLICATION_QA_REPORT.md`, gate P1) — de-anonymising must not reintroduce a host
   name or account identifier from an institutional address.

## 4. What must not be added

- No co-author who did not contribute.
- No acknowledgement, funder, grant, ethics approval or conflict-of-interest statement that has not been
  confirmed by the authors. None has been invented here, and none should be.
