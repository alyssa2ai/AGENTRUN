# Release checklist

Go through this list before tagging a release, posting a new preprint version, or submitting to a venue.

## Science

- [ ] `python results/verify_results.py` produces no diff. Base 22/23, V1 18/23, E4 18/23, V2 23/23.
- [ ] README, `publication/manuscript.tex`, `docs/experiment-log.md`, `provenance/experiment_provenance.json` and `results/experiment_summary.json` agree on all four scores and on the V1→E4 transitions (2 recovered, 2 regressed).
- [ ] V1→E4 is described as adapter-fixed with **both** the parser and the evaluation client changed. It is not described as a parser-only effect unless a client-matched E4 has been run with `evaluation/run_eval_e4.py`.
- [ ] The E4→V2 step is described as an iterative, failure-informed intervention that also changed the optimizer and memory settings. It is not described as an isolated data effect.
- [ ] Nothing claims generalization, state of the art, multiple seeds, confidence intervals, or a held-out evaluation beyond prompt-level disjointness.
- [ ] Every new experiment has committed artifacts. Proposed experiments are labelled as proposed.

## Software

- [ ] `ruff check .` and `python -m pytest` pass locally and in CI.
- [ ] The notebook is valid JSON and contains no credentials. CI checks this.
- [ ] Run a secret scan over tracked files, for example `gitleaks detect --no-git` or a targeted `git grep` for key prefixes.
- [ ] No absolute local paths and no files over a few MB, apart from the committed PDFs.

## Publication status

- [ ] Status wording is current everywhere: README "Publication status", `publication/README.md`, and `docs/experiment-log.md`.
- [ ] Venue claims (submitted, under review, accepted) are made only with evidence. The WI-IAT submission was withdrawn on 2026-10-09.

## Publishing a new Zenodo version (if the updated manuscript is posted)

The existing record (DOI `10.5281/zenodo.22346935`, 2026-09-05) is the published preprint. **Do not edit its files or metadata to represent the newer manuscript.**

1. On the existing Zenodo record, choose **New version**. Zenodo keeps both versions under the concept DOI `10.5281/zenodo.22346934` and assigns a new version DOI.
2. Upload the new PDF. Set the version, for example `v2`, and add a description of what changed, for example "adds E4 parser-only ablation; corrects V1/V2 optimizer description".
3. Once the new DOI exists, update `CITATION.cff`, the README citation block, and the profile README. Until then, cite the 2026-09-05 version.
