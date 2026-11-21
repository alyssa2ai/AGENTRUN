# Cover letter (draft)

> Draft for the authors to review and sign. TMLR submissions do not require a cover letter; this text is provided
> for the OpenReview submission note, for a desk-editor enquiry, or for re-use if the paper is sent to a venue
> that does require one. It contains no author or institution name.

---

Dear Editors,

We submit **"Evidence-Basis Arbitration for Conflicting Persistent Memory in Small Tool-Using Agents: A
Pre-registered Evaluation of Gated Enforcement"** for consideration at *Transactions on Machine Learning
Research*.

**What the paper does.** Agents with persistent memory must act on records that contradict each other. The usual
remedy — label records by reliability, derived from record metadata, and enforce those labels at the terminal
action — can make small models worse rather than better. We test an alternative in which the arbiter reports the
*evidence basis* for each resolution and the policy enforces only resolutions that basis supports. The mechanism,
the analysis and the hypotheses were frozen and pre-registered before the confirmatory data set existed. The
campaign ran 18 model × decoding cells over 12 conditions on 268 sealed tasks: 57,888 agent runs with no missing
pair, duplicate or harness error.

**Why TMLR.** Your acceptance criteria ask whether the claims are supported by accurate and convincing evidence,
and explicitly decline to reject work for not being novel enough or not setting a state of the art. That matters
here, because the most interesting result in the paper argues against our own design: removing the evidence gate,
so that every arbitration is enforced, scored 9.7 percentage points *higher* on task success while more than
doubling the harmful-answer rate and raising false resolution from 1.9% to 12.9%. We report that as prominently as
the four supported pre-registered contrasts, and we do not resolve the trade in our mechanism's favour, because
the benchmark assigns no relative cost to a wrong confident answer and a missed correct one. A venue selecting on
novelty would push us to bury that result; your criteria let us lead with it.

The paper also fits TMLR's stated scope in two further ways: it is an experimental study yielding insight into the
behaviour of a class of systems, and it formalises an evaluation task together with a method for assessing
performance on it.

**What we claim and what we do not.** We do not claim novelty for temporal ordering, bitemporal reasoning,
deterministic arbitration or gating in isolation; all are established, and we say so explicitly with citations.
The contribution is the measurement — of label-induced and enforcement-induced harm on small open-weight agents —
and a pre-registered test of whether basis-gated enforcement reduces that harm without losing the benefit of
enforcement. Our literature search covered arXiv and closed on 14 November 2026, with most entries read at
abstract level; we state in the paper that "we found none" should be read as "in the work we examined".

**Disclosures.** An unplanned compute-node reboot during the campaign changed the host kernel and GPU driver
partway through two of the eighteen cells, affecting 980 of 57,888 rows (1.69%). We disclose it in full, including
what it means and what cannot be established from it: removing the affected cell moves the pooled estimates by at
most 0.1 percentage points, but no task and condition was run on both platforms, so we cannot demonstrate the
driver change was inert, and we say so. The deviation ledger, the forensic record and a reporting-only
platform-continuity check are part of the artifact package.

**Artifacts.** Code, frozen manifests, the pre-registration, development data and runs, all aggregate results, and
a reproducibility package with SHA-256 manifests accompany the submission. The confirmatory evaluation items,
their annotations and the per-run transcripts are withheld until publication so that the test set stays
uncontaminated; their hashes are public so a later release can be verified against the frozen versions. The
supplementary material is anonymised and contains no evaluation text, credential or infrastructure identifier.

**Originality.** The manuscript is original and is not an expanded version of a conference paper. It does not
overlap with any other archival submission. A separate, earlier study in the same repository concerns
parameter-efficient fine-tuning and is unrelated; it is referenced in one sentence and shares no text, figure or
result with this paper.

We look forward to the reviewers' comments.

Sincerely,

*(authors)*
