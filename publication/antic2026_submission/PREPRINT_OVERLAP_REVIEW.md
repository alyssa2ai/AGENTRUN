# Preprint Overlap Review

## The existing preprint

| Field | Value (from the Zenodo API, record 22346935, read 2026-10-09) |
|---|---|
| Title | AGENTRUN: Failure-Driven QLoRA Specialization for Multi-Tool Agent Behavior in a 7B Language Model |
| Author | L, Alyssa |
| Type | Publication / preprint. Not peer reviewed. |
| Date | 2026-09-05 |
| DOI | 10.5281/zenodo.22346935 (version); concept DOI 10.5281/zenodo.22346934 |
| Licence | CC BY 4.0 |
| File | `AGENTICRUN_preprint.pdf`, 10 pages, about 4,200 words before references |

The record was only read; it was not modified. It predates the E4 run (2026-09-16).

## What overlaps and what is new

| Element | Preprint | ANTIC paper |
|---|---|---|
| Benchmark (23 tasks), tools, harness | described | described (same) |
| Base / V1 / V2 results (22 / 18 / 23) | reported | reported (same numbers, same runs) |
| Training setup, 35 and 46 trajectories | described | described, with the corrected V1/V2 optimiser difference |
| E4 (V1 adapter, two-pass parser) | not present (planned as future work) | reported, with the client/tool-stack confound |
| Evaluation-stack audit (notebook client vs `ft_agent.py`/MCP) | not present | new |
| Failure attribution | category (A) attributes a V1 failure to a parser defect on `adversarial_search_then_calc` | shows that this task name does not exist, that the closest task passed in V1, and that no recorded final answer contains unparsed tool-call markup; the attribution is withdrawn |
| Predicate-strength audit | not present | new (15 / 7 / 1 split; scoring artifacts) |
| Paired statistics (Wilson CIs, exact McNemar) | not present | new |
| Related work | 10 references | 29 references, all re-verified |
| Text | — | written from scratch: 0.7% of the new paper's 5-word sequences and 0.2% of its 8-word sequences also occur in the preprint (before references) |

**Assessment.** The text is new, and the framing and main conclusions differ from the preprint and correct it. However, the paper reports the **same Base, V1 and V2 experiments and numbers** as the preprint. A reviewer or Springer's plagiarism screening would rightly treat this as an extended and corrected version of previously posted work, not as entirely unpublished results.

## What the official sources say

- **ANTIC call for papers:** asks for "original and unpublished results" (https://antic.co.in/). It does not say whether a non-peer-reviewed preprint on a repository such as Zenodo or arXiv counts as publication.
- **Springer Nature Book Authors' Code of Conduct, "Originality":** work "should not have been published elsewhere in any form or language". It lists exceptions, including a "complete work that follows up on a published preliminary report", a work that "substantially re-analyses study findings or re-interprets results", and "a new iteration of the same work with some degree of change" (https://www.springernature.com/gp/authors/book-authors-code-of-conduct).
- **Same document, "Redundant publication":** "In case of overlap with a previously accepted / published paper transparency should be provided on how much is new … in a letter to the series editor and / or Publisher and consequently in the work itself."
- **Proceedings preprint policy:** no explicit preprint policy for Springer proceedings (CCIS/LNCS) was found on the official pages checked: the series' information-for-authors page, the Instructions for Authors PDF, and the Book Publishing Policies page. **Status: unresolved.**

## What has been done in the manuscript

- The preprint is cited ([12] in the PDF) in the introduction and in the failure-analysis correction. The manuscript states that the preprint was written before E4 and identifies which of its statements are withdrawn.
- The preprint is not described as peer reviewed or as a proceedings paper.

## Recommended action (needs your decision)

1. Before submitting, ask the organisers whether a prior non-peer-reviewed Zenodo preprint of an earlier version is acceptable. A draft is below. **Not sent.**
2. If the submission goes ahead, include a sentence in the Meteor submission comments (if there is a field for it) that discloses the preprint and summarises what is new.
3. Do not alter or delete the Zenodo record. If the new paper is accepted and the licence-to-publish permits it, consider posting a new Zenodo version only within whatever Springer allows. `docs/release-checklist.md` describes the versioning workflow.
4. Double-blind review is not stated on the ANTIC site. If the organisers say review is double-blind, the self-citation and the repository URL would need anonymising, and the Zenodo DOI would identify the author regardless.

## Draft inquiry to the organisers (not sent)

To: antic.bhu@gmail.com (the correspondence address listed on https://antic.co.in/)
Subject: ANTIC 2026: question about a prior preprint before submission

> Dear ANTIC 2026 organisers,
>
> I am preparing a submission to ANTIC 2026 and would like to check one eligibility point before the 15 October deadline.
>
> An earlier version of this work was posted as a non-peer-reviewed preprint on Zenodo on 5 September 2026 (doi:10.5281/zenodo.22346935). It has not been published in, or submitted to, any journal or proceedings. The planned ANTIC submission is a substantially rewritten and extended version. It adds a new experimental condition, an audit of the evaluation setup, a statistical analysis, and corrections to the preprint's failure attribution. It does reuse the same baseline and fine-tuning experiments reported in the preprint, and it cites the preprint explicitly.
>
> Is a submission with this relationship to a prior preprint acceptable for ANTIC 2026 and the CCIS proceedings? If so, is there anything specific you would like me to state in the submission?
>
> Thank you,
> Alyssa L
> Department of Information Science and Engineering, Siddaganga Institute of Technology, Tumakuru, India
