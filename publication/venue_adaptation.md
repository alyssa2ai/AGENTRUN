# Venue Adaptation Guide

This document explains what would change to submit the master
manuscript to each of four venue families. It does **not** claim that
the manuscript is currently compliant with any of them.

## IEEE conference (IEEEtran)

- Change document class to `\documentclass[conference]{IEEEtran}`.
- Replace the author block with `\author{\IEEEauthorblockN{...}\IEEEauthorblockA{...}}`.
- Replace `\bibliographystyle{plainnat}` with `\bibliographystyle{IEEEtranN}`.
- Add an IEEE-style index-terms line after the abstract.
- Ensure AI-use disclosure complies with the current IEEE policy.

## Springer / LNCS

- Change document class to `\documentclass[runningheads]{llncs}`.
- Replace `\maketitle` block with `\author{...}\institute{...}`.
- Bibliography style: `splncs04`.
- Abstract must be 150-250 words (currently approximately 230).

## Elsevier journal

- Change document class to `\documentclass[preprint,12pt]{elsarticle}`.
- Add a structured abstract if the target journal requires one.
- Add a CRediT author statement.
- Add a generative-AI-use disclosure per the current Elsevier policy.

## arXiv

- No formatting constraints. The manuscript as written is
  near-submittable as-is.

## ML/AI workshop (ICLR/NeurIPS/ACL workshop on agents or evaluation)

- Workshop templates vary; most provide their own `.sty` files.
- Add a broader-impact paragraph if required.
- Add a reproducibility checklist if required.

## General notes

- The master uses `natbib` with `plainnat`. If a target venue requires
  `biblatex`, the `references.bib` entries can be reused as-is.
- All figures are inline TikZ. If the venue requires a separate
  `figures/` directory, extract each TikZ block into its own `.tex`
  file, compile it with `standalone`, and include the resulting PDF.
