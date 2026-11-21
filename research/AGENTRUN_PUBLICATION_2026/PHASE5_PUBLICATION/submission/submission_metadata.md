# Submission metadata

Prepared for the TMLR OpenReview form. Fields marked **you** need the authors before anything is entered.

## Title

> Evidence-Basis Arbitration for Conflicting Persistent Memory in Small Tool-Using Agents: A Pre-registered
> Evaluation of Gated Enforcement

## Abstract

Use the abstract from `build/main.pdf` verbatim (source: `sections/00_abstract.tex`). It is a single block of
four paragraphs, about 350 words.

## Keywords

persistent memory for LLM agents; memory conflict resolution; evidence-basis arbitration; selective enforcement;
pre-registered evaluation; reliability and harmful answers; small open-weight models

## Primary subject area

Evaluation and benchmarking of language-model agents; reliability and trustworthy ML.

## Suggested action editors

**you** — TMLR asks authors to recommend action editors. Choose editors with evaluation-methodology or
agent-reliability expertise; do not list anyone with a conflict of interest.

## Authors, affiliations, ORCIDs

**you** — see `AUTHOR_INFORMATION.md`. All authors need complete OpenReview profiles.

## Conflicts of interest

**you**

## Human subjects / IRB

Not applicable: no human subjects, no human annotation, no user study. Confirm.

## Broader impact statement

Our judgement is that none is required: TMLR asks for one only where the work carries a significant risk of harm,
and this work measures the failure modes of a defensive mechanism and releases no capability uplift. The paper
nonetheless reports, prominently, that one configuration of the mechanism *increases* harmful answers, which is
the finding a deployer most needs. Confirm, and add a statement if you disagree.

## Supplementary material

`supplementary/supplementary.pdf` (9 pp), anonymised. Well under the 100 MB limit. Contains the complete result
tables, the benchmark and annotation protocol, the deviation record with the epistemic status of each fact, and
the reproduction instructions. It contains no evaluation task text, gold label, per-run transcript, credential or
infrastructure identifier.

## Code and data

- **Released with the paper:** mechanism, harness, runner, analysis, integrity gates, tests, frozen manifests, the
  pre-registration, development splits and runs, all aggregate results (JSON and CSV), and the reproducibility
  package with SHA-256 manifests.
- **Withheld until publication:** the eval3 items, their annotations, the per-run transcripts and the cluster
  logs, so the confirmatory set stays uncontaminated. Their hashes are public.
- **Not redistributed:** model weights; exact snapshot hashes are listed.

## Preprint / dual submission

The manuscript is original, is not an expanded version of a conference paper, and is not under review elsewhere.
Posting to a preprint server is permitted at any time, but the double-blind submission must not link to a version
naming the authors. **you** — decide whether to post.

## Declared relationship to other work by the same authors

A separate, earlier study in the same repository concerns parameter-efficient fine-tuning. It is unrelated, is
referenced in one sentence, and shares no text, figure or result with this paper.

## Reproducibility statement

Every reported number is produced by one batch job from the archived raw outputs; an independent re-implementation
recomputes the headline counts and effect sizes and must agree exactly or the pipeline stops. The limits of
reproduction — GPU non-determinism, two cells not produced on a single host platform, and one cell that re-seeded
its sampler on resume — are stated in §14.3 and Table 5.
