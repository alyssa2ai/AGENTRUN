# AGENTRUN 2.0 -- Publication Source Package

This directory contains the complete, venue-neutral source package for
the AGENTRUN 2.0 manuscript.

## Contents

- `manuscript.tex`            -- master manuscript (non-anonymous).
- `manuscript_anonymous.tex`  -- anonymous review version. Identical to the
  master except for the `\author{}` block; regenerate it from the master
  (copy the file, then swap `\author{}`) rather than editing it separately.
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
- The Colab notebook at the repository root
  (`NEXTAGENTRUNV2final (2).ipynb`) is the raw session log for the E4 run.
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
