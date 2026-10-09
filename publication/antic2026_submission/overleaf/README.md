# AGENTRUN — ANTIC 2026 manuscript (Overleaf project)

*A Trace-Level Case Study of Fine-Tuning Regression and Evaluation-Stack
Confounds in a Tool-Using 7B Language Model*

## Contents

| File | Purpose |
|---|---|
| `main.tex` | The manuscript (the only document in this project) |
| `references.bib` | Bibliography (BibTeX) |
| `llncs.cls`, `splncs04.bst` | Springer class v2.24 and bibliography style, copied unmodified from the ANTIC-hosted template (`https://antic.co.in/static/files/LaTeX2e-Template.zip`) |
| `figures/fig*.pdf` | Vector figures included by `main.tex` |
| `figures/src/make_figures.py` | Script that regenerates the figures |
| `figures/data/results_snapshot.json` | Data the figures are drawn from: per-task outcomes and traces extracted from the AGENTRUN result files, with their SHA-256 hashes |

## Import into Overleaf

1. In Overleaf, choose **New Project → Upload Project** and select
   `AGENTRUN_ANTIC2026_Overleaf.zip`.
2. If Overleaf does not pick the main file automatically, open **Menu → Main
   document** and select `main.tex`.
3. Set **Menu → Compiler** to **pdfLaTeX**. BibTeX runs automatically.
4. Click **Recompile**.

## Build locally

With a TeX distribution that includes `latexmk`, the `cm-super` fonts and the
`underscore`, `booktabs` and `hyperref` packages:

```
latexmk -pdf main.tex
```

or, without latexmk:

```
pdflatex main
bibtex main
pdflatex main
pdflatex main
```

If `cm-super` is missing, the PDF still builds but uses bitmap (Type 3)
fonts, which Springer asks authors to avoid. Overleaf has `cm-super`
installed.

## Regenerate the figures (optional)

```
python figures/src/make_figures.py
```

This needs Python 3 and matplotlib (tested with matplotlib 3.11). It writes
vector PDFs with TrueType fonts, not Type 3.

## Notes

- `\Description{...}` holds the alt text for each figure, as required by the
  Springer accessibility instructions. llncs v2.25 defines this command. The
  ANTIC-hosted v2.24 class used here does not, so `main.tex` provides a no-op
  fallback via `\providecommand`. The alt text stays in the source either
  way.
- Neither the class nor the bibliography style has been modified, and no
  spacing or page-size commands are used.
