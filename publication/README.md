# AGENTRUN 2.0 -- Publication Source Package

## Status (2026-10-09)

- **Published:** Zenodo preprint, 2026-09-05,
  doi:10.5281/zenodo.22346935 (concept DOI 10.5281/zenodo.22346934),
  *AGENTRUN: Failure-Driven QLoRA Specialization for Multi-Tool Agent
  Behavior in a 7B Language Model*. Not peer reviewed. Predates E4.
- **This directory:** the updated manuscript *Disentangling Parser and Data
  Effects in Tool-Using LLM Fine-Tuning*, which adds E4. It has not been
  published or peer reviewed, and is not currently submitted to any venue.
- **WI-IAT:** the submission was withdrawn on 2026-10-09.
  `cover_letter.md` and `submission_checklist.md` are generic,
  venue-neutral drafts kept for a future submission.
- **Correction applied 2026-10-09:** E4 is no longer described as a
  parser-only ablation, because the reported E4 score came from a
  notebook-local evaluation client (see `docs/e4-experiment-guide.md`). The
  failure analysis now follows the V1 traces, and the subtitle changed from
  "A Controlled Ablation" to "A Case Study". The main title
  ("Disentangling...") is unchanged and still needs an author decision.
- **Venue-specific work outstanding:** the manuscript uses the generic
  `article` class. Converting to a venue template (e.g. LNCS/CCIS
  `llncs` + `splncs04`) has not been done; see `venue_adaptation.md`.
  The current build has a few overfull boxes (largest about 43 pt, in a table).
  Posting this manuscript as a new Zenodo version is covered in
  `docs/release-checklist.md`.

This directory contains the complete, venue-neutral source package for
the AGENTRUN 2.0 manuscript.

## Contents

- `manuscript.tex`            -- master manuscript (non-anonymous).
- `manuscript_anonymous.tex`  -- anonymous review version. Identical to the
  master except for the `\author{}` block and the withheld repository URL in
  the artifact section; regenerate it from the master (copy the file, swap
  `\author{}`, replace the URL) rather than editing it separately.
- `references.bib`            -- BibTeX bibliography.
- `supplementary.tex`         -- supplementary material.
- `manuscript.pdf`, `manuscript_anonymous.pdf`, `supplementary.pdf`
                              -- compiled output, committed so a reader does
  not need a TeX installation. LaTeX build by-products (`*.aux`, `*.log`,
  `*.out`, `*.blg`, `*.bbl`) are not committed.
- Administrative docs: `cover_letter.md`, `data_availability.md`,
  `code_availability.md`, `ethics_statement.md`, `conflict_of_interest.md`,
  `funding_statement.md`, `author_contributions.md`,
  `ai_use_disclosure.md`, `submission_checklist.md`.
- `venue_adaptation.md`       -- how to adapt the master to specific venues.

## How to compile

From a terminal with `pdflatex` and `bibtex` installed:

    pdflatex manuscript.tex
    bibtex manuscript
    pdflatex manuscript.tex
    pdflatex manuscript.tex

That produces `manuscript.pdf`. Repeat with `manuscript_anonymous.tex`
for the anonymous version, and with `supplementary.tex` for the
supplementary PDF.

On Windows PowerShell:

    pdflatex manuscript.tex ; bibtex manuscript ; pdflatex manuscript.tex ; pdflatex manuscript.tex

## Figures

All figures are drawn inline with TikZ inside `manuscript.tex`.
There is no `figures/` directory and no external image assets. This is
deliberate: it makes the manuscript a single-file build and avoids
missing-figure errors. Required LaTeX packages: `geometry`, `times`,
`amsmath`, `amssymb`, `booktabs`, `graphicx`, `xcolor`, `tikz`,
`pgfplots`, `natbib`, `hyperref`.

## What must change for a specific venue

See `venue_adaptation.md`.

## What NOT to upload publicly

- Do not upload any file containing API keys, ngrok tokens, or Tavily
  keys. The manuscript and supplementary files do not contain any.
- The Colab notebook `notebooks/colab_e4_session.ipynb` (formerly
  `NEXTAGENTRUNV2final (2).ipynb` at the repository root) is the raw
  session log for the E4 run.
  Its live ngrok authtoken and Tavily API keys have been replaced with
  `REDACTED_*` placeholders in the committed copy. Because those values
  remain in the repository's git history, the corresponding keys should be
  rotated regardless of this redaction.

## Author-confirmation items

Before submitting, confirm:

1. ORCID.
2. Funding source (if any).
3. Whether any co-authors contributed.
4. Exact scope of generative-AI assistance used during preparation,
   so the AI-use disclosure can be filled in.
