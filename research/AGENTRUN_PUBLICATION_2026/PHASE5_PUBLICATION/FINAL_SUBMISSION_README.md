# Final submission package

**Nothing has been submitted.** No venue account was created, no manuscript was uploaded, no preprint was posted.
The venue recommendation in `VENUE_SELECTION.md` and the author fields in `submission/AUTHOR_INFORMATION.md` are
both waiting on you.

## What to open first

| | |
|---|---|
| The paper | `build/main.pdf` (30 pp, anonymous) |
| The supplement | `build/supplementary.pdf` (9 pp) |
| The non-anonymous build | `build/main_preprint.pdf` — placeholder authors; fill them in before use |
| Why this venue | `VENUE_SELECTION.md` |
| What was checked | `PUBLICATION_QA_REPORT.md` |
| What you must supply | `submission/AUTHOR_INFORMATION.md`, `submission/author_checklist.md` |

## Rebuilding the PDF

Requires a TeX distribution with `pdflatex` and `bibtex`. No shell-escape, no external image conversion and no
network access are needed: every figure is TikZ/PGFPlots compiled from the `.dat` files in `figures/data/`.

```bash
cd submission
pdflatex main && bibtex main && pdflatex main && pdflatex main
```

```bash
cd submission/supplementary && pdflatex supplementary && pdflatex supplementary
```

The non-anonymous build is `main_preprint.tex`, which is `main.tex` with `\usepackage[preprint]{tmlr}`. For the
camera-ready, switch `main.tex` to `\usepackage[accepted]{tmlr}` and fill in the author block.

## Regenerating the figure data and the supplement tables

Both read the verified Phase 3 outputs and overwrite the generated files in place. Run them if the analysis is
ever re-run; they are not needed to rebuild the PDF.

```bash
python figures_source/make_figure_data.py ../..
```

```bash
python figures_source/make_supplement_tables.py ../..
```

## Verifying the package

```bash
sha256sum -c SOURCE_MANIFEST.sha256
```

```bash
python tools/package_qa.py .
```

The second command re-runs every mechanical gate in `PUBLICATION_QA_REPORT.md`: the privacy scan, font embedding,
undefined references, overfull boxes, citation resolution and figure-data provenance. It exits non-zero if any
gate fails.

## Layout of the package

```
PHASE5_PUBLICATION/
├── VENUE_SELECTION.md            venue comparison, each fact sourced or marked unverified
├── PUBLICATION_QA_REPORT.md      every quality gate, PASS/FAIL with evidence
├── PRIVACY_SCRUB_REPORT.md       what was scrubbed repository-wide, and what was deliberately not
├── FINAL_SUBMISSION_README.md    this file
├── SOURCE_MANIFEST.sha256        hashes of everything shippable
├── submission/                   the LaTeX project
│   ├── main.tex                  anonymous build
│   ├── main_preprint.tex         non-anonymous build
│   ├── tmlr.sty, tmlr.bst, fancyhdr.sty    official template, unmodified
│   ├── references.bib            37 entries, all cited
│   ├── sections/                 17 section files
│   ├── figures/                  9 figure sources, palette, and data/ with provenance
│   ├── tables/                   8 table sources
│   ├── supplementary/            the supplement and its generated long tables
│   ├── cover_letter.md, author_checklist.md, submission_metadata.md
│   └── AUTHOR_INFORMATION.md     the only place author details go
├── figures_source/               generators that pull numbers from the analysis outputs
├── tools/                        QA, contact sheets, redaction, manifest rebuild
└── build/                        compiled PDFs and the page contact sheets used for review
```

## What is deliberately not here

- **Author, affiliation, funding, acknowledgement, ethics and conflict-of-interest text.** None was invented.
- **The eval3 items, annotations and per-run transcripts.** Restricted until publication; hashes are public.
- **Cluster host names, addresses and account identifiers.** Removed everywhere and checked by gate P1.
- **Any claim that the paper has been submitted or accepted anywhere.**
